import { type CSSProperties, useMemo, useState } from 'react'
import ImmersiveAppShell from '../components/ImmersiveAppShell'
import { RESEARCH_SKILL_DISCIPLINES, type ResearchSkillDiscipline } from '../data/appsSkillZone'

/** 与参考稿一致的主强调色（teal-600） */
const ACCENT = '#0d9488'

type SortTab = 'hot' | 'score' | 'latest'

function SearchIcon({ className, style }: { className?: string; style?: CSSProperties }) {
  return (
    <svg className={className} style={style} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 110-15 7.5 7.5 0 010 15z" />
    </svg>
  )
}

function BulbIcon({ className, style }: { className?: string; style?: CSSProperties }) {
  return (
    <svg className={className} style={style} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 21h6M12 17v4M8.5 10.5a3.5 3.5 0 117 0c0 1.5-.5 2.5-1.2 3.2-.6.6-.8 1.3-.8 2.3v.5H11v-.5c0-1-.2-1.7-.8-2.3-.7-.7-1.2-1.7-1.2-3.2z" />
    </svg>
  )
}

function GridAllIcon({ className, style }: { className?: string; style?: CSSProperties }) {
  return (
    <svg className={className} style={style} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 5.5h6v6H4v-6zm10 0h6v6h-6v-6zM4 15.5h6v6H4v-6zm10 0h6v6h-6v-6z" />
    </svg>
  )
}

