import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import type { ExpertInfo } from '../api/client'

const CARD_CLASS = 'flex sm:inline-flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors w-full min-w-0 sm:min-w-[180px] sm:max-w-[280px] sm:w-auto'

interface ExpertCardViewProps {
  expert: ExpertInfo
  mode: 'view'
  descriptionLines?: 1 | 2
  showName?: boolean
  onClick: (expert: ExpertInfo) => void
}

interface ExpertCardSelectProps {
  expert: ExpertInfo
  mode: 'select'
  isSelected: boolean
  onToggle: (expert: ExpertInfo) => void
  onDetailClick?: (expert: ExpertInfo) => void
}

export type ExpertCardProps = ExpertCardViewProps | ExpertCardSelectProps

export default function ExpertCard(props: ExpertCardProps) {
  const { expert } = props

  if (props.mode === 'view') {
    const { descriptionLines = 1, showName = false, onClick } = props
    return (
      <button
        type="button"
        onClick={() => onClick(expert)}
        className="flex flex-col gap-1 px-4 py-3 rounded-lg border w-full min-w-0 sm:min-w-[200px] sm:max-w-[280px] sm:w-auto text-left cursor-pointer overflow-hidden transition-all"
        style={{
          borderColor: 'var(--border-default)',
          backgroundColor: 'var(--bg-container)',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = 'var(--border-hover)'
          e.currentTarget.style.backgroundColor = 'var(--bg-hover)'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = 'var(--border-default)'
          e.currentTarget.style.backgroundColor = 'var(--bg-container)'
        }}
      >
        <div className="flex items-center gap-2 min-w-0">
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center font-serif text-xs flex-shrink-0 text-white"
            style={{ backgroundColor: 'var(--text-primary)' }}
          >
            {expert.label.charAt(0)}
          </div>
          <span
            className="text-sm font-serif font-medium truncate"
            style={{ color: 'var(--text-primary)' }}
            title={expert.label}
          >
            {expert.label}
          </span>
        </div>
        {expert.description && (
          <span
            className={`text-xs min-w-0 ${descriptionLines === 2 ? 'line-clamp-2' : 'line-clamp-1'}`}
            style={{ color: 'var(--text-secondary)' }}
            title={expert.description}
          >
            {expert.description}
          </span>
        )}
        {showName && (
          <span
            className="text-[10px] font-mono truncate min-w-0"
            style={{ color: 'var(--text-tertiary)' }}
            title={expert.name}
          >
            {expert.name}
          </span>
        )}
      </button>
    )
  }

  const { isSelected, onToggle, onDetailClick } = props
  return (
    <div
      className={`${CARD_CLASS} transition-all`}
      style={{
        borderColor: isSelected ? 'var(--text-tertiary)' : 'var(--border-default)',
        backgroundColor: isSelected ? 'var(--bg-secondary)' : 'var(--bg-container)',
      }}
      onMouseEnter={(e) => {
        if (!isSelected) {
          e.currentTarget.style.borderColor = 'var(--border-hover)'
          e.currentTarget.style.backgroundColor = 'var(--bg-hover)'
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.borderColor = 'var(--border-default)'
          e.currentTarget.style.backgroundColor = 'var(--bg-container)'
        }
      }}
    >
      <div
        className={`flex-1 min-w-0 overflow-hidden text-left ${onDetailClick ? 'cursor-pointer' : ''}`}
        onClick={onDetailClick ? () => onDetailClick(expert) : undefined}
        onKeyDown={
          onDetailClick ? (e) => e.key === 'Enter' && onDetailClick(expert) : undefined
        }
        role={onDetailClick ? 'button' : undefined}
        tabIndex={onDetailClick ? 0 : undefined}
        title={onDetailClick ? '点击查看详情' : undefined}
      >
        <div className="flex items-center gap-2 min-w-0">
          <div
            className="w-6 h-6 rounded-full flex items-center justify-center font-serif text-[10px] flex-shrink-0 text-white"
            style={{ backgroundColor: 'var(--text-primary)' }}
          >
            {expert.label.charAt(0)}
          </div>
          <span
            className="text-sm font-serif font-medium truncate"
            style={{ color: 'var(--text-primary)' }}
            title={expert.label}
          >
            {expert.label}
          </span>
        </div>
        {expert.description && (
          <span
            className="text-xs line-clamp-1 min-w-0 block"
            style={{ color: 'var(--text-secondary)' }}
            title={expert.description}
          >
            {expert.description}
          </span>
        )}
      </div>
      <button
        type="button"
        onClick={() => onToggle(expert)}
        className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-sm font-medium text-white transition-all"
        style={{
          backgroundColor: isSelected ? 'var(--text-tertiary)' : 'var(--text-primary)',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.opacity = '0.8'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.opacity = '1'
        }}
        aria-label={isSelected ? '移除' : '添加'}
        title={isSelected ? '从话题移除' : '添加到话题'}
      >
        {isSelected ? '×' : '+'}
      </button>
    </div>
  )
}

