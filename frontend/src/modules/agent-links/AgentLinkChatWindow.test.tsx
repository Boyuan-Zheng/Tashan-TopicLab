import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AgentLinkChatWindow } from './AgentLinkChatWindow'
import {
  getAgentLink,
  startAgentLinkSession,
} from './agentLinksApi'

vi.mock('./agentLinksApi', async () => {
  const actual = await vi.importActual<typeof import('./agentLinksApi')>('./agentLinksApi')
  return {
    ...actual,
    getAgentLink: vi.fn(),
    startAgentLinkSession: vi.fn(),
    chatWithAgentLink: vi.fn(),
    uploadAgentLinkWorkspaceFile: vi.fn(),
  }
})

const mockedGetAgentLink = vi.mocked(getAgentLink)
const mockedStartAgentLinkSession = vi.mocked(startAgentLinkSession)

describe('AgentLinkChatWindow', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()

    mockedGetAgentLink.mockResolvedValue({
      slug: 'research-twin',
      name: '科研数字分身',
      description: '科研数字分身描述',
      module: 'agent_links.research_twin',
      entry_skill: 'profile-collector',
      blueprint_root: '/tmp/blueprint',
      agent_workdir: '/tmp/workdir',
      rule_file_path: '.cursor/rules/profile-collector.mdc',
      skills_path: '/tmp/skills',
      docs_path: '/tmp/docs',
      template_path: '/tmp/template',
      welcome_message: '你好，我是科研数字分身采集助手。',
      default_model: 'qwen3.5-plus',
    })
    mockedStartAgentLinkSession.mockResolvedValue({
      session_id: 'session-1',
      agent_link: {
        slug: 'research-twin',
        name: '科研数字分身',
        description: '科研数字分身描述',
        module: 'agent_links.research_twin',
        entry_skill: 'profile-collector',
        blueprint_root: '/tmp/blueprint',
        agent_workdir: '/tmp/workdir',
        rule_file_path: '.cursor/rules/profile-collector.mdc',
        skills_path: '/tmp/skills',
        docs_path: '/tmp/docs',
        template_path: '/tmp/template',
        welcome_message: '你好，我是科研数字分身采集助手。',
        default_model: 'qwen3.5-plus',
      },
      welcome_message: '你好，我是科研数字分身采集助手。',
      agent_workdir: '/tmp/workdir',
    })
  })

  it('未登录时显示提示且不初始化会话', async () => {
    render(
      <MemoryRouter>
        <AgentLinkChatWindow slug="research-twin" />
      </MemoryRouter>,
    )

    await screen.findByText('科研数字分身')

    await waitFor(() => {
      expect(screen.getByText('请先登录后再开始对话。')).toBeInTheDocument()
    })

    expect(mockedStartAgentLinkSession).not.toHaveBeenCalled()
    expect(screen.getByPlaceholderText('Message agent. Enter to send, Shift+Enter for newline.')).toBeDisabled()
    expect(screen.getByRole('button', { name: '↑' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '+' })).toBeDisabled()
    expect(screen.getByRole('combobox')).toBeDisabled()
  })
})
