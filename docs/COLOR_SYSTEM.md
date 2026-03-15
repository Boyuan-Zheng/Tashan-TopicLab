# 他山世界 - 统一颜色系统

基于 UI/UX Pro Max 设计系统分析，为学术研究协作平台定制的颜色规范。

---

## 一、颜色系统总览

### 设计原则
- **学术专业**：沉稳、可信赖的色调
- **柔和舒适**：长时间阅读不疲劳
- **层次分明**：清晰的信息层级
- **无障碍**：WCAG AA+ 对比度标准

### 风格定位
**Soft UI Evolution** - 演进版柔和 UI，更好的对比度、现代美感、微妙深度

---

## 二、核心颜色定义

### 2.1 主题色 (Brand Colors)

用于品牌标识、Logo、重要标题。

| 名称 | 色值 | 用途 | CSS 变量 |
|------|------|------|----------|
| **主题蓝** | `#3B82F6` | 主品牌色、Logo、品牌元素 | `--brand-primary` |
| **主题深蓝** | `#1E40AF` | 品牌深色变体、Footer 背景 | `--brand-dark` |
| **主题淡蓝** | `#DBEAFE` | 品牌浅色背景、标签背景 | `--brand-light` |

### 2.2 强调色 (Accent Colors)

用于交互元素、状态指示、CTA 按钮。

| 名称 | 色值 | 用途 | CSS 变量 |
|------|------|------|----------|
| **强调蓝** | `#0EA5E9` | 链接、聚焦状态、选中态 | `--accent-primary` |
| **成功绿** | `#10B981` | 成功状态、创建按钮、正向反馈 | `--accent-success` |
| **警告橙** | `#F59E0B` | 警告状态、待处理提示 | `--accent-warning` |
| **错误红** | `#EF4444` | 错误状态、删除按钮、负向反馈 | `--accent-error` |
| **信息蓝** | `#3B82F6` | 信息提示、帮助说明 | `--accent-info` |

### 3.3 底色 (Background Colors)

用于页面背景、卡片背景、容器背景。

| 名称 | 色值 | 用途 | CSS 变量 |
|------|------|------|----------|
| **页面背景** | `#F8FAFC` | 全局页面底色 | `--bg-page` |
| **容器背景** | `#FFFFFF` | 卡片、面板、弹窗背景 | `--bg-container` |
| **次级背景** | `#F1F5F9` | 次级区域、表格斑马纹 | `--bg-secondary` |
| **悬停背景** | `#F1F5F9` | 可交互元素悬停态 | `--bg-hover` |
| **选中背景** | `#E0F2FE` | 选中项背景 | `--bg-selected` |
| **禁用背景** | `#E2E8F0` | 禁用状态背景 | `--bg-disabled` |
| **Footer 背景** | `#0E2E4F` | 页脚深色背景 | `--bg-footer` |

### 3.4 文字色 (Text Colors)

用于各类文字、标签、说明文字。

| 名称 | 色值 | 用途 | CSS 变量 |
|------|------|------|----------|
| **主文字** | `#1E293B` | 标题、正文、重要信息 | `--text-primary` |
| **次文字** | `#475569` | 描述、说明、次要信息 | `--text-secondary` |
| **弱文字** | `#94A3B8` | 占位符、辅助说明 | `--text-tertiary` |
| **禁用文字** | `#CBD5E1` | 禁用状态文字 | `--text-disabled` |
| **反白文字** | `#FFFFFF` | 深色背景上的文字 | `--text-inverse` |

### 3.5 边框色 (Border Colors)

用于分割线、边框、轮廓。

| 名称 | 色值 | 用途 | CSS 变量 |
|------|------|------|----------|
| **默认边框** | `#E2E8F0` | 常规边框、分割线 | `--border-default` |
| **悬停边框** | `#CBD5E1` | 可交互元素悬停态边框 | `--border-hover` |
| **聚焦边框** | `#3B82F6` | 输入框聚焦边框 | `--border-focus` |
| **强调边框** | `#0EA5E9` | 选中、激活状态边框 | `--border-active` |