function EmptySearchIllustration({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 96 96" fill="none" aria-hidden>
      <circle cx="40" cy="40" r="22" stroke="#7dd3fc" strokeWidth="2.5" />
      <path d="M56 56l18 18" stroke="#7dd3fc" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

function sortDisciplines(items: ResearchSkillDiscipline[], mode: SortTab): ResearchSkillDiscipline[] {
  const copy = [...items]
  if (mode === 'hot') {
    return copy
  }
  if (mode === 'score') {
    return copy.reverse()
  }
  return copy.sort((a, b) => String(b.key).localeCompare(String(a.key), undefined, { numeric: true }))
}

const SORT_TABS: { id: SortTab; label: string }[] = [
  { id: 'hot', label: '热门' },
  { id: 'score', label: '高分' },
  { id: 'latest', label: '最新' },
]

export default function AppsSkillLibraryPage() {
  const [query, setQuery] = useState('')
  const [disciplineKey, setDisciplineKey] = useState<string>('all')
  const [sort, setSort] = useState<SortTab>('hot')

  const normalizedQuery = query.trim().toLowerCase()

  const filtered = useMemo(() => {
    let list = RESEARCH_SKILL_DISCIPLINES
    if (disciplineKey !== 'all') {
      list = list.filter((d) => d.key === disciplineKey)
    }
    if (normalizedQuery) {
      list = list.filter(
        (d) =>
          d.name.toLowerCase().includes(normalizedQuery)
          || d.summary.toLowerCase().includes(normalizedQuery)
          || d.key.toLowerCase().includes(normalizedQuery),
      )
    }
    return sortDisciplines(list, sort)
  }, [disciplineKey, normalizedQuery, sort])

  const resetFilters = () => {
    setQuery('')
    setDisciplineKey('all')
    setSort('hot')
  }

  const chips: { key: string; label: string }[] = useMemo(
    () => [{ key: 'all', label: '全部' }, ...RESEARCH_SKILL_DISCIPLINES.map((d) => ({ key: d.key, label: d.name }))],
    [],
  )

  return (
    <ImmersiveAppShell
      title="科研 Skill 专区"
      subtitle="按一级学科浏览与检索；以下为站内科研技能分类示意，后续可接入真实技能目录。"
    >
      <div className="mx-auto max-w-3xl space-y-3">
          <div className="relative">
            <SearchIcon
              className="pointer-events-none absolute left-3.5 top-1/2 h-[1.125rem] w-[1.125rem] -translate-y-1/2"
              style={{ color: 'var(--text-tertiary)' }}
            />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="搜索技能…"
              autoComplete="off"
              className="w-full rounded-full border py-2.5 pl-10 pr-4 text-sm outline-none transition-[box-shadow,border-color] motion-reduce:transition-none focus-visible:ring-2 focus-visible:ring-offset-1"
              style={{
                borderColor: 'var(--border-default)',
                backgroundColor: 'var(--bg-container)',
                color: 'var(--text-primary)',
                boxShadow: 'var(--shadow-sm)',
              }}
              aria-label="搜索技能"
            />
          </div>

          <div className="flex flex-wrap gap-1.5 sm:gap-2" role="toolbar" aria-label="一级学科">
            {chips.map((c) => {
              const active = disciplineKey === c.key
              return (
                <button
                  key={c.key}
                  type="button"
                  onClick={() => setDisciplineKey(c.key)}
                  aria-pressed={active}
                  className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors motion-reduce:transition-none sm:px-3 sm:py-1.5 sm:text-[13px] cursor-pointer"
                  style={
                    active
                      ? {
                          backgroundColor: ACCENT,
                          borderColor: ACCENT,
                          color: '#fff',
                        }
                      : {
                          backgroundColor: 'var(--bg-container)',
                          borderColor: 'var(--border-default)',
                          color: 'var(--text-primary)',
                        }
                  }
                >
                  {c.key === 'all' ? (
                    <GridAllIcon className="h-3.5 w-3.5 shrink-0 sm:h-4 sm:w-4" style={{ color: active ? '#fff' : 'var(--text-tertiary)' }} />
                  ) : (
                    <BulbIcon className="h-3.5 w-3.5 shrink-0 sm:h-4 sm:w-4" style={{ color: active ? '#fff' : 'var(--text-tertiary)' }} />
                  )}
                  {c.label}
                </button>
              )
            })}
          </div>

          <div
            role="tablist"
            aria-label="排序"
            className="inline-flex max-w-full flex-wrap gap-0 rounded-full p-1"
            style={{ backgroundColor: 'var(--bg-secondary)' }}
          >
            {SORT_TABS.map((t) => {
              const active = sort === t.id
              return (
                <button
                  key={t.id}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => setSort(t.id)}
                  className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors motion-reduce:transition-none sm:text-[13px] cursor-pointer"
                  style={
                    active
                      ? {
                          backgroundColor: 'var(--bg-container)',
                          color: 'var(--text-primary)',
                          boxShadow: 'var(--shadow-sm)',
                          fontWeight: 600,
                        }
                      : {
                          backgroundColor: 'transparent',
                          color: 'var(--text-secondary)',
                        }
                  }
                >
                  {t.label}
                </button>
              )
            })}
          </div>

          <section
            className="min-h-[16rem] rounded-[var(--radius-lg)] border px-4 py-4 sm:px-5 sm:py-5"
            style={{
              borderColor: 'var(--border-default)',
              backgroundColor: 'var(--bg-container)',
              boxShadow: 'var(--shadow-sm)',
            }}
            aria-live="polite"
          >
            {filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 sm:py-16">
                <EmptySearchIllustration className="h-20 w-20 sm:h-24 sm:w-24" />
                <p className="mt-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
                  未找到匹配的技能
                </p>
                <button
                  type="button"
                  onClick={resetFilters}
                  className="mt-3 text-sm font-medium underline-offset-4 transition-opacity hover:opacity-80 motion-reduce:transition-none cursor-pointer"
                  style={{ color: ACCENT }}
                >
                  查看全部
                </button>
              </div>
            ) : (
              <ul className="divide-y" style={{ borderColor: 'var(--border-default)' }}>
                {filtered.map((d) => (
                  <li key={d.key} className="flex gap-3 py-3 first:pt-0 last:pb-0">
                    <span
                      className="w-9 shrink-0 pt-0.5 font-mono text-[11px] tabular-nums sm:w-10 sm:text-xs"
                      style={{ color: 'var(--text-tertiary)' }}
                    >
                      {d.key}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                        {d.name}
                      </p>
                      <p className="mt-0.5 text-xs leading-relaxed sm:text-[13px]" style={{ color: 'var(--text-secondary)' }}>
                        {d.summary}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
      </div>
    </ImmersiveAppShell>
  )
}
