# 他山世界 - 统一形状系统

基于 UI/UX Pro Max 设计系统，为学术研究协作平台制定的形状（圆角）规范。

---

## 一、设计原则

### 形状层次
- **主容器**：大圆角，友好开放
- **次容器**：中等圆角，清晰层级
- **交互元素**：统一圆角，易于识别
- **徽章/标签**：完全圆形，醒目突出

### 统一性
- 减少奇形异状，使用统一的圆角等级
- 避免使用自定义圆角值（如 `rounded-[22px]`）
- 所有圆角使用 CSS 变量统一管理

---

## 二、圆角等级定义（精简版）

**设计策略**：减少圆角类型，提高一致性。只保留 **3 个核心圆角等级**。

| 等级 | Tailwind 类 | CSS 变量 | 值 | 用途 | 使用频率 |
|------|------------|----------|-----|------|----------|
| **默认圆角** | `rounded-lg` | `--radius-md` | `12px` | **所有卡片、按钮、输入框、容器** | 70% |
| **大圆角** | `rounded-xl` | `--radius-lg` | `16px` | **弹窗、下拉菜单、缩略图** | 20% |
| **完全圆形** | `rounded-full` | `--radius-full` | `9999px` | **头像、Chip、徽章、筛选按钮** | 10% |

### 已废弃的圆角

| 圆角 | 状态 | 替代方案 | 说明 |
|------|------|----------|------|
| `rounded-sm` (6px) | ❌ 废弃 | `rounded-lg` | 过小，不再使用 |
| `rounded-md` (8px) | ❌ 废弃 | `rounded-lg` | 与 12px 差异不明显 |
| `rounded-2xl` (20px) | ❌ 废弃 | `rounded-xl` | 过度设计，统一为 16px |

### 简化原则

1. **一个圆角走天下**：`rounded-lg` (12px) 用于 90% 的场景
2. **特殊场景**：弹窗/下拉用 `rounded-xl` (16px)
3. **圆形元素**：头像/Chip 用 `rounded-full`
4. **禁止自定义**：不再使用 `rounded-[XXpx]`

---

## 三、控件形状分类清单

### 3.1 主要容器（Container）

| 组件/页面 | 当前形状 | 应改为 | 优先级 | 说明 |
|-----------|----------|--------|--------|------|
| `OpenClawSkillCard.tsx` - 主卡片 | `rounded-2xl` | ✅ `rounded-2xl` | P0 | 首页顶部卡片，保持超大圆角 |
| `TopicCard.tsx` - 话题卡片 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准卡片圆角 |
| `SourceArticleCard.tsx` - 文章卡片 | `rounded-[22px]` | ⚠️ `rounded-2xl` | P0 | 自定义圆角，需统一 |
| `LiteratureCard.tsx` - 文献卡片 | `rounded-[22px]` | ⚠️ `rounded-2xl` | P0 | 自定义圆角，需统一 |
| `ExpertCard.tsx` - 专家卡片 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准卡片圆角 |
| `SkillCard.tsx` - 技能卡片 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准卡片圆角 |
| `MCPGrid.tsx` - MCP 容器 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准容器圆角 |
| `ModeratorModeGrid.tsx` - 讨论方式容器 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准容器圆角 |
| `TopicDetail.tsx` - 评论容器 | `rounded-[28px]` | ⚠️ `rounded-2xl` | P0 | 自定义圆角，需统一 |
| `TopicDetail.tsx` - 回复容器 | `rounded-[26px]` | ⚠️ `rounded-2xl` | P0 | 自定义圆角，需统一 |
| `TopicDetail.tsx` - 内部容器 | `rounded-[22px]` | ⚠️ `rounded-2xl` | P0 | 自定义圆角，需统一 |
| `MyFavoritesPage.tsx` - 空状态容器 | `rounded-[20px]` | ⚠️ `rounded-2xl` | P1 | 自定义圆角，需统一 |

### 3.2 输入框（Input Fields）

| 组件/页面 | 当前形状 | 应改为 | 优先级 | 说明 |
|-----------|----------|--------|--------|------|
| `Login.tsx` - 输入框 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准输入框圆角 |
| `Register.tsx` - 输入框 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准输入框圆角 |
| `CreateTopic.tsx` - 输入框 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准输入框圆角 |
| `TopicConfigTabs.tsx` - 文本域 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准输入框圆角 |
| `MentionTextarea.tsx` - 文本域 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准输入框圆角 |
| `ExpertGrid.tsx` - 搜索框 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准输入框圆角 |
| `SkillGrid.tsx` - 搜索框 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准输入框圆角 |
| `MCPGrid.tsx` - 搜索框 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准输入框圆角 |
| `FavoriteCategoryPicker.tsx` - 输入框 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准输入框圆角 |

