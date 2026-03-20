/** Parse FastAPI-style error bodies; avoid JSON.parse on HTML/plain 500 pages from proxies. */

function detailToMessage(detail: unknown): string | null {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const parts = detail.map((item) => {
      if (item && typeof item === 'object' && 'msg' in item && typeof (item as { msg: unknown }).msg === 'string') {
        return (item as { msg: string }).msg
      }
      return String(item)
    })
    return parts.join('; ')
  }
  return null
}

export async function readApiError(res: Response, fallback: string): Promise<string> {
  const raw = await res.text()
  if (!raw.trim()) {
    return res.status >= 500 ? '服务暂时不可用，请稍后重试' : fallback
  }
  try {
    const data = JSON.parse(raw) as { detail?: unknown }
    const msg = detailToMessage(data?.detail)
    if (msg) return msg
  } catch {
    /* not JSON */
  }
  if (res.status >= 500) {
    return '服务暂时不可用，请稍后重试'
  }
  const snippet = raw.trim().slice(0, 200)
  return snippet || fallback
}
