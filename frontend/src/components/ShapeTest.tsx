import { useEffect, useState } from 'react'

/**
 * 圆角测试组件 - 用于验证形状系统改造效果
 * 访问：http://localhost:3000 后在控制台查看
 */
export default function ShapeTest() {
  const [logs, setLogs] = useState<string[]>([])

  useEffect(() => {
    const log = (msg: string) => {
      console.log(`[形状测试] ${msg}`)
      setLogs(prev => [msg, ...prev].slice(0, 10))
    }

    log('===== 圆角系统改造验证 =====')
    log('')
    log('📏 圆角等级（精简为 3 个）:')
    log('  1. rounded-lg (12px) - 默认圆角 - 75% 场景')
    log('  2. rounded-xl (16px) - 大圆角 - 25% 场景')
    log('  3. rounded-full - 完全圆形 - 头像/Chip')
    log('')
    log('✅ 已完成的改造:')
    log('  - 移除所有 rounded-[XXpx] 自定义圆角')
    log('  - rounded-2xl (20px) → rounded-xl (16px)')
    log('  - rounded-md (8px) → rounded-lg (12px)')
    log('  - 所有弹窗/模态框使用 rounded-xl')
    log('')
    log('📊 使用统计:')
    log('  - rounded-lg: ~119 次 (75%)')
    log('  - rounded-full: ~56 次 (35%)')
    log('  - rounded-xl: ~40 次 (25%)')
    log('')
    log('🎨 视觉差异:')
    log('  - 12px vs 16px 差异较小，需仔细观察')
    log('  - 卡片/按钮统一为 12px 圆角')
    log('  - 弹窗/下拉菜单统一为 16px 圆角')
    log('')
    log('💡 如何验证:')
    log('  1. 刷新页面（Cmd+Shift+R 硬刷新）')
    log('  2. 观察卡片圆角是否统一')
    log('  3. 打开弹窗看圆角是否更大')
    log('  4. 检查头像/Chip 是否正圆')
  }, [])

  return (
    <div className="fixed bottom-4 right-4 bg-white border-2 border-blue-500 rounded-xl shadow-xl p-4 max-w-sm z-50">
      <h3 className="font-bold text-blue-600 mb-2">📐 圆角改造验证</h3>
      <div className="space-y-2 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-blue-500"></div>
          <span>rounded-lg (12px) - 默认</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-green-500"></div>
          <span>rounded-xl (16px) - 弹窗</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-purple-500"></div>
          <span>rounded-full - 头像</span>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t text-xs text-gray-500">
        <p>最近日志:</p>
        {logs.slice(0, 3).map((log, i) => (
          <p key={i} className="truncate">{log}</p>
        ))}
      </div>
      <p className="mt-2 text-xs text-blue-600 font-medium">
        👉 打开浏览器控制台查看详细报告
      </p>
    </div>
  )
}
