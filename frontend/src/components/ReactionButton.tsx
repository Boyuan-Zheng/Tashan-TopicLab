import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ReactionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string
  count?: number
  active?: boolean
  pending?: boolean
  icon: ReactNode
  subtle?: boolean
  hideLabel?: boolean
}

export default function ReactionButton({
  label,
  count = 0,
  active = false,
  pending = false,
  icon,
  subtle = false,
  hideLabel = true,
  className = '',
  disabled,
  ...props
}: ReactionButtonProps) {
  const getColor = () => {
    if (active) return 'var(--text-primary)'
    if (subtle) return 'var(--text-tertiary)'
    return 'var(--text-secondary)'
  }

  return (
    <button
      type="button"
      aria-label={pending ? `${label}处理中` : label}
      disabled={disabled || pending}
      className={`group inline-flex min-h-[32px] items-center gap-1.5 rounded-lg px-1 py-1 text-sm transition-colors duration-200 cursor-pointer focus:outline-none disabled:cursor-not-allowed disabled:opacity-40 sm:min-h-[34px] ${className}`.trim()}
      style={{ color: getColor() }}
      onMouseEnter={(e) => {
        e.currentTarget.style.color = 'var(--text-primary)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.color = getColor()
      }}
      {...props}
    >
      <span className="flex h-6 w-6 items-center justify-center transition-transform duration-200 group-hover:scale-[1.03] group-active:scale-90">
        {icon}
      </span>
      {hideLabel ? <span className="sr-only">{label}</span> : <span className="font-medium tracking-[0.01em]">{pending ? '处理中...' : label}</span>}
      <span className="text-[11px] font-medium tabular-nums sm:text-xs">
        {pending ? '...' : count}
      </span>
    </button>
  )
}