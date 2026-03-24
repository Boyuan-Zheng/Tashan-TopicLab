import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import TopicList from '../TopicList'
import { topicsApi } from '../../api/client'

vi.mock('../../components/OpenClawSkillCard', () => ({
  default: () => <section data-testid="openclaw-skill-card" />,
}))

vi.mock('../../api/client', async () => {
  const actual = await vi.importActual<typeof import('../../api/client')>('../../api/client')
  return {
    ...actual,
    topicsApi: {
      ...actual.topicsApi,
      list: vi.fn(),
      delete: vi.fn(),
    },
  }
})

const mockedTopicsApiList = vi.mocked(topicsApi.list)
const mockedTopicsApiDelete = vi.mocked(topicsApi.delete)

describe('TopicList', () => {
  afterEach(() => {
    cleanup()
  })

  beforeEach(() => {
    vi.clearAllMocks()
    HTMLElement.prototype.scrollIntoView = vi.fn()
    mockedTopicsApiList.mockResolvedValue({
      data: {
        items: [
          {
            id: 'topic-1',
            session_id: 'topic-1',
            category: 'research',
            title: '带图片的话题',
            body: '正文中没有图片',
            status: 'open',
            discussion_status: 'completed',
            preview_image: '../generated_images/list_preview.png',
            source_feed_name: 'Nature',
            creator_name: 'openclaw-user',
            creator_auth_type: 'openclaw_key',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
        ],
        next_cursor: null,
      },
    } as any)
  })

  it('renders one topic preview image when topic contains image markdown', async () => {
    render(
      <MemoryRouter>
        <TopicList />
      </MemoryRouter>,
    )

    const image = await screen.findByRole('img', { name: '带图片的话题 预览图' })
    expect(screen.getByTestId('openclaw-skill-card')).toBeInTheDocument()
    expect(screen.getByText('板块：科研')).toBeInTheDocument()
    expect(screen.getByText('信源：Nature')).toBeInTheDocument()
    expect(screen.getByText('发起人：openclaw-user · OpenClaw')).toBeInTheDocument()
    expect(screen.getByText('AI 话题讨论')).toBeInTheDocument()
    expect(screen.queryByTestId('status-badge')).not.toBeInTheDocument()
    expect(image.getAttribute('src')).toMatch(
      /\/api\/topics\/topic-1\/assets\/generated_images\/list_preview\.png\?w=128&h=128&q=72&fm=webp$/,
    )
  })

  it('filters topics by selected category', async () => {
    const scrollToMock = vi.fn()
    Object.defineProperty(HTMLElement.prototype, 'scrollTo', {
      configurable: true,
      value: scrollToMock,
    })
    mockedTopicsApiList.mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 'topic-1',
            session_id: 'topic-1',
            category: 'thought',
            title: '思考话题',
            body: 'A',
            status: 'open',
            discussion_status: 'pending',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
          {
            id: 'topic-2',
            session_id: 'topic-2',
            category: 'research',
            title: '科研话题',
            body: 'B',
            status: 'open',
            discussion_status: 'pending',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
        ],
        next_cursor: null,
      },
    } as any)

    render(
      <MemoryRouter>
        <TopicList />
      </MemoryRouter>,
    )

    fireEvent.click((await screen.findAllByRole('button', { name: '思考' }))[0])

    await waitFor(() => {
      expect(mockedTopicsApiList).toHaveBeenCalledTimes(1)
    })
    expect(mockedTopicsApiList).toHaveBeenLastCalledWith({ q: undefined, limit: 20 })
    expect(scrollToMock).toHaveBeenCalled()
  })

  it('searches topics from the right-aligned search input', async () => {
    render(
      <MemoryRouter>
        <TopicList />
      </MemoryRouter>,
    )

    fireEvent.change(await screen.findByRole('searchbox', { name: '搜索话题' }), {
      target: { value: '多智能体' },
    })

    await waitFor(() => {
      expect(mockedTopicsApiList).toHaveBeenLastCalledWith({ q: '多智能体', limit: 20 })
    })
  })

  it('shows delete action in admin mode and deletes topic', async () => {
    mockedTopicsApiDelete.mockResolvedValue({ data: { ok: true, topic_id: 'topic-1' } } as any)
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    localStorage.setItem('auth_token', 'jwt-token')
    localStorage.setItem('auth_user', JSON.stringify({
      id: 1,
      phone: '13800000001',
      username: 'admin',
      is_admin: true,
      created_at: '2026-03-12T00:00:00Z',
    }))

    render(
      <MemoryRouter>
        <TopicList />
      </MemoryRouter>,
    )

    fireEvent.click(await screen.findByRole('button', { name: '删除话题' }))

    await waitFor(() => {
      expect(mockedTopicsApiDelete).toHaveBeenCalledWith('topic-1')
    })
  })

  it('keeps latest order inside each category column', async () => {
    mockedTopicsApiList.mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 'topic-1',
            session_id: 'topic-1',
            category: 'research',
            title: '科研话题 A',
            body: 'A',
            status: 'open',
            discussion_status: 'pending',
            source_feed_name: 'Nature',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
          {
            id: 'topic-2',
            session_id: 'topic-2',
            category: 'research',
            title: '科研话题 B',
            body: 'B',
            status: 'open',
            discussion_status: 'pending',
            source_feed_name: 'Nature',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
          {
            id: 'topic-4',
            session_id: 'topic-4',
            category: 'research',
            title: '科研话题 C',
            body: 'C',
            status: 'open',
            discussion_status: 'pending',
            source_feed_name: '站内创建',
            created_at: '2026-03-11T00:00:00Z',
            updated_at: '2026-03-11T00:00:00Z',
          },
          {
            id: 'topic-3',
            session_id: 'topic-3',
            category: 'product',
            title: '产品话题',
            body: 'D',
            status: 'open',
            discussion_status: 'pending',
            source_feed_name: 'TechCrunch',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
        ],
        next_cursor: null,
      },
    } as any)

    render(
      <MemoryRouter>
        <TopicList />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: '科研' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '产品' })).toBeInTheDocument()
    expect(screen.getByText('科研话题 A')).toBeInTheDocument()
    expect(screen.getByText('科研话题 B')).toBeInTheDocument()
    expect(screen.getByText('科研话题 C')).toBeInTheDocument()
    expect(screen.getByText('产品话题')).toBeInTheDocument()

    const researchSection = screen.getByTestId('topic-category-research')
    const researchCards = Array.from(researchSection.querySelectorAll('h3')).map((node) => node.textContent)
    expect(researchCards).toEqual(['科研话题 A', '科研话题 B', '科研话题 C'])
  })

  it('sorts category columns by topic count descending', async () => {
    mockedTopicsApiList.mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 'topic-1',
            session_id: 'topic-1',
            category: 'research',
            title: '科研话题 A',
            body: 'A',
            status: 'open',
            discussion_status: 'pending',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
          {
            id: 'topic-2',
            session_id: 'topic-2',
            category: 'research',
            title: '科研话题 B',
            body: 'B',
            status: 'open',
            discussion_status: 'pending',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
          {
            id: 'topic-3',
            session_id: 'topic-3',
            category: 'research',
            title: '科研话题 C',
            body: 'C',
            status: 'open',
            discussion_status: 'pending',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
          {
            id: 'topic-4',
            session_id: 'topic-4',
            category: 'product',
            title: '产品话题',
            body: 'D',
            status: 'open',
            discussion_status: 'pending',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
        ],
        next_cursor: null,
      },
    } as any)

    render(
      <MemoryRouter>
        <TopicList />
      </MemoryRouter>,
    )

    await screen.findByText('科研话题 C')
    const sections = ['research', 'product'].map((id) => screen.getByTestId(`topic-category-${id}`))
    expect(sections[0].compareDocumentPosition(sections[1]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('keeps tab order aligned with the category rail order', async () => {
    mockedTopicsApiList.mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 'topic-1',
            session_id: 'topic-1',
            category: 'news',
            title: '资讯话题 A',
            body: 'A',
            status: 'open',
            discussion_status: 'pending',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
          {
            id: 'topic-2',
            session_id: 'topic-2',
            category: 'news',
            title: '资讯话题 B',
            body: 'B',
            status: 'open',
            discussion_status: 'pending',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
          {
            id: 'topic-3',
            session_id: 'topic-3',
            category: 'research',
            title: '科研话题',
            body: 'C',
            status: 'open',
            discussion_status: 'pending',
            created_at: '2026-03-12T00:00:00Z',
            updated_at: '2026-03-12T00:00:00Z',
          },
        ],
        next_cursor: null,
      },
    } as any)

    render(
      <MemoryRouter>
        <TopicList />
      </MemoryRouter>,
    )

    await screen.findByText('资讯话题 B')
    const tabButtons = screen.getAllByRole('button').filter((button) =>
      ['资讯', '科研'].includes(button.textContent ?? ''),
    )
    expect(tabButtons.slice(0, 2).map((button) => button.textContent)).toEqual(['资讯', '科研'])
  })
})
