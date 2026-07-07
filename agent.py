"""Study Agent implementation for RAG, flashcard generation, and oral evaluations."""

import asyncio
import json
import re
from typing import Any

from core.graph import graph_db
from core.observability.logging import get_logger
from core.services.llm import get_llm_service

from .persistence import StudyDAO

logger = get_logger(__name__)


def _parse_llm_json(response: str) -> Any:
    """Strip an optional markdown code fence and parse the LLM's JSON output."""
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(json)?\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
    return json.loads(cleaned.strip())


class StudyAgent:
    """
    Coordinative agent that handles tutoring queries, flashcard generation,
    and simulated oral exam questioning and evaluation.
    """

    name = "study-agent"

    def __init__(self, service: Any = None):
        """Initialize StudyAgent using LLMService."""
        self.llm_service = service or get_llm_service()

    async def answer_study_query(self, subject_id: int, query: str) -> dict[str, Any]:
        """
        Answer a student question about homework or concepts using RAG over subject materials.
        """
        # 1. Retrieve subject details
        subjects = await StudyDAO.get_subjects()
        subject = next((s for s in subjects if s["id"] == subject_id), None)
        subject_name = subject["name"] if subject else "Generale"

        # 2. Retrieve documents and find matching text (RAG context)
        docs = await StudyDAO.get_documents(subject_id)
        context_parts = []
        matched_doc_names = []

        # Simple RAG: load matching document content
        for doc in docs:
            full_doc = await StudyDAO.get_document(doc["id"])
            if full_doc and full_doc.get("raw_text"):
                # Simple keyword filtering
                raw_text = full_doc["raw_text"]
                words = re.findall(r"\w+", query.lower())

                # Check for word occurrences to select matching paragraphs
                paragraphs = raw_text.split("\n\n")
                doc_matched = False
                for para in paragraphs:
                    if len(para.strip()) < 20:
                        continue
                    # Match if any query word appears
                    matches = sum(1 for w in words if w in para.lower())
                    if matches > 0:
                        context_parts.append(para.strip())
                        doc_matched = True
                        if len(context_parts) >= 8:  # Limit context
                            break
                if doc_matched:
                    matched_doc_names.append(doc["name"])
            if len(context_parts) >= 8:
                break

        context = (
            "\n\n---\n\n".join(context_parts)
            if context_parts
            else "Nessun documento di supporto trovato."
        )

        # Graph RAG query if enabled
        graph_context = ""
        keywords = []
        cypher = ""
        matched_concepts = []
        matched_relations = []

        if graph_db.is_enabled():
            try:
                words = re.findall(r"\w+", query.lower())
                keywords = [w for w in words if len(w) > 3]

                # Fetch all concepts and relationships for this subject in the graph database
                cypher = (
                    "MATCH (c:study_concept {subject_id: $subject_id}) "
                    "OPTIONAL MATCH (c)-[r]->(other:study_concept {subject_id: $subject_id}) "
                    "RETURN c.name, c.definition, type(r), r.description, other.name"
                )
                results = graph_db.query(cypher, {"subject_id": subject_id})

                # RedisGraph compact format parsing
                if results and len(results) > 1:
                    data_rows = results[1]
                    for row in data_rows:
                        if isinstance(row, list) and len(row) >= 2:
                            c_name = row[0]
                            c_def = row[1]
                            r_type = row[2] if len(row) > 2 else None
                            r_desc = row[3] if len(row) > 3 else None
                            other_name = row[4] if len(row) > 4 else None

                            matches = (
                                any(kw in str(c_name).lower() for kw in keywords)
                                if keywords
                                else True
                            )
                            if matches:
                                if (
                                    c_def
                                    and f"{c_name}: {c_def}" not in matched_concepts
                                ):
                                    matched_concepts.append(f"{c_name}: {c_def}")
                                if r_type and other_name:
                                    rel_str = f"- {c_name} --[{r_type}: {r_desc or ''}]--> {other_name}"
                                    if rel_str not in matched_relations:
                                        matched_relations.append(rel_str)

                if matched_concepts or matched_relations:
                    graph_parts = []
                    if matched_concepts:
                        graph_parts.append(
                            "CONCETTI CHIAVE RILEVATI:\n" + "\n".join(matched_concepts)
                        )
                    if matched_relations:
                        graph_parts.append(
                            "RELAZIONI LOGICHE RILEVATE:\n"
                            + "\n".join(matched_relations)
                        )
                    graph_context = "\n\n".join(graph_parts)
            except Exception as g_err:
                logger.warning(f"Failed to retrieve Graph RAG context: {g_err}")

        # 3. Ask LLM
        graph_rag_section = (
            ("CONTESTO STRUTTURATO (GRAPH RAG):\n" + graph_context)
            if graph_context
            else ""
        )
        prompt = f"""Sei un assistente universitario esperto nella materia '{subject_name}'.
Il tuo scopo è supportare lo studente nello studio, nello svolgimento di esercizi e nel chiarimento di dubbi teorici.

CONTESTO DIDATTICO DISPONIBILE:
{context}

{graph_rag_section}

DOMANDA DELLO STUDENTE:
{query}

Fornisci una risposta estremamente chiara, esaustiva, didattica e precisa. Se ci sono formule o passaggi matematici, mostrali passo dopo passo.
Rispondi in italiano in formato Markdown."""

        response = await self.llm_service.generate_response(prompt)

        # Log Graph RAG search to DebugTracker
        try:
            from .debug_tracker import DebugTracker

            DebugTracker.add_event(
                "graph_rag",
                {
                    "query": query,
                    "keywords": keywords,
                    "cypher": cypher,
                    "db_enabled": graph_db.is_enabled(),
                    "matched_concepts": matched_concepts,
                    "matched_relations": matched_relations,
                    "standard_context_len": len(context),
                    "graph_context_len": len(graph_context),
                    "prompt_len": len(prompt),
                    "response_len": len(response),
                },
            )
        except Exception as d_err:
            logger.error(f"Failed to log debug event for Graph RAG: {d_err}")

        return {"answer": response, "sources_used": matched_doc_names}

    async def generate_flashcards(
        self, subject_id: int, num_flashcards: int = 10
    ) -> list[dict[str, str]]:
        """
        Generate flashcards automatically from subject documents.
        """
        docs = await StudyDAO.get_documents(subject_id)
        if not docs:
            return []

        # Read text from all documents up to a limit to generate flashcards
        combined_text = ""
        for d in docs:
            full_doc = await StudyDAO.get_document(d["id"])
            if full_doc and full_doc.get("raw_text"):
                combined_text += (
                    f"\n--- Documento: {d['name']} ---\n" + full_doc["raw_text"]
                )
                if len(combined_text) > 8000:  # Limit size sent to LLM
                    break

        if not combined_text.strip():
            return []

        prompt = f"""Sei un assistente didattico. Genera una lista di {num_flashcards} flashcard di studio (domande e risposte) a partire dal seguente materiale universitario.
Le domande devono focalizzarsi su concetti chiave, definizioni importanti, teoremi, formule o applicazioni pratiche essenziali per superare l'esame.

MATERIALE DIDATTICO:
{combined_text[:8000]}

Devi rispondere ESCLUSIVAMENTE con un array JSON valido, senza preamboli, commenti o blocchi di codice markdown.
Ciascun elemento dell'array deve essere un oggetto con le chiavi "question" e "answer".

Esempio di output:
[
  {{"question": "Qual è il teorema fondamentale del calcolo integrale?", "answer": "Il teorema stabilisce che se f è continua in [a,b], allora la funzione integrale F(x) è derivabile e F'(x) = f(x)."}}
]"""

        try:
            response = await self.llm_service.generate_response(prompt)
            cards = _parse_llm_json(response)
            return [{"question": c["question"], "answer": c["answer"]} for c in cards]
        except Exception as e:
            logger.error(f"Failed to generate flashcards via LLM: {e}")
            return []

    async def formulate_oral_question(
        self,
        subject_name: str,
        topic: str,
        style: str,
        strictness: str,
        difficulty: int,
        context_docs: list[dict[str, Any]],
    ) -> str:
        """
        Generate a natural question phrased in the persona of the professor.
        """
        # Load context matching topic if any
        context_text = ""
        for doc in context_docs:
            if doc.get("raw_text") and topic.lower() in doc["raw_text"].lower():
                context_text += doc["raw_text"][:2000]
                break

        strictness_descr = {
            "amichevole": "amichevole, incoraggiante, empatico, tollerante, che cerca di guidare lo studente e metterlo a suo agio",
            "equo": "equo, professionale, oggettivo, chiaro, bilanciato",
            "scrupoloso": "esigente, estremamente preciso, formale, rigoroso, attento ai dettagli e alle definizioni esatte",
        }.get(strictness, "equo")

        style_descr = {
            "theory": "una domanda teorica di definizione o spiegazione di un teorema/concetto",
            "application": "un esercizio pratico o una richiesta di applicazione di un concetto a un caso specifico",
            "trick": "una domanda trabocchetto, un caso limite (es. cosa succede se salta un'ipotesi del teorema) o un dettaglio minuzioso",
            "hint": "un suggerimento costruttivo per aiutare lo studente che ha avuto difficoltà con la domanda precedente",
        }.get(style, "theory")

        prompt = f"""Sei un professore universitario di nome 'Professore'. Insegni la materia '{subject_name}'.
Il tuo profilo caratteriale è: {strictness_descr}.
Il livello di difficoltà dell'esame è: {difficulty}/5.

MATERIALE DELLA MATERIA SULL'ARGOMENTO '{topic}' (se disponibile):
{context_text[:1500]}

Compito: Formula {style_descr} sull'argomento '{topic}'.
La domanda deve essere in italiano, naturale e discorsiva come in un vero colloquio d'esame orale. Non aggiungere spiegazioni o testo al di fuori delle parole pronunciate dal professore.

Rispondi solo con le parole del professore, racchiuse tra virgolette o dirette."""

        response = await self.llm_service.generate_response(prompt)
        return response.strip().strip('"').strip("«").strip("»")

    async def evaluate_oral_answer(
        self,
        subject_name: str,
        topic: str,
        question: str,
        answer: str,
        strictness: str,
        difficulty: int,
    ) -> dict[str, Any]:
        """
        Evaluate the student's answer in the persona of the professor.
        """
        strictness_descr = {
            "amichevole": "Prof. Amichevole: incoraggiante, apprezza lo sforzo, valuta con manica larga (se l'idea è corretta dà la sufficienza), consiglia e corregge dolcemente.",
            "equo": "Prof. Equo: oggettivo, standard accademico, valuta la precisione tecnica e la completezza in modo bilanciato.",
            "scrupoloso": "Prof. Scrupoloso: severo, esigente, toglie punti per imprecisioni terminologiche, richiede rigore formale, non si accontenta di concetti vaghi.",
        }.get(strictness, "equo")

        prompt = f"""Sei un professore universitario che insegna '{subject_name}'.
Stai valutando una risposta all'esame orale.
Il tuo stile di valutazione è: {strictness_descr}
Difficoltà impostata: {difficulty}/5

DOMANDA FATTA:
"{question}" (sull'argomento '{topic}')

RISPOSTA DELLO STUDENTE:
"{answer}"

Valuta la risposta dello studente. Devi restituire un oggetto JSON contenente tre chiavi:
1. "score": un voto numerico da 0.0 a 10.0 (dove 6.0 è la sufficienza).
2. "feedback": un breve commento del professore in italiano in cui spiega cosa è andato bene, cosa manca o cosa è errato, parlando direttamente allo studente (es. "Hai risposto bene alla prima parte ma...").
3. "is_correct": booleano (true se il voto è >= 6.0, altrimenti false).

Devi rispondere ESCLUSIVAMENTE con l'oggetto JSON, senza commenti esterni o markdown format blocks."""

        try:
            response = await self.llm_service.generate_response(prompt)
            result = _parse_llm_json(response)
            score = float(result["score"])
            return {
                "score": score,
                "feedback": result.get("feedback", ""),
                "is_correct": bool(result.get("is_correct", score >= 6.0)),
            }
        except Exception as e:
            logger.error(f"Failed to evaluate student oral answer via LLM: {e}")
            return {
                "score": 5.0,
                "feedback": "Errore nella valutazione della risposta. Per favore ripeti.",
                "is_correct": False,
            }

    async def select_feynman_concept(self, subject_id: int) -> str:
        """
        Dynamically suggest a difficult concept to study using Feynman technique based on uploaded docs.
        """
        subjects = await StudyDAO.get_subjects()
        subject = next((s for s in subjects if s["id"] == subject_id), None)
        subject_name = subject["name"] if subject else "Generale"

        docs = await StudyDAO.get_documents(subject_id)
        if not docs:
            return "Concetto Generale"

        combined_text = ""
        for d in docs:
            full_doc = await StudyDAO.get_document(d["id"])
            if full_doc and full_doc.get("raw_text"):
                combined_text += full_doc["raw_text"][:2000]
                if len(combined_text) > 4000:
                    break

        prompt = f"""Sei un assistente universitario esperto della materia '{subject_name}'. 
Analizza il seguente estratto dei materiali di studio e individua un SINGOLO concetto teorico importante, complesso o tipicamente ostico per gli studenti (ad esempio: 'Il teorema delle contrazioni', 'La memoria virtuale', 'Le equazioni di Maxwell', ecc.).

MATERIALE:
{combined_text[:4000]}

Rispondi ESCLUSIVAMENTE con il nome del concetto (2-6 parole), senza prefazioni, virgolette o spiegazioni."""

        try:
            concept = await self.llm_service.generate_response(prompt)
            return concept.strip().strip('"').strip("«").strip("»")
        except Exception as e:
            logger.error(f"Failed to extract Feynman concept: {e}")
            return "Concetto Fondamentale"

    async def evaluate_feynman_step(
        self,
        subject_id: int,
        concept_name: str,
        explanation: str,
        history: list[dict[str, str]],
    ) -> dict[str, Any]:
        """
        Analyze student's Feynman explanation, listing strengths, gaps, errors, a simple analogy, and a follow-up question.
        """
        subjects = await StudyDAO.get_subjects()
        subject = next((s for s in subjects if s["id"] == subject_id), None)
        subject_name = subject["name"] if subject else "Generale"

        # Gather context
        docs = await StudyDAO.get_documents(subject_id)
        context_text = ""
        for d in docs:
            full_doc = await StudyDAO.get_document(d["id"])
            if full_doc and full_doc.get("raw_text"):
                context_text += full_doc["raw_text"][:2000]
                if len(context_text) > 4000:
                    break

        history_str = ""
        for h in history:
            role = "Tutor" if h.get("role") == "assistant" else "Studente"
            history_str += f"{role}: {h.get('text')}\n"

        prompt = f"""Sei un tutor didattico universitario. Stai aiutando lo studente a capire '{concept_name}' (materia: '{subject_name}') usando la Tecnica di Feynman (spiegare un concetto difficile con parole semplicissime, come a un bambino di 10 anni).

MATERIALE DI RIFERIMENTO:
{context_text[:4000]}

CRONOLOGIA DI DISCUSSIONE PRECEDENTE:
{history_str}

SPIEGAZIONE DEL CONCETTO DATA ORA DALLO STUDENTE:
"{explanation}"

Analizza la spiegazione dello studente. Devi rispondere ESCLUSIVAMENTE con un oggetto JSON valido, senza preamboli, commenti o blocchi di codice markdown.
L'oggetto JSON deve contenere esattamente queste chiavi:
1. "punti_di_forza": array di stringhe (aspetti del concetto spiegati correttamente, in modo semplice e chiaro).
2. "lacune": array di stringhe (elementi chiave del concetto che lo studente ha omesso o dimenticato di spiegare).
3. "inesattezze": array di stringhe (errori tecnici, concettuali o contraddizioni nella sua risposta).
4. "analogia": stringa (una brevissima spiegazione intuitiva o un'analogia simpatica e semplice che lo studente può usare come gancio mentale).
5. "domanda_followup": stringa (una domanda di chiarimento o approfondimento in tono socratico e incoraggiante per spingerlo a riflettere sulle sue lacune).

Assicurati che l'output sia solo JSON valido, ben strutturato."""

        try:
            response = await self.llm_service.generate_response(prompt)
            return _parse_llm_json(response)
        except Exception as e:
            logger.error(f"Feynman step evaluation failed via LLM: {e}")
            return {
                "punti_di_forza": ["Hai provato a spiegare il concetto."],
                "lacune": ["Errore tecnico durante la valutazione, riprova."],
                "inesattezze": [],
                "analogia": "Non è stato possibile elaborare un'analogia al momento.",
                "domanda_followup": "Puoi provare a rispiegare il concetto?",
            }

    async def deconstruct_subject_concepts(
        self, subject_id: int, force_refresh: bool = False
    ) -> dict[str, Any]:
        """
        Deconstruct subject documents into focus cheat-sheets, likely questions, mental hooks, and concept maps.
        """
        if not force_refresh:
            subjects = await StudyDAO.get_subjects()
            subject = next((s for s in subjects if s["id"] == subject_id), None)

            # Check cache first
            if subject and subject.get("deconstructed_data"):
                val = subject["deconstructed_data"]
                if isinstance(val, str):
                    try:
                        return json.loads(val)
                    except Exception:
                        pass
                elif isinstance(val, dict):
                    return val

        subjects = await StudyDAO.get_subjects()
        subject = next((s for s in subjects if s["id"] == subject_id), None)
        subject_name = subject["name"] if subject else "Generale"

        docs = await StudyDAO.get_documents(subject_id)
        if not docs:
            return {
                "cheat_sheet": [],
                "likely_questions": [],
                "mental_hooks": [],
                "concept_map": [],
            }

        combined_text = ""
        for d in docs:
            full_doc = await StudyDAO.get_document(d["id"])
            if full_doc and full_doc.get("raw_text"):
                combined_text += (
                    f"\n--- {d['name']} ---\n" + full_doc["raw_text"][:4000]
                )
                if len(combined_text) > 12000:
                    break

        prompt = f"""Sei un tutor accademico esperto. Devi de-costruire ed estrarre dal materiale didattico della materia '{subject_name}' una mappa di studio avanzata ed estremamente elaborata, profonda e strutturata, per preparare lo studente all'esame.

MATERIALE DIDATTICO:
{combined_text[:12000]}

Genera un oggetto JSON valido contenente ESATTAMENTE queste quattro chiavi:
1. "cheat_sheet": array di oggetti. Ciascun oggetto ha "term" (concetto chiave, formula o teorema) e "definition" (spiegazione dettagliata ma sintetica). Estrai esattamente tra gli 8 e i 10 elementi.
2. "likely_questions": array di oggetti. Ciascun oggetto ha "question" (domanda d'esame probabile e stimolante) e "focus_answer" (risposta ideale strutturata con parole chiave evidenziate, che dimostri approfondimento). Estrai esattamente tra i 6 e gli 8 elementi.
3. "mental_hooks": array di oggetti. Ciascun oggetto ha "concept" (concetto difficile da ricordare) e "mnemonic" (trucco mnemonico, analogia visiva o associazione concettuale forte per memorizzarlo). Estrai esattamente tra i 6 e gli 8 elementi.
4. "concept_map": un oggetto con due chiavi:
   - "nodes": array di 25-40 oggetti, ciascuno con:
     - "name": nome del concetto (2-5 parole, senza underscore)
     - "definition": definizione accademica completa e densa (2-4 frasi)
     - "cluster": gruppo tematico di appartenenza (scegli tra 3-6 cluster tematici distinti, es. "Fondamenti", "Algoritmi", "Strutture Dati")
   - "edges": array di 40-70 oggetti, ciascuno con:
     - "source": nome del nodo sorgente (deve corrispondere esattamente a un "name" in "nodes")
     - "target": nome del nodo destinazione (deve corrispondere esattamente a un "name" in "nodes")
     - "relationship": descrizione verbale sintetica della relazione (3-8 parole)
     - "relation_type": uno tra: "gerarchia", "dipendenza", "contrasto", "implementa", "esempio_di", "precede", "causa"
   Costruisci una vera rete di conoscenza con cluster tematici interconnessi tra loro, non una semplice catena lineare.
   Assicurati che tutti i "source" e "target" degli edges corrispondano esattamente ai "name" dei nodi dichiarati in "nodes".

Rispondi ESCLUSIVAMENTE con l'oggetto JSON valido, senza blocchi di codice markdown o commenti esterni."""

        try:
            response = await self.llm_service.generate_response(prompt)
            result = _parse_llm_json(response)

            # Save to cache
            await StudyDAO.update_deconstructed_data(subject_id, result)

            # Ingest to GraphDB if enabled
            if graph_db.is_enabled() and isinstance(result, dict):
                try:
                    # 1. Upsert subject node
                    subject_node_id = f"subject_{subject_id}"
                    graph_db.upsert_node(
                        node_id=subject_node_id,
                        labels=["study_subject"],
                        properties={"name": subject_name, "subject_id": subject_id},
                    )

                    # 2. Process cheat_sheet terms
                    cheat_sheet = result.get("cheat_sheet", [])
                    for item in cheat_sheet:
                        term = item.get("term")
                        definition = item.get("definition")
                        if term and definition:
                            concept_node_id = f"subj_{subject_id}_concept_{term.lower().replace(' ', '_')}"
                            graph_db.upsert_node(
                                node_id=concept_node_id,
                                labels=["study_concept"],
                                properties={
                                    "name": term,
                                    "definition": definition,
                                    "subject_id": subject_id,
                                },
                            )
                            graph_db.upsert_edge(
                                source_id=subject_node_id,
                                relationship="STUDY_CONTAINS",
                                target_id=concept_node_id,
                                properties={},
                            )

                    # 3. Process concept_map relationships (supports both old array and new {nodes,edges} format)
                    concept_map_data = result.get("concept_map", [])
                    if isinstance(concept_map_data, dict):
                        concept_map = concept_map_data.get("edges", [])
                    else:
                        concept_map = (
                            concept_map_data
                            if isinstance(concept_map_data, list)
                            else []
                        )
                    for rel in concept_map:
                        source = rel.get("source")
                        target = rel.get("target")
                        relationship = rel.get("relationship", "RELATED")
                        relation_type = rel.get("relation_type", "RELATED").upper()

                        if source and target:
                            src_node_id = f"subj_{subject_id}_concept_{source.lower().replace(' ', '_')}"
                            tgt_node_id = f"subj_{subject_id}_concept_{target.lower().replace(' ', '_')}"

                            # Ensure both nodes exist
                            graph_db.upsert_node(
                                node_id=src_node_id,
                                labels=["study_concept"],
                                properties={"name": source, "subject_id": subject_id},
                            )
                            graph_db.upsert_node(
                                node_id=tgt_node_id,
                                labels=["study_concept"],
                                properties={"name": target, "subject_id": subject_id},
                            )

                            # Create edge
                            graph_db.upsert_edge(
                                source_id=src_node_id,
                                relationship=relation_type,
                                target_id=tgt_node_id,
                                properties={"description": relationship},
                            )
                except Exception as g_err:
                    logger.warning(
                        f"Failed to ingest deconstructed concepts to GraphDB: {g_err}"
                    )

            return result
        except Exception as e:
            logger.error(f"Failed to deconstruct subject concepts: {e}")
            return {
                "cheat_sheet": [
                    {
                        "term": "Nessun concetto estratto",
                        "definition": "Carica dei materiali di studio validi per procedere.",
                    }
                ],
                "likely_questions": [],
                "mental_hooks": [],
                "concept_map": [],
            }

    async def extract_document_topics(self, subject_id: int) -> list[str]:
        """
        Extract 8-12 specific study topics based on the subject's uploaded documents.
        """
        subjects = await StudyDAO.get_subjects()
        subject = next((s for s in subjects if s["id"] == subject_id), None)
        subject_name = subject["name"] if subject else "Generale"

        docs = await StudyDAO.get_documents(subject_id)
        if not docs:
            return []

        # Read some text from documents (first 2000 chars of each document up to 6000 total) to understand the content
        combined_text = ""
        doc_names = []
        for d in docs:
            doc_names.append(d["name"])
            full_doc = await StudyDAO.get_document(d["id"])
            if full_doc and full_doc.get("raw_text"):
                combined_text += (
                    f"\n--- Documento: {d['name']} ---\n" + full_doc["raw_text"][:2000]
                )
                if len(combined_text) > 6000:
                    break

        prompt = f"""Sei un assistente accademico esperto della materia '{subject_name}'. 
Analizza i seguenti materiali o nomi dei documenti e individua una lista di 8-12 argomenti (topic) specifici su cui uno studente dovrebbe concentrarsi per l'esame.
Gli argomenti devono derivare ESCLUSIVAMENTE dai documenti caricati o dai loro titoli se il testo è limitato. Non inventare argomenti generici o non attinenti (ad esempio, consiglia 'derivate' solo se nel testo si parla effettivamente di calcolo differenziale o derivate).

NOMI DEI DOCUMENTI DISPONIBILI:
{", ".join(doc_names)}

ESTRATTO DEL CONTENUTO DEI DOCUMENTI:
{combined_text[:6000]}

Rispondi ESCLUSIVAMENTE con un array JSON di stringhe, ad esempio:
[
  "Definizione di limite",
  "Teorema di unicità del limite",
  ...
]
Non inserire altri commenti, codice markdown o prefazioni."""

        try:
            response = await self.llm_service.generate_response(prompt)
            topics = _parse_llm_json(response)
            if isinstance(topics, list):
                return [str(t).strip() for t in topics if str(t).strip()]
            return []
        except Exception as e:
            logger.error(f"Failed to extract document topics: {e}")
            # Fallback to document names without extensions
            return [
                d["name"].replace(".pdf", "").replace(".txt", "").replace(".md", "")
                for d in docs
            ][:8]

    async def generate_episode_script(
        self,
        professor_name: str,
        subject_name: str,
        topic: str,
        episode_number: int,
        episode_title: str,
        num_episodes: int,
        context: str,
    ) -> str:
        """Generate the full script for a single podcast episode."""
        prompt = f"""Sei {professor_name}, un docente universitario esperto. Stai registrando la puntata {episode_number} di {num_episodes} di un podcast didattico sulla materia '{subject_name}', argomento: '{topic}'.
Il titolo di questa puntata è: '{episode_title}'.

CONTESTO E MATERIALI DI STUDIO:
{context[:12000]}

Scrivi lo script completo e dettagliato per questa puntata.
REQUISITI TASSATIVI:
- Scrivi in italiano, in prima persona ("io"), tono discorsivo e coinvolgente come in una trasmissione radio.
- Lo script deve essere di ALMENO 3200 caratteri e non superare i 4000 caratteri (limite OpenAI TTS).
- Spiega concetti passo dopo passo, usa metafore, esempi reali, approfondimenti matematici o teorici.
- NON inserire annotazioni registiche tipo [Musica] o [Pausa]. Solo testo parlato pulito.
- Se è la puntata {episode_number}/{num_episodes}, contestualizza rispetto alle puntate precedenti/successive.

Restituisci SOLO il testo dello script, senza titoli, numeri di puntata, JSON o commenti."""

        return await self.llm_service.generate_response(prompt)

    async def choose_podcast_professor(
        self, subject_name: str, topic: str
    ) -> dict[str, str]:
        """
        Decide the professor name and voice based on subject name and topic context.
        """
        prompt = f"""Dato la materia '{subject_name}' e l'argomento '{topic}', decidi il profilo di un professore o professoressa ideale che presenterà il podcast. Scegli:
1. Un nome italiano realistico per il/la docente (es. 'Prof. Francesco Rossi' o 'Prof.ssa Elena Bianchi').
2. Una delle seguenti voci di OpenAI che meglio si adatta alla materia e al tono:
   - 'onyx' (voce maschile profonda, adatta per materie analitiche/scientifiche o toni molto formali)
   - 'echo' (voce maschile calda ed equilibrata, adatta per spiegazioni discorsive)
   - 'nova' (voce femminile energica e dinamica, adatta per materie interattive, scienze umane, o toni coinvolgenti)
   - 'shimmer' (voce femminile professionale ed equilibrata, adatta per presentazioni chiare e strutturate)
   - 'alloy' (voce neutra e bilanciata)
   - 'fable' (voce maschile creativa)

Restituisci un oggetto JSON valido con le seguenti chiavi:
- "professor_name": il nome del professore/professoressa
- "voice": la voce scelta (rigorosamente una tra 'onyx', 'echo', 'nova', 'shimmer', 'alloy', 'fable')
- "description": una brevissima spiegazione del perché questo profilo è adatto (es. 'Un tono chiaro e accattivante adatto a spiegare...')

Rispondi ESCLUSIVAMENTE con l'oggetto JSON, senza commenti esterni o markdown format blocks."""
        try:
            response = await self.llm_service.generate_response(prompt)
            return _parse_llm_json(response)
        except Exception as e:
            logger.error(f"Failed to choose professor profile dynamically: {e}")
            return {
                "professor_name": "Prof. Alessandro Neri",
                "voice": "echo",
                "description": "Un tono equilibrato e discorsivo per lo studio di questo argomento.",
            }

    @staticmethod
    def _split_text_into_chunks(text: str, max_chars: int = 4000) -> list:
        """Split text at sentence boundaries without exceeding max_chars."""
        sentences = re.split(r"(?<=[.!?…])\s+", text)
        chunks = []
        current = ""
        for sent in sentences:
            if not sent.strip():
                continue
            candidate = (current + " " + sent).strip() if current else sent
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(sent) > max_chars:
                    words = sent.split()
                    current = ""
                    for w in words:
                        test = (current + " " + w).strip() if current else w
                        if len(test) <= max_chars:
                            current = test
                        else:
                            if current:
                                chunks.append(current)
                            current = w
                else:
                    current = sent
        if current:
            chunks.append(current)
        return chunks if chunks else [text[:max_chars]]

    async def _synthesize_episode(
        self,
        ep: dict[str, Any],
        podcast_id: int,
        voice: str,
        voice_service: Any,
        podcasts_dir: str,
    ) -> dict[str, Any]:
        import os
        import uuid

        from core.services.voice.models import AudioFormat, VoiceProvider

        TTS_CHAR_LIMIT = 4000

        episode_num = ep.get("episode_number", 1)
        episode_title = ep.get("title", f"Puntata {episode_num}")
        script_text = ep.get("script_text", "")

        if not script_text.strip():
            raise ValueError(f"Lo script della puntata {episode_num} è vuoto.")

        # Generate filename
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join(podcasts_dir, filename)

        # Chunk and synthesize — OpenAI TTS has a 4096-char hard limit
        if len(script_text) > TTS_CHAR_LIMIT:
            chunks = StudyAgent._split_text_into_chunks(script_text, TTS_CHAR_LIMIT)
            audio_parts = []
            for chunk in chunks:
                if chunk.strip():
                    part_res = await voice_service.text_to_speech(
                        text=chunk.strip(),
                        voice=voice,
                        format=AudioFormat.MP3,
                        provider=VoiceProvider.OPENAI,
                    )
                    audio_parts.append(part_res.audio_bytes)
            audio_bytes = b"".join(audio_parts)
        else:
            voice_res = await voice_service.text_to_speech(
                text=script_text,
                voice=voice,
                format=AudioFormat.MP3,
                provider=VoiceProvider.OPENAI,
            )
            audio_bytes = voice_res.audio_bytes

        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        # Save episode to DB
        ep_id = await StudyDAO.create_podcast_episode(
            podcast_id=podcast_id,
            episode_number=episode_num,
            title=episode_title,
            script_text=script_text,
            audio_filename=filename,
        )

        return {
            "id": ep_id,
            "episode_number": episode_num,
            "title": episode_title,
            "script_text": script_text,
            "audio_filename": filename,
        }

    async def generate_podcast(
        self,
        subject_id: int,
        topic: str,
        depth_level: str,
    ) -> dict[str, Any]:
        """
        Generate educational podcast episodes for a topic, calling OpenAI TTS and saving files locally.
        """
        import os

        from core.services.voice.service import VoiceService

        # 1. Fetch subject details
        subjects = await StudyDAO.get_subjects()
        subject = next((s for s in subjects if s["id"] == subject_id), None)
        subject_name = subject["name"] if subject else "Generale"

        # 2. Let Baselith dynamically choose professor profile based on context
        prof_profile = await self.choose_podcast_professor(subject_name, topic)
        professor_name = prof_profile.get("professor_name", "Prof. Alessandro Neri")
        voice = prof_profile.get("voice", "echo")

        # 3. Build rich RAG context from all subject documents
        docs = await StudyDAO.get_documents(subject_id)
        context_parts = []
        for doc in docs:
            full_doc = await StudyDAO.get_document(doc["id"])
            if full_doc and full_doc.get("raw_text"):
                context_parts.append(f"[{doc['name']}]\n{full_doc['raw_text']}")
                if sum(len(p) for p in context_parts) >= 14000:
                    break
        combined_context = "\n\n---\n\n".join(context_parts)
        context = (
            combined_context[:14000]
            if combined_context
            else "Usa le tue conoscenze generali."
        )

        # 4. Define depth instructions
        if depth_level == "breve":
            depth_desc = "1 singola puntata molto estesa, dettagliata e approfondita (circa 3-4 minuti di lettura, di minimo 3000 caratteri e massimo 4000 caratteri)."
        elif depth_level == "approfondito":
            depth_desc = "3 o 4 puntate estremamente approfondite, accademiche e dettagliate (ciascuna di circa 4-5 minuti di lettura, ciascuna di minimo 3500 caratteri e massimo 4000 caratteri)."
        else:  # "normale"
            depth_desc = "2 puntate ampie e bilanciate (ciascuna di circa 4 minuti di lettura, ciascuna di minimo 3200 caratteri e massimo 4000 caratteri)."

        # 5. Build prompt for script generation
        prompt = f"""Sei il {professor_name}, un docente esperto e appassionato. Devi registrare un podcast didattico a puntate sulla materia '{subject_name}' incentrato sull'argomento: '{topic}'.
Il livello di approfondimento richiesto è: {depth_desc}

CONTESTO E MATERIALI DI STUDIO:
{context[:8000]}

ISTRUZIONI DI SCRITTURA:
- Scrivi in italiano, in prima persona singolare ("io"), mantenendo un tono discorsivo, appassionante, coinvolgente e fluido. Come se parlassi a un microfono in radio.
- Spiega i concetti in modo chiaro, usando metafore, esempi reali, e affrontando i punti difficili passo dopo passo.
- Dividi il contenuto in puntate sequenziali che coprono organicamente l'argomento.
- Ciascuna puntata deve avere un titolo specifico e il testo completo dello script da leggere.
- Per ciascuna puntata, lo script deve contenere una spiegazione accademica estesa ed elaborata, di almeno 3000 caratteri e non superiore a 4000 caratteri (limite tassativo per la sintesi vocale di OpenAI). Non scrivere script sintetici o corti. Vogliamo spiegazioni dettagliate, ricche di esempi reali e approfondimenti matematici/teorici.
- Non inserire annotazioni registiche (es. "[Musica]", "[Professore ride]", ecc.), scrivi solo il testo parlato pulito.

Formatta la risposta RIGOROSAMENTE come un unico oggetto JSON con questa struttura:
{{
  "title": "Titolo generale del podcast (es. Alla scoperta di...)",
  "episodes": [
    {{
      "episode_number": 1,
      "title": "Titolo della puntata 1",
      "script_text": "Testo completo da leggere per la puntata 1..."
    }},
    ...
  ]
}}

Rispondi ESCLUSIVAMENTE con l'oggetto JSON, senza commenti esterni o markdown format blocks."""

        # 6. Call LLM for script
        podcast_data = {}
        try:
            response = await self.llm_service.generate_response(prompt)
            podcast_data = _parse_llm_json(response)
        except Exception as e:
            logger.error(f"Failed to generate podcast script via LLM: {e}")
            raise ValueError(f"Generazione dello script fallita: {e}") from e

        # Validate structured data
        if not podcast_data.get("title") or not podcast_data.get("episodes"):
            raise ValueError(
                "L'LLM non ha generato uno script podcast valido nel formato richiesto."
            )

        # 7. Create podcast entry in DB
        podcast_title = podcast_data["title"]
        podcast_id = await StudyDAO.create_podcast(
            subject_id=subject_id,
            title=podcast_title,
            topic=topic,
            professor_voice=voice,
            professor_name=professor_name,
            depth_level=depth_level,
        )

        if podcast_id == -1:
            raise ValueError(
                "Salvataggio dei metadati del podcast nel database fallito."
            )

        # Ensure static/podcasts directory exists
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        podcasts_dir = os.path.join(plugin_dir, "static", "podcasts")
        os.makedirs(podcasts_dir, exist_ok=True)

        voice_service = VoiceService()

        # 8. Synthesize episodes in parallel using asyncio.gather
        tasks = []
        for ep in podcast_data["episodes"]:
            tasks.append(
                self._synthesize_episode(
                    ep=ep,
                    podcast_id=podcast_id,
                    voice=voice,
                    voice_service=voice_service,
                    podcasts_dir=podcasts_dir,
                )
            )

        try:
            generated_episodes = await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"TTS Synthesis parallel execution failed: {e}")
            # Clean up the podcast row created above so a failed generation
            # doesn't leave a permanent episode-less entry in the library.
            try:
                await StudyDAO.delete_podcast(podcast_id)
            except Exception as cleanup_err:
                logger.error(
                    f"Failed to clean up orphaned podcast {podcast_id}: {cleanup_err}"
                )
            raise ValueError(f"Sintesi vocale parallela fallita: {e}") from e

        return {
            "id": podcast_id,
            "title": podcast_title,
            "topic": topic,
            "professor_name": professor_name,
            "professor_voice": voice,
            "depth_level": depth_level,
            "episodes": generated_episodes,
        }
