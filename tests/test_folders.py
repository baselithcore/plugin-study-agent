"""Unit tests for study assistant folder operations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from plugins.study_agent.persistence import StudyDAO


def setup_mock_db(mock_cursor):
    """Helper to setup mock database connection and cursor context managers."""
    mock_conn = MagicMock()

    # mock_conn.cursor() returns an object that supports async context manager yielding mock_cursor
    mock_cursor_manager = MagicMock()
    mock_cursor_manager.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor_manager.__aexit__ = AsyncMock()

    mock_conn.cursor = MagicMock(return_value=mock_cursor_manager)

    # get_connection() returns an object that supports async context manager yielding mock_conn
    mock_conn_manager = MagicMock()
    mock_conn_manager.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn_manager.__aexit__ = AsyncMock()

    return mock_conn_manager


@pytest.mark.asyncio
async def test_create_folder():
    """Test creating a folder."""
    mock_cursor = AsyncMock()
    mock_cursor.fetchone.return_value = [42]
    mock_db_manager = setup_mock_db(mock_cursor)

    with patch(
        "plugins.study_agent.persistence.get_connection", return_value=mock_db_manager
    ):
        folder_id = await StudyDAO.create_folder(
            subject_id=1, name="Appunti", parent_id=None
        )
        assert folder_id == 42
        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO study_folders (subject_id, name, parent_id, tenant_id) VALUES (%s, %s, %s, %s) RETURNING id",
            (1, "Appunti", None, "default"),
        )


@pytest.mark.asyncio
async def test_get_folders():
    """Test retrieving folders."""
    mock_cursor = AsyncMock()
    expected_folders = [
        {"id": 1, "subject_id": 1, "name": "Folder 1", "parent_id": None},
        {"id": 2, "subject_id": 1, "name": "Folder 2", "parent_id": 1},
    ]
    mock_cursor.fetchall.return_value = expected_folders
    mock_db_manager = setup_mock_db(mock_cursor)

    with patch(
        "plugins.study_agent.persistence.get_connection", return_value=mock_db_manager
    ):
        folders = await StudyDAO.get_folders(subject_id=1)
        assert folders == expected_folders
        mock_cursor.execute.assert_called_once_with(
            "SELECT id, subject_id, name, parent_id, created_at FROM study_folders WHERE subject_id = %s AND tenant_id = %s ORDER BY name",
            (1, "default"),
        )


@pytest.mark.asyncio
async def test_delete_folder():
    """Test deleting a folder."""
    mock_cursor = AsyncMock()
    mock_cursor.rowcount = 1
    mock_db_manager = setup_mock_db(mock_cursor)

    with patch(
        "plugins.study_agent.persistence.get_connection", return_value=mock_db_manager
    ):
        success = await StudyDAO.delete_folder(folder_id=10)
        assert success is True
        mock_cursor.execute.assert_called_once_with(
            "DELETE FROM study_folders WHERE id = %s AND tenant_id = %s",
            (10, "default"),
        )


@pytest.mark.asyncio
async def test_rename_folder():
    """Test renaming a folder."""
    mock_cursor = AsyncMock()
    mock_cursor.rowcount = 1
    mock_db_manager = setup_mock_db(mock_cursor)

    with patch(
        "plugins.study_agent.persistence.get_connection", return_value=mock_db_manager
    ):
        success = await StudyDAO.rename_folder(folder_id=5, name="Nuovo Nome")
        assert success is True
        mock_cursor.execute.assert_called_once_with(
            "UPDATE study_folders SET name = %s WHERE id = %s AND tenant_id = %s",
            ("Nuovo Nome", 5, "default"),
        )


@pytest.mark.asyncio
async def test_rename_document():
    """Test renaming a document."""
    mock_cursor = AsyncMock()
    mock_cursor.rowcount = 1
    mock_db_manager = setup_mock_db(mock_cursor)

    with patch(
        "plugins.study_agent.persistence.get_connection", return_value=mock_db_manager
    ):
        success = await StudyDAO.rename_document(doc_id=12, name="Doc Rinomato")
        assert success is True
        mock_cursor.execute.assert_called_once_with(
            "UPDATE study_documents SET name = %s WHERE id = %s AND tenant_id = %s",
            ("Doc Rinomato", 12, "default"),
        )


@pytest.mark.asyncio
async def test_move_document():
    """Test moving a document."""
    mock_cursor = AsyncMock()
    mock_cursor.rowcount = 1
    mock_db_manager = setup_mock_db(mock_cursor)

    with patch(
        "plugins.study_agent.persistence.get_connection", return_value=mock_db_manager
    ):
        success = await StudyDAO.move_document(doc_id=12, folder_id=4)
        assert success is True
        mock_cursor.execute.assert_called_once_with(
            "UPDATE study_documents SET folder_id = %s WHERE id = %s AND tenant_id = %s",
            (4, 12, "default"),
        )


@pytest.mark.asyncio
async def test_move_folder_success_no_cycle():
    """Test successfully moving a folder to another parent when no cycle is detected."""
    mock_cursor = AsyncMock()
    mock_cursor.fetchone.side_effect = [
        [1],  # parent_id of 2 is 1
        [None],  # parent_id of 1 is None
    ]
    mock_cursor.rowcount = 1
    mock_db_manager = setup_mock_db(mock_cursor)

    with patch(
        "plugins.study_agent.persistence.get_connection", return_value=mock_db_manager
    ):
        success = await StudyDAO.move_folder(folder_id=3, parent_id=2)
        assert success is True


@pytest.mark.asyncio
async def test_move_folder_cycle_detected():
    """Test that moving a folder inside its own descendant fails the cycle check."""
    mock_cursor = AsyncMock()
    mock_cursor.fetchone.side_effect = [
        [2],  # parent_id of 3 is 2
        [1],  # parent_id of 2 is 1
    ]
    mock_db_manager = setup_mock_db(mock_cursor)

    with patch(
        "plugins.study_agent.persistence.get_connection", return_value=mock_db_manager
    ):
        success = await StudyDAO.move_folder(folder_id=1, parent_id=3)
        assert success is False
        # Ensure update was not executed
        assert not any(
            "UPDATE study_folders" in str(args)
            for args, kwargs in mock_cursor.execute.call_args_list
        )


def test_router_bulk_delete():
    """Test bulk deletion of documents and folders via router."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from plugins.study_agent.plugin import StudyAgentPlugin

    app = FastAPI()
    plugin = StudyAgentPlugin()
    router = plugin.create_router()
    app.include_router(router)
    client = TestClient(app)

    with (
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_documents",
            new_callable=AsyncMock,
            return_value=[{"id": 10}, {"id": 11}],
        ),
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_folders",
            new_callable=AsyncMock,
            return_value=[{"id": 20}, {"id": 21}],
        ),
        patch(
            "plugins.study_agent.persistence.StudyDAO.delete_document",
            return_value=True,
        ) as mock_del_doc,
        patch(
            "plugins.study_agent.persistence.StudyDAO.delete_folder", return_value=True
        ) as mock_del_folder,
    ):
        response = client.post(
            "/subjects/1/bulk-delete",
            json={"document_ids": [10, 11], "folder_ids": [20, 21]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted_documents"] == 2
        assert data["deleted_folders"] == 2

        assert mock_del_doc.call_count == 2
        mock_del_doc.assert_any_call(10)
        mock_del_doc.assert_any_call(11)

        assert mock_del_folder.call_count == 2
        mock_del_folder.assert_any_call(20)
        mock_del_folder.assert_any_call(21)


def test_router_bulk_delete_skips_ids_outside_subject():
    """IDs that don't belong to the subject are silently skipped, not deleted."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from plugins.study_agent.plugin import StudyAgentPlugin

    app = FastAPI()
    plugin = StudyAgentPlugin()
    router = plugin.create_router()
    app.include_router(router)
    client = TestClient(app)

    with (
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_documents",
            new_callable=AsyncMock,
            return_value=[{"id": 10}],
        ),
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_folders",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "plugins.study_agent.persistence.StudyDAO.delete_document",
            return_value=True,
        ) as mock_del_doc,
        patch(
            "plugins.study_agent.persistence.StudyDAO.delete_folder", return_value=True
        ) as mock_del_folder,
    ):
        response = client.post(
            "/subjects/1/bulk-delete",
            json={
                "document_ids": [10, 999],  # 999 belongs to another subject
                "folder_ids": [20],  # belongs to another subject
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_documents"] == 1
        assert data["deleted_folders"] == 0

        mock_del_doc.assert_called_once_with(10)
        mock_del_folder.assert_not_called()


def test_router_bulk_move_success():
    """Test successful bulk move of documents and folders via router."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from plugins.study_agent.plugin import StudyAgentPlugin

    app = FastAPI()
    plugin = StudyAgentPlugin()
    router = plugin.create_router()
    app.include_router(router)
    client = TestClient(app)

    mock_folders = [
        {"id": 30, "subject_id": 1, "name": "Target Folder", "parent_id": None}
    ]

    with (
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_folders",
            return_value=mock_folders,
        ),
        patch(
            "plugins.study_agent.persistence.StudyDAO.move_folder", return_value=True
        ) as mock_move_folder,
        patch(
            "plugins.study_agent.persistence.StudyDAO.move_document", return_value=True
        ) as mock_move_doc,
    ):
        response = client.post(
            "/subjects/1/bulk-move",
            json={
                "document_ids": [10, 11],
                "folder_ids": [20, 21],
                "target_folder_id": 30,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["moved_documents"] == 2
        assert data["moved_folders"] == 2

        assert mock_move_doc.call_count == 2
        mock_move_doc.assert_any_call(10, 30)
        mock_move_doc.assert_any_call(11, 30)

        assert mock_move_folder.call_count == 2
        mock_move_folder.assert_any_call(20, 30)
        mock_move_folder.assert_any_call(21, 30)


def test_router_bulk_move_invalid_target():
    """Test bulk move fails when target folder does not exist or doesn't belong to subject."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from plugins.study_agent.plugin import StudyAgentPlugin

    app = FastAPI()
    plugin = StudyAgentPlugin()
    router = plugin.create_router()
    app.include_router(router)
    client = TestClient(app)

    mock_folders = [
        {"id": 30, "subject_id": 1, "name": "Target Folder", "parent_id": None}
    ]

    with patch(
        "plugins.study_agent.persistence.StudyDAO.get_folders",
        return_value=mock_folders,
    ):
        response = client.post(
            "/subjects/1/bulk-move",
            json={"document_ids": [10], "folder_ids": [20], "target_folder_id": 999},
        )
        assert response.status_code == 400
        assert "Target folder not found" in response.json()["detail"]


def test_router_bulk_move_cycle_detected():
    """Test bulk move handles cycle prevention logic gracefully without crashing."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from plugins.study_agent.plugin import StudyAgentPlugin

    app = FastAPI()
    plugin = StudyAgentPlugin()
    router = plugin.create_router()
    app.include_router(router)
    client = TestClient(app)

    mock_folders = [
        {"id": 30, "subject_id": 1, "name": "Target Folder", "parent_id": None}
    ]

    with (
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_folders",
            return_value=mock_folders,
        ),
        patch(
            "plugins.study_agent.persistence.StudyDAO.move_folder", return_value=False
        ),
        patch(
            "plugins.study_agent.persistence.StudyDAO.move_document", return_value=True
        ),
    ):
        response = client.post(
            "/subjects/1/bulk-move",
            json={"document_ids": [10], "folder_ids": [20], "target_folder_id": 30},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["moved_documents"] == 1
        assert data["moved_folders"] == 0
        assert data["failed_folders"] == [20]


# --- Additional OCR and Upload Parsing Tests ---


def test_parse_docx():
    from plugins.study_agent.router import parse_docx

    mock_para = MagicMock()
    mock_para.text = "Hello Docx Paragraph"

    mock_cell = MagicMock()
    mock_cell.text = "Table Cell Content"

    mock_row = MagicMock()
    mock_row.cells = [mock_cell]

    mock_table = MagicMock()
    mock_table.rows = [mock_row]

    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_para]
    mock_doc.tables = [mock_table]

    with patch("docx.Document", return_value=mock_doc):
        res = parse_docx(b"fake_docx_bytes")
        assert "Hello Docx Paragraph" in res
        assert "Table Cell Content" in res


def test_parse_pptx():
    from plugins.study_agent.router import parse_pptx

    mock_shape = MagicMock()
    mock_shape.text = "Slide Bullet Point"

    mock_slide = MagicMock()
    mock_slide.shapes = [mock_shape]

    mock_prs = MagicMock()
    mock_prs.slides = [mock_slide]

    with patch("pptx.Presentation", return_value=mock_prs):
        res = parse_pptx(b"fake_pptx_bytes")
        assert "Slide Bullet Point" in res
        assert "Slide 1" in res


@patch("plugins.study_agent.router.get_paddle_ocr")
def test_run_paddle_ocr_on_image(mock_get_ocr):
    from plugins.study_agent.router import run_paddle_ocr_on_image

    mock_ocr_instance = MagicMock()
    mock_ocr_instance.predict.return_value = [{"rec_texts": ["Extracted Image Text"]}]
    mock_get_ocr.return_value = mock_ocr_instance

    res = run_paddle_ocr_on_image(b"fake_image_bytes", "png")
    assert res == "Extracted Image Text"


@patch("plugins.study_agent.router.run_paddle_ocr_on_image")
def test_run_paddle_ocr_on_pdf(mock_run_ocr_img):
    from plugins.study_agent.router import run_paddle_ocr_on_pdf

    mock_run_ocr_img.return_value = "Page text"

    mock_page = MagicMock()
    mock_pix = MagicMock()
    mock_pix.tobytes.return_value = b"png_bytes"
    mock_page.get_pixmap.return_value = mock_pix

    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 2
    mock_doc.load_page.return_value = mock_page

    with patch("fitz.open", return_value=mock_doc) as mock_fitz_open:
        res = run_paddle_ocr_on_pdf(b"fake_pdf_bytes")
        assert res == "Page text\n\nPage text"
        mock_fitz_open.assert_called_once()
        assert mock_page.get_pixmap.call_count == 2


def test_upload_route_standard_pdf():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from plugins.study_agent.plugin import StudyAgentPlugin

    app = FastAPI()
    plugin = StudyAgentPlugin()
    app.include_router(plugin.create_router())
    client = TestClient(app)

    mock_pypdf_page = MagicMock()
    mock_pypdf_page.extract_text.return_value = (
        "This is a long standard PDF text that is more than fifty characters."
    )

    mock_pypdf_reader = MagicMock()
    mock_pypdf_reader.pages = [mock_pypdf_page]

    with (
        patch("pypdf.PdfReader", return_value=mock_pypdf_reader),
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_subjects",
            new_callable=AsyncMock,
            return_value=[{"id": 1, "name": "Analisi 1"}],
        ),
        patch(
            "plugins.study_agent.persistence.StudyDAO.add_document", return_value=123
        ) as mock_add_doc,
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_folders",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_get_folders,
        patch(
            "plugins.study_agent.persistence.StudyDAO.create_folder",
            new_callable=AsyncMock,
            return_value=999,
        ) as mock_create_folder,
        patch("plugins.study_agent.router.run_paddle_ocr_on_pdf") as mock_run_pdf_ocr,
    ):
        response = client.post(
            "/subjects/1/upload",
            files={"file": ("test.pdf", b"pdf_data", "application/pdf")},
            data={"relative_path": "subdir/test.pdf"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == 123
        mock_run_pdf_ocr.assert_not_called()
        mock_add_doc.assert_called_once()
        mock_get_folders.assert_called_once_with(1)
        mock_create_folder.assert_called_once_with(1, "subdir", None)


def test_upload_route_scanned_pdf_fallback():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from plugins.study_agent.plugin import StudyAgentPlugin

    app = FastAPI()
    plugin = StudyAgentPlugin()
    app.include_router(plugin.create_router())
    client = TestClient(app)

    mock_pypdf_page = MagicMock()
    mock_pypdf_page.extract_text.return_value = ""  # Empty text triggers fallback

    mock_pypdf_reader = MagicMock()
    mock_pypdf_reader.pages = [mock_pypdf_page]

    with (
        patch("pypdf.PdfReader", return_value=mock_pypdf_reader),
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_subjects",
            new_callable=AsyncMock,
            return_value=[{"id": 1, "name": "Analisi 1"}],
        ),
        patch(
            "plugins.study_agent.persistence.StudyDAO.add_document", return_value=123
        ) as mock_add_doc,
        patch(
            "plugins.study_agent.router.run_paddle_ocr_on_pdf",
            return_value="Extracted OCR text",
        ) as mock_run_pdf_ocr,
    ):
        response = client.post(
            "/subjects/1/upload",
            files={"file": ("test.pdf", b"pdf_data", "application/pdf")},
        )
        assert response.status_code == 200
        assert response.json()["id"] == 123
        mock_run_pdf_ocr.assert_called_once()
        # Ensure OCR text was saved
        mock_add_doc.assert_called_once_with(
            subject_id=1,
            name="test.pdf",
            file_path="",
            file_type="pdf",
            raw_text="Extracted OCR text",
            folder_id=None,
        )


def test_upload_route_subject_not_found():
    """Uploading to a non-existent subject returns 404 without running the parsing pipeline."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from plugins.study_agent.plugin import StudyAgentPlugin

    app = FastAPI()
    plugin = StudyAgentPlugin()
    app.include_router(plugin.create_router())
    client = TestClient(app)

    with (
        patch(
            "plugins.study_agent.persistence.StudyDAO.get_subjects",
            new_callable=AsyncMock,
            return_value=[{"id": 1, "name": "Analisi 1"}],
        ),
        patch("plugins.study_agent.persistence.StudyDAO.add_document") as mock_add_doc,
    ):
        response = client.post(
            "/subjects/9999/upload",
            files={"file": ("test.txt", b"some text", "text/plain")},
        )
        assert response.status_code == 404
        mock_add_doc.assert_not_called()
