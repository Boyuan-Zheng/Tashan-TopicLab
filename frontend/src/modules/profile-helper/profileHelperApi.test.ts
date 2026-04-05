import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  getChatHistory,
  getFieldRecommendations,
  publishTwin,
  sendMessage,
  sendMessageBlocks,
} from './profileHelperApi'

function makeStreamResponse(chunks: string[], init?: ResponseInit) {
  const encoder = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk))
      }
      controller.close()
    },
  })
  return new Response(stream, init)
}

afterEach(() => {
  vi.restoreAllMocks()
  localStorage.clear()
})

describe('profileHelperApi', () => {
  it('parses classic SSE chat chunks with CRLF separators', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        makeStreamResponse(
          [
            'data: {"content":"你"}\r\n\r\n',
            'data: {"content":"好"}\r\n\r\n',
            'data: [DONE]\r\n\r\n',
          ],
          { status: 200 },
        ),
      ),
    )

    const chunks: string[] = []
    await sendMessage('sid-1', 'hello', (chunk) => chunks.push(chunk))

    expect(chunks).toEqual(['你', '好'])
    expect(fetch).toHaveBeenCalledWith(
      '/api/profile-helper/chat',
      expect.objectContaining({
        method: 'POST',
      }),
    )
  })

  it('parses block SSE chunks with CRLF separators', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        makeStreamResponse(
          [
            'data: {"type":"text","content":"第一段"}\r\n\r\n',
            'data: {"type":"choice","id":"next","question":"下一步？","options":[{"id":"a","label":"继续"}]}\r\n\r\n',
            'data: [DONE]\r\n\r\n',
          ],
          { status: 200 },
        ),
      ),
    )

    const blocks: Array<Record<string, unknown>> = []
    await sendMessageBlocks('sid-2', 'hello', (block) => blocks.push(block as Record<string, unknown>))

    expect(blocks).toEqual([
      { type: 'text', content: '第一段' },
      {
        type: 'choice',
        id: 'next',
        question: '下一步？',
        options: [{ id: 'a', label: '继续' }],
      },
    ])
  })

  it('returns empty recommendations array when payload omits recommendations', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({}), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(getFieldRecommendations('sid-3')).resolves.toEqual([])
  })

  it('returns chat history payload unchanged', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            messages: [{ role: 'user', content: 'hello' }],
            count: 1,
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      ),
    )

    await expect(getChatHistory('sid-4')).resolves.toEqual({
      messages: [{ role: 'user', content: 'hello' }],
      count: 1,
    })
  })

  it('preserves publish sync fields from backend response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            ok: true,
            agent_name: 'my_twin_expert',
            display_name: '我的分身',
            visibility: 'private',
            exposure: 'brief',
            sync_status: 'ok',
            twin_id: 'twin_123',
            twin_version: 2,
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      ),
    )

    await expect(
      publishTwin({
        session_id: 'sid-5',
        visibility: 'private',
        exposure: 'brief',
        display_name: '我的分身',
      }),
    ).resolves.toMatchObject({
      sync_status: 'ok',
      twin_id: 'twin_123',
      twin_version: 2,
    })
  })
})
