import { useState, useEffect, useCallback, useRef } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { createPortal } from 'react-dom'
import { refreshCurrentUserProfile, tokenManager, User } from '../api/auth'

const navLinks = [
  { to: '/', label: '话题列表', match: (path: string) => path === '/' && !path.startsWith('/topics') && !path.startsWith('/source-feed') && !path.startsWith('/library') && !path.startsWith('/profile-helper') && !path.startsWith('/agent-links') },
  { to: '/source-feed', label: '信源', match: (path: string) => path.startsWith('/source-feed') },
  { to: '/library', label: '库', match: (path: string) => path.startsWith('/library') || path.startsWith('/experts') || path.startsWith('/skills') || path.startsWith('/mcp') || path.startsWith('/moderator-modes') },
] as const

const mobileTabs = [
  {
    to: '/',
    label: '话题',
    match: (path: string) => path === '/' || path.startsWith('/topics'),
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M7 8h10M7 12h10M7 16h6" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M5.5 4.75h13A1.75 1.75 0 0120.25 6.5v11A1.75 1.75 0 0118.5 19.25h-13A1.75 1.75 0 013.75 17.5v-11A1.75 1.75 0 015.5 4.75z" />
      </svg>
    ),
  },
  {
    to: '/source-feed',
    label: '信源',
    match: (path: string) => path.startsWith('/source-feed'),
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M5.75 6.5A1.75 1.75 0 017.5 4.75h8.25A1.75 1.75 0 0117.5 6.5v11.25A1.5 1.5 0 0019 19.25h-10.5A2.75 2.75 0 015.75 16.5v-10z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M8.5 8.25h6M8.5 11.5h6M8.5 14.75h3.25" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M19 19.25a1.5 1.5 0 001.5-1.5V9.5h-3" />
      </svg>
    ),
  },
  {
    to: '/me',
    label: '我的',
    match: (path: string) =>
      path.startsWith('/me') ||
      path.startsWith('/profile-helper') ||
      path.startsWith('/favorites') ||
      path.startsWith('/library') ||
      path.startsWith('/experts') ||
      path.startsWith('/skills') ||
      path.startsWith('/mcp') ||
      path.startsWith('/moderator-modes'),
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 12a3.25 3.25 0 100-6.5 3.25 3.25 0 000 6.5z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M5 19.25a7 7 0 0114 0" />
      </svg>
    ),
  },
] as const