### 3.6 阴影色 (Shadow Colors)

用于层次感、浮起效果。

| 名称 | 色值 | 用途 | CSS 变量 |
|------|------|------|----------|
| **轻微阴影** | `0 1px 2px rgba(0,0,0,0.05)` | 轻微浮起 | `--shadow-sm` |
| **常规阴影** | `0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)` | 卡片、按钮 | `--shadow-md` |
| **中等阴影** | `0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)` | 弹窗、下拉菜单 | `--shadow-lg` |
| **深度阴影** | `0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05)` | 模态框 | `--shadow-xl` |

---

## 三、控件颜色映射

### 3.1 按钮控件

| 控件 | 背景 | 文字 | 边框 | 悬停背景 | 悬停效果 |
|------|------|------|------|----------|----------|
| **主按钮** | `--text-primary` | `--text-inverse` | 无 | `#1E293B` | 上浮 1px + 阴影增强 |
| **次按钮** | `--bg-container` | `--text-primary` | `--border-default` | `--bg-hover` | 边框变深 |
| **成功按钮** | `--accent-success` | `--text-inverse` | 无 | `#059669` | 上浮 1px |
| **危险按钮** | `--accent-error` | `--text-inverse` | 无 | `#DC2626` | 上浮 1px |
| **幽灵按钮** | 透明 | `--text-primary` | 无 | `--bg-hover` | 背景显现 |
| **禁用按钮** | `--bg-disabled` | `--text-disabled` | 无 | 无变化 | 无 |

### 3.2 输入控件

| 控件 | 背景 | 文字 | 边框 | 聚焦边框 | 占位符 |
|------|------|------|------|----------|--------|
| **输入框** | `--bg-container` | `--text-primary` | `--border-default` | `--border-focus` | `--text-tertiary` |
| **输入框悬停** | `--bg-container` | `--text-primary` | `--border-hover` | - | - |
| **输入框禁用** | `--bg-disabled` | `--text-disabled` | `--border-default` | - | - |
| **输入框错误** | `--bg-container` | `--text-primary` | `--accent-error` | - | - |

### 3.3 卡片控件

| 控件 | 背景 | 边框 | 悬停边框 | 悬停效果 |
|------|------|------|----------|----------|
| **基础卡片** | `--bg-container` | `--border-default` | `--border-hover` | 上浮 2px + 阴影增强 |
| **选中卡片** | `--bg-selected` | `--border-active` | - | - |
| **禁用卡片** | `--bg-secondary` | `--border-default` | 无变化 | 无 |
| **可点击卡片** | 添加 `cursor-pointer` | - | - | - |

### 3.4 标签/徽章控件

| 控件 | 背景 | 文字 | 边框 |
|------|------|------|------|
| **默认标签** | `--bg-secondary` | `--text-secondary` | 无 |
| **主题标签** | `--brand-light` | `--brand-primary` | 无 |
| **成功标签** | `#D1FAE5` | `--accent-success` | 无 |
| **警告标签** | `#FEF3C7` | `--accent-warning` | 无 |
| **错误标签** | `#FEE2E2` | `--accent-error` | 无 |

### 3.5 链接控件

| 控件 | 默认颜色 | 悬停颜色 | 下划线 |
|------|----------|----------|--------|
| **正文链接** | `--accent-primary` | `--brand-dark` | 无悬停显示 |
| **导航链接** | `--text-secondary` | `--text-primary` | 底部滑入 |

### 3.6 图标控件

| 控件 | 颜色 | 悬停颜色 |
|------|------|----------|
| **默认图标** | `--text-tertiary` | `--text-primary` |
| **强调图标** | `--accent-primary` | `--brand-dark` |
| **禁用图标** | `--text-disabled` | 无变化 |

---

## 四、CSS 变量定义

将以下内容替换到 `src/index.css` 的 `:root` 部分：

