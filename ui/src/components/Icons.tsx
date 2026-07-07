import type { SVGProps } from 'react';

function Icon({ paths: d, ...rest }: SVGProps<SVGSVGElement> & { paths: string | string[] }) {
  const paths = Array.isArray(d) ? d : [d];
  return (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5} {...rest}>
      {paths.map((p, i) => (
        <path key={i} strokeLinecap="round" strokeLinejoin="round" d={p} />
      ))}
    </svg>
  );
}

export const ChatIcon = (p: SVGProps<SVGSVGElement>) => (
  <Icon
    {...p}
    paths="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"
  />
);

export const MicIcon = (p: SVGProps<SVGSVGElement>) => (
  <Icon
    {...p}
    paths="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.62 48.62 0 0112 20.904a48.62 48.62 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 019.918 5.84 50.45 50.45 0 00-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M12 21v-3.417"
  />
);

export const FolderIcon = (p: SVGProps<SVGSVGElement>) => (
  <Icon
    {...p}
    paths="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"
  />
);

export const FlashcardsIcon = (p: SVGProps<SVGSVGElement>) => (
  <Icon
    {...p}
    paths="M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z M9 8.25h6M9 12h6M9 15.75h6"
  />
);

export const BookIcon = (p: SVGProps<SVGSVGElement>) => (
  <Icon
    {...p}
    paths="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"
  />
);

export const LightbulbIcon = (p: SVGProps<SVGSVGElement>) => (
  <Icon
    {...p}
    paths={[
      'M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z',
      'M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z',
    ]}
  />
);

export const UploadIcon = (p: SVGProps<SVGSVGElement>) => (
  <Icon
    {...p}
    paths="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z"
  />
);

export const PencilIcon = (p: SVGProps<SVGSVGElement>) => (
  <Icon
    {...p}
    paths="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125"
  />
);

export const CloseIcon = (p: SVGProps<SVGSVGElement>) => (
  <Icon {...p} paths="M6 18L18 6M6 6l12 12" />
);

export const DocumentIcon = (p: SVGProps<SVGSVGElement>) => (
  <Icon
    {...p}
    paths="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m5.231 13.481L15 17.25m-1.519-3.75L12 17.25m0 0l-1.519-3.75M12 17.25V6.75"
  />
);
