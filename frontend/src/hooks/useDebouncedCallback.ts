import { useCallback, useRef } from 'react'

/**
 * 防抖：延迟 delayMs 后执行，若在 delayMs 内再次调用则重置计时。
 * 适合搜索输入、表单提交等「合并多次触发为一次」的场景。
 */
export function useDebouncedCallback<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delayMs: number
): T {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  return useCallback(
    ((...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      timeoutRef.current = setTimeout(() => {
        timeoutRef.current = null
        fn(...args)
      }, delayMs)
    }) as T,
    [fn, delayMs]
  ) as T
}
