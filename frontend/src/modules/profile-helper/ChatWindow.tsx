import { useState, useRef, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { MessageBubble } from './MessageBubble'
import { LoadingDots, RobotAvatar } from './LoadingDots'
import {
  getOrCreateSession,
  sendMessage,
  resetSession,
  getProfile,
} from './profileHelperApi'
import { PROFILE_HELPER_MODELS } from '../../api/client'
import { refreshCurrentUserProfile, tokenManager, User } from '../../api/auth'
import { toast } from '../../utils/toast'

const SESSION_KEYS = ['tashan_session_id', 'tashan_profile_session_id'] as const

function getStoredSessionId(): string | null {
  for (const key of SESSION_KEYS) {
    const value = localStorage.getItem(key)
    if (value) return value
  }
  return null
}

function setStoredSessionId(id: string) {
  for (const key of SESSION_KEYS) {
    localStorage.setItem(key, id)
  }
}

export function ChatWindow() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([])
  const [, setProfile] = useState('')
  const [, setForumProfile] = useState('')
  const [input, setInput] = useState('帮我建立分身')
  const [loading, setLoading] = useState(false)
  const [initialized, setInitialized] = useState(false)
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [selectedModel, setSelectedModel] = useState<string>(PROFILE_HELPER_MODELS[0]?.value ?? '')
  const [, setImportResult] = useState<string | null>(null)
  const [isComposing, setIsComposing] = useState(false)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const navigate = useNavigate()

  const requireCurrentUser = useCallback(() => {
    if (currentUser) return true
    toast.error('请先登录后再与数字分身助手对话')
    return false
  }, [currentUser])

  const fetchProfile = useCallback(async (sid: string) => {
    try {
      const data = await getProfile(sid)
      setProfile(data.profile)
      setForumProfile(data.forum_profile)
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    async function init() {
      const token = tokenManager.get()
      if (!token) {
        setCurrentUser(null)
        setInitialized(true)
        return
      }
      try {
        const user = await refreshCurrentUserProfile()
        setCurrentUser(user ?? null)
        if (!user) {
          setInitialized(true)
          return
        }
        const stored = getStoredSessionId()
        const id = await getOrCreateSession(stored ?? undefined)
        setSessionId(id)
        setStoredSessionId(id)
        await fetchProfile(id)
      } catch {
        setCurrentUser(null)
      } finally {
        setInitialized(true)
      }
    }
    init()
  }, [fetchProfile])

  useEffect(() => {
    if (!sessionId) return
    try {
      const raw = localStorage.getItem(`profile_helper_chat_${sessionId}`)
      if (raw) {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed)) {
          setMessages(parsed)
        }
      }
    } catch {
      // ignore
    }
  }, [sessionId])

  useEffect(() => {
    if (!sessionId) return
    try {
      localStorage.setItem(`profile_helper_chat_${sessionId}`, JSON.stringify(messages))
    } catch {
      // ignore
    }
  }, [sessionId, messages])

  useEffect(() => {
    const el = messagesContainerRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages])

  const handleSubmit = async () => {
    if (!requireCurrentUser()) return
    const text = input.trim()
    if (!text || !sessionId || loading) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)

    const assistantContent: string[] = []
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }])

    try {
      await sendMessage(sessionId, text, (chunk) => {
        assistantContent.push(chunk)
        setMessages((prev) => {
          const next = [...prev]
          const last = next[next.length - 1]
          if (last?.role === 'assistant') {
            next[next.length - 1] = {
              ...last,
              content: assistantContent.join(''),
            }
          }
          return next
        })
      }, selectedModel || undefined)
      await fetchProfile(sessionId)
    } catch (e) {
      setMessages((prev) => {
        const next = [...prev]
        const last = next[next.length - 1]
        if (last?.role === 'assistant' && last.content === '') {
          next[next.length - 1] = {
            ...last,
            content: `请求失败: ${e instanceof Error ? e.message : String(e)}`,
          }
        }
        return next
      })
    } finally {
      setLoading(false)
    }
  }

  const handleReset = async () => {
    if (!requireCurrentUser() || !sessionId) return
    try {
      await resetSession(sessionId)
      setMessages([])
      setImportResult(null)
      await fetchProfile(sessionId)
      inputRef.current?.focus()
    } catch (e) {
      alert(`重置失败: ${e instanceof Error ? e.message : String(e)}`)
    }
  }

  const showLoadingDots =
    loading &&
    messages.length > 0 &&
    messages[messages.length - 1]?.role === 'assistant' &&
    messages[messages.length - 1]?.content === ''

  if (!initialized) {
    return <div className="chat-loading">加载中...</div>
  }

  return (
    <div className="chat-layout">
      <div className="chat-window">
        <div ref={messagesContainerRef} className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <p>你好，我是科研数字分身采集助手。</p>
              <p>可以说「帮我建立分身」开始。</p>
            </div>
          )}
          {messages
            .filter(
              (m, i) =>
                !(
                  showLoadingDots &&
                  i === messages.length - 1 &&
                  m.role === 'assistant' &&
                  m.content === ''
                )
            )
            .map((m, i) => (
              <MessageBubble key={i} role={m.role} content={m.content} />
            ))}
          {showLoadingDots && (
            <div className="loading-message-row">
              <RobotAvatar />
              <div className="message-bubble assistant loading-bubble">
                <LoadingDots />
              </div>
            </div>
          )}
        </div>

        <form
          className="chat-input-container"
          onSubmit={(e) => {
            e.preventDefault()
            handleSubmit()
          }}
        >
          <div className="chat-input-inner">
            {!currentUser ? (
              <div className="chat-login-prompt">
                <p>请先登录后再与数字分身助手对话</p>
                <Link to="/login" state={{ from: '/profile-helper' }} className="chat-login-link">
                  去登录
                </Link>
              </div>
            ) : (
              <>
            {/* 输入区域 */}
            <div className="chat-input-row">
              <div className="chat-input-wrapper">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
                      e.preventDefault()
                      handleSubmit()
                    }
                  }}
                  onCompositionStart={() => setIsComposing(true)}
                  onCompositionEnd={() => setIsComposing(false)}
                  placeholder="输入消息..."
                  rows={3}
                  className="chat-textarea"
                />
              </div>
              <button
                type="submit"
                className="chat-send-btn"
                disabled={loading || !input.trim()}
              >
                {loading ? (
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </button>
            </div>

            {/* 底部：提示 + 模型选择 + 操作按钮 */}
            <div className="chat-hint-row">
              <span className="input-hint">Enter 发送 · Shift+Enter 换行</span>
              <div className="chat-hint-actions">
                <select
                  className="model-select-single"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  title="选择模型"
                >
                  {PROFILE_HELPER_MODELS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="chat-action-btn"
                  onClick={() => navigate('/profile-helper/profile')}
                >
                  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  我的分身
                </button>
                <button
                  type="button"
                  className="chat-action-btn"
                  onClick={handleReset}
                  disabled={loading}
                >
                  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  重置会话
                </button>
              </div>
            </div>
              </>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}