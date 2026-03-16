import { useCallback, useRef } from 'react'

const DEFAULT_THROTTLE_MS = 400

/**
 * 节流：首次调用立即执行，在 delayMs 内忽略后续调用。
 * 用于防止用户短期多次点击触发重复请求。
 */
export function useThrottledCallback<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delayMs: number = DEFAULT_THROTTLE_MS
): T {
  const lastRunRef = useRef<number>(0)

  return useCallback(
    ((...args: Parameters<T>) => {
      const now = Date.now()
      const elapsed = now - lastRunRef.current

      if (elapsed >= delayMs) {
        lastRunRef.current = now
        return fn(...args) as ReturnType<T>
      }
      // 若在冷却期内，忽略此次调用
      return undefined
    }) as T,
    [fn, delayMs]
  ) as T
}

/**
 * 按 key 节流：同一 key 在 delayMs 内只执行一次，不同 key 互不影响。
 * 用于列表场景（如多个话题的点赞/收藏按钮）。
 */
export function useThrottledCallbackByKey<K, A extends unknown[], R>(
  fn: (...args: A) => R,
  getKey: (...args: A) => K,
  delayMs: number = DEFAULT_THROTTLE_MS
): (...args: A) => R | undefined {
  const lastRunByKeyRef = useRef<Map<K, number>>(new Map())

  return useCallback(
    (...args: A) => {
      const key = getKey(...args)
      const now = Date.now()
      const last = lastRunByKeyRef.current.get(key) ?? 0

      if (now - last >= delayMs) {
        lastRunByKeyRef.current.set(key, now)
        return fn(...args)
      }
      return undefined
    },
    [fn, getKey, delayMs]
  )
}
