# Scientist Perspective Skill System

## 1. 目标

这层不是 `corpus`，也不是 `dossier`，而是 TopicLab 里真正面向“分身 / perspective”使用的历史科学家 skill 层。

它的角色是把现有三层资产接起来：

1. `data/scientist-corpora/<slug>/`
2. `docs/cognition-portrait/scientist-dossiers/archive/<slug>.md`
3. `.cursor/skills/<slug>-perspective/`

一句话说：

- `corpus` 负责尽可能收全公开语料
- `dossier` 负责把人物写成可比较档案
- `perspective skill` 负责把人物变成可调用的分身

---

## 2. 当前实现状态（2026-04-10）

当前已经生成：

- `120` 个 scientist perspective skill 目录
- `120` 个 `SKILL.md`
- `720` 个 `references/research/*.md`
- `120` 个 `references/sources/README.md`
- `1` 份总索引：
  - `.cursor/skills/scientist-perspectives-index.md`
  - `.cursor/skills/scientist-perspectives-index.csv`

生成脚本：

- [scripts/generate_scientist_perspectives.py](/Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scripts/generate_scientist_perspectives.py)

输出根目录：

- [.cursor/skills](/Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/.cursor/skills)

---

## 3. 输出结构

每位科学家当前都生成成下面这套结构：

```text
.cursor/skills/<slug>-perspective/
├── SKILL.md
└── references/
    ├── research/
    │   ├── 01-facts-and-biography.md
    │   ├── 02-writings-and-primary-materials.md
    │   ├── 03-work-style-and-method.md
    │   ├── 04-public-expression-and-reception.md
    │   ├── 05-turning-points-and-controversies.md
    │   └── 06-anchor-summary.md
    └── sources/
        └── README.md
```

这套结构不是凭空写的，而是对齐了 `nuwa-skill` 的人物 skill 要求：

- 顶层 `SKILL.md`
- 六路 research 支撑层
- sources 入口

但当前版本没有复制 raw corpus 文件，而是让 skill 通过 links 指回 TopicLab 内的 corpus workspace。

---

## 4. 数据来源与生成逻辑

当前 skill 不是人工逐个手写，而是从已有结构化资产生成：

### 4.1 主要输入

- `scientist-dossiers/INDEX.csv`
- `archive/<slug>.md`
- `data/scientist-corpora/<slug>/manifests/project.json`
- `package/<slug>_text_only_v1/DATASET_MANIFEST.json`

### 4.2 生成逻辑

脚本会：

1. 读取每位人物的 dossier 索引行
2. 解析 archive 中的固定 section：
   - 基本信息
   - 人物定位
   - 研究气质
   - 工作方式
   - 公共风格
   - 转折点
   - 张力与限制
   - 锚点适配
   - `4+1` 初判
   - 可信度
3. 读取 corpus package 的覆盖统计：
   - papers discovered
   - pdf downloaded
   - media discovered
   - books/courses discovered
4. 生成面向角色调用的 `SKILL.md`
5. 生成 6 个 research 摘要文件
6. 生成 source README，把使用者导回 corpus workspace

---

## 5. 当前 skill 的成熟度语义

这层一定要分清：

- `reviewed` skill
- `seeded` skill

当前 skill 目录虽然已经都有了，但**不是 120 个都同等成熟**。

### 5.1 `reviewed`

对应强锚点或已补实人物。

特点：

- dossier 本身信息比较完整
- `SKILL.md` 里能形成更像样的心智模型、启发式和表达 DNA
- 更适合作为第一批可真正拿来用的 scientist twin

### 5.2 `seeded`

对应已经有 corpus 和 dossier，但档案仍较薄的人物。

特点：

- skill 已经存在
- 可以进入角色，但默认更保守
- 明确强调证据边界
- 适合做方向性视角，而不适合做强拟人表演

所以当前最准确的表述是：

**120 位科学家的分身层已经建好，但其中很多仍是“seeded perspective”，后续要继续用 dossier/corpus 补厚。**

---

## 6. 已验证的工作流

这条链路现在已经验证可用：

1. 先建 `corpus`
2. 再建 `dossier`
3. 再从 `dossier + corpus` 生成 `perspective skill`
4. 以后当某位人物的 dossier 补强后，直接重新跑 skill 生成脚本即可刷新

这比一开始就手写 120 个 skill 更稳，因为：

- skill 不再脱离证据层
- 语料更新后可以重建
- 低证据人物可以先保守输出，不必伪装完整

---

## 7. 如何刷新

### 7.1 全量刷新

```bash
python3 scripts/generate_scientist_perspectives.py
```

### 7.2 单人刷新

```bash
python3 scripts/generate_scientist_perspectives.py --slugs richard-feynman
```

### 7.3 典型刷新时机

- 某位人物的 archive 明显补实后
- 某位人物的 corpus package 新增了大量 PDF / media
- 某批强锚点人物被重新评审后

---

## 8. 当前边界

这层已经是“分身层”，但还不是最终完美版。

当前边界很明确：

- 它是根据 dossier 结构化生成的，不是逐人深写版
- 对高信息密度人物，效果已经明显可用
- 对低信息密度人物，仍然偏保守和模板化
- 当前研究支撑层是从 TopicLab 资产回填，不是 `nuwa-skill` 式逐人六路人工深采

因此后续更合理的工作不是“推翻重做”，而是：

1. 继续补 dossier
2. 继续补 corpus
3. 按需重生成 skill
4. 对重点人物再做人工精修版 skill

---

## 9. 推荐的下一步

如果要继续把这层做强，最值得优先做的是：

1. 挑 `20-30` 位强锚点人物做人工精修版 skill
2. 把这些精修版作为真正高质量 scientist twin
3. 其余 `seeded` 人物继续保持可调用但保守的版本

也就是说：

**当前已经从“没有分身层”走到了“120 个可持续刷新的分身目录”，下一步该从“全量存在”转向“重点做强”。**
