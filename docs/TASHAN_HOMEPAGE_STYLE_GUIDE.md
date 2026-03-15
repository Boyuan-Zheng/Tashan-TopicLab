# 他山官网 UI 单文件规范

本文件包含复刻"他山官网"视觉与交互风格所需的**最小规范集合**：设计 Token、关键 CSS 类、控件行为契约、内容数据 Schema 与页面模板。无需依赖原项目源码即可落地实现。

---

## 0. 一页速记

- **视觉气质**：浅色、学术/创新；主色"淡蓝 + 淡绿"渐变；卡片化信息结构；大标题/数字使用渐变字。
- **布局骨架**（每个页面固定）：`page-wrapper` → `page-header`（统一头图）→ 内容 `section` + `container`。
- **交互触感**：可点击元素 hover 微上浮（`y:-2~5`）+ 轻微缩放（`scale:1.02`）+ 阴影增强。
- **动效策略**：进入视口渐入（建议 Framer Motion），避免夸张；统一过渡曲线 `cubic-bezier(0.4,0,0.2,1)`。
- **组件语言**：Header 固定顶栏 + 滚动磨砂态 + 下拉菜单；Footer 深色底；内容以"卡片/轮播/列表"组合。

---

## 1. 必须复制的 Design Token（CSS 变量）

将下述 `:root` 变量复制到全局 CSS（例如 `App.css` / `global.css`），可对齐约 80% 的视觉风格。

```css
:root {
  /* 品牌色（淡蓝 + 淡绿） */
  --color-primary: #5B9BD5;
  --color-secondary: #9FD4C4;
  --color-accent: #6BC5D6;
  --color-accent-light: #B5E5C8;

  /* 中性色 */
  --color-dark: #0E2E4F;
  --color-darker: #0A1F35;
  --color-light: #FFFFFF;
  --color-gray: #6C757D;
  --color-gray-light: #E9ECEF;
  --color-gray-dark: #495057;

  /* 渐变 */
  --gradient-primary: linear-gradient(135deg, #5B9BD5 0%, #9FD4C4 100%);
  --gradient-secondary: linear-gradient(135deg, #6BC5D6 0%, #B5E5C8 100%);
  --gradient-accent: linear-gradient(135deg, #5B9BD5 0%, #B5E5C8 100%);
  --gradient-dark: linear-gradient(135deg, #0E2E4F 0%, #0A1F35 100%);
  --gradient-banner: linear-gradient(135deg, #5B9BD5 0%, #B5E5C8 100%);

  /* 阴影 */
  --shadow-sm: 0 2px 8px rgba(15, 46, 79, 0.08);
  --shadow-md: 0 4px 16px rgba(15, 46, 79, 0.12);
  --shadow-lg: 0 8px 32px rgba(15, 46, 79, 0.15);
  --shadow-accent: 0 4px 16px rgba(107, 197, 214, 0.25);

  /* 圆角 */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --radius-xl: 32px;

  /* 动效 */
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## 2. 必须实现的关键 CSS 类

下述为"最小必要"的类集合：实现这些类即可获得一致的页面版式与视觉语法。

```css
/* Reset + 基础 */
* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: var(--color-light);
  color: var(--color-dark);
  line-height: 1.6;
  overflow-x: hidden;
}

/* 布局骨架 */
.page-wrapper { width: 100%; min-height: calc(100vh - 400px); }
.container { max-width: 1200px; width: 100%; margin: 0 auto; padding: 0 24px; }
section { padding: 100px 0; position: relative; width: 100%; }

