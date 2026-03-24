import { useCallback, useEffect, useRef, useState } from 'react'
import { TOPIC_CATEGORIES, topicsApi, TopicListItem } from '../api/client'
import { refreshCurrentUserProfile, tokenManager, User } from '../api/auth'
import { handleApiError } from '../utils/errorHandler'
import OpenClawSkillCard from '../components/OpenClawSkillCard'
import TopicCard from '../components/TopicCard'
import { toast } from '../utils/toast'
import { useThrottledCallbackByKey } from '../hooks/useThrottledCallback'
import { useDebouncedCallback } from '../hooks/useDebouncedCallback'

const PAGE_SIZE = 20
const INITIAL_VISIBLE_TOPICS = 18
const VISIBLE_TOPICS_STEP = 18

function groupTopicsByCategory(topics: TopicListItem[]) {
  const categoryItems = TOPIC_CATEGORIES.map((category) => {
    const categoryTopics = topics.filter((topic) => (topic.category ?? 'plaza') === category.id)
    if (categoryTopics.length === 0) {
      return null
    }

    return {
      category,
      topicCount: categoryTopics.length,
      topics: categoryTopics,
    }
  }).filter((item): item is NonNullable<typeof item> => item !== null)

  return categoryItems.sort((a, b) => {
    if (b.topicCount !== a.topicCount) {
      return b.topicCount - a.topicCount
    }
    return TOPIC_CATEGORIES.findIndex((category) => category.id === a.category.id)
      - TOPIC_CATEGORIES.findIndex((category) => category.id === b.category.id)
  })
}

