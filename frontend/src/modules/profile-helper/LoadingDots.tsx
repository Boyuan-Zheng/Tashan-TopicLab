/** User avatar SVG */
export function UserAvatar() {
  return (
    <div className="message-avatar message-avatar-user" aria-hidden>
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="12" cy="8" r="4" />
        <path d="M4 20c0-4 4-6 8-6s8 2 8 6" />
      </svg>
    </div>
  )
}

/** Robot avatar SVG */
export function RobotAvatar() {
  return (
    <div className="message-avatar message-avatar-robot" aria-hidden>
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <rect x="4" y="8" width="16" height="12" rx="2" />
        <circle cx="9" cy="12" r="1.5" fill="currentColor" />
        <circle cx="15" cy="12" r="1.5" fill="currentColor" />
        <path d="M9 15h6" />
        <path d="M12 8v2" />
        <path d="M12 4v2" />
        <path d="M8 4h8" />
      </svg>
    </div>
  )
}

/** Loading dots */
export function LoadingDots() {
  return (
    <div className="loading-dots" aria-label="思考中">
      <span className="dot" />
      <span className="dot" />
      <span className="dot" />
    </div>
  )
}
