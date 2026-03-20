import { describe, expect, it } from 'vitest'
import { readApiError } from './httpError'

describe('readApiError', () => {
  it('returns friendly message for plain-text 500', async () => {
    const res = new Response('Internal Server Error', { status: 500 })
    const msg = await readApiError(res, 'fallback')
    expect(msg).toBe('服务暂时不可用，请稍后重试')
  })

  it('parses FastAPI detail string', async () => {
    const res = new Response(JSON.stringify({ detail: '验证码错误' }), { status: 400 })
    expect(await readApiError(res, 'fallback')).toBe('验证码错误')
  })

  it('uses fallback for empty 4xx body', async () => {
    const res = new Response('', { status: 400 })
    expect(await readApiError(res, '注册失败')).toBe('注册失败')
  })
})
