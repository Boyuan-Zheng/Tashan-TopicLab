import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import LibraryPageLayout from '../components/LibraryPageLayout'
import { AppCatalogItem, appsApi } from '../api/client'
import { handleApiError } from '../utils/errorHandler'
import { toast } from '../utils/toast'

const QUICK_LINKS = [
  { label: 'SkillHub', href: 'https://skillhub.tencent.com/' },
]

type AppDisplayItem = AppCatalogItem & {
  install_command?: string
}

function AppIcon({ kind }: { kind?: string }) {
  if (kind === 'spark') {
    return (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 3.75l1.7 4.8 4.8 1.7-4.8 1.7-1.7 4.8-1.7-4.8-4.8-1.7 4.8-1.7 1.7-4.8z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M18.25 15.75l.75 2.25 2.25.75-2.25.75-.75 2.25-.75-2.25-2.25-.75 2.25-.75.75-2.25zM4.75 14.75l.55 1.65 1.65.55-1.65.55-.55 1.65-.55-1.65-1.65-.55 1.65-.55.55-1.65z" />
      </svg>
    )
  }

  return (
    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4.75 17.25V6.75A1.75 1.75 0 016.5 5h11a1.75 1.75 0 011.75 1.75v10.5A1.75 1.75 0 0117.5 19h-11a1.75 1.75 0 01-1.75-1.75z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M7.75 15.25l2.5-3 2.25 2 3.75-4.5" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M7.75 9.25h.01M16.25 9.25h.01" />
    </svg>
  )
}

function openFeedbackDraft(app: AppDisplayItem) {
  window.dispatchEvent(new CustomEvent('open-feedback-draft', {
    detail: {
      scenario: app.openclaw?.review_feedback?.scenario ?? `apps:${app.id}`,
      body: app.openclaw?.review_feedback?.body_template ?? `我要评价应用 ${app.name}。\n`,
    },
  }))
}

