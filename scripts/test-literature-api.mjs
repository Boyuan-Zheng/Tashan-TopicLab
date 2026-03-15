#!/usr/bin/env node
/**
 * 测试 Literature 服务 GET /api/v1/literature/recent
 * 用法：
 *   LITERATURE_API_BASE=http://127.0.0.1:8011 LITERATURE_SHARED_TOKEN=your_token node scripts/test-literature-api.mjs
 * 或先 export 再执行：
 *   export LITERATURE_API_BASE=http://127.0.0.1:8011
 *   export LITERATURE_SHARED_TOKEN=your_token
 *   node scripts/test-literature-api.mjs
 */

const base = process.env.LITERATURE_API_BASE || process.env.VITE_LITERATURE_API_BASE || ''
const token = process.env.LITERATURE_SHARED_TOKEN || process.env.VITE_LITERATURE_SHARED_TOKEN || ''

const url = `${base.replace(/\/$/, '')}/api/v1/literature/recent?limit=5&offset=0`

console.log('Request URL:', url)
console.log('x-ingest-token:', token ? `${token.slice(0, 8)}...` : '(未设置)')
console.log('')

if (!base) {
  console.error('请设置 LITERATURE_API_BASE 或 VITE_LITERATURE_API_BASE，例如:')
  console.error('  export LITERATURE_API_BASE=http://127.0.0.1:8011')
  process.exit(1)
}

const headers = { 'Content-Type': 'application/json' }
if (token) headers['x-ingest-token'] = token

try {
  const res = await fetch(url, { headers })
  const text = await res.text()
  console.log('HTTP Status:', res.status, res.statusText)
  console.log('Response body:')
  try {
    const json = JSON.parse(text)
    console.log(JSON.stringify(json, null, 2))
    if (json.list && Array.isArray(json.list)) {
      console.log('')
      console.log('--- 列表长度:', json.list.length)
      if (json.list.length > 0) {
        console.log('--- 首条字段:', Object.keys(json.list[0]).join(', '))
      }
    }
  } catch {
    console.log(text)
  }
} catch (err) {
  console.error('请求失败:', err.message)
  if (err.cause) console.error('原因:', err.cause.message)
  process.exit(1)
}
