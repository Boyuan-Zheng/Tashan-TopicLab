# 他山世界 - 页面与组件空间清单

本文档列出网站所有页面和组件，用于统一配色和风格改造。

---

## 一、全局层 (Global)

| 文件 | 说明 | 状态 |
|------|------|------|
| `src/index.css` | 全局样式、CSS 变量、动画 | ✅ 已改造 |
| `src/App.tsx` | 应用入口、路由配置 | ✅ 已改造 |
| `src/components/TopNav.tsx` | 顶部导航栏 | ✅ 已改造 |
| `src/components/Footer.tsx` | 页脚 | ✅ 已改造 |
| `src/components/AppErrorBoundary.tsx` | 错误边界 | ✅ 已改造 |
| `tailwind.config.js` | Tailwind 配置 | ✅ 已改造 |

---

## 二、页面 (Pages)

### 2.1 话题相关

| 文件 | 路由 | 说明 | 状态 |
|------|------|------|------|
| `src/pages/TopicList.tsx` | `/` | 话题列表首页 | ⏳ 待改造 |
| `src/pages/TopicDetail.tsx` | `/topics/:id` | 话题详情页 | ⏳ 待改造 |
| `src/pages/CreateTopic.tsx` | `/topics/new` | 创建话题页 | ⏳ 待改造 |

### 2.2 信源相关

| 文件 | 路由 | 说明 | 状态 |
|------|------|------|------|
| `src/pages/SourceFeedPage.tsx` | `/source-feed/:section` | 信源页面 | ⏳ 待改造 |

### 2.3 库相关

| 文件 | 路由 | 说明 | 状态 |
|------|------|------|------|
| `src/pages/LibraryPage.tsx` | `/library/:section` | 库页面（统一入口） | ⏳ 待改造 |
| `src/pages/ExpertList.tsx` | - | 专家列表（被 LibraryPage 引用） | ⏳ 待改造 |
| `src/pages/ExpertEdit.tsx` | `/experts/:name/edit` | 专家编辑页 | ⏳ 待改造 |
| `src/pages/SkillLibrary.tsx` | - | 技能库（被 LibraryPage 引用） | ⏳ 待改造 |
| `src/pages/MCPLibrary.tsx` | - | MCP 库（被 LibraryPage 引用） | ⏳ 待改造 |
| `src/pages/ModeratorModeLibrary.tsx` | - | 主持人模式库（被 LibraryPage 引用） | ⏳ 待改造 |

### 2.4 Agent Link 相关

| 文件 | 路由 | 说明 | 状态 |
|------|------|------|------|
| `src/pages/AgentLinkLibraryPage.tsx` | `/agent-links` | Agent Link 库页面 | ⏳ 待改造 |
| `src/pages/AgentLinkChatPage.tsx` | `/agent-links/:slug` | Agent Link 聊天页面 | ⏳ 待改造 |

### 2.5 用户相关

| 文件 | 路由 | 说明 | 状态 |
|------|------|------|------|
| `src/pages/Login.tsx` | `/login` | 登录页 | ⏳ 待改造 |
| `src/pages/Register.tsx` | `/register` | 注册页 | ⏳ 待改造 |
| `src/pages/MyFavoritesPage.tsx` | `/favorites` | 我的收藏页 | ⏳ 待改造 |

### 2.6 科研数字分身

| 文件 | 路由 | 说明 | 状态 |
|------|------|------|------|
| `src/pages/ProfileHelperPage.tsx` | `/profile-helper/*` | 数字分身主页 | ⏳ 待改造 |

---

## 三、通用组件 (Components)

### 3.1 布局组件

| 文件 | 说明 | 状态 |
|------|------|------|
| `src/components/LibraryPageLayout.tsx` | 库页面通用布局 | ✅ 已改造 |
| `src/components/TabPanel.tsx` | Tab 面板 | ⏳ 待改造 |
| `src/components/ResizableToc.tsx` | 可调整大小的目录 | ⏳ 待改造 |

### 3.2 卡片组件

| 文件 | 说明 | 状态 |
|------|------|------|
| `src/components/TopicCard.tsx` | 话题卡片 | ⏳ 待改造 |
| `src/components/ExpertCard.tsx` | 专家卡片 | ⏳ 待改造 |
| `src/components/SkillCard.tsx` | 技能卡片 | ⏳ 待改造 |
| `src/components/MCPCard.tsx` | MCP 卡片 | ⏳ 待改造 |
| `src/components/OpenClawSkillCard.tsx` | OpenClaw 技能卡片（首页顶部） | ⏳ 待改造 |
| `src/components/ModeratorModeCard.tsx` | 主持人模式卡片 | ⏳ 待改造 |
| `src/components/SourceArticleCard.tsx` | 信源文章卡片 | ⏳ 待改造 |
| `src/components/SourceArticlePreviewCard.tsx` | 信源文章预览卡片 | ⏳ 待改造 |
| `src/components/LiteratureCard.tsx` | 文献卡片 | ⏳ 待改造 |

### 3.3 网格组件

| 文件 | 说明 | 状态 |
|------|------|------|
| `src/components/ExpertGrid.tsx` | 专家网格 | ⏳ 待改造 |
| `src/components/SkillGrid.tsx` | 技能网格 | ⏳ 待改造 |
| `src/components/MCPGrid.tsx` | MCP 网格 | ⏳ 待改造 |
| `src/components/ModeratorModeGrid.tsx` | 主持人模式网格 | ⏳ 待改造 |

### 3.4 弹窗组件