```css
:root {
  /* ========== 主题色 (Brand) ========== */
  --brand-primary: #3B82F6;
  --brand-dark: #1E40AF;
  --brand-light: #DBEAFE;

  /* ========== 强调色 (Accent) ========== */
  --accent-primary: #0EA5E9;
  --accent-success: #10B981;
  --accent-warning: #F59E0B;
  --accent-error: #EF4444;
  --accent-info: #3B82F6;

  /* ========== 底色 (Background) ========== */
  --bg-page: #F8FAFC;
  --bg-container: #FFFFFF;
  --bg-secondary: #F1F5F9;
  --bg-hover: #F1F5F9;
  --bg-selected: #E0F2FE;
  --bg-disabled: #E2E8F0;

  /* ========== 文字色 (Text) ========== */
  --text-primary: #0F172A;
  --text-secondary: #475569;
  --text-tertiary: #94A3B8;
  --text-disabled: #CBD5E1;
  --text-inverse: #FFFFFF;

  /* ========== 边框色 (Border) ========== */
  --border-default: #E2E8F0;
  --border-hover: #CBD5E1;
  --border-focus: #3B82F6;
  --border-active: #0EA5E9;

  /* ========== 阴影 (Shadow) ========== */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06);
  --shadow-xl: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);

  /* ========== 圆角 (Radius) ========== */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* ========== 过渡 (Transition) ========== */
  --transition-fast: 150ms ease;
  --transition-normal: 200ms ease;
  --transition-slow: 300ms ease;
}
```

---

## 五、Tailwind 配置扩展

在 `tailwind.config.js` 中添加：

```javascript
export default {
  theme: {
    extend: {
      colors: {
        // 主题色
        brand: {
          primary: 'var(--brand-primary)',
          dark: 'var(--brand-dark)',
          light: 'var(--brand-light)',
        },
        // 强调色
        accent: {
          primary: 'var(--accent-primary)',
          success: 'var(--accent-success)',
          warning: 'var(--accent-warning)',
          error: 'var(--accent-error)',
          info: 'var(--accent-info)',
        },
        // 背景色
        surface: {
          page: 'var(--bg-page)',
          container: 'var(--bg-container)',
          secondary: 'var(--bg-secondary)',
          hover: 'var(--bg-hover)',
          selected: 'var(--bg-selected)',
          disabled: 'var(--bg-disabled)',
        },
      },
    },
  },
}
```

---

## 六、迁移指南

### 旧变量 → 新变量映射

| 旧变量 | 新变量 | 说明 |
|--------|--------|------|
| `--color-primary` | `--brand-primary` | 品牌主色 |
| `--color-secondary` | `--accent-primary` | 强调色 |
| `--color-dark` | `--text-primary` | 主文字色 |
| `--color-gray` | `--text-secondary` | 次文字色 |
| `--color-gray-light` | `--border-default` | 边框色 |
| `--gradient-primary` | 移除 | 不再使用渐变 |
| `--gradient-dark` | `--brand-dark` | Footer 使用纯色 |

### 常见替换模式

```css
/* 旧写法 */
color: var(--color-dark);
background: var(--color-primary);
border-color: var(--color-gray-light);

/* 新写法 */
color: var(--text-primary);
background: var(--brand-primary);
border-color: var(--border-default);
```

---

## 七、使用示例

### 按钮示例

```tsx
// 主按钮
<button className="bg-[var(--text-primary)] text-white hover:bg-[#1E293B] transition-all rounded-lg px-4 py-2">
  创建话题
</button>

// 次按钮
<button className="bg-white text-[var(--text-primary)] border border-[var(--border-default)] hover:bg-[var(--bg-hover)] rounded-lg px-4 py-2">
  取消
</button>
```

### 卡片示例

```tsx
<div className="bg-white border border-[var(--border-default)] rounded-xl hover:border-[var(--border-hover)] hover:shadow-md transition-all cursor-pointer">
  {/* 卡片内容 */}
</div>
```

### 标签示例

```tsx
<span className="bg-[var(--bg-secondary)] text-[var(--text-secondary)] px-2 py-0.5 rounded-md text-sm">
  默认标签
</span>

<span className="bg-[var(--brand-light)] text-[var(--brand-primary)] px-2 py-0.5 rounded-md text-sm">
  主题标签
</span>
```

---

*更新时间：2026-03-15*