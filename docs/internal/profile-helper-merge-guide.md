# Profile Helper 完整合并指南（技术负责人）

> 对应郑总本地完善版：结构化画像前端 + Block 协议对话 + 科学家匹配 + `libs/profile_helper` 内置 Skill 全量同步。  
> 合并方式：**两个 PR 按顺序处理**（先 Resonnet 子模块，再 TopicLab 主仓）。

## PR 1：Resonnet（后端 + 内置 Skill）

| 项 | 内容 |
|----|------|
| **Fork 分支** | `Boyuan-Zheng/Resonnet` → `feature/profile-helper-complete` |
| **目标仓库** | `TashanGKD/Resonnet` |
| **开 PR** | https://github.com/Boyuan-Zheng/Resonnet/pull/new/feature/profile-helper-complete |

### 本 PR 包含

- `app/api/profile_helper.py`：与前端对齐的 API（含 `POST /chat/blocks`、`GET /chat-history/{session_id}`、`GET .../scientists/famous|field` 等）。
- `app/services/profile_helper/`：新增 `block_agent.py`、`scientist_match.py`、`scientists_db.py`；更新 `prompts.py`、`sessions.py` 等。
- `libs/profile_helper/`：**全目录同步**（`skills/*`、`docs/*`、`_template.md`），含 `collect-basic-info`、`import-ai-memory` 等 SKILL 修订。

### 合并后必做

在 **TopicLab 主仓库** 中更新子模块指针，使 `backend` 指向 Resonnet `main`（或合并后的目标分支）上包含本 PR 的 commit：

```bash
cd backend && git fetch origin && git checkout <合并后的 SHA>
cd .. && git add backend && git commit -m "chore(backend): bump Resonnet for profile-helper complete"
```

---

## PR 2：Tashan-TopicLab（前端）

| 项 | 内容 |
|----|------|
| **Fork 分支** | `Boyuan-Zheng/Tashan-TopicLab` → `feature/profile-helper-enhanced` |
| **目标仓库** | `TashanGKD/Tashan-TopicLab` |
| **开 PR** | https://github.com/Boyuan-Zheng/Tashan-TopicLab/pull/new/feature/profile-helper-enhanced |

### 本 PR 包含

- `frontend/src/modules/profile-helper/` 全量替换为增强版（约 32 个文件）。
- 新增 `blocks/`（Block 渲染）、`components/profile/`（各维度 Section）、科学家匹配 UI 等。
- 更新 `ProfilePage.tsx`、`profileHelperApi.ts`、`types.ts`、聊天相关组件与样式。

### 与 PR 1 的关系

前端依赖 PR 1 中新增的 HTTP 端点；**建议先合并并发布 Resonnet，再合并本 PR**（或同一发布窗口内先 bump 子模块再合前端）。

---

## 验证建议

1. Resonnet：`pytest` / 现有 CI；手动 hit `/profile-helper` 下新增路由（需与 `main.py` 中 `prefix` 一致）。
2. TopicLab：`frontend` build；本地联调：Resonnet 8000 + topiclab-backend（若用）+ Vite 3000。

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-04-02 | 初版：双 PR 说明与合并顺序 |
