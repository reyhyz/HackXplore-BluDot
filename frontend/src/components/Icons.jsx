export const IconError = ({ size = 22 }) => (
  <svg width={size} height={size} viewBox="0 0 22 22" fill="none">
    <circle cx="11" cy="11" r="10" fill="#ef4444" stroke="#ef4444" />
    <line x1="7"  y1="7"  x2="15" y2="15" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
    <line x1="15" y1="7"  x2="7"  y2="15" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
  </svg>
);

export const IconOk = ({ size = 22 }) => (
  <svg width={size} height={size} viewBox="0 0 22 22" fill="none">
    <rect x="1" y="1" width="20" height="20" rx="4" fill="#22c55e" />
    <polyline points="5,11 9,15 17,7" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const IconWarn = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 22 22" fill="none">
    <polygon points="11,2 21,20 1,20" fill="#eab308" stroke="#eab308" strokeLinejoin="round" />
    <line x1="11" y1="9" x2="11" y2="14" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
    <circle cx="11" cy="17" r="1.1" fill="white" />
  </svg>
);

export const IconChevron = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <path d="M4 6l4 4 4-4" stroke="#6b7280" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const IconBack = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <path d="M11 4L6 9l5 5" stroke="#6b7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const IconUpload = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <path d="M9 12V4M9 4L6 7M9 4l3 3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M3 13v1a1 1 0 001 1h10a1 1 0 001-1v-1" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

export const IconSpinner = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 18 18" fill="none" className="animate-spin">
    <circle cx="9" cy="9" r="7" stroke="#d1d5db" strokeWidth="2.5" />
    <path d="M9 2a7 7 0 017 7" stroke="#2F70B3" strokeWidth="2.5" strokeLinecap="round" />
  </svg>
);