export default function TopNav() {
  const location = useLocation()
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [adminMode, setAdminMode] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [userMenuPosition, setUserMenuPosition] = useState({ top: 0, left: 0 })
  const [scrolled, setScrolled] = useState(false)
  const userMenuTriggerRef = useRef<HTMLButtonElement | null>(null)
  const userMenuRef = useRef<HTMLDivElement | null>(null)

  // 滚动监听 - 实现磨砂效果
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const loadUser = useCallback(async () => {
    const token = tokenManager.get()
    if (token) {
      const latestUser = await refreshCurrentUserProfile()
      if (latestUser) {
        setUser(latestUser)
        setAdminMode(Boolean(latestUser.is_admin))
        return
      }
    }
    const savedUser = tokenManager.getUser()
    if (savedUser && token) {
      setUser(savedUser)
      setAdminMode(Boolean(savedUser.is_admin))
    } else {
      setUser(null)
      setAdminMode(false)
    }
  }, [])

  useEffect(() => {
    void loadUser()
  }, [location.pathname, loadUser])

  useEffect(() => {
    const handleStorageChange = () => { void loadUser() }
    const handleAuthChange = () => { void loadUser() }
    window.addEventListener('storage', handleStorageChange)
    window.addEventListener('auth-change', handleAuthChange)
    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('auth-change', handleAuthChange)
    }
  }, [loadUser])

  const updateUserMenuPosition = useCallback(() => {
    const trigger = userMenuTriggerRef.current
    if (!trigger) return
    const rect = trigger.getBoundingClientRect()
    setUserMenuPosition({
      top: rect.bottom + 8,
      left: rect.right,
    })
  }, [])

  useEffect(() => {
    setUserMenuOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (!userMenuOpen) return
    updateUserMenuPosition()

    const handleWindowChange = () => updateUserMenuPosition()
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      if (
        userMenuRef.current?.contains(target) ||
        userMenuTriggerRef.current?.contains(target)
      ) {
        return
      }
      setUserMenuOpen(false)
    }
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setUserMenuOpen(false)
      }
    }

    window.addEventListener('resize', handleWindowChange)
    window.addEventListener('scroll', handleWindowChange, true)
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      window.removeEventListener('resize', handleWindowChange)
      window.removeEventListener('scroll', handleWindowChange, true)
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [userMenuOpen, updateUserMenuPosition])

  const handleLogout = () => {
    tokenManager.remove()
    tokenManager.clearUser()
    setUser(null)
    setUserMenuOpen(false)
    window.dispatchEvent(new CustomEvent('auth-change'))
    navigate('/')
  }

  const hideNav = location.pathname === '/login' || location.pathname === '/register'

  if (hideNav) {
    return null
  }

  return (
    <>
      <nav
        className={`fixed top-0 left-0 right-0 z-50 w-full safe-area-inset-top overflow-x-hidden transition-all duration-300 ${
          scrolled
            ? 'bg-white/95 backdrop-blur-xl shadow-[0_2px_8px_rgba(15,46,79,0.08)] border-b border-[var(--color-gray-light)]'
            : 'bg-white border-b border-[var(--color-gray-light)]'
        }`}
      >
        {adminMode && location.pathname === '/' ? (
          <div className="w-full bg-red-600 px-4 py-2 text-center text-xs font-medium tracking-[0.18em] text-white">
            ADMIN MODE
          </div>
        ) : null}
        <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-3 min-w-0">
          <Link to="/" className="flex items-center gap-2 sm:gap-3 min-w-0 shrink overflow-hidden">
            <img
              src="/media/logo_complete.svg"
              alt="他山"
              className="h-8 sm:h-9 w-auto shrink-0"
            />
            <span
              className="font-sans font-semibold text-base sm:text-lg tracking-[0.2em] sm:tracking-[0.3em]"
              style={{ color: 'var(--color-dark)' }}
            >
              · 世 界
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-6 lg:gap-8">
            {navLinks.map(({ to, label, match }) => (
              <Link
                key={to}
                to={to}
                className="relative text-sm font-serif transition-all py-2 group"
                style={{
                  color: match(location.pathname) ? 'var(--color-dark)' : 'var(--color-gray)',
                }}
              >
                <span className={match(location.pathname) ? 'font-medium' : ''}>{label}</span>
                <span
                  className={`absolute bottom-0 left-0 h-0.5 transition-all duration-300 ${
                    match(location.pathname) ? 'w-full' : 'w-0 group-hover:w-full'
                  }`}
                  style={{
                    background: 'var(--color-dark)',
                  }}
                />
              </Link>
            ))}
            <Link
              to="/profile-helper"
              className="relative text-sm font-serif font-medium transition-all whitespace-nowrap py-2 group"
              style={{
                color: location.pathname.startsWith('/profile-helper') ? 'var(--color-dark)' : 'var(--color-gray)',
              }}
            >
              科研数字分身
              <span
                className={`absolute bottom-0 left-0 h-0.5 transition-all duration-300 ${
                  location.pathname.startsWith('/profile-helper') ? 'w-full' : 'w-0 group-hover:w-full'
                }`}
                style={{
                  background: 'var(--color-dark)',
                }}
              />
            </Link>
            <Link
              to="/topics/new"
              className="text-white px-4 py-1.5 rounded-[var(--radius-lg)] text-sm font-serif font-medium transition-all hover:-translate-y-0.5 whitespace-nowrap shrink-0"
              style={{
                background: 'var(--color-dark)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              + 创建话题
            </Link>

            {user ? (
              <div>
                <button
                  ref={userMenuTriggerRef}
                  type="button"
                  onClick={() => {
                    setUserMenuOpen(v => {
                      const next = !v
                      if (next) {
                        requestAnimationFrame(updateUserMenuPosition)
                      }
                      return next
                    })
                  }}
                  className="flex items-center gap-2 text-sm font-serif transition-all hover:opacity-80"
                  style={{ color: 'var(--color-gray)' }}
                >
                  <div
                    className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium text-white"
                    style={{ background: 'var(--color-dark)' }}
                  >
                    {(user.username || user.phone).charAt(0)}
                  </div>
                  <span className="max-w-[100px] truncate">{user.username || user.phone}</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="text-sm font-serif transition-all hover:opacity-80"
                  style={{ color: 'var(--color-gray)' }}
                >
                  登录
                </Link>
                <Link
                  to="/register"
                  className="px-3 py-1.5 rounded-[var(--radius-md)] text-sm font-serif font-medium transition-all hover:opacity-90 whitespace-nowrap"
                  style={{
                    background: 'var(--color-gray-light)',
                    color: 'var(--color-dark)',
                  }}
                >
                  注册
                </Link>
              </div>
            )}
          </div>

          <div className="flex md:hidden items-center shrink-0">
            <Link
              to="/topics/new"
              className="text-white px-3 py-2 rounded-[var(--radius-md)] text-sm font-serif font-medium transition-all shrink-0 min-h-[36px] flex items-center touch-manipulation"
              style={{ background: 'var(--color-dark)' }}
            >
              + 创建话题
            </Link>
          </div>
        </div>
      </nav>
      {userMenuOpen &&
        createPortal(
          <div
            ref={userMenuRef}
            className="fixed bg-white rounded-[var(--radius-md)] py-1 min-w-[120px] z-[9999]"
            style={{
              top: `${userMenuPosition.top}px`,
              left: `${userMenuPosition.left}px`,
              transform: 'translateX(-100%)',
              boxShadow: 'var(--shadow-lg)',
              border: '1px solid var(--color-gray-light)',
            }}
          >
            <Link
              to="/favorites"
              className="block px-4 py-2 text-sm font-serif transition-all hover:bg-gray-50"
              style={{ color: 'var(--color-gray-dark)' }}
              onClick={() => setUserMenuOpen(false)}
            >
              我的收藏
            </Link>
            <Link
              to="/profile-helper"
              className="block px-4 py-2 text-sm font-serif transition-all hover:bg-gray-50"
              style={{ color: 'var(--color-gray-dark)' }}
              onClick={() => setUserMenuOpen(false)}
            >
              数字分身
            </Link>
            <button
              type="button"
              onClick={handleLogout}
              className="block w-full text-left px-4 py-2 text-sm font-serif transition-all hover:bg-gray-50"
              style={{ color: 'var(--color-gray-dark)' }}
            >
              退出登录
            </button>
          </div>,
          document.body,
        )}
      <div
        className="fixed bottom-0 left-0 right-0 z-50 border-t bg-white/95 backdrop-blur-xl md:hidden"
        style={{
          borderColor: 'var(--border-default)',
          paddingBottom: 'env(safe-area-inset-bottom)',
          boxShadow: '0 -8px 24px rgba(15, 23, 42, 0.08)',
        }}
        >
          <div className="mx-auto flex h-16 max-w-md items-stretch px-2">
          {mobileTabs.map((tab) => {
            const active = tab.match(location.pathname)
            return (
              <Link
                key={tab.to}
                to={tab.to}
                className="flex min-w-0 flex-1 flex-col items-center justify-center gap-1 rounded-[var(--radius-md)] text-xs font-medium transition-colors"
                style={{
                  color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                  backgroundColor: active ? 'var(--bg-secondary)' : 'transparent',
                }}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </Link>
            )
          })}
        </div>
      </div>
    </>
  )
}
