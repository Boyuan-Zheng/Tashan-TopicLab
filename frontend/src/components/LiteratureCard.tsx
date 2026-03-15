import { LiteratureRecentItem } from '../api/client'
import ReactionButton from './ReactionButton'

function ShareIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" className="h-4 w-4">
      <path d="M8 10.5l4-2.5m-4 1.5l4 2.5M13.5 6.5a1.75 1.75 0 100-3.5 1.75 1.75 0 000 3.5zm0 10.5a1.75 1.75 0 100-3.5 1.75 1.75 0 000 3.5zM5.5 12.25a1.75 1.75 0 100-3.5 1.75 1.75 0 000 3.5z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

/** paper_id 如 2603.11048v1 -> https://arxiv.org/abs/2603.11048 */
function getArxivUrl(paperId: string): string {
  const base = paperId.replace(/v\d+$/i, '')
  return `https://arxiv.org/abs/${base}`
}

function formatPublishedDay(day: string): string {
  if (day.length >= 6) {
    const y = day.slice(0, 4)
    const m = day.slice(4, 6)
    const d = day.length >= 8 ? day.slice(6, 8) : ''
    return d ? `${y}-${m}-${d}` : `${y}-${m}`
  }
  return day
}

interface LiteratureCardProps {
  item: LiteratureRecentItem
  onShare?: (item: LiteratureRecentItem) => void
}

export default function LiteratureCard({ item, onShare }: LiteratureCardProps) {
  const url = getArxivUrl(item.paper_id)
  const authorsText = Array.isArray(item.authors) ? item.authors.slice(0, 3).join(', ') : ''
  const moreAuthors = Array.isArray(item.authors) && item.authors.length > 3 ? `等${item.authors.length}人` : ''

  return (
    <article className="group relative rounded-[22px] border border-gray-200 bg-white p-4 transition-colors hover:border-black">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold text-gray-700">
            学
          </div>
          <div className="min-w-0 truncate text-sm font-serif font-semibold text-gray-700">
            学术
          </div>
        </div>
        <div className="rounded-lg bg-gray-100 px-2.5 py-1 text-xs font-serif text-gray-500">
          论文
        </div>
      </div>

      <a href={url} target="_blank" rel="noreferrer" className="block">
        <h2 className="text-[16px] leading-[1.55] font-serif font-semibold text-gray-800">
          {item.title}
        </h2>
      </a>

      {(authorsText || item.compact_category) && (
        <p className="mt-3 line-clamp-2 text-[13px] leading-7 font-serif text-gray-600">
          {authorsText}
          {moreAuthors}
          {item.compact_category ? ` · ${item.compact_category}` : ''}
        </p>
      )}

      <div className="mt-4 text-xs font-serif text-gray-400">
        {formatPublishedDay(item.published_day)}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {onShare ? (
          <ReactionButton
            label="分享"
            icon={<ShareIcon />}
            subtle
            onClick={() => onShare(item)}
          />
        ) : null}
      </div>
    </article>
  )
}