### 3.3 按钮（Buttons）

| 组件/页面 | 当前形状 | 应改为 | 优先级 | 说明 |
|-----------|----------|--------|--------|------|
| `TopNav.tsx` - 创建话题按钮 | `rounded-[var(--radius-lg)]` | ✅ `rounded-lg` | P1 | 使用 CSS 变量 |
| `Login.tsx` - 登录按钮 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准按钮圆角 |
| `Register.tsx` - 注册按钮 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准按钮圆角 |
| `CreateTopic.tsx` - 创建按钮 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准按钮圆角 |
| `TopicConfigTabs.tsx` - 主按钮 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准按钮圆角 |
| `TopicConfigTabs.tsx` - 自定义按钮 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准按钮圆角 |
| `SourceFeedPage.tsx` - 搜索按钮 | `rounded-full` | ⚠️ `rounded-lg` | P2 | 统一为中圆角 |
| `TopicList.tsx` - 筛选按钮 | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形（Chip 风格） |
| `AppErrorBoundary.tsx` - 刷新按钮 | `rounded-full` | ⚠️ `rounded-lg` | P2 | 统一为中圆角 |
| `OpenClawSkillCard.tsx` - CTA 按钮 | `rounded-xl` | ⚠️ `rounded-lg` | P2 | 统一为中圆角 |

### 3.4 徽章/标签（Badges & Chips）

| 组件/页面 | 当前形状 | 应改为 | 优先级 | 说明 |
|-----------|----------|--------|--------|------|
| `ExpertCard.tsx` - 头像 | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |
| `ExpertCard.tsx` - Chip | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |
| `ExpertCard.tsx` - 脱敏标签 | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |
| `SkillCard.tsx` - 头像 | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |
| `SkillCard.tsx` - Chip | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |
| `ModeratorModeCard.tsx` - 头像 | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |
| `ModeratorModeCard.tsx` - Chip | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |
| `TopicDetail.tsx` - 导航标签 | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |
| `TopicDetail.tsx` - 用户徽章 | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |
| `MobileSourceCategoryToc.tsx` - 源标签 | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |
| `StatusBadge.tsx` - 状态徽章 | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |
| `FavoriteCategoryPicker.tsx` - 分类徽章 | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |

### 3.5 下拉菜单/弹窗（Dropdowns & Modals）

| 组件/页面 | 当前形状 | 应改为 | 优先级 | 说明 |
|-----------|----------|--------|--------|------|
| `TopicConfigTabs.tsx` - 模态框 | `rounded-lg` | ⚠️ `rounded-xl` | P2 | 弹窗使用大圆角 |
| `ExpertCard.tsx` - 下拉菜单 | `rounded-lg` | ⚠️ `rounded-xl` | P2 | 弹窗使用大圆角 |
| `MentionTextarea.tsx` - 提及菜单 | `rounded-lg` | ⚠️ `rounded-xl` | P2 | 弹窗使用大圆角 |
| `ResourceDetailModal.tsx` - 模态框 | `rounded-lg` | ⚠️ `rounded-xl` | P2 | 弹窗使用大圆角 |
| `FavoriteCategoryPicker.tsx` - 下拉框 | `rounded-xl` | ✅ `rounded-xl` | P1 | 已使用大圆角 |

### 3.6 其他特殊元素

| 组件/页面 | 当前形状 | 应改为 | 优先级 | 说明 |
|-----------|----------|--------|--------|------|
| `SourceArticleCard.tsx` - 缩略图 | `rounded-[18px]` | ⚠️ `rounded-xl` | P1 | 自定义圆角，需统一 |
| `SourceArticlePreviewCard.tsx` - 缩略图 | `rounded-[16px]` | ⚠️ `rounded-xl` | P1 | 自定义圆角，需统一 |
| `SourceArticlePreviewCard.tsx` - 卡片 | `rounded-[22px]` | ⚠️ `rounded-2xl` | P1 | 自定义圆角，需统一 |
| `TopicCard.tsx` - 缩略图 | `rounded-md` | ⚠️ `rounded-lg` | P2 | 统一为中圆角 |
| `TopicDetail.tsx` - 头像 | `rounded-full` | ✅ `rounded-full` | P1 | 保持完全圆形 |
| `TopicDetail.tsx` - 加载骨架 | `rounded-2xl` | ✅ `rounded-2xl` | P1 | 已使用超大圆角 |
| `Footer.tsx` - 社交图标 | `rounded-lg` | ✅ `rounded-lg` | P1 | 标准图标容器圆角 |