export default function AppsPage() {
  const navigate = useNavigate()
  const [apps, setApps] = useState<AppDisplayItem[]>([])
  const [version, setVersion] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pendingTopicIds, setPendingTopicIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    let alive = true

    const load = async () => {
      try {
        setLoading(true)
        setError(null)
        const res = await appsApi.list()
        if (!alive) return
        setApps(res.data.list)
        setVersion(res.data.version)
      } catch (err) {
        if (!alive) return
        setError(err instanceof Error ? err.message : '应用目录加载失败')
      } finally {
        if (alive) {
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      alive = false
    }
  }, [])

  const openTopic = async (app: AppDisplayItem) => {
    setPendingTopicIds((prev) => new Set(prev).add(app.id))
    try {
      const res = await appsApi.ensureTopic(app.id)
      navigate(`/topics/${res.data.topic.id}`)
      toast.success('已打开对应话题')
    } catch (err) {
      handleApiError(err, '打开应用对应话题失败')
    } finally {
      setPendingTopicIds((prev) => {
        const next = new Set(prev)
        next.delete(app.id)
        return next
      })
    }
  }

  return (
    <LibraryPageLayout title="应用">
      <div className="max-w-5xl">
        <p className="text-sm leading-6 sm:text-[15px]" style={{ color: 'var(--text-secondary)' }}>
          我们准备了一系列 Claw Ready 应用，您的 OpenClaw 可以直接使用这些应用帮助您完成场景化复杂任务。
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-2.5">
          <div className="mr-1 flex items-center gap-2 rounded-full border px-3 py-2" style={{ borderColor: 'var(--border-default)', backgroundColor: 'var(--bg-secondary)' }}>
            <span className="text-sm font-serif font-semibold" style={{ color: 'var(--text-primary)' }}>Apps</span>
            <span className="text-xs font-serif" style={{ color: 'var(--text-tertiary)' }}>外部导航</span>
          </div>
          {QUICK_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              target="_blank"
              rel="noreferrer"
              aria-label={link.label}
              className="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-serif font-semibold transition-colors"
              style={{ borderColor: 'var(--border-default)', backgroundColor: 'var(--bg-container)', color: 'var(--text-secondary)' }}
            >
              <span>{link.label}</span>
              <span className="flex h-6 w-6 items-center justify-center rounded-full" style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-tertiary)' }}>
                <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" className="h-3.5 w-3.5">
                  <path d="M7 13L13 7M8 7h5v5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
            </a>
          ))}
        </div>
        {version ? (
          <p className="mt-2 text-xs" style={{ color: 'var(--text-tertiary)' }}>
            Catalog version: {version}
          </p>
        ) : null}
      </div>

      {loading ? (
        <div className="mt-6 rounded-[var(--radius-xl)] border p-5 text-sm" style={{ borderColor: 'var(--border-default)', color: 'var(--text-secondary)' }}>
          正在加载应用目录…
        </div>
      ) : null}

      {error ? (
        <div className="mt-6 rounded-[var(--radius-xl)] border p-5 text-sm" style={{ borderColor: 'var(--accent-error)', color: 'var(--accent-error)' }}>
          {error}
        </div>
      ) : null}

      {!loading && !error ? (
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {apps.map((app) => (
            <article
              key={app.id}
              className="rounded-[var(--radius-xl)] border p-5 sm:p-6"
              style={{
                borderColor: 'var(--border-default)',
                backgroundColor: 'var(--bg-container)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <div className="flex items-start gap-4">
                <div
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl"
                  style={{
                    background: 'linear-gradient(180deg, rgba(241,245,249,0.95) 0%, rgba(226,232,240,0.92) 100%)',
                    color: 'var(--text-primary)',
                  }}
                >
                  <AppIcon kind={app.icon} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-serif font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {app.name}
                    </h2>
                    {app.command ? (
                      <span
                        className="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium"
                        style={{
                          backgroundColor: 'var(--bg-secondary)',
                          color: 'var(--text-secondary)',
                        }}
                      >
                        {app.command}
                      </span>
                    ) : null}
                  </div>
                  {app.install_command ? (
                    <div className="mt-3 rounded-[var(--radius-md)] border px-3 py-2" style={{ borderColor: 'var(--border-subtle)', backgroundColor: 'var(--bg-secondary)' }}>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em]" style={{ color: 'var(--text-tertiary)' }}>
                        安装
                      </p>
                      <p className="mt-1 font-mono text-xs sm:text-sm" style={{ color: 'var(--text-primary)' }}>
                        {app.install_command}
                      </p>
                    </div>
                  ) : null}
                  {app.summary ? (
                    <p className="mt-3 text-sm leading-6" style={{ color: 'var(--text-primary)' }}>
                      {app.summary}
                    </p>
                  ) : null}
                  {app.description ? (
                    <p className="mt-2 text-sm leading-6" style={{ color: 'var(--text-secondary)' }}>
                      {app.description}
                    </p>
                  ) : null}
                  {app.tags?.length ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {app.tags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center rounded-full px-2.5 py-1 text-xs"
                          style={{
                            backgroundColor: 'var(--bg-secondary)',
                            color: 'var(--text-tertiary)',
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>

              <div className="mt-5 flex flex-wrap gap-3">
                {app.links?.docs ? (
                  <a
                    href={app.links.docs}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center rounded-[var(--radius-md)] px-3 py-2 text-sm font-medium transition-opacity hover:opacity-90"
                    style={{
                      backgroundColor: 'var(--text-primary)',
                      color: 'var(--bg-container)',
                    }}
                  >
                    查看文档
                  </a>
                ) : null}
                {app.links?.repo ? (
                  <a
                    href={app.links.repo}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center rounded-[var(--radius-md)] border px-3 py-2 text-sm font-medium transition-colors"
                    style={{
                      borderColor: 'var(--border-default)',
                      color: 'var(--text-primary)',
                    }}
                  >
                    GitHub
                  </a>
                ) : null}
                <button
                  type="button"
                  onClick={() => void openTopic(app)}
                  disabled={pendingTopicIds.has(app.id)}
                  className="inline-flex items-center rounded-[var(--radius-md)] border px-3 py-2 text-sm font-medium transition-colors"
                  style={{
                    borderColor: 'var(--border-default)',
                    color: 'var(--text-primary)',
                  }}
                >
                  {pendingTopicIds.has(app.id) ? '打开中…' : '进入话题'}
                </button>
                <button
                  type="button"
                  onClick={() => openFeedbackDraft(app)}
                  className="inline-flex items-center rounded-[var(--radius-md)] border px-3 py-2 text-sm font-medium transition-colors"
                  style={{
                    borderColor: 'var(--border-default)',
                    color: 'var(--text-primary)',
                  }}
                >
                  评价应用
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </LibraryPageLayout>
  )
}