export function ExpertChip({
  expert,
  onRemove,
  onEdit,
  onShare,
  onClick,
}: {
  expert: { name: string; label: string; masked?: boolean; origin_visibility?: string }
  onRemove: () => void
  onEdit?: () => void
  onShare?: () => void
  onClick?: () => void
}) {
  const [menuOpen, setMenuOpen] = useState(false)
  const menuButtonRef = useRef<HTMLButtonElement>(null)
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 })

  useEffect(() => {
    if (menuOpen && menuButtonRef.current) {
      const rect = menuButtonRef.current.getBoundingClientRect()
      setMenuPosition({ top: rect.bottom + 4, left: rect.right - 80 })
    }
  }, [menuOpen])

  const portalRoot = typeof document !== 'undefined' ? document.getElementById('portal-root') : null
  const menuContent =
    menuOpen && (onEdit || onShare) && portalRoot
      ? createPortal(
          <>
            <div
              style={{ position: 'fixed', inset: 0, zIndex: 10001, pointerEvents: 'auto' }}
              onClick={(e) => {
                e.stopPropagation()
                setMenuOpen(false)
              }}
              aria-hidden="true"
            />
            <div
              className="py-1 rounded-lg shadow-lg min-w-[80px]"
              style={{
                position: 'fixed',
                top: menuPosition.top,
                left: menuPosition.left,
                zIndex: 10002,
                pointerEvents: 'auto',
                backgroundColor: 'var(--bg-container)',
                border: '1px solid var(--border-default)',
              }}
            >
              {onEdit && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    onEdit()
                    setMenuOpen(false)
                  }}
                  className="block w-full text-left px-3 py-1.5 text-xs transition-colors"
                  style={{ color: 'var(--text-secondary)' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-hover)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }}
                >
                  编辑
                </button>
              )}
              {onShare && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    onShare()
                    setMenuOpen(false)
                  }}
                  className="block w-full text-left px-3 py-1.5 text-xs transition-colors"
                  style={{ color: 'var(--text-secondary)' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-hover)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }}
                >
                  共享
                </button>
              )}
            </div>
          </>,
          portalRoot
        )
      : null

  return (
    <span
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
      title={expert.label}
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border cursor-pointer sm:flex sm:gap-2 sm:px-3 sm:py-2 sm:rounded-lg sm:min-w-[180px] sm:max-w-[280px] sm:w-auto transition-colors"
      style={{
        backgroundColor: 'var(--bg-secondary)',
        borderColor: 'var(--border-default)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = 'var(--bg-hover)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'var(--bg-secondary)'
      }}
    >
      <span
        className="flex-1 min-w-0 text-left truncate max-w-[100px] sm:max-w-none font-serif font-medium"
        style={{ color: 'var(--text-primary)' }}
      >
        {expert.label}
      </span>
      {expert.masked && (
        <span
          className="text-[10px] px-1.5 py-0.5 rounded-full border"
          style={{
            borderColor: 'var(--accent-warning)',
            color: '#92400E',
            backgroundColor: '#FEF3C7',
          }}
          title="私密分身来源，内容已脱敏"
        >
          脱敏
        </span>
      )}
      <div className="flex items-center gap-0.5 flex-shrink-0">
        {(onEdit || onShare) && (
          <div className="relative">
            <button
              ref={menuButtonRef}
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                setMenuOpen((v) => !v)
              }}
              className="w-6 h-6 rounded flex items-center justify-center text-xs transition-colors"
              style={{ color: 'var(--text-tertiary)' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--text-primary)'
                e.currentTarget.style.backgroundColor = 'var(--bg-hover)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--text-tertiary)'
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
              aria-label="更多"
              title="更多"
            >
              ⋮
            </button>
            {menuContent}
          </div>
        )}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          className="w-5 h-5 sm:w-7 sm:h-7 rounded-full flex items-center justify-center text-xs sm:text-sm font-medium transition-colors touch-manipulation"
          style={{ color: 'var(--text-tertiary)' }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--text-primary)'
            e.currentTarget.style.backgroundColor = 'var(--bg-hover)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text-tertiary)'
            e.currentTarget.style.backgroundColor = 'transparent'
          }}
          aria-label="移除"
        >
          ×
        </button>
      </div>
    </span>
  )
}