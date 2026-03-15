import { useMemo } from 'react'
import { useMCPGrid } from '../hooks/useMCPGrid'
import SourceCategoryToc from './SourceCategoryToc'
import ResizableToc from './ResizableToc'
import MobileSourceCategoryToc from './MobileSourceCategoryToc'
import MCPCard, { MCPChip } from './MCPCard'
import { sourceDisplayName } from '../utils/mcps'
import type { AssignableMCP } from '../api/client'

interface MCPGridViewProps {
  mode: 'view'
  onMcpClick: (mcp: AssignableMCP) => void
}

interface MCPGridSelectProps {
  mode: 'select'
  value: string[]
  onChange: (ids: string[]) => void
  onMcpClick?: (mcp: AssignableMCP) => void
}

type MCPGridProps = (MCPGridViewProps | MCPGridSelectProps) & {
  layout?: 'page' | 'embed'
  placeholder?: string
  maxHeight?: string
  fillHeight?: boolean
}

export default function MCPGrid(props: MCPGridProps) {
  const {
    layout = 'page',
    placeholder = '搜索 MCP 服务器名称、描述、分类...',
    maxHeight = '400px',
    fillHeight = false,
  } = props

  const sectionIdPrefix = layout === 'embed' ? 'mcp-section' : 'section'
  const {
    allMcps,
    filteredMcps,
    grouped,
    sourceOrder,
    loading,
    search,
    setSearch,
    tocTree,
    sectionRefs,
    scrollToSection,
    getMcpSectionId,
  } = useMCPGrid({ sectionIdPrefix })

  const selectedSet = useMemo(
    () => (props.mode === 'select' ? new Set(props.value) : new Set<string>()),
    [props.mode, props.mode === 'select' ? props.value : []]
  )

  const mcpById = useMemo(() => Object.fromEntries(allMcps.map((m) => [m.id, m])), [allMcps])

  const mobileTocData = useMemo(() => {
    const sources = sourceOrder.map((s) => ({
      id: `source-${s}`,
      label: sourceDisplayName(s),
    }))
    const categoriesBySource: Record<string, { id: string; label: string; sourceId: string }[]> = {}
    for (const source of sourceOrder) {
      const sid = `source-${source}`
      categoriesBySource[sid] = (tocTree[source] || []).map((c) => ({
        id: c.id,
        label: c.label,
        sourceId: sid,
      }))
    }
    return { sources, categoriesBySource }
  }, [tocTree, sourceOrder])

  const selectedMcps =
    props.mode === 'select'
      ? props.value.map((id) => mcpById[id]).filter(Boolean)
      : []

  const addMcp =
    props.mode === 'select'
      ? (id: string) => {
          if (selectedSet.has(id)) return
          props.onChange([...props.value, id])
        }
      : undefined

  const removeMcp =
    props.mode === 'select'
      ? (id: string) => {
          props.onChange(props.value.filter((x) => x !== id))
        }
      : undefined

  const renderGridContent = () => (
    <>
      {sourceOrder.map((source) => {
        const cats = grouped[source]
        const catKeys = Object.keys(cats).sort((a, b) =>
          a === '' ? 1 : b === '' ? -1 : a.localeCompare(b)
        )
        return (
          <div key={source} className="border-b last:border-b-0" style={{ borderColor: 'var(--border-default)' }}>
            <div
              id={`source-${source}`}
              ref={(el) => { sectionRefs.current[`source-${source}`] = el }}
              className="px-4 py-2.5 border-b sticky top-0 z-10 scroll-mt-6"
              style={{
                backgroundColor: 'var(--bg-secondary)',
                borderColor: 'var(--border-default)',
              }}
            >
              <h3 className="text-xs font-serif font-semibold uppercase tracking-wide" style={{ color: 'var(--text-primary)' }}>
                {sourceDisplayName(source)}
              </h3>
            </div>
            <div style={{ backgroundColor: 'var(--bg-tertiary)' }}>
              {catKeys.map((catId) => {
                const items = cats[catId]
                const catName = items[0]?.category_name || catId || '未分类'
                const sectionId = `${sectionIdPrefix}-${source}-${catId || '_'}`.replace(/\s+/g, '-')
                return (
                  <div
                    key={catId || '_'}
                    id={sectionId}
                    ref={(el) => { sectionRefs.current[sectionId] = el }}
                    className="p-3 scroll-mt-6"
                  >
                    <div className="text-[11px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-tertiary)' }}>
                      {catName}
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-4">
                      {items.map((m) =>
                        props.mode === 'view' ? (
                          <MCPCard
                            key={m.id}
                            mcp={m}
                            mode="view"
                            onClick={props.onMcpClick}
                            descriptionLines={layout === 'page' ? 2 : 1}
                            showId={layout === 'page'}
                          />
                        ) : (
                          <MCPCard
                            key={m.id}
                            mcp={m}
                            mode="select"
                            isSelected={selectedSet.has(m.id)}
                            onToggle={(mcp) =>
                              selectedSet.has(mcp.id) ? removeMcp!(mcp.id) : addMcp!(mcp.id)
                            }
                            onDetailClick={props.mode === 'select' ? props.onMcpClick : undefined}
                          />
                        )
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}
    </>
  )

  const isFill = layout === 'embed' && fillHeight
  const rootClass = isFill ? 'flex flex-col h-full min-h-0' : 'space-y-3'
  const gridHeightStyle = isFill ? undefined : (layout === 'embed' ? { maxHeight } : undefined)

  const searchInput = (
    <input
      type="text"
      placeholder={placeholder}
      value={search}
      onChange={(e) => setSearch(e.target.value)}
      className={
        isFill
          ? 'w-full flex-shrink-0 border-0 border-b rounded-none px-3 py-2 text-sm font-serif focus:outline-none transition-colors'
          : 'w-full border rounded-lg px-4 py-2.5 text-sm font-serif focus:outline-none transition-colors'
      }
      style={{
        backgroundColor: isFill ? 'var(--bg-secondary)' : 'var(--bg-container)',
        borderColor: isFill ? 'var(--border-default)' : 'var(--border-default)',
        color: 'var(--text-primary)',
      }}
      onFocus={(e) => {
        e.target.style.borderColor = 'var(--border-focus)'
      }}
      onBlur={(e) => {
        e.target.style.borderColor = 'var(--border-default)'
      }}
    />
  )

  const instructionText =
    props.mode === 'select' ? (
      <p className="text-xs mb-2 flex-shrink-0" style={{ color: 'var(--text-tertiary)' }}>
        点击 + 选择要启用的 MCP 服务器，选中的会拷贝到话题工作区。
        {selectedMcps.length === 0 && (
          <span className="ml-1">不选择则自动使用全部 MCP 服务器（共 {allMcps.length} 个）。</span>
        )}
      </p>
    ) : null

  const selectedChipsSection =
    props.mode === 'select' && selectedMcps.length > 0 ? (
      <div
        className={
          layout === 'embed' && filteredMcps.length > 0
            ? 'flex flex-wrap gap-2 px-4 py-2.5 border-b flex-shrink-0 max-h-28 overflow-y-auto overflow-x-hidden'
            : 'flex flex-wrap gap-2 p-3 rounded-lg border'
        }
        style={{
          backgroundColor: 'var(--bg-secondary)',
          borderColor: 'var(--border-default)',
        }}
      >
        <span className="text-xs font-semibold uppercase tracking-wide w-full mb-1" style={{ color: 'var(--text-tertiary)' }}>
          已选 MCP 服务器（点击跳转）
        </span>
        {selectedMcps.map((m) => (
          <MCPChip
            key={m.id}
            mcp={m}
            onRemove={() => removeMcp!(m.id)}
            onClick={() => scrollToSection(getMcpSectionId(m))}
          />
        ))}
      </div>
    ) : null

  return (
    <div className={rootClass}>
      {!isFill && searchInput}

      {instructionText}

      {selectedChipsSection && !(layout === 'embed' && filteredMcps.length > 0) && selectedChipsSection}

      {loading && <p className="font-serif text-sm" style={{ color: 'var(--text-tertiary)' }}>加载中...</p>}
      {!loading && filteredMcps.length === 0 && (
        <p className="font-serif text-sm" style={{ color: 'var(--text-tertiary)' }}>{search ? '无匹配 MCP' : '暂无 MCP 配置'}</p>
      )}

      {!loading && filteredMcps.length > 0 && (
        <div
          className={
            layout === 'embed' && selectedChipsSection
              ? `flex flex-col border rounded-lg overflow-hidden ${isFill ? 'flex-1 min-h-0' : ''}`
              : `flex ${layout === 'embed' ? 'gap-0 border rounded-lg overflow-hidden' : 'gap-8'} ${isFill ? 'flex-1 min-h-0' : ''}`
          }
          style={{
            borderColor: 'var(--border-default)',
            ...gridHeightStyle
          }}
        >
          {layout === 'embed' && selectedChipsSection && selectedChipsSection}
          <div
            className={
              layout === 'embed' && selectedChipsSection
                ? 'flex flex-1 min-h-0 min-w-0 overflow-x-hidden items-start'
                : layout === 'embed'
                  ? 'flex gap-0 flex-1 min-h-0 min-w-0 overflow-x-hidden items-start'
                  : 'flex gap-8 flex-1 min-h-0 min-w-0 overflow-x-hidden items-start'
            }
          >
          <div className={layout === 'embed' ? 'hidden sm:flex flex-shrink-0 self-start' : 'hidden md:flex flex-shrink-0 self-start'}>
            <ResizableToc
              defaultWidth={layout === 'embed' ? 128 : 176}
              minWidth={layout === 'embed' ? 100 : 120}
              maxWidth={layout === 'embed' ? 280 : 360}
              maxHeight={layout === 'embed' ? (isFill ? '100%' : maxHeight) : 'calc(100vh - 6rem)'}
              className={layout === 'page' ? 'sticky top-20 self-start' : ''}
            >
              <SourceCategoryToc
                tree={tocTree}
                sourceOrder={sourceOrder}
                sourceDisplayName={sourceDisplayName}
                onNavigate={scrollToSection}
                className="py-2"
              />
            </ResizableToc>
          </div>
          <div
            className={`flex-1 min-w-0 flex flex-col min-h-0 ${layout === 'embed' ? 'pl-3' : ''}`}
          >
            {layout === 'embed' && isFill && (
              <div className="flex-shrink-0">{searchInput}</div>
            )}
            {mobileTocData.sources.length > 0 && (
              <MobileSourceCategoryToc
                sources={mobileTocData.sources}
                categoriesBySource={mobileTocData.categoriesBySource}
                sourceOrder={sourceOrder}
                onNavigate={scrollToSection}
                visibleClass={layout === 'embed' ? 'sm:hidden' : 'md:hidden'}
              />
            )}
            <div
              className={`flex-1 min-h-0 ${layout === 'embed' ? 'overflow-auto' : ''}`}
            >
            {layout === 'page' ? (
              <div className="space-y-8">
                {sourceOrder.map((source) => {
                  const cats = grouped[source]
                  const catKeys = Object.keys(cats).sort((a, b) =>
                    a === '' ? 1 : b === '' ? -1 : a.localeCompare(b)
                  )
                  return (
                    <div key={source} className="border rounded-lg overflow-hidden" style={{ borderColor: 'var(--border-default)' }}>
                      <div
                        id={`source-${source}`}
                        ref={(el) => { sectionRefs.current[`source-${source}`] = el }}
                        className="px-4 py-3 border-b scroll-mt-6"
                        style={{
                          backgroundColor: 'var(--bg-secondary)',
                          borderColor: 'var(--border-default)',
                        }}
                      >
                        <h2 className="text-sm font-serif font-semibold uppercase tracking-wide" style={{ color: 'var(--text-primary)' }}>
                          {sourceDisplayName(source)}
                        </h2>
                      </div>
                      <div style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                        {catKeys.map((catId) => {
                          const items = cats[catId]
                          const catName = items[0]?.category_name || catId || '未分类'
                          const sectionId = `section-${source}-${catId || '_'}`.replace(/\s+/g, '-')
                          return (
                            <div
                              key={catId || '_'}
                              id={sectionId}
                              ref={(el) => { sectionRefs.current[sectionId] = el }}
                              className="p-4 scroll-mt-6"
                            >
                              <div className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--text-tertiary)' }}>
                                {catName}
                              </div>
                              <div className="grid grid-cols-1 sm:grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-4">
                                {items.map((m) =>
                                  props.mode === 'view' ? (
                                    <MCPCard
                                      key={m.id}
                                      mcp={m}
                                      mode="view"
                                      onClick={props.onMcpClick}
                                      descriptionLines={2}
                                      showId
                                    />
                                  ) : (
                                    <MCPCard
                                      key={m.id}
                                      mcp={m}
                                      mode="select"
                                      isSelected={selectedSet.has(m.id)}
                                      onToggle={(mcp) =>
                                        selectedSet.has(mcp.id) ? removeMcp!(mcp.id) : addMcp!(mcp.id)
                                      }
                                      onDetailClick={props.mode === 'select' ? props.onMcpClick : undefined}
                                    />
                                  )
                                )}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              renderGridContent()
            )}
            </div>
          </div>
          </div>
        </div>
      )}
    </div>
  )
}