| 文件 | 说明 | 状态 |
|------|------|------|
| `src/components/ExpertDetailModal.tsx` | 专家详情弹窗 | ⏳ 待改造 |
| `src/components/SkillDetailModal.tsx` | 技能详情弹窗 | ⏳ 待改造 |
| `src/components/MCPDetailModal.tsx` | MCP 详情弹窗 | ⏳ 待改造 |
| `src/components/ModeratorModeDetailModal.tsx` | 主持人模式详情弹窗 | ⏳ 待改造 |
| `src/components/ResourceDetailModal.tsx` | 资源详情弹窗 | ⏳ 待改造 |

### 3.5 选择器组件

| 文件 | 说明 | 状态 |
|------|------|------|
| `src/components/ExpertSelector.tsx` | 专家选择器 | ⏳ 待改造 |
| `src/components/SkillSelector.tsx` | 技能选择器 | ⏳ 待改造 |
| `src/components/MCPServerSelector.tsx` | MCP 服务器选择器 | ⏳ 待改造 |
| `src/components/ModeratorModeSelector.tsx` | 主持人模式选择器 | ⏳ 待改造 |
| `src/components/FavoriteCategoryPicker.tsx` | 收藏分类选择器 | ⏳ 待改造 |

### 3.6 其他组件

| 文件 | 说明 | 状态 |
|------|------|------|
| `src/components/TopicConfigTabs.tsx` | 话题配置标签页 | ⏳ 待改造 |
| `src/components/PostThread.tsx` | 帖子线程 | ⏳ 待改造 |
| `src/components/MentionTextarea.tsx` | @ 提及文本框 | ⏳ 待改造 |
| `src/components/ReactionButton.tsx` | 反应按钮（点赞等） | ⏳ 待改造 |
| `src/components/StatusBadge.tsx` | 状态徽章 | ⏳ 待改造 |
| `src/components/SourceCategoryToc.tsx` | 信源分类目录 | ⏳ 待改造 |
| `src/components/MobileSourceCategoryToc.tsx` | 移动端信源分类目录 | ⏳ 待改造 |
| `src/components/ModeratorModeConfig.tsx` | 主持人模式配置 | ⏳ 待改造 |
| `src/components/ExpertManagement.tsx` | 专家管理 | ⏳ 待改造 |

---

## 四、模块 (Modules)

### 4.1 Profile Helper 模块

| 文件 | 说明 | 状态 |
|------|------|------|
| `src/modules/profile-helper/pages/ProfilePage.tsx` | 档案页 | ✅ 已改造 |
| `src/modules/profile-helper/pages/ChatPage.tsx` | 聊天页 | ⏳ 待改造 |
| `src/modules/profile-helper/pages/ScalesPage.tsx` | 量表页 | ⏳ 待改造 |
| `src/modules/profile-helper/pages/ScaleTestPage.tsx` | 量表测试页 | ⏳ 待改造 |
| `src/modules/profile-helper/ProfilePanel.tsx` | 档案面板 | ✅ 已改造 |
| `src/modules/profile-helper/ChatWindow.tsx` | 聊天窗口 | ⏳ 待改造 |
| `src/modules/profile-helper/MessageBubble.tsx` | 消息气泡 | ⏳ 待改造 |
| `src/modules/profile-helper/LoadingDots.tsx` | 加载动画 | ⏳ 待改造 |
| `src/modules/profile-helper/profile-helper.css` | 模块样式 | ✅ 已改造 |

### 4.2 Agent Links 模块

| 文件 | 说明 | 状态 |
|------|------|------|
| `src/modules/agent-links/AgentLinkChatWindow.tsx` | Agent Link 聊天窗口 | ⏳ 待改造 |
| `src/modules/agent-links/agent-link-chat.css` | 模块样式 | ⏳ 待改造 |

---

## 五、改造优先级建议

### P0 - 核心页面（用户最先看到）
1. `TopicList.tsx` - 首页
2. `TopNav.tsx` - 导航栏（已完成）
3. `Footer.tsx` - 页脚（已完成）
4. `OpenClawSkillCard.tsx` - 首页顶部卡片

### P1 - 主要功能页面
1. `TopicDetail.tsx` - 话题详情
2. `SourceFeedPage.tsx` - 信源页
3. `LibraryPage.tsx` + 相关库页面
4. `Login.tsx` / `Register.tsx` - 登录注册

### P2 - 卡片和列表组件
1. 各类 Card 组件
2. 各类 Grid 组件
3. 各类 Modal 组件

### P3 - 选择器和辅助组件
1. 各类 Selector 组件
2. 表单相关组件
3. 其他辅助组件

### P4 - 模块页面
1. Profile Helper 模块
2. Agent Links 模块

---

## 六、设计规范要点

### 颜色系统
- **主色**：`--color-primary: #5B9BD5`（淡蓝）
- **次色**：`--color-secondary: #9FD4C4`（淡绿）
- **强调色**：`--color-accent: #6BC5D6`
- **深色**：`--color-dark: #0E2E4F`
- **更深深色**：`--color-darker: #0A1F35`

### 背景色
- **页面背景**：`#F8FAFB` + 微妙渐变光晕
- **卡片背景**：`#FFFFFF`
- **Footer 背景**：`--gradient-dark`

### 按钮
- **主按钮**：使用 `--color-dark`（非渐变）
- **次按钮**：边框样式
- **hover 效果**：微上浮 + 阴影增强

### 文字
- **品牌文字**：无衬线字体 + 字间距
- **正文**：衬线字体（Noto Serif SC）
- **标题**：可使用深色，避免高亮渐变

---

*更新时间：2026-03-15*