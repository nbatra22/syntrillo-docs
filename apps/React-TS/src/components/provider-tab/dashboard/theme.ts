// Design tokens for the Data Dashboard
// Clean light theme — white backgrounds, navy accents

export const c = {
  // Backgrounds
  bgMain:    '#f4f7fb',           // very light blue-gray page bg
  bgCard:    '#ffffff',           // white cards
  bgCardHov: '#eef3fc',           // light navy tint on hover
  bgOverlay: 'rgba(10, 25, 50, 0.5)',

  // Borders
  border:    'rgba(15, 37, 80, 0.12)',
  borderHov: 'rgba(15, 37, 80, 0.38)',
  divider:   'rgba(15, 37, 80, 0.07)',

  // Text
  txt1: '#0d2046',  // dark navy — primary
  txt2: '#3a5a8a',  // medium navy — secondary
  txt3: '#7a96b8',  // muted slate — tertiary

  // Accent
  accent: '#1a4c9e',

  // Status: good
  green:   '#16a34a',
  greenBg: 'rgba(22, 163, 74, 0.1)',
  greenBd: 'rgba(22, 163, 74, 0.3)',

  // Status: bad
  red:   '#dc2626',
  redBg: 'rgba(220, 38, 38, 0.08)',
  redBd: 'rgba(220, 38, 38, 0.3)',

  // Status: warn
  amber:   '#b45309',
  amberBg: 'rgba(180, 83, 9, 0.08)',
  amberBd: 'rgba(180, 83, 9, 0.3)',

  // Shadows
  shadow:   '0 2px 12px rgba(15, 37, 80, 0.08)',
  shadowLg: '0 6px 24px rgba(15, 37, 80, 0.14)',

  // Border radii
  r:   '12px',
  rSm: '8px',
  rXs: '5px',
} as const;
