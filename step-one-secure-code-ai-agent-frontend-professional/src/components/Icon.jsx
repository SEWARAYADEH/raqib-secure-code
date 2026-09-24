const paths = {
  projects: 'M3 6h7l2 2h9v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6Z',
  scan: 'M4 7V4h3M17 4h3v3M20 17v3h-3M7 20H4v-3M8 12h8M12 8v8',
  report: 'M6 3h12v18H6V3Zm3 5h6m-6 4h6m-6 4h4',
  settings: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm0-5v2m0 14v2m9-9h-2M5 12H3m15.4-6.4-1.4 1.4M7 17l-1.4 1.4m12.8 0L17 17M7 7 5.6 5.6',
  language: 'M3 5h11M8 3v2m0 0c0 5-2 8-5 10m5-10c0 5 2 8 5 10m1-6h7m-3-3 3 9m-6 0 3-9',
  upload: 'M12 16V4m0 0-4 4m4-4 4 4M5 14v5h14v-5',
  download: 'M12 4v12m0 0 4-4m-4 4-4-4M5 14v5h14v-5',
  code: 'm8 9-3 3 3 3m8-6 3 3-3 3m-3-8-2 10',
  shield: 'M12 3 5 6v5c0 4.6 3 8.7 7 10 4-1.3 7-5.4 7-10V6l-7-3Z',
  search: 'm21 21-4.2-4.2M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15Z',
  check: 'm5 12 4 4L19 6',
  alert: 'M12 3 2 21h20L12 3Zm0 6v5m0 3v1',
  file: 'M6 3h8l4 4v14H6V3Zm8 0v5h5',
  function: 'M8 4h8M9 9h6M8 20c3 0 3-16 6-16m-6 8h8',
  zoomIn: 'm21 21-4.2-4.2M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15Zm0-11v7m-3.5-3.5h7',
  zoomOut: 'm21 21-4.2-4.2M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15Zm-3.5-7.5h7',
  expand: 'M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5',
  panel: 'M4 5h16v14H4V5Zm5 0v14m6-14v14',
  arrow: 'm9 6 6 6-6 6',
  arrowBack: 'm15 6-6 6 6 6',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 9a7 7 0 0 1 14 0',
  logout: 'M10 5H5v14h5m4-4 4-3-4-3m4 3H9',
  lock: 'M7 10V7a5 5 0 0 1 10 0v3m-11 0h12v11H6V10Zm6 4v3',
  mail: 'M3 5h18v14H3V5Zm0 2 9 6 9-6',
  eye: 'M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Zm9.5 3a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z',
  key: 'M15 7a4 4 0 1 1-7.7 1.5L3 13v3h3v3h3l4.5-4.3A4 4 0 0 1 15 7Z',
  menu: 'M4 7h16M4 12h16M4 17h16',
  close: 'M6 6l12 12M18 6 6 18',
  findings: 'M5 4h14v16H5V4Zm3 4h8m-8 4h8m-8 4h5',
  info: 'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Zm0-11v6m0-10v1',
  robot: 'M8 5h8l2 3v8l-2 3H8l-2-3V8l2-3Zm1 6h.01M15 11h.01M9 15h6M12 2v3',
};

export default function Icon({ name, size = 20, strokeWidth = 1.8 }) {
  const path = paths[name] ?? paths.info;

  return (
    <svg
      aria-hidden="true"
      className={`icon icon-${name}`}
      fill="none"
      height={size}
      viewBox="0 0 24 24"
      width={size}
    >
      <path
        d={path}
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={strokeWidth}
      />
    </svg>
  );
}
