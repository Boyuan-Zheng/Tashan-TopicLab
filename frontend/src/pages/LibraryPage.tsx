import { Link, Navigate, useParams } from 'react-router-dom'
import LibraryPageLayout from '../components/LibraryPageLayout'
import { ExpertLibraryContent } from './ExpertList'
import { ModeratorModeLibraryContent } from './ModeratorModeLibrary'
import { SkillLibraryContent } from './SkillLibrary'
import { MCPLibraryContent } from './MCPLibrary'

const librarySections = [
  {
    id: 'experts',
    label: '角色库',
    description: '查看平台角色库，快速浏览与打开角色详情。',
    render: () => <ExpertLibraryContent />,
  },
  {
    id: 'moderator-modes',
    label: '讨论方式库',
    description: '切换不同主持模式，查看可复用的讨论编排方案。',
    render: () => <ModeratorModeLibraryContent />,
  },
  {
    id: 'skills',
    label: '技能库',
    description: '浏览可分配技能与详细说明。',
    render: () => <SkillLibraryContent />,
  },
  {
    id: 'mcp',
    label: 'MCP 库',
    description: '查看可接入的 MCP 服务配置与说明。',
    render: () => <MCPLibraryContent />,
  },
] as const

type LibrarySectionId = (typeof librarySections)[number]['id']

function isLibrarySectionId(value: string | undefined): value is LibrarySectionId {
  return librarySections.some((section) => section.id === value)
}

export default function LibraryPage() {
  const { section } = useParams<{ section: string }>()

  if (!isLibrarySectionId(section)) {
    return <Navigate to="/library/experts" replace />
  }

  const activeSection = librarySections.find((item) => item.id === section)

  if (!activeSection) {
    return <Navigate to="/library/experts" replace />
  }

  return (
    <LibraryPageLayout title="库">
      <div className="flex flex-col md:flex-row md:items-start md:gap-8">
        <div className="relative md:w-[172px] md:flex-shrink-0">
          <div
            className="flex items-center gap-2 overflow-x-auto border-b px-4 py-3 md:flex-col md:items-stretch md:gap-0.5 md:border-b-0 md:px-0 md:py-0 md:sticky md:top-20 scrollbar-hide"
            style={{
              borderColor: 'var(--border-default)',
              backgroundColor: 'transparent',
            }}
          >
            {librarySections.map((item) => {
              const active = item.id === activeSection.id
              return (
                <Link
                  key={item.id}
                  to={`/library/${item.id}`}
                  className={`block rounded-lg px-3 py-1.5 text-sm font-serif whitespace-nowrap transition-colors md:w-full ${
                    active
                      ? 'font-semibold'
                      : ''
                  }`}
                  style={{
                    backgroundColor: active ? 'var(--bg-secondary)' : 'transparent',
                    color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                  }}
                  onMouseEnter={(e) => {
                    if (!active) {
                      e.currentTarget.style.backgroundColor = 'var(--bg-hover)'
                      e.currentTarget.style.color = 'var(--text-primary)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!active) {
                      e.currentTarget.style.backgroundColor = 'transparent'
                      e.currentTarget.style.color = 'var(--text-secondary)'
                    }
                  }}
                >
                  {item.label}
                </Link>
              )
            })}
          </div>
          <div className="md:hidden absolute right-0 top-0 bottom-0 w-6 pointer-events-none" style={{ background: 'linear-gradient(to left, var(--bg-container), transparent)' }} aria-hidden />
        </div>

        <div className="flex-1 min-w-0 pt-5 md:pt-0">
          <p className="text-sm mb-6" style={{ color: 'var(--text-secondary)' }}>{activeSection.description}</p>
          {activeSection.render()}
        </div>
      </div>
    </LibraryPageLayout>
  )
}
