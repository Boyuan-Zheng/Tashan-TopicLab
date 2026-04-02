# tashan-profile-helper-frontend

> 他山生态·科研数字分身（profile-helper）前端共享模块  
> 版本：v1.0 | 创建：2026-03-19

---

## ⚠️ 重要规则

**此仓库是他山生态中所有产品的画像系统前端唯一真源。**

- ✅ 所有对画像功能的前端修改，必须在**本仓库**中进行
- ❌ 严禁在各产品仓库（tashan-world、Tashan-TopicLab 等）中直接修改 `profile-helper/` 目录
- 直接修改各产品中的 submodule 内容，会在下次 `git submodule update` 时被覆盖丢失

---

## 使用方式

```bash
# 在新产品的 frontend/ 目录下添加 submodule
git submodule add https://github.com/TashanGKD/tashan-profile-helper-frontend.git \
    src/modules/profile-helper

# 更新到最新版本
git submodule update --remote src/modules/profile-helper
```

---

## 接入产品列表

| 产品 | 状态 | 备注 |
|------|------|------|
| Tashan-TopicLab | ✅ 已接入 | 标准版来源 |
| tashan-world | ✅ 已接入 | 2026-03-19 迁移为 submodule |

---

## 依赖说明

使用本模块的产品需要在 `package.json` 中安装：
- `react-markdown`
- `remark-gfm`
- `remark-math`
- `rehype-katex`
- `katex`