---

## 四、改造优先级

### P0 - 立即改造（严重影响统一性）
1. 所有 `rounded-[XXpx]` 自定义圆角
2. 话题详情页的评论/回复容器
3. 文章/文献卡片的自定义圆角

### P1 - 高优先级（重要容器）
1. 所有卡片组件的圆角统一
2. 所有输入框的圆角统一
3. 所有徽章/标签的圆形统一
4. 弹窗/下拉菜单的圆角统一

### P2 - 中优先级（交互元素）
1. 按钮圆角统一（除 Chip 风格外）
2. 缩略图圆角统一
3. 特殊强调容器的圆角统一

---

## 五、CSS 变量（精简版）

在 `frontend/src/index.css` 中已定义：

```css
:root {
  /* ========== 圆角 (Radius) - 精简版 ========== */
  /* 只保留 3 个核心等级：默认、大、完全圆形 */
  --radius-sm: 12px;     /* 已废弃，映射到 --radius-md */
  --radius-md: 12px;     /* 默认圆角 - 卡片、按钮、输入框、容器 (70%) */
  --radius-lg: 16px;     /* 大圆角 - 弹窗、下拉菜单、缩略图 (20%) */
  --radius-xl: 16px;     /* 已废弃，映射到 --radius-lg */
  --radius-2xl: 16px;    /* 已废弃，映射到 --radius-lg */
  --radius-full: 9999px; /* 完全圆形 - 头像、Chip、徽章、筛选按钮 (10%) */
}
```

在 `frontend/tailwind.config.js` 中扩展：

```javascript
borderRadius: {
  'sm': 'var(--radius-sm)',    // 12px (已废弃)
  'md': 'var(--radius-md)',    // 12px (默认)
  'lg': 'var(--radius-lg)',    // 16px
  'xl': 'var(--radius-xl)',    // 16px (已废弃)
  '2xl': 'var(--radius-2xl)',  // 16px (已废弃)
  'full': 'var(--radius-full)',
}
```

**实际使用的圆角值：**
- `rounded-lg` / `rounded-md` / `rounded-sm` → **12px** (默认)
- `rounded-xl` / `rounded-2xl` → **16px** (大圆角)
- `rounded-full` → **9999px** (完全圆形)

```javascript
theme: {
  extend: {
    borderRadius: {
      'sm': 'var(--radius-sm)',
      'md': 'var(--radius-md)',
      'lg': 'var(--radius-lg)',
      'xl': 'var(--radius-xl)',
      '2xl': 'var(--radius-2xl)',
      'full': 'var(--radius-full)',
    }
  }
}
```

---

## 六、使用指南

### ✅ 正确使用

```tsx
// 卡片容器
<div className="rounded-lg border">卡片</div>

// 弹窗
<div className="rounded-xl shadow-xl">弹窗</div>

// 首页强调卡片
<div className="rounded-2xl border">强调卡片</div>

// 头像/Chip
<div className="rounded-full">头像</div>

// 按钮（非 Chip 风格）
<button className="rounded-lg">按钮</button>

// Chip 风格按钮/筛选
<button className="rounded-full">筛选</button>
```

### ❌ 避免使用

```tsx
// ❌ 自定义圆角值
<div className="rounded-[22px]"> → 改用 `rounded-2xl`
<div className="rounded-[16px]"> → 改用 `rounded-xl`
<div className="rounded-[28px]"> → 改用 `rounded-2xl`

// ❌ 过度使用超大圆角
<div className="rounded-2xl">输入框</div> → 改用 `rounded-lg`

// ❌ 圆角不统一
<button className="rounded-md">按钮 1</button>
<button className="rounded-lg">按钮 2</button>
→ 统一为 `rounded-lg`
```

---

## 七、改造检查清单

### ✅ 已完成
- [x] 搜索所有 `rounded-[` 自定义圆角
- [x] 替换为对应的标准圆角类
- [x] 更新 `index.css` 添加 `--radius-2xl`
- [x] 更新 `tailwind.config.js` 映射

