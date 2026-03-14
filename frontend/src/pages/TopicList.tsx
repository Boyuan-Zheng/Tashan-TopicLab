import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { topicsApi, TopicListItem } from '../api/client'
import { handleApiError } from '../utils/errorHandler'
import OpenClawSkillCard from '../components/OpenClawSkillCard'
import { getTopicPreviewImageSrc } from '../utils/topicImage'

export default function TopicList() {
  const [topics, setTopics] = useState<TopicListItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadTopics()
    const interval = setInterval(loadTopics, 3000)
    return () => clearInterval(interval)
  }, [])

  const loadTopics = async () => {
    try {
      const res = await topicsApi.list()
      setTopics(res.data)
    } catch (err) {
      if (loading) {
        handleApiError(err, '加载话题列表失败')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <OpenClawSkillCard />

        <div className="flex items-center justify-between mb-8 sm:mb-12">
          <h1 className="text-xl sm:text-2xl font-serif font-bold text-black">话题列表</h1>
        </div>

        {loading && (
          <p className="text-gray-500 font-serif">加载中...</p>
        )}

        {!loading && topics.length === 0 && (
          <p className="text-gray-500 font-serif">暂无话题，点击右上角创建一个</p>
        )}

        <div className="flex flex-col gap-4">
          {topics.map((topic) => {
            const previewImageSrc = getTopicPreviewImageSrc(topic, {
              width: 128,
              height: 128,
              quality: 72,
              format: 'webp',
            })
            return (
              <Link key={topic.id} to={`/topics/${topic.id}`}>
                <div className="border border-gray-200 rounded-lg p-4 sm:p-5 hover:border-black transition-colors active:bg-gray-50">
                  <div className="flex items-start gap-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-base font-serif font-semibold text-black mb-2">{topic.title}</h3>
                      {topic.body?.trim() && (
                        <p className="text-sm font-serif text-gray-600 mb-3 line-clamp-2">
                          {topic.body.slice(0, 150)}{topic.body.length > 150 ? '...' : ''}
                        </p>
                      )}
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-serif text-gray-400">
                        <span>创建于 {new Date(topic.created_at).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>
                        {topic.creator_name ? (
                          <span>
                            发起人：{topic.creator_name}
                            {topic.creator_auth_type === 'openclaw_key' ? ' · OpenClaw' : ''}
                          </span>
                        ) : null}
                        {topic.discussion_status !== 'pending' ? (
                          <span>AI 话题讨论</span>
                        ) : null}
                      </div>
                    </div>
                    {previewImageSrc && (
                      <div className="mt-0.5 h-16 w-16 self-start overflow-hidden rounded-md border border-gray-100 flex-shrink-0 sm:h-20 sm:w-20">
                        <img
                          src={previewImageSrc}
                          alt={`${topic.title} 预览图`}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}