/* 头图区域（统一背景：横向背景图 + 淡渐变遮罩） */
.page-header {
  background-image: url('/media/bg_horizontal.webp');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  padding: 120px 0 80px;
  text-align: center;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-md);
  z-index: 1;
}
.page-header::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(91, 155, 213, 0.05) 0%, rgba(159, 212, 196, 0.05) 100%);
  z-index: -1;
}
.page-title {
  font-size: 56px;
  font-weight: 800;
  margin-bottom: 16px;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.page-subtitle { font-size: 20px; color: var(--color-gray); font-weight: 500; }

/* 标题体系 */
.section-header { text-align: center; margin-bottom: 60px; }
.section-title {
  font-size: 48px; font-weight: 700; margin-bottom: 16px;
  background: var(--gradient-primary);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.subsection-title {
  font-size: 32px; font-weight: 700; margin-bottom: 32px; text-align: center;
  background: var(--gradient-primary);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.gradient-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

/* 按钮 */
.btn { display: inline-flex; align-items: center; gap: 8px; padding: 14px 32px; border-radius: var(--radius-lg); font-size: 16px; font-weight: 600; text-decoration: none; cursor: pointer; transition: var(--transition); border: none; }
.btn-primary { background: var(--gradient-primary); color: #fff; box-shadow: var(--shadow-md); }
.btn-primary:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); background: var(--gradient-accent); }
.btn-secondary { background: #fff; color: var(--color-primary); border: 2px solid var(--color-primary); }
.btn-secondary:hover { background: var(--color-primary); color: #fff; }

/* 卡片（白底卡：通用信息承载） */
.card {
  background: #fff;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
  border: 1px solid var(--color-gray-light);
}
.card:hover { box-shadow: var(--shadow-md); border-color: rgba(91, 155, 213, 0.35); transform: translateY(-2px); }

/* 玻璃卡（Hero / 强视觉卡） */
.glass-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  border: 1px solid rgba(91, 155, 213, 0.1);
}

@media (max-width: 768px) {
  .container { padding: 0 16px; }
  .page-title { font-size: 40px; }
  .page-subtitle { font-size: 16px; }
  .page-header { padding: 100px 0 60px; }
  section { padding: 60px 0; }
}
```

---

## 3. 组件/控件规范

不要求实现相同代码，但需实现**相同功能与交互行为**，以保证一致的体验与视觉语言。

### 3.1 Header（固定顶栏 + 滚动磨砂 + 下拉 + 移动端抽屉）

- **固定顶栏**：始终在顶部（`position: fixed`），初始透明。
- **滚动态**（滚动 > 50px）：变成半透明白底 + blur + `shadow-sm`，高度略缩小。
- **导航链接**：
  - hover 出现渐变下划线从 0% 延展到 100%
  - active 文字变主色、下划线常驻
- **下拉菜单**：
  - 桌面：hover/点击可展开浮层；点击页面其他区域关闭
  - 菜单样式：白底 + 圆角 + `shadow-lg` + 轻边框
- **移动端**（<=768）：
  - 顶部右侧汉堡按钮打开菜单
  - 菜单为全宽面板（从左滑入），下拉菜单改为"静态展开块"

### 3.2 Footer（深色底 + 列表链接 + 社交入口）

- 背景使用 `--color-dark`，文本白/灰分层；链接 hover 变亮。
- 社交 icon 使用方形/圆角按钮：默认半透明白，hover 变主色底。

### 3.3 轮播（通用 Carousel 契约）

无论你用什么库，实现以下行为即可：

- **输入**：`items[]`，长度 > 1 才显示控制器
- **自动播放**：5s/次
- **切换动效**：左右滑入滑出 + opacity + 轻微 scale（0.98→1）
- **控制器**：
  - 左右圆形按钮（hover 主色底 + 白字）
  - 指示器：小点，active 时变主色并拉长（8px → 24px）

### 3.4 内容卡（ContentCard 契约：左文右媒）

卡片统一布局：**左侧文字**（标题/描述/要点）+ **右侧媒体**（视频/图片/链接列表三选一）。

---

## 4. 数据 Schema（让内容更新"只改数据不改 UI"）

约束字段后，可实现"只改数据不改 UI"的内容更新与扩展。

### 4.1 `ContentCardItem`（推荐）

- **必填**：
  - `title: string`
  - `description: string`
- **可选**：
  - `stats?: string`（短数据，例如"播放量破百万"）
  - `details?: string[]`（要点列表）
  - `tags?: string[]`（标签）
  - `videos?: { title?: string; url: string }[]`（url 可为 iframe 地址或 `.mp4`）
  - `linkList?: { title: string; url: string }[]`（右侧列表）
  - `image?: string`（右侧图片）
  - `videoLink?: string`（图片可点击跳转视频）
  - `link?: string | { text: string; url: string; label?: string }`（卡片底部"查看更多/查看论文"等）

### 4.2 `CarouselItem`（推荐）

- `title?: string`
- `description?: string`
- `date?: string`
- `location?: string`
- `images?: string[]`（多图时按网格展示）
- `link?: string`（外链）

---

## 5. 新页面模板

下述为"风格一致"的最小页面结构（React 写法）；非 React 技术栈也可复用其 DOM 与 class 体系。

```jsx
// FeaturePage.jsx（示例模板）
// 依赖建议：react + framer-motion（可选）+ lucide-react（可选）

import { motion } from 'framer-motion'

const items = [
  {
    title: '示例内容卡标题',
    description: '一段简短介绍，语气偏学术/专业，信息密度中等。',
    stats: '可选：100万+',
    details: ['要点 1', '要点 2', '要点 3'],
    link: { text: '了解更多', url: 'https://example.com', label: '外链' }
  }
]

export default function FeaturePage() {
  return (
    <div className="page-wrapper">
      <section className="page-header">
        <div className="container">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <h1 className="page-title">
              新功能页面 <span className="gradient-text">专题</span>
            </h1>
            <p className="page-subtitle">一句话副标题：概括方向与价值</p>
          </motion.div>
        </div>
      </section>

      <section style={{ background: '#fff', padding: '80px 0' }}>
        <div className="container" style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          {items.map((it, idx) => (
            <motion.div
              key={idx}
              className="card"
              style={{ padding: 40 }}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              whileHover={{ y: -5 }}
            >
              <h3 style={{ fontSize: 24, marginBottom: 12 }}>{it.title}</h3>
              {it.stats && <div style={{ color: 'var(--color-primary)', fontWeight: 600, marginBottom: 12 }}>{it.stats}</div>}
              <p style={{ color: 'var(--color-gray)', lineHeight: 1.8, marginBottom: 16 }}>{it.description}</p>
              {it.details?.length ? (
                <ul style={{ listStyle: 'none' }}>
                  {it.details.map((d) => (
                    <li key={d} style={{ padding: '6px 0', paddingLeft: 20, position: 'relative', color: 'var(--color-gray-dark)' }}>
                      <span style={{ position: 'absolute', left: 0, color: 'var(--color-primary)', fontWeight: 700 }}>→</span>
                      {d}
                    </li>
                  ))}
                </ul>
              ) : null}
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  )
}
```

---

## 6. 内容更新方式

推荐以"数据驱动"组织页面：后续通过修改数组/JSON 更新内容。

- **推荐方式**：把所有可编辑内容集中为一个 `const content = { ... }` 或 `const items = [...]`
  - 页面只做 `map(items)`，不在 JSX 里硬编码大量文本
- **更进一步**：把内容放到 `public/content/*.json`（运行时 fetch）
  - 适合"非开发者"更新：替换 JSON 即可
  - 必须遵循上面的 schema（否则 UI 会坏）

---

## 7. 资源与部署注意

- **图片格式**：优先 `webp`；图片加 `loading="lazy"`。
- **资源路径**：
  - 若部署在子路径（GitHub Pages 等），资源需要加 base 前缀（例如 `BASE_URL + 'media/...'`）
  - 如果不确定部署方式：**至少不要在代码里写死域名**
- **已知坑**：
  - 有项目版本里曾出现 `var(--color-text)` 未定义的写法；单文件复刻时请统一使用 `--color-dark` / `--color-gray-dark`。

---

## 8. 验收清单（让输出"看起来就是同一套站"）

- **Token**：颜色/渐变/阴影/圆角/transition 全部来自本文件的变量
- **版式**：必须有 `page-header` 统一头图与渐变标题字
- **卡片**：圆角大、阴影柔，hover 上浮 + 阴影增强
- **动效**：首屏渐入 + 内容进入视口渐入（可选用 Framer Motion）
- **移动端**：`<=768px` 容器 padding 变 16px、标题字号缩小、section padding 缩小