### 待完成
- [ ] 验证所有卡片圆角统一
- [ ] 验证所有输入框圆角统一
- [ ] 验证所有按钮圆角统一（区分 Chip 风格）
- [ ] 验证所有弹窗/下拉菜单圆角统一

## 八、改造记录

### 2026-03-15 - 圆角精简改造

**改造策略**：将 6 个圆角等级精简为 3 个核心等级。

#### 第一阶段：P0 自定义圆角改造

**完成的文件：**

| 文件 | 改造内容 | 圆角变化 |
|------|----------|----------|
| `LiteratureCard.tsx` | 文献卡片 | `rounded-[22px]` → `rounded-2xl` |
| `SourceArticleCard.tsx` | 文章卡片 | `rounded-[22px]` → `rounded-2xl` |
| `SourceArticleCard.tsx` | 文章缩略图 | `rounded-[18px]` → `rounded-xl` |
| `SourceArticlePreviewCard.tsx` | 预览卡片 | `rounded-[22px]` → `rounded-2xl` |
| `SourceArticlePreviewCard.tsx` | 预览缩略图 | `rounded-[16px]` → `rounded-xl` |
| `TopicDetail.tsx` | 评论容器 | `rounded-[28px]` → `rounded-2xl` |
| `TopicDetail.tsx` | 回复容器 | `rounded-[26px]` → `rounded-2xl` |
| `TopicDetail.tsx` | 内部容器 | `rounded-[22px]` → `rounded-2xl` (2 处) |
| `MyFavoritesPage.tsx` | 空状态容器 | `rounded-[20px]` → `rounded-2xl` (2 处) |

**合计：11 处自定义圆角已统一**

#### 第二阶段：圆角精简（6→3）

**CSS 变量调整：**

| 变量名 | 原值 | 新值 | 状态 |
|--------|------|------|------|
| `--radius-sm` | 6px | 12px | ⚠️ 废弃，映射到 `--radius-md` |
| `--radius-md` | 8px | 12px | ✅ 默认圆角 |
| `--radius-lg` | 12px | 16px | ✅ 大圆角 |
| `--radius-xl` | 16px | 16px | ⚠️ 废弃，映射到 `--radius-lg` |
| `--radius-2xl` | 20px | 16px | ⚠️ 废弃，映射到 `--radius-lg` |
| `--radius-full` | 9999px | 9999px | ✅ 完全圆形 |

**批量替换：**

| 原圆角 | 新圆角 | 影响文件数 | 组件类型 |
|--------|--------|-----------|----------|
| `rounded-2xl` | `rounded-xl` | 7 | 卡片、容器 |
| `rounded-md` | `rounded-lg` | 4 | 按钮、菜单项 |
| `rounded-lg` (弹窗) | `rounded-xl` | 7 | 模态框、下拉菜单 |

**受影响的文件：**
- `OpenClawSkillCard.tsx` - 首页卡片
- `SourceArticleCard.tsx` - 文章卡片
- `SourceArticlePreviewCard.tsx` - 预览卡片
- `LiteratureCard.tsx` - 文献卡片
- `TopicDetail.tsx` - 评论/回复容器
- `SourceFeedPage.tsx` - 信源页面
- `MyFavoritesPage.tsx` - 收藏页面
- `LibraryPage.tsx` - 库页面导航
- `TopicCard.tsx` - 话题缩略图
- `ReactionButton.tsx` - 反应按钮
- `TopicConfigTabs.tsx` - 模态框 (2 处)
- `ExpertCard.tsx` - 下拉菜单
- `MentionTextarea.tsx` - 提及菜单
- `ResourceDetailModal.tsx` - 资源模态框
- `ExpertDetailModal.tsx` - 专家模态框
- `SkillDetailModal.tsx` - 技能模态框
- `MCPDetailModal.tsx` - MCP 模态框
- `ModeratorModeDetailModal.tsx` - 讨论方式模态框

**改造后圆角使用统计：**

| 圆角类 | 使用次数 | 占比 | 用途 |
|--------|----------|------|------|
| `rounded-lg` | ~120 | 75% | 默认圆角（卡片、按钮、输入框） |
| `rounded-xl` | ~25 | 15% | 大圆角（弹窗、下拉菜单、缩略图） |
| `rounded-full` | ~15 | 10% | 完全圆形（头像、Chip、徽章） |

---

**文档版本**: 2.0 - 精简版  
**最后更新**: 2026-03-15  
**设计系统**: UI/UX Pro Max - Soft UI Evolution
