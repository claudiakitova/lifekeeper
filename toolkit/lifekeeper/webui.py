"""The Lifekeeper window: a small web page shown in a native window (pywebview). Same look as the page it makes."""

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Lifekeeper</title>
<style>
  :root {
    --bg: #f6f5f2; --card: #ffffff; --ink: #1d1d1f; --soft: #6e6e73; --faint: #a1a1a6;
    --line: #e4e2dd; --field: #f6f5f2; --accent: #1d1d1f; --on-accent: #ffffff; --ok: #2d6a4f; --bad: #b3261e;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #141416; --card: #1d1d20; --ink: #f2f2ef; --soft: #a1a1a6; --faint: #6e6e73;
      --line: #2e2e33; --field: #26262a; --accent: #f2f2ef; --on-accent: #141416; --ok: #7cc8a0; --bad: #ff8a80;
    }
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; background: var(--bg); color: var(--ink); }
  body { font: 15px/1.5 "Segoe UI Variable Text", "Segoe UI", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
         -webkit-font-smoothing: antialiased; user-select: none; }
  main { max-width: 600px; margin: 0 auto; padding: 30px 28px 36px; }
  header { display: flex; align-items: center; gap: 12px; margin: 4px 0 6px; }
  header svg { width: 34px; height: 34px; color: var(--ink); }
  header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.02em; margin: 0; }
  .lede { color: var(--soft); margin: 0 0 22px; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 20px 20px 18px; margin-bottom: 16px; }
  .card h2 { font-size: 13px; font-weight: 600; color: var(--soft); margin: 0 0 12px; letter-spacing: 0.01em; }
  .row { display: flex; gap: 10px; align-items: center; }
  .path { flex: 1; min-width: 0; color: var(--faint); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; direction: rtl; text-align: left; }
  .path.set { color: var(--ink); }
  input, textarea { width: 100%; font: inherit; color: var(--ink); background: var(--field); border: 1px solid transparent;
                    border-radius: 10px; padding: 10px 12px; outline: none; user-select: text; }
  input:focus, textarea:focus { border-color: var(--faint); }
  input::placeholder, textarea::placeholder { color: var(--faint); }
  .field { margin-top: 12px; }
  button { font: inherit; cursor: pointer; border-radius: 999px; border: 1px solid var(--line); background: var(--card);
           color: var(--ink); padding: 8px 16px; white-space: nowrap; }
  button:hover:not(:disabled) { border-color: var(--faint); }
  button.primary { background: var(--accent); color: var(--on-accent); border-color: var(--accent); padding: 10px 20px; font-weight: 600; }
  button:disabled { opacity: 0.4; cursor: default; }
  .actions { display: flex; align-items: center; gap: 14px; margin-top: 16px; }
  .status { color: var(--soft); font-size: 13.5px; }
  .status.bad { color: var(--bad); }
  .link { border: none; background: none; padding: 0; color: var(--ink); text-decoration: underline; text-underline-offset: 3px; }
  .ask { position: relative; }
  .ask textarea { resize: none; height: 76px; padding-right: 54px; }
  .send { position: absolute; right: 10px; bottom: 10px; width: 36px; height: 36px; padding: 0; border-radius: 50%;
          background: var(--accent); color: var(--on-accent); border: none; display: grid; place-items: center; }
  .send svg { width: 16px; height: 16px; }
  .modes { display: inline-flex; background: var(--field); border-radius: 999px; padding: 3px; margin-top: 12px; }
  .modes button { border: none; background: transparent; padding: 6px 13px; font-size: 13.5px; color: var(--soft); }
  .modes button.on { background: var(--card); color: var(--ink); box-shadow: 0 1px 2px rgba(0,0,0,.12); }
  .note { color: var(--faint); font-size: 12.5px; margin-top: 8px; }
  .answer { margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--line); user-select: text; }
  .answer p { margin: 0 0 10px; }
  .answer .from { color: var(--soft); font-size: 12.5px; font-weight: 600; margin: 12px 0 6px; }
  .answer ol { list-style: none; margin: 0; padding: 0; }
  .answer li { font-size: 13.5px; color: var(--soft); padding: 5px 0; border-top: 1px solid var(--line); display: flex; gap: 10px; }
  .answer li:first-child { border-top: none; }
  .answer li b { color: var(--ink); font-weight: 600; min-width: 22px; }
  ::-webkit-scrollbar { width: 10px; }
  ::-webkit-scrollbar-thumb { background: var(--line); border-radius: 10px; border: 3px solid var(--bg); }
  ::-webkit-scrollbar-track { background: transparent; }
  .hidden { display: none; }
  .spin { display: inline-block; width: 12px; height: 12px; border: 2px solid var(--line); border-top-color: var(--soft);
          border-radius: 50%; animation: s .8s linear infinite; vertical-align: -1px; margin-right: 6px; }
  @keyframes s { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<main>
  <header><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" aria-hidden="true"><mask id="crack" maskUnits="userSpaceOnUse" x="-5" y="-5" width="110" height="110"><rect x="-5" y="-5" width="110" height="110" fill="#fff"/><path d="M60.24,58.00 L93.61,78.32 L88.03,85.46 Z" fill="#000"/></mask><g transform="translate(0.00 0.00) scale(1.0000)"><g mask="url(#crack)" fill="currentColor"><path fill-rule="evenodd" d="M96.00,50.00 L95.97,51.61 L95.89,53.21 L95.75,54.81 L95.55,56.40 L95.30,57.99 L94.99,59.56 L94.63,61.13 L94.22,62.68 L93.75,64.21 L93.23,65.73 L92.65,67.23 L92.02,68.71 L91.34,70.17 L90.62,71.60 L89.84,73.00 L89.01,74.38 L88.14,75.72 L87.21,77.04 L86.25,78.32 L85.24,79.57 L84.18,80.78 L83.09,81.95 L81.95,83.09 L80.78,84.18 L79.57,85.24 L78.32,86.25 L77.04,87.21 L75.72,88.14 L74.38,89.01 L73.00,89.84 L71.60,90.62 L70.17,91.34 L68.71,92.02 L67.23,92.65 L65.73,93.23 L64.21,93.75 L62.68,94.22 L61.13,94.63 L59.56,94.99 L57.99,95.30 L56.40,95.55 L54.81,95.75 L53.21,95.89 L51.61,95.97 L50.00,96.00 L48.39,95.97 L46.79,95.89 L45.19,95.75 L43.60,95.55 L42.01,95.30 L40.44,94.99 L38.87,94.63 L37.32,94.22 L35.79,93.75 L34.27,93.23 L32.77,92.65 L31.29,92.02 L29.83,91.34 L28.40,90.62 L27.00,89.84 L25.62,89.01 L24.28,88.14 L22.96,87.21 L21.68,86.25 L20.43,85.24 L19.22,84.18 L18.05,83.09 L16.91,81.95 L15.82,80.78 L14.76,79.57 L13.75,78.32 L12.79,77.04 L11.86,75.72 L10.99,74.38 L10.16,73.00 L9.38,71.60 L8.66,70.17 L7.98,68.71 L7.35,67.23 L6.77,65.73 L6.25,64.21 L5.78,62.68 L5.37,61.13 L5.01,59.56 L4.70,57.99 L4.45,56.40 L4.25,54.81 L4.11,53.21 L4.03,51.61 L4.00,50.00 L4.03,48.39 L4.11,46.79 L4.25,45.19 L4.45,43.60 L4.70,42.01 L5.01,40.44 L5.37,38.87 L5.78,37.32 L6.25,35.79 L6.77,34.27 L7.35,32.77 L7.98,31.29 L8.66,29.83 L9.38,28.40 L10.16,27.00 L10.99,25.62 L11.86,24.28 L12.79,22.96 L13.75,21.68 L14.76,20.43 L15.82,19.22 L16.91,18.05 L18.05,16.91 L19.22,15.82 L20.43,14.76 L21.68,13.75 L22.96,12.79 L24.28,11.86 L25.62,10.99 L27.00,10.16 L28.40,9.38 L29.83,8.66 L31.29,7.98 L32.77,7.35 L34.27,6.77 L35.79,6.25 L37.32,5.78 L38.87,5.37 L40.44,5.01 L42.01,4.70 L43.60,4.45 L45.19,4.25 L46.79,4.11 L48.39,4.03 L50.00,4.00 L51.61,4.03 L53.21,4.11 L54.81,4.25 L56.40,4.45 L57.99,4.70 L59.56,5.01 L61.13,5.37 L62.68,5.78 L64.21,6.25 L65.73,6.77 L67.23,7.35 L68.71,7.98 L70.17,8.66 L71.60,9.38 L73.00,10.16 L74.38,10.99 L75.72,11.86 L77.04,12.79 L78.32,13.75 L79.57,14.76 L80.78,15.82 L81.95,16.91 L83.09,18.05 L84.18,19.22 L85.24,20.43 L86.25,21.68 L87.21,22.96 L88.14,24.28 L89.01,25.62 L89.84,27.00 L90.62,28.40 L91.34,29.83 L92.02,31.29 L92.65,32.77 L93.23,34.27 L93.75,35.79 L94.22,37.32 L94.63,38.87 L94.99,40.44 L95.30,42.01 L95.55,43.60 L95.75,45.19 L95.89,46.79 L95.97,48.39 Z M90.50,50.00 L90.48,51.41 L90.40,52.83 L90.28,54.23 L90.11,55.64 L89.88,57.03 L89.61,58.42 L89.30,59.80 L88.93,61.16 L88.52,62.52 L88.06,63.85 L87.55,65.17 L87.00,66.47 L86.40,67.75 L85.76,69.01 L85.07,70.25 L84.35,71.46 L83.58,72.65 L82.77,73.81 L81.91,74.93 L81.02,76.03 L80.10,77.10 L79.13,78.13 L78.13,79.13 L77.10,80.10 L76.03,81.02 L74.93,81.91 L73.81,82.77 L72.65,83.58 L71.46,84.35 L70.25,85.07 L69.01,85.76 L67.75,86.40 L66.47,87.00 L65.17,87.55 L63.85,88.06 L62.52,88.52 L61.16,88.93 L59.80,89.30 L58.42,89.61 L57.03,89.88 L55.64,90.11 L54.23,90.28 L52.83,90.40 L51.41,90.48 L50.00,90.50 L48.59,90.48 L47.17,90.40 L45.77,90.28 L44.36,90.11 L42.97,89.88 L41.58,89.61 L40.20,89.30 L38.84,88.93 L37.48,88.52 L36.15,88.06 L34.83,87.55 L33.53,87.00 L32.25,86.40 L30.99,85.76 L29.75,85.07 L28.54,84.35 L27.35,83.58 L26.19,82.77 L25.07,81.91 L23.97,81.02 L22.90,80.10 L21.87,79.13 L20.87,78.13 L19.90,77.10 L18.98,76.03 L18.09,74.93 L17.23,73.81 L16.42,72.65 L15.65,71.46 L14.93,70.25 L14.24,69.01 L13.60,67.75 L13.00,66.47 L12.45,65.17 L11.94,63.85 L11.48,62.52 L11.07,61.16 L10.70,59.80 L10.39,58.42 L10.12,57.03 L9.89,55.64 L9.72,54.23 L9.60,52.83 L9.52,51.41 L9.50,50.00 L9.52,48.59 L9.60,47.17 L9.72,45.77 L9.89,44.36 L10.12,42.97 L10.39,41.58 L10.70,40.20 L11.07,38.84 L11.48,37.48 L11.94,36.15 L12.45,34.83 L13.00,33.53 L13.60,32.25 L14.24,30.99 L14.93,29.75 L15.65,28.54 L16.42,27.35 L17.23,26.19 L18.09,25.07 L18.98,23.97 L19.90,22.90 L20.87,21.87 L21.87,20.87 L22.90,19.90 L23.97,18.98 L25.07,18.09 L26.19,17.23 L27.35,16.42 L28.54,15.65 L29.75,14.93 L30.99,14.24 L32.25,13.60 L33.53,13.00 L34.83,12.45 L36.15,11.94 L37.48,11.48 L38.84,11.07 L40.20,10.70 L41.58,10.39 L42.97,10.12 L44.36,9.89 L45.77,9.72 L47.17,9.60 L48.59,9.52 L50.00,9.50 L51.41,9.52 L52.83,9.60 L54.23,9.72 L55.64,9.89 L57.03,10.12 L58.42,10.39 L59.80,10.70 L61.16,11.07 L62.52,11.48 L63.85,11.94 L65.17,12.45 L66.47,13.00 L67.75,13.60 L69.01,14.24 L70.25,14.93 L71.46,15.65 L72.65,16.42 L73.81,17.23 L74.93,18.09 L76.03,18.98 L77.10,19.90 L78.13,20.87 L79.13,21.87 L80.10,22.90 L81.02,23.97 L81.91,25.07 L82.77,26.19 L83.58,27.35 L84.35,28.54 L85.07,29.75 L85.76,30.99 L86.40,32.25 L87.00,33.53 L87.55,34.83 L88.06,36.15 L88.52,37.48 L88.93,38.84 L89.30,40.20 L89.61,41.58 L89.88,42.97 L90.11,44.36 L90.28,45.77 L90.40,47.17 L90.48,48.59 Z M81.60,47.69 L81.54,48.89 L81.43,50.08 L81.27,51.27 L81.07,52.45 L80.83,53.61 L80.53,54.77 L80.20,55.91 L79.83,57.04 L79.41,58.15 L78.96,59.24 L78.46,60.31 L77.94,61.36 L77.37,62.39 L76.78,63.40 L76.15,64.39 L75.49,65.35 L74.80,66.29 L74.08,67.20 L73.34,68.09 L72.57,68.95 L71.77,69.79 L70.95,70.60 L70.11,71.39 L69.25,72.14 L68.36,72.87 L67.45,73.57 L66.52,74.25 L65.58,74.89 L64.61,75.51 L63.63,76.09 L62.63,76.65 L61.61,77.18 L60.58,77.67 L59.53,78.13 L58.46,78.56 L57.39,78.96 L56.30,79.32 L55.20,79.64 L54.08,79.93 L52.96,80.19 L51.83,80.40 L50.69,80.58 L49.54,80.72 L48.39,80.82 L47.23,80.88 L46.07,80.90 L44.91,80.88 L43.75,80.82 L42.59,80.71 L41.43,80.56 L40.28,80.38 L39.14,80.14 L38.00,79.87 L36.88,79.55 L35.76,79.20 L34.66,78.80 L33.57,78.36 L32.50,77.88 L31.45,77.36 L30.42,76.80 L29.41,76.20 L28.42,75.57 L27.46,74.90 L26.52,74.20 L25.60,73.46 L24.72,72.69 L23.86,71.89 L23.03,71.06 L22.23,70.20 L21.46,69.31 L20.72,68.40 L20.02,67.46 L19.34,66.50 L18.71,65.51 L18.10,64.51 L17.53,63.48 L17.00,62.44 L16.50,61.37 L16.03,60.29 L15.61,59.20 L15.22,58.09 L14.86,56.97 L14.55,55.84 L14.27,54.70 L14.03,53.54 L13.83,52.38 L13.67,51.22 L13.55,50.05 L13.47,48.87 L13.43,47.69 L13.43,46.51 L13.47,45.33 L13.56,44.15 L13.68,42.98 L13.85,41.80 L14.06,40.64 L14.31,39.48 L14.60,38.34 L14.94,37.20 L15.32,36.08 L15.74,34.97 L16.20,33.87 L16.70,32.80 L17.24,31.75 L17.82,30.71 L18.44,29.70 L19.10,28.72 L19.80,27.76 L20.53,26.83 L21.29,25.93 L22.09,25.06 L22.93,24.22 L23.79,23.42 L24.68,22.65 L25.60,21.91 L26.54,21.21 L27.51,20.55 L28.50,19.92 L29.51,19.33 L30.54,18.79 L31.59,18.27 L32.65,17.80 L33.73,17.37 L34.82,16.97 L35.92,16.61 L37.03,16.29 L38.14,16.01 L39.27,15.76 L40.40,15.56 L41.53,15.38 L42.67,15.25 L43.81,15.15 L44.95,15.08 L46.09,15.05 L47.23,15.06 L48.37,15.09 L49.50,15.17 L50.64,15.27 L51.77,15.41 L52.89,15.58 L54.01,15.78 L55.13,16.02 L56.23,16.28 L57.34,16.58 L58.43,16.92 L59.51,17.28 L60.59,17.68 L61.65,18.11 L62.71,18.58 L63.75,19.08 L64.77,19.61 L65.78,20.18 L66.78,20.78 L67.75,21.42 L68.71,22.09 L69.65,22.79 L70.56,23.53 L71.45,24.30 L72.31,25.10 L73.15,25.94 L73.95,26.81 L74.73,27.71 L75.47,28.64 L76.17,29.60 L76.84,30.59 L77.47,31.61 L78.06,32.65 L78.61,33.72 L79.11,34.81 L79.58,35.92 L79.99,37.04 L80.36,38.19 L80.69,39.35 L80.96,40.52 L81.19,41.70 L81.37,42.89 L81.50,44.09 L81.59,45.29 L81.62,46.49 Z M77.91,47.69 L77.85,48.76 L77.76,49.82 L77.62,50.88 L77.44,51.94 L77.21,52.98 L76.96,54.01 L76.66,55.03 L76.32,56.03 L75.95,57.02 L75.55,58.00 L75.11,58.95 L74.64,59.89 L74.13,60.81 L73.60,61.71 L73.04,62.59 L72.45,63.45 L71.84,64.29 L71.20,65.11 L70.53,65.90 L69.85,66.67 L69.14,67.42 L68.40,68.14 L67.65,68.84 L66.88,69.52 L66.09,70.17 L65.28,70.79 L64.45,71.39 L63.60,71.97 L62.74,72.52 L61.87,73.04 L60.97,73.54 L60.06,74.01 L59.14,74.45 L58.21,74.86 L57.26,75.24 L56.30,75.60 L55.32,75.92 L54.34,76.21 L53.35,76.47 L52.34,76.70 L51.33,76.89 L50.31,77.05 L49.29,77.17 L48.26,77.26 L47.23,77.32 L46.19,77.33 L45.16,77.31 L44.12,77.26 L43.09,77.16 L42.05,77.03 L41.03,76.86 L40.01,76.66 L38.99,76.41 L37.99,76.13 L36.99,75.81 L36.01,75.45 L35.04,75.06 L34.09,74.63 L33.15,74.17 L32.23,73.67 L31.33,73.14 L30.44,72.58 L29.58,71.98 L28.74,71.35 L27.93,70.69 L27.14,70.01 L26.37,69.29 L25.63,68.55 L24.91,67.78 L24.23,66.99 L23.57,66.17 L22.94,65.34 L22.34,64.48 L21.77,63.60 L21.23,62.70 L20.72,61.78 L20.25,60.85 L19.80,59.90 L19.39,58.94 L19.00,57.96 L18.66,56.97 L18.34,55.97 L18.06,54.96 L17.81,53.94 L17.60,52.91 L17.42,51.88 L17.28,50.84 L17.17,49.79 L17.10,48.74 L17.06,47.69 L17.06,46.64 L17.10,45.58 L17.17,44.53 L17.29,43.48 L17.44,42.44 L17.62,41.40 L17.85,40.36 L18.11,39.34 L18.41,38.33 L18.75,37.32 L19.12,36.33 L19.53,35.36 L19.98,34.40 L20.46,33.46 L20.98,32.54 L21.54,31.64 L22.12,30.76 L22.75,29.90 L23.40,29.07 L24.08,28.27 L24.80,27.49 L25.54,26.74 L26.31,26.03 L27.10,25.34 L27.92,24.68 L28.76,24.06 L29.63,23.46 L30.51,22.91 L31.41,22.38 L32.33,21.89 L33.27,21.44 L34.22,21.01 L35.18,20.63 L36.15,20.27 L37.13,19.95 L38.12,19.67 L39.12,19.41 L40.12,19.20 L41.13,19.01 L42.14,18.86 L43.16,18.74 L44.18,18.65 L45.19,18.59 L46.21,18.56 L47.23,18.56 L48.24,18.60 L49.26,18.66 L50.27,18.75 L51.28,18.88 L52.28,19.03 L53.28,19.21 L54.28,19.42 L55.27,19.66 L56.25,19.93 L57.23,20.22 L58.19,20.55 L59.15,20.91 L60.10,21.29 L61.04,21.71 L61.97,22.15 L62.89,22.63 L63.79,23.14 L64.68,23.67 L65.55,24.24 L66.40,24.84 L67.24,25.47 L68.05,26.12 L68.85,26.81 L69.62,27.53 L70.36,28.28 L71.08,29.06 L71.77,29.86 L72.43,30.69 L73.06,31.55 L73.66,32.43 L74.22,33.34 L74.75,34.27 L75.24,35.22 L75.69,36.19 L76.10,37.18 L76.47,38.19 L76.80,39.21 L77.09,40.24 L77.34,41.29 L77.54,42.34 L77.70,43.41 L77.82,44.47 L77.89,45.55 L77.92,46.62 Z M66.07,45.47 L66.01,46.22 L65.93,46.97 L65.81,47.71 L65.68,48.44 L65.52,49.17 L65.34,49.89 L65.14,50.60 L64.91,51.31 L64.67,52.00 L64.40,52.69 L64.11,53.37 L63.81,54.04 L63.48,54.70 L63.14,55.35 L62.77,55.98 L62.39,56.61 L61.99,57.22 L61.57,57.83 L61.13,58.41 L60.68,58.99 L60.20,59.55 L59.71,60.10 L59.20,60.63 L58.68,61.15 L58.14,61.65 L57.58,62.13 L57.01,62.59 L56.41,63.04 L55.81,63.46 L55.19,63.87 L54.55,64.25 L53.90,64.62 L53.24,64.96 L52.57,65.28 L51.88,65.57 L51.18,65.84 L50.48,66.08 L49.76,66.30 L49.04,66.49 L48.30,66.66 L47.56,66.80 L46.82,66.91 L46.07,66.99 L45.32,67.04 L44.57,67.07 L43.81,67.07 L43.06,67.04 L42.31,66.98 L41.56,66.90 L40.81,66.78 L40.07,66.64 L39.33,66.47 L38.60,66.28 L37.88,66.06 L37.17,65.81 L36.46,65.54 L35.77,65.24 L35.08,64.92 L34.41,64.57 L33.75,64.20 L33.11,63.81 L32.48,63.40 L31.86,62.96 L31.26,62.51 L30.67,62.03 L30.10,61.54 L29.55,61.02 L29.02,60.49 L28.50,59.94 L28.00,59.37 L27.52,58.79 L27.07,58.19 L26.63,57.57 L26.21,56.94 L25.81,56.30 L25.44,55.64 L25.09,54.97 L24.76,54.29 L24.46,53.60 L24.18,52.89 L23.92,52.18 L23.69,51.46 L23.49,50.73 L23.31,49.99 L23.16,49.25 L23.03,48.50 L22.94,47.75 L22.87,46.99 L22.83,46.23 L22.81,45.47 L22.83,44.71 L22.87,43.96 L22.95,43.20 L23.05,42.45 L23.18,41.70 L23.34,40.96 L23.53,40.23 L23.74,39.50 L23.98,38.78 L24.25,38.08 L24.54,37.38 L24.86,36.70 L25.21,36.03 L25.58,35.38 L25.97,34.74 L26.38,34.11 L26.82,33.50 L27.28,32.91 L27.76,32.34 L28.25,31.78 L28.77,31.25 L29.30,30.73 L29.85,30.23 L30.41,29.75 L30.99,29.29 L31.58,28.85 L32.19,28.43 L32.80,28.03 L33.43,27.65 L34.07,27.29 L34.72,26.95 L35.38,26.63 L36.04,26.33 L36.72,26.05 L37.40,25.79 L38.09,25.55 L38.79,25.33 L39.50,25.13 L40.21,24.95 L40.92,24.80 L41.64,24.66 L42.37,24.54 L43.10,24.45 L43.83,24.38 L44.57,24.33 L45.31,24.30 L46.05,24.30 L46.79,24.32 L47.53,24.36 L48.28,24.43 L49.02,24.52 L49.76,24.64 L50.50,24.78 L51.23,24.95 L51.96,25.15 L52.69,25.37 L53.41,25.62 L54.12,25.90 L54.82,26.20 L55.50,26.53 L56.18,26.89 L56.85,27.27 L57.50,27.68 L58.13,28.12 L58.75,28.58 L59.34,29.06 L59.92,29.57 L60.48,30.11 L61.01,30.66 L61.53,31.24 L62.02,31.84 L62.48,32.46 L62.92,33.10 L63.33,33.75 L63.71,34.42 L64.07,35.10 L64.40,35.80 L64.70,36.51 L64.97,37.23 L65.21,37.96 L65.42,38.70 L65.61,39.44 L65.76,40.19 L65.89,40.94 L65.99,41.70 L66.06,42.45 L66.10,43.21 L66.12,43.97 L66.11,44.72 Z M62.67,45.47 L62.62,46.10 L62.55,46.73 L62.45,47.35 L62.34,47.97 L62.21,48.58 L62.06,49.19 L61.88,49.79 L61.70,50.38 L61.49,50.97 L61.26,51.55 L61.02,52.12 L60.77,52.68 L60.49,53.24 L60.20,53.79 L59.89,54.32 L59.57,54.85 L59.23,55.37 L58.88,55.87 L58.51,56.37 L58.13,56.85 L57.73,57.33 L57.32,57.79 L56.89,58.23 L56.45,58.67 L55.99,59.09 L55.52,59.49 L55.04,59.88 L54.54,60.26 L54.03,60.62 L53.51,60.96 L52.97,61.28 L52.43,61.59 L51.87,61.88 L51.30,62.14 L50.73,62.39 L50.14,62.62 L49.54,62.82 L48.94,63.01 L48.33,63.17 L47.71,63.31 L47.09,63.42 L46.46,63.52 L45.83,63.59 L45.20,63.63 L44.57,63.65 L43.93,63.65 L43.30,63.63 L42.66,63.58 L42.03,63.51 L41.40,63.41 L40.78,63.29 L40.16,63.15 L39.55,62.99 L38.94,62.80 L38.34,62.59 L37.74,62.36 L37.16,62.11 L36.58,61.84 L36.02,61.55 L35.46,61.24 L34.92,60.91 L34.39,60.56 L33.87,60.20 L33.36,59.81 L32.87,59.41 L32.39,59.00 L31.93,58.56 L31.48,58.12 L31.04,57.65 L30.62,57.17 L30.22,56.68 L29.83,56.18 L29.46,55.66 L29.11,55.13 L28.78,54.59 L28.47,54.03 L28.17,53.47 L27.89,52.90 L27.64,52.31 L27.40,51.72 L27.19,51.12 L26.99,50.51 L26.82,49.90 L26.67,49.28 L26.54,48.65 L26.44,48.02 L26.36,47.39 L26.30,46.75 L26.26,46.11 L26.25,45.47 L26.27,44.83 L26.31,44.20 L26.37,43.56 L26.45,42.93 L26.56,42.30 L26.70,41.67 L26.85,41.06 L27.03,40.44 L27.24,39.84 L27.46,39.25 L27.71,38.66 L27.98,38.09 L28.27,37.52 L28.58,36.97 L28.91,36.43 L29.26,35.91 L29.63,35.40 L30.01,34.90 L30.41,34.42 L30.83,33.95 L31.27,33.50 L31.71,33.06 L32.17,32.64 L32.65,32.24 L33.14,31.85 L33.63,31.48 L34.14,31.13 L34.66,30.79 L35.19,30.47 L35.73,30.17 L36.28,29.88 L36.83,29.61 L37.39,29.36 L37.96,29.12 L38.54,28.90 L39.12,28.70 L39.71,28.52 L40.30,28.35 L40.90,28.20 L41.50,28.07 L42.10,27.95 L42.72,27.85 L43.33,27.78 L43.95,27.71 L44.57,27.67 L45.19,27.65 L45.81,27.65 L46.44,27.66 L47.07,27.70 L47.69,27.76 L48.32,27.84 L48.94,27.93 L49.56,28.06 L50.18,28.20 L50.79,28.36 L51.40,28.55 L52.01,28.76 L52.61,28.99 L53.19,29.25 L53.77,29.52 L54.35,29.83 L54.90,30.15 L55.45,30.49 L55.98,30.86 L56.50,31.25 L57.01,31.66 L57.49,32.09 L57.96,32.54 L58.41,33.01 L58.85,33.49 L59.26,34.00 L59.65,34.52 L60.02,35.05 L60.36,35.60 L60.69,36.17 L60.99,36.74 L61.26,37.33 L61.51,37.93 L61.74,38.53 L61.95,39.15 L62.13,39.77 L62.28,40.39 L62.41,41.02 L62.52,41.66 L62.60,42.29 L62.66,42.93 L62.70,43.57 L62.71,44.20 L62.70,44.84 Z"/><circle cx="44.0" cy="45.0" r="6.0"/></g></g></svg><h1>Lifekeeper</h1></header>
  <p class="lede">Your photos, chats and posts as one page of your life.</p>

  <section class="card">
    <h2>Your page</h2>
    <div class="row">
      <button id="choose">Choose folder…</button>
      <span class="path" id="path">The folder with your exports. Zips can stay zipped</span>
    </div>
    <div class="field"><input id="name" placeholder="Your name as it appears in your chats (optional)"></div>
    <div class="actions">
      <button class="primary" id="make" disabled>Make my page</button>
      <span class="status" id="status">Nothing leaves this computer</span>
    </div>
  </section>

  <section class="card">
    <h2>Ask about your life</h2>
    <div class="ask">
      <textarea id="question" placeholder="When did I meet Leo?" disabled></textarea>
      <button class="send" id="send" title="Ask" disabled>
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 13V3M3.5 7.5 8 3l4.5 4.5"/></svg>
      </button>
    </div>
    <div class="modes" id="modes">
      <button data-mode="records" class="on">My records</button>
      <button data-mode="ollama">Model on this computer</button>
      <button data-mode="gemini">Google Gemini</button>
    </div>
    <div class="field hidden" id="extraBox"><input id="extra"></div>
    <div class="note" id="modeNote">Shows the records that match. No AI, nothing leaves this computer</div>
    <div class="answer hidden" id="answer"></div>
  </section>
</main>
<script>
const $ = id => document.getElementById(id);
let folder = null, mode = "records", ready = false, busy = false;
const notes = {
  records: "Shows the records that match. No AI, nothing leaves this computer",
  ollama: "A model running in Ollama on this computer writes the answer. Nothing leaves this computer",
  gemini: "Sends your question and the matching records to Google. Your key isn't saved",
};
const placeholders = { ollama: "The model's name in Ollama, for example gemma3", gemini: "Your Gemini API key" };
const saved = k => { try { return localStorage.getItem(k) || ""; } catch { return ""; } };
const save = (k, v) => { try { localStorage.setItem(k, v); } catch {} };

function setFolder(p) {
  folder = p; $("path").textContent = p; $("path").classList.add("set"); $("make").disabled = false;
  ready = false; refreshAsk();
}
function refreshAsk() {
  const on = ready && !busy;
  $("question").disabled = !ready; $("send").disabled = !on;
  $("question").placeholder = ready ? "When did I meet Leo?" : "Make your page first";
}
$("choose").onclick = async () => { const p = await pywebview.api.choose_folder(); if (p) setFolder(p); };
$("make").onclick = async () => {
  if (!folder) return;
  $("make").disabled = true; $("status").className = "status";
  $("status").innerHTML = '<span class="spin"></span>Reading your exports. Big exports can take a few minutes';
  const r = await pywebview.api.make_page(folder, $("name").value);
  $("make").disabled = false;
  if (r.error) { $("status").className = "status bad"; $("status").textContent = r.error; return; }
  $("status").innerHTML = 'Your page is ready. <button class="link" id="open">Open it</button>';
  $("open").onclick = () => pywebview.api.open_page();
  ready = true; refreshAsk(); $("question").focus();
};
document.querySelectorAll("#modes button").forEach(b => b.onclick = () => {
  document.querySelectorAll("#modes button").forEach(x => x.classList.toggle("on", x === b));
  mode = b.dataset.mode; $("modeNote").textContent = notes[mode];
  $("extraBox").classList.toggle("hidden", mode === "records");
  $("extra").type = mode === "gemini" ? "password" : "text";
  $("extra").placeholder = placeholders[mode] || "";
  $("extra").value = mode === "ollama" ? saved("lk.model") : "";
});
function show(text) {
  const box = $("answer"); box.classList.remove("hidden"); box.innerHTML = "";
  const marker = text.match(/^(From your records:|Records that match \(no AI was used\):|Your records don't say\. The closest ones:|The model's answer couldn't be checked against your records, so it isn't shown\. The records that match:)\s*$/m);
  const head = marker ? text.slice(0, marker.index).trim() : text.trim();
  const rest = marker ? text.slice(marker.index + marker[0].length).trim() : "";
  if (head) head.split(/\n\s*\n/).forEach(t => { const p = document.createElement("p"); p.textContent = t; box.appendChild(p); });
  if (marker) {
    const label = document.createElement("div"); label.className = "from";
    label.textContent = marker[0].replace(/:\s*$/, ""); box.appendChild(label);
    const ol = document.createElement("ol");
    rest.split("\n").map(s => s.trim()).filter(Boolean).forEach(s => {
      const m = s.match(/^\[(\d+)\]\s*(.*)$/); const li = document.createElement("li");
      const n = document.createElement("b"); n.textContent = m ? m[1] : "·"; li.appendChild(n);
      const t = document.createElement("span"); t.textContent = m ? m[2] : s; li.appendChild(t); ol.appendChild(li);
    });
    box.appendChild(ol);
  }
}
async function ask() {
  const q = $("question").value.trim(); if (!q || !ready || busy) return;
  const value = $("extra").value.trim();
  if (mode !== "records" && !value) { show(mode === "ollama" ? "Type the model's name first." : "Paste your Gemini API key first. A free key: aistudio.google.com/apikey"); return; }
  if (mode === "ollama") save("lk.model", value);
  busy = true; refreshAsk();
  const box = $("answer"); box.classList.remove("hidden"); box.innerHTML = '<p class="status"><span class="spin"></span>Looking through your records</p>';
  const r = await pywebview.api.ask(q, mode, value);
  busy = false; refreshAsk(); show(r.error || r.text);
}
$("send").onclick = ask;
$("question").addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(); } });
refreshAsk();
</script>
</body>
</html>
"""