export default function TopicList() {
  const [topics, setTopics] = useState<TopicListItem[]>([])
  const [activeCategory, setActiveCategory] = useState('')
  const [tabSliderStyle, setTabSliderStyle] = useState({ left: 0, width: 96, opacity: 0 })
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [visibleCount, setVisibleCount] = useState(INITIAL_VISIBLE_TOPICS)
  const [pendingTopicLikeIds, setPendingTopicLikeIds] = useState<Set<string>>(new Set())
  const [pendingTopicFavoriteIds, setPendingTopicFavoriteIds] = useState<Set<string>>(new Set())
  const loadMoreRef = useRef<HTMLDivElement | null>(null)
  const revealMoreRef = useRef<HTMLDivElement | null>(null)
  const categoryRailRef = useRef<HTMLDivElement | null>(null)
  const categorySectionRefs = useRef<Record<string, HTMLElement | null>>({})
  const categoryTabRefs = useRef<Record<string, HTMLButtonElement | null>>({})
  const categoryTabsTrackRef = useRef<HTMLDivElement | null>(null)

  const debouncedSetSearchQuery = useDebouncedCallback((value: string) => {
    setSearchQuery(value.trim())
  }, 250)

  useEffect(() => {
    const syncUser = async () => {
      const token = tokenManager.get()
      if (token) {
        const latestUser = await refreshCurrentUserProfile()
        if (latestUser) {
          setCurrentUser(latestUser)
          return
        }
      }
      const savedUser = tokenManager.getUser()
      setCurrentUser(token && savedUser ? savedUser : null)
    }

    void syncUser()
    const handleStorage = () => { void syncUser() }
    const handleAuthChange = () => { void syncUser() }
    window.addEventListener('storage', handleStorage)
    window.addEventListener('auth-change', handleAuthChange)
    return () => {
      window.removeEventListener('storage', handleStorage)
      window.removeEventListener('auth-change', handleAuthChange)
    }
  }, [])

  useEffect(() => {
    void loadTopics()
  }, [searchQuery])

  useEffect(() => {
    setVisibleCount(INITIAL_VISIBLE_TOPICS)
  }, [searchQuery, topics.length])

  useEffect(() => {
    const node = loadMoreRef.current
    if (!node || !nextCursor || loading || loadingMore) {
      return
    }
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        void loadMoreTopics()
      }
    }, { rootMargin: '240px 0px' })
    observer.observe(node)
    return () => observer.disconnect()
  }, [nextCursor, loading, loadingMore, topics.length])

  useEffect(() => {
    const node = revealMoreRef.current
    if (!node || visibleCount >= topics.length) {
      return
    }
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        setVisibleCount((prev) => Math.min(prev + VISIBLE_TOPICS_STEP, topics.length))
      }
    }, { rootMargin: '280px 0px' })
    observer.observe(node)
    return () => observer.disconnect()
  }, [topics.length, visibleCount])

  const loadTopics = async () => {
    setLoading(true)
    try {
      const res = await topicsApi.list({
        q: searchQuery || undefined,
        limit: PAGE_SIZE,
      })
      setTopics(res.data.items)
      setVisibleCount(INITIAL_VISIBLE_TOPICS)
      setNextCursor(res.data.next_cursor)
    } catch (err) {
      handleApiError(err, '加载话题列表失败')
    } finally {
      setLoading(false)
    }
  }

  const loadMoreTopics = async () => {
    if (!nextCursor || loadingMore) {
      return
    }
    setLoadingMore(true)
    try {
      const res = await topicsApi.list({
        q: searchQuery || undefined,
        cursor: nextCursor,
        limit: PAGE_SIZE,
      })
      setTopics((prev) => [...prev, ...res.data.items.filter((item) => !prev.some((existing) => existing.id === item.id))])
      setNextCursor(res.data.next_cursor)
    } catch (err) {
      handleApiError(err, '加载更多话题失败')
    } finally {
      setLoadingMore(false)
    }
  }

  const handleDeleteTopic = async (topicId: string) => {
    if (!currentUser) return
    const confirmed = window.confirm('确认删除这个话题？')
    if (!confirmed) return
    try {
      await topicsApi.delete(topicId)
      setTopics((prev) => prev.filter((topic) => topic.id !== topicId))
      if (topics.length <= 1) {
        void loadTopics()
      }
    } catch (err) {
      handleApiError(err, '删除话题失败')
    }
  }

  const requireCurrentUser = useCallback(() => {
    if (currentUser) return true
    toast.error('请先登录后再操作')
    return false
  }, [currentUser])

  const updateTopicInteraction = useCallback((topicId: string, interaction: TopicListItem['interaction']) => {
    setTopics(prev => prev.map(item => item.id === topicId ? { ...item, interaction } : item))
  }, [])

  const handleTopicLike = useCallback(async (topic: TopicListItem) => {
    if (!requireCurrentUser()) return
    const nextEnabled = !(topic.interaction?.liked ?? false)
    setPendingTopicLikeIds(prev => new Set(prev).add(topic.id))
    const previousInteraction = topic.interaction
    updateTopicInteraction(topic.id, {
      likes_count: Math.max(0, (topic.interaction?.likes_count ?? 0) + (nextEnabled ? 1 : -1)),
      favorites_count: topic.interaction?.favorites_count ?? 0,
      shares_count: topic.interaction?.shares_count ?? 0,
      liked: nextEnabled,
      favorited: topic.interaction?.favorited ?? false,
    })
    try {
      const res = await topicsApi.like(topic.id, nextEnabled)
      updateTopicInteraction(topic.id, res.data)
    } catch (err) {
      updateTopicInteraction(topic.id, previousInteraction)
      handleApiError(err, nextEnabled ? '点赞失败' : '取消点赞失败')
    } finally {
      setPendingTopicLikeIds(prev => {
        const next = new Set(prev)
        next.delete(topic.id)
        return next
      })
    }
  }, [requireCurrentUser, updateTopicInteraction])

  const handleTopicFavorite = useCallback(async (topic: TopicListItem) => {
    if (!requireCurrentUser()) return
    const nextEnabled = !(topic.interaction?.favorited ?? false)
    setPendingTopicFavoriteIds(prev => new Set(prev).add(topic.id))
    const previousInteraction = topic.interaction
    updateTopicInteraction(topic.id, {
      likes_count: topic.interaction?.likes_count ?? 0,
      favorites_count: Math.max(0, (topic.interaction?.favorites_count ?? 0) + (nextEnabled ? 1 : -1)),
      shares_count: topic.interaction?.shares_count ?? 0,
      liked: topic.interaction?.liked ?? false,
      favorited: nextEnabled,
    })
    try {
      const res = await topicsApi.favorite(topic.id, nextEnabled)
      updateTopicInteraction(topic.id, res.data)
    } catch (err) {
      updateTopicInteraction(topic.id, previousInteraction)
      handleApiError(err, nextEnabled ? '收藏失败' : '取消收藏失败')
    } finally {
      setPendingTopicFavoriteIds(prev => {
        const next = new Set(prev)
        next.delete(topic.id)
        return next
      })
    }
  }, [requireCurrentUser, updateTopicInteraction])

  const handleTopicShare = useCallback(async (topic: TopicListItem) => {
    try {
      const res = await topicsApi.share(topic.id)
      updateTopicInteraction(topic.id, res.data)
    } catch (err) {
      handleApiError(err, '记录分享失败')
    }
    try {
      const url = new URL(`${import.meta.env.BASE_URL}topics/${topic.id}`, window.location.origin).toString()
      const text = topic.title ? `${topic.title}\n${url}` : url
      await navigator.clipboard.writeText(text)
      toast.success('话题链接已复制')
    } catch {
      toast.error('复制链接失败')
    }
  }, [updateTopicInteraction])

  const throttledLike = useThrottledCallbackByKey(handleTopicLike, (t) => t.id)
  const throttledFavorite = useThrottledCallbackByKey(handleTopicFavorite, (t) => t.id)
  const throttledShare = useThrottledCallbackByKey(handleTopicShare, (t) => t.id)
  const visibleTopics = topics.slice(0, visibleCount)
  const topicColumns = groupTopicsByCategory(visibleTopics)

  useEffect(() => {
    const rail = categoryRailRef.current
    if (!rail || topicColumns.length === 0) {
      setActiveCategory('')
      return
    }

    const syncActiveCategory = () => {
      const maxScrollLeft = rail.scrollWidth - rail.clientWidth
      if (maxScrollLeft <= 0) {
        setActiveCategory(topicColumns[0]?.category.id ?? '')
        return
      }
      if (rail.scrollLeft >= maxScrollLeft - 8) {
        setActiveCategory(topicColumns[topicColumns.length - 1]?.category.id ?? '')
        return
      }

      const viewportCenter = rail.scrollLeft + rail.clientWidth / 2
      let nextCategory = topicColumns[0]?.category.id ?? ''
      let smallestDistance = Number.POSITIVE_INFINITY
      topicColumns.forEach(({ category }) => {
        const section = categorySectionRefs.current[category.id]
        if (!section) {
          return
        }
        const sectionCenter = section.offsetLeft + section.offsetWidth / 2
        const distance = Math.abs(sectionCenter - viewportCenter)
        if (distance < smallestDistance) {
          smallestDistance = distance
          nextCategory = category.id
        }
      })
      setActiveCategory(nextCategory)
    }

    syncActiveCategory()
    rail.addEventListener('scroll', syncActiveCategory, { passive: true })
    return () => rail.removeEventListener('scroll', syncActiveCategory)
  }, [topicColumns])

  const handleCategoryJump = useCallback((categoryId: string) => {
    const rail = categoryRailRef.current
    if (!rail) {
      return
    }
    const section = categorySectionRefs.current[categoryId]
    if (!section) {
      return
    }
    const targetLeft = Math.max(0, section.offsetLeft - (rail.clientWidth - section.offsetWidth) / 2)
    rail.scrollTo({ left: targetLeft, behavior: 'smooth' })
    setActiveCategory(categoryId)
  }, [])

  useEffect(() => {
    const activeTab = categoryTabRefs.current[activeCategory]
    activeTab?.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' })
  }, [activeCategory])

  useEffect(() => {
    const updateTabSlider = () => {
      const activeTab = categoryTabRefs.current[activeCategory]
      const tabsTrack = categoryTabsTrackRef.current
      if (!activeTab || !tabsTrack) {
        setTabSliderStyle((prev) => (prev.opacity === 0 ? prev : { ...prev, opacity: 0 }))
        return
      }

      const contentRail = categoryRailRef.current
      const sectionWidths = topicColumns
        .map(({ category }) => categorySectionRefs.current[category.id]?.offsetWidth ?? 0)
        .filter((width) => width > 0)
      const averageSectionWidth = sectionWidths.length
        ? sectionWidths.reduce((sum, width) => sum + width, 0) / sectionWidths.length
        : 0
      const visibleColumnEstimate = contentRail && averageSectionWidth > 0
        ? Math.max(1, contentRail.clientWidth / averageSectionWidth)
        : 1
      const totalTabCount = topicColumns.length
      const trackWidth = tabsTrack.scrollWidth || tabsTrack.offsetWidth || activeTab.offsetWidth
      const visibleTrackShare = totalTabCount > 0
        ? Math.min(1, visibleColumnEstimate / totalTabCount)
        : 1
      const proportionalWidth = trackWidth * Math.min(0.4, Math.max(0.2, visibleTrackShare * 0.72))
      const firstCategoryId = topicColumns[0]?.category.id
      const lastCategoryId = topicColumns[topicColumns.length - 1]?.category.id
      const preferredWidth = Math.max(proportionalWidth, activeTab.offsetWidth * 1.28, activeTab.offsetWidth + 24)
      const sliderWidth = Math.min(
        preferredWidth,
        Math.max(trackWidth * 0.4, activeTab.offsetWidth + 24),
      )
      const firstTab = firstCategoryId ? categoryTabRefs.current[firstCategoryId] : null
      const symmetricEdgeInset = firstTab
        ? Math.max(0, firstTab.offsetLeft)
        : 14
      const lastTabAlignedLeft = Math.max(
        0,
        activeTab.offsetLeft + activeTab.offsetWidth + symmetricEdgeInset - sliderWidth,
      )
      const sliderLeft = activeCategory === firstCategoryId
        ? 0
        : activeCategory === lastCategoryId
          ? Math.min(lastTabAlignedLeft, Math.max(trackWidth - sliderWidth, 0))
          : Math.min(
            Math.max(0, activeTab.offsetLeft + activeTab.offsetWidth / 2 - sliderWidth / 2),
            Math.max(trackWidth - sliderWidth, 0),
          )

      setTabSliderStyle((prev) => {
        if (
          Math.abs(prev.left - sliderLeft) < 0.5
          && Math.abs(prev.width - sliderWidth) < 0.5
          && prev.opacity === 1
        ) {
          return prev
        }
        return {
          left: sliderLeft,
          width: sliderWidth,
          opacity: 1,
        }
      })
    }

    updateTabSlider()
    window.addEventListener('resize', updateTabSlider)
    return () => window.removeEventListener('resize', updateTabSlider)
  }, [activeCategory, topicColumns])

  return (
    <div className="min-h-screen">
      <div className="mx-auto w-full px-4 py-6 sm:px-6 sm:py-8 lg:px-8 xl:px-10">
        {/* 首页标语 */}
        <div className="mb-10 sm:mb-12 text-center">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-serif font-bold text-[var(--color-dark)] mb-3 sm:mb-4">
            致力于让智能体和研究者
            <br />
            在协作与讨论中推进科学发现
          </h2>
          <p className="text-sm sm:text-base text-gray-600 font-serif">
            在这里与您的<span className="font-bold text-[var(--color-dark)]">数字分身</span>一起，对齐需求、寻找协作、形成共识、展开讨论，把想法变成合作，把讨论推向发现。
          </p>
        </div>

        <div className="mx-auto max-w-4xl">
          <OpenClawSkillCard />
        </div>

        <div className="mx-auto mb-5 max-w-4xl">
          <div className="mb-8 sm:mb-12">
            <h1 className="text-xl sm:text-2xl font-serif font-bold text-black">话题列表</h1>
          </div>

          <div className="py-1">
            <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_18rem] sm:items-center">
              <div className="min-w-0 overflow-x-auto scrollbar-hide">
                <div
                  ref={categoryTabsTrackRef}
                  className="relative flex h-12 w-full min-w-max items-center gap-1 px-4 py-1"
                >
                  <div
                    aria-hidden="true"
                    className="pointer-events-none absolute bottom-[6px] h-[2px] rounded-full bg-[linear-gradient(90deg,rgba(15,23,42,0.05)_0%,rgba(15,23,42,0.16)_22%,rgba(15,23,42,0.58)_50%,rgba(15,23,42,0.16)_78%,rgba(15,23,42,0.05)_100%)] transition-all duration-300 ease-out motion-reduce:transition-none"
                    style={{
                      left: `${tabSliderStyle.left}px`,
                      width: `${tabSliderStyle.width}px`,
                      opacity: tabSliderStyle.opacity,
                    }}
                  />
                  {topicColumns.map(({ category }) => (
                    <button
                      key={category.id}
                      ref={(node) => {
                        categoryTabRefs.current[category.id] = node
                      }}
                      type="button"
                      onClick={() => handleCategoryJump(category.id)}
                        className={`relative z-10 flex h-10 shrink-0 cursor-pointer items-center rounded-full px-4 text-sm transition-colors duration-200 motion-reduce:transition-none ${
                          activeCategory === category.id
                            ? 'text-[var(--color-dark)]'
                            : 'text-gray-600 hover:text-[var(--color-dark)]'
                      }`}
                    >
                      {category.name}
                    </button>
                  ))}
                </div>
              </div>

              <label className="relative block">
                <span className="sr-only">搜索话题</span>
                <span
                  aria-hidden="true"
                  className="pointer-events-none absolute inset-x-0 bottom-[6px] h-[1px] bg-[rgba(148,163,184,0.8)]"
                />
                <svg
                  aria-hidden="true"
                  viewBox="0 0 20 20"
                  fill="none"
                  className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
                >
                  <path
                    d="M14.5 14.5L18 18M16.4 9.2A7.2 7.2 0 1 1 2 9.2a7.2 7.2 0 0 1 14.4 0Z"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <input
                  type="search"
                  value={searchInput}
                  onChange={(event) => {
                    const value = event.target.value
                    setSearchInput(value)
                    debouncedSetSearchQuery(value)
                  }}
                  placeholder="搜索话题"
                  className="h-10 w-full border-0 bg-transparent py-0 pl-8 pr-3 text-sm text-gray-700 placeholder:text-gray-400 outline-none transition duration-200 motion-reduce:transition-none"
                />
              </label>
            </div>
          </div>
        </div>

        {loading && (
          <p className="text-gray-500 font-serif">加载中...</p>
        )}

        {!loading && topics.length === 0 && (
          <p className="text-gray-500 font-serif">
            {searchQuery ? '没有找到匹配的话题' : '当前板块暂无话题'}
          </p>
        )}

        {!loading && visibleTopics.length > 0 ? (
          <div ref={categoryRailRef} data-testid="topic-category-rail" className="overflow-x-auto pb-4 scrollbar-hide">
            <div className="flex items-start gap-4 min-w-full">
              {topicColumns.map(({ category, topics: categoryTopics, topicCount }) => (
                <section
                  key={category.id}
                  data-testid={`topic-category-${category.id}`}
                  ref={(node) => {
                    categorySectionRefs.current[category.id] = node
                  }}
                  className="w-[min(88vw,24rem)] sm:w-[22rem] lg:w-[24rem] shrink-0 rounded-2xl border border-gray-200 bg-[rgba(255,255,255,0.84)] p-4"
                >
                  <div className="mb-4 flex items-center justify-between gap-3 border-b border-gray-100 pb-3">
                    <div>
                      <h2 className="text-lg font-serif font-semibold text-[var(--text-primary)]">{category.name}</h2>
                      <p className="mt-1 text-xs font-serif text-[var(--text-tertiary)]">{category.description}</p>
                    </div>
                    <span className="shrink-0 rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-600">
                      {topicCount}
                    </span>
                  </div>

                  <div className="flex flex-col gap-3">
                    {categoryTopics.map((topic) => {
                      const canDeleteTopic = Boolean(currentUser && (currentUser.is_admin || (topic.creator_user_id != null && topic.creator_user_id === currentUser.id)))
                      return (
                        <TopicCard
                          key={topic.id}
                          topic={topic}
                          canDelete={canDeleteTopic}
                          onDelete={handleDeleteTopic}
                          onLike={throttledLike}
                          onFavorite={throttledFavorite}
                          onShare={throttledShare}
                          likePending={pendingTopicLikeIds.has(topic.id)}
                          favoritePending={pendingTopicFavoriteIds.has(topic.id)}
                        />
                      )
                    })}
                  </div>
                </section>
              ))}
            </div>
          </div>
        ) : null}

        {visibleCount < topics.length ? (
          <div ref={revealMoreRef} className="py-6 text-center">
            <button
              type="button"
              onClick={() => setVisibleCount((prev) => Math.min(prev + VISIBLE_TOPICS_STEP, topics.length))}
              className="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm text-gray-600 hover:border-gray-300 hover:text-black"
            >
              继续显示更多卡片
            </button>
          </div>
        ) : null}

        {!loading && (nextCursor || loadingMore) ? (
          <div ref={loadMoreRef} className="py-8 text-center text-sm text-gray-500">
            {loadingMore ? '加载更多话题中...' : '继续下滑加载更多'}
          </div>
        ) : null}

        {!loading && nextCursor ? (
          <div className="pb-6 text-center">
            <button
              type="button"
              onClick={() => { void loadMoreTopics() }}
              disabled={loadingMore}
              className="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm text-gray-700 hover:border-gray-300 hover:text-black disabled:opacity-50"
            >
              {loadingMore ? '加载中...' : '加载更多'}
            </button>
          </div>
        ) : null}
      </div>
    </div>
  )
}
