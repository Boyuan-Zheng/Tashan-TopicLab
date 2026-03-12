import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import TopicConfigTabs from '../TopicConfigTabs'
import { moderatorModesApi, topicsApi } from '../../api/client'

vi.mock('../TabPanel', () => ({
  default: ({ tabs }: { tabs: Array<{ content: ReactNode }> }) => <div>{tabs[0].content}</div>,
}))

vi.mock('../ExpertManagement', () => ({
  default: () => <div data-testid="expert-management" />,
}))

vi.mock('../ModeratorModeSelector', () => ({
  default: () => <div data-testid="moderator-mode-selector" />,
}))

vi.mock('../SkillSelector', () => ({
  default: () => <div data-testid="skill-selector" />,
}))

vi.mock('../MCPServerSelector', () => ({
  default: () => <div data-testid="mcp-selector" />,
}))

vi.mock('../../api/client', async () => {
  const actual = await vi.importActual<typeof import('../../api/client')>('../../api/client')
  return {
    ...actual,
    moderatorModesApi: {
      ...actual.moderatorModesApi,
      getConfig: vi.fn(),
      listAssignable: vi.fn(),
      setConfig: vi.fn(),
    },
    topicsApi: {
      ...actual.topicsApi,
      update: vi.fn(),
    },
  }
})

const mockedGetConfig = vi.mocked(moderatorModesApi.getConfig)
const mockedListAssignable = vi.mocked(moderatorModesApi.listAssignable)
const mockedUpdateTopic = vi.mocked(topicsApi.update)

describe('TopicConfigTabs detail editing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedGetConfig.mockResolvedValue({
      data: {
        mode_id: 'standard',
        num_rounds: 5,
        custom_prompt: null,
        skill_list: [],
        mcp_server_ids: [],
        model: 'qwen3.5-plus',
      },
    } as any)
    mockedListAssignable.mockResolvedValue({ data: [] } as any)
    mockedUpdateTopic.mockResolvedValue({
      data: {
        id: 'topic-1',
        session_id: 'topic-1',
        title: '测试',
        body: '新的描述',
        category: null,
        status: 'open',
        mode: 'discussion',
        num_rounds: 5,
        expert_names: [],
        discussion_result: null,
        discussion_status: 'pending',
        created_at: '2026-03-13T00:00:00Z',
        updated_at: '2026-03-13T00:00:00Z',
      },
    } as any)
  })

  it('edits and saves topic body in detail tab', async () => {
    const onTopicBodyUpdated = vi.fn()
    render(
      <TopicConfigTabs topicId="topic-1" topicBody="旧描述" onTopicBodyUpdated={onTopicBodyUpdated} />,
    )

    fireEvent.click(await screen.findByRole('button', { name: '编辑描述' }))
    fireEvent.change(screen.getByPlaceholderText('输入话题描述（支持 Markdown）'), {
      target: { value: '新的描述' },
    })
    fireEvent.click(screen.getByRole('button', { name: '保存' }))

    await waitFor(() => {
      expect(mockedUpdateTopic).toHaveBeenCalledWith('topic-1', { body: '新的描述' })
    })
    expect(onTopicBodyUpdated).toHaveBeenCalledWith('新的描述')
    expect(await screen.findByRole('button', { name: '编辑描述' })).toBeInTheDocument()
  })
})
