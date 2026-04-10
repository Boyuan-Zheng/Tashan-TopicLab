# 已故科学家档案采集流水线：从 120 人宽池到可比较的人物档案库

## 1. 文档目标

本文定义 TopicLab 后续为 `120 位已故科学家候选池` 建档时应采用的统一流水线。

目标不是做一堆松散的传记笔记，而是建立一个后续可用于：

1. 画像类型锚点选择
2. 结果卡科学人物参考
3. 类型命名灵感提取
4. 研究风格比较与收缩

的**结构化科学家档案库**。

---

## 2. 为什么要先定义流水线

当前方向已经明确：

- 我们需要的不是 10 个名人
- 而是一个足够宽的、可继续收缩的 `120 人已故科学家档案池`

但如果直接开始收集，很容易出现三个问题：

1. 每个人的资料结构不一致，后面无法横向比较
2. 有的人写成传记，有的人写成轶事，有的人只有成就列表
3. 后面做类型映射时，发现缺少“研究气质”“工作方式”“公共风格”等关键字段

所以必须先把采集标准和档案模板定住。

---

## 3. 这套流程参考了什么

本流程不是凭空发明，而是明确参考了本地仓库 [nuwa-skill](/Users/boyuan/aiwork/0310_huaxiang/nuwa-skill/README.md) 的方法论。

从 `nuwa-skill` 借鉴的关键点：

- 不把“公开信息很多”误当成“已经可用”
- 先按固定维度分路收集
- 保留一手 / 二手 / 推断的区分
- 保留矛盾，不强行调和
- 先做结构化摘要，再做更高阶提炼

但 TopicLab 的目标和 `nuwa-skill` 不完全相同：

- `nuwa-skill` 主要是在蒸馏“一个人的思维方式”，生成可运行的 perspective skill
- TopicLab 这里要的是“已故科学家人物档案库”，目的是后续画像锚点与比较

因此，我们只借用其采集思想，不照搬最终产物形式。

---

## 4. 总体结构：两层资产

后续每位科学家应至少沉淀两层资产。

### 第一层：原始研究资产

作用：

- 保留来源
- 支撑追溯
- 便于后续修正

内容包括：

- 生平事实
- 著作 / 论文 / 演讲 / 书信 / 访谈
- 外部传记与评价
- 关键事件与争议

### 第二层：结构化人物档案

作用：

- 统一比较
- 用于画像系统
- 用于后续类型收缩

内容包括：

- 基本信息
- 研究气质
- 工作方式
- 表达与公共风格
- 价值张力
- 适合作为哪类画像锚点

一句话说：

- **第一层是证据**
- **第二层是可比较的人物卡**

---

## 5. 推荐目录结构

建议后续在认知 / 画像文档目录下新增一个专门的科学家档案库目录，例如：

```text
docs/cognition-portrait/scientist-dossiers/
├── README.md
├── _template.md
├── archive/
│   ├── euclid.md
│   ├── archimedes.md
│   ├── hypatia.md
│   └── ...
└── research/
    ├── euclid/
    │   ├── 01-facts-and-biography.md
    │   ├── 02-writings-and-primary-materials.md
    │   ├── 03-work-style-and-method.md
    │   ├── 04-public-expression-and-reception.md
    │   ├── 05-turning-points-and-controversies.md
    │   └── 06-anchor-summary.md
    └── ...
```

说明：

- `archive/` 放最终给产品和设计使用的单人档案
- `research/人名/` 放该人的原始调研文件
- `06-anchor-summary.md` 是从研究资产向最终档案过渡的中间摘要层

---

## 6. 单人采集应拆成 6 个固定维度

参考 `nuwa-skill` 的“六路并行采集”，这里建议每位科学家统一按 6 个固定维度建档。

### 6.1 基本事实与生平

回答：

- 他是谁
- 生卒年
- 核心学科
- 代表贡献
- 所处时代与机构背景

建议来源：

- Nobel Prize
- MacTutor
- NAS Biographical Memoirs
- Science History Institute
- Britannica

输出文件：

- `01-facts-and-biography.md`

### 6.2 主要著作与一手材料

回答：

- 他留下了哪些可直接代表其思考方式的文本 / 演讲 / 讲稿 / 书信 / memoir
- 哪些是一手材料
- 哪些材料最能体现其研究品味

建议来源：

- 官方档案
- 著作目录
- 论文代表作
- 书信 / 演讲 / 回忆录

输出文件：

- `02-writings-and-primary-materials.md`

### 6.3 研究方法与工作风格

回答：

- 更偏理论还是实验
- 更偏整合还是深挖
- 更偏长期打磨还是高频试探
- 更偏独立推进还是协作组织

这是最重要的一层，因为它直接对应后续画像锚点。

建议来源：

- 传记
- 学术机构回忆录
- 同行评价
- 重大研究过程复盘

输出文件：

- `03-work-style-and-method.md`

### 6.4 表达方式与公共风格

回答：

- 他是否擅长公开表达
- 风格是简洁、锋利、幽默、庄重还是克制
- 是“公众型科学家”还是“沉潜型科学家”

建议来源：

- 讲演记录
- 访谈
- 回忆录
- 他人对其表达风格的描述

输出文件：

- `04-public-expression-and-reception.md`

### 6.5 转折点、冲突与争议

回答：

- 他做过哪些关键选择
- 研究生涯中有哪些转折点
- 有没有争议、误判、冲突、被低估或被误读的部分

这一步不是为了“八卦”，而是为了避免把人物写成过度平滑的英雄模板。

输出文件：

- `05-turning-points-and-controversies.md`

### 6.6 锚点摘要

回答：

- 这个人最适合被记成什么样的“研究气质样本”
- 他不适合作为什么
- 他适合成为哪些画像维度的主锚点 / 备选锚点

输出文件：

- `06-anchor-summary.md`

---

## 7. 证据标注规则

每份研究文件都要明确区分三类信息：

- `一手资料`
  - 本人著作、本人讲演、本人信件、本人公开谈话
- `二手资料`
  - 传记、机构回忆录、学者综述、权威百科
- `推断`
  - 基于多条证据归纳出的判断

建议在文档里显式标记：

- `事实`
- `外部评价`
- `推断`

---

## 8. 已验证的 Bootstrap 实现（2026-04-10）

这套流水线已经在 TopicLab 仓库内按 `public_only` 跑出一版真实可用的 corpus 根目录：

- 根目录：`data/scientist-corpora/`
- 覆盖范围：120 位已故科学家
- 每位都已生成：
  - corpus workspace
  - `manifests/*`
  - clean texts
  - AI-ready package
  - 回填后的 dossier / research 链接

### 8.1 这轮实际采用的公开源

- `Wikipedia`：身份与生平基线
- `Wikidata`：结构化 claims、aliases、occupation、notable works
- `OpenLibrary`：作者页与 works catalog
- `OpenAlex`：现代人物的作者解析与 works catalog

### 8.2 这轮验证出的时代适配规则

- 前现代 / 19 世纪著作型人物：
  - 不强行套 `OpenAlex`
  - 以身份资料、著作目录、学术史入口为主
- 20 世纪及更现代人物：
  - 增加 `OpenAlex` works discovery
  - 记录 abstract fallback 与 public PDF candidates
- 历史人物缺少媒体 / 课程材料时：
  - 在 `missing_items.csv` 中显式标记为历史非适用
  - 不把它当作“漏抓”

### 8.3 这轮真实踩到的坑

- `OpenAlex` 对高 work-count 人物会非常慢，尤其是 Darwin / Einstein / Feynman 这类人物。
- 如果逐条直接下载 public PDF，会把 120 人批处理拖成超长阻塞任务。
- `OpenLibrary` 对很多科学人物能提供作者页，但 `works` 覆盖远不稳定，不能把它误当成“著作全量目录”的可靠替代。
- 因此 bootstrap pass 的实际规则改成了：
  - `全量发现 works`
  - `全量记录 public PDF candidates`
  - 把 binary PDF 下载显式记为 `pending_retry`
  - 不做 silent sampling

### 8.4 这轮实现后的目录分工

- `docs/cognition-portrait/scientist-dossiers/`
  - 可比较人物档案
  - research 摘要层
- `data/scientist-corpora/<slug>/`
  - raw / metadata / manifests / texts / package

这意味着后续再补强某个人，不需要重新设计目录，只需要继续增量更新现有 corpus workspace。

### 8.5 第二轮增量清理已验证结果（2026-04-10）

在 bootstrap pass 之后，又执行了一轮真正的增量清理：

- 清理目标：
  - `1929` 个 `pending_pdf_candidates`
  - `82` 个 `media_pending_retry`
- 实现方式：
  - 对 `downloads.csv` 中 `paper_pdf / pending_retry` 逐条实际发起下载
  - 对 `sources.csv` 中 `media_catalog / pending_retry` 逐条执行公开 YouTube metadata 搜索
  - 每位人物刷新 package `README.md / INDEX.csv / DATASET_MANIFEST.json`

按第二轮结束后的**最终文件状态**聚合，结果是：

- `downloaded_public_pdfs: 473`
- `blocked_pdf_candidates: 1442`
- `remaining_pdf_pending_retry: 14`
- `media_catalog_done: 82`
- `media_catalog_missing: 38`
- `media_catalog_pending_retry: 0`

这轮验证出的结论：

- `media_pending_retry` 可以在一次集中增量里清零，因为视频元数据发现成本相对低，适合批处理。
- `pending_pdf_candidates` 不能指望全部清零，很多公开候选最后会落成：
  - 404 / 403
  - HTML 落地页而不是 PDF
  - 重定向后非 PDF 内容
  - 超时后仍需再试
- 第二轮之后，剩余 `14` 个 `pending_retry` 已经高度集中在少数现代高产人物上：
  - `santiago-ramon-y-cajal`: 2
  - `niels-bohr`: 2
  - `albert-einstein`: 1
  - `ernest-rutherford`: 1
  - `herbert-a-simon`: 1
  - `inge-lehmann`: 1
  - `joshua-lederberg`: 1
  - `ludwig-boltzmann`: 1
  - `max-planck`: 1
  - `paul-dirac`: 1
  - `seymour-papert`: 1
  - `vera-rubin`: 1

这说明第三轮不该再跑 120 人全量，而应该针对残留的少数人物和少数 URL 做 focused retry。

### 8.6 第二轮真实踩到的坑

- 同一个人物如果先做了单人 dry-run，再跑全量 batch，终端 aggregate 只会统计“本轮真正处理到的 pending”，不会自动补上 dry-run 已解决的部分。
- 因此做最终验收时，必须以 `downloads.csv / sources.csv / package manifest` 的**最终文件状态**为准，而不是只看全量脚本最后一行 aggregate。
- `INDEX.csv` 的正确统计口径应是：
  - package 内真实文件数
  - 排除 `INDEX.csv` 本身
  - 再与 `DATASET_MANIFEST.json.file_count` 对账
- 这一步已经通过抽样人物验证：
  - `max-planck`
  - `santiago-ramon-y-cajal`
  - `marie-curie`
  - `vera-rubin`

关键原则：

- 不要把“人物轶事”直接升级成“人格结论”
- 不要把“公众印象”直接升级成“研究风格事实”
- 不要因为想要类型锚点，就强行把每个人写成极端化样本

---

## 8. 推荐的批量推进顺序

不建议 120 人完全随机推进。

建议分 4 批做：

### 第一批：高识别度强锚点人物（20 位）

目标：

- 快速建立模板可用性
- 先拿到最容易被产品化的核心锚点

特点：

- 公众识别度高
- 研究风格叙事强
- 来源容易找全

### 第二批：补风格缺口人物（30 位）

目标：

- 专门补那些第一批里没有覆盖好的风格维度

例如：

- 极端沉潜型
- 长周期观察型
- 系统组织型
- 工程调度型
- 低公共表达但高研究强度型

### 第三批：补学科与时代多样性（40 位）

目标：

- 避免名单过度偏物理、偏欧美、偏 20 世纪

### 第四批：扩展边界人物（30 位）

目标：

- 为后续命名与锚点选择留冗余

例如：

- 更跨界的人物
- 更少见但很有研究风格辨识度的人物

---

## 9. 不建议直接复用 nuwa-skill 的地方

虽然 `nuwa-skill` 方法论非常有帮助，但这里有几件事不能直接照搬：

### 9.1 不能过度强调“表达 DNA”

因为很多已故科学家根本不是以公开表达见长，资料量也不均衡。

在 TopicLab 档案里：

- “表达方式”是一个维度
- 但不是每个人都必须有强烈可扮演风格

### 9.2 不能强求每个人都有完整“心智模型”

这里的目标不是做 120 个 perspective skill。

很多科学家更适合被提炼为：

- 研究方法
- 工作气质
- 问题处理方式

而不是完整的“可模拟人格”。

### 9.3 不能过度依赖长对话语料

很多现代人物可以靠播客、采访、长视频；但历史科学家不一定有这些材料。

所以这里必须承认：

- 资料结构天然不均匀
- 档案质量应以“可证据支撑的研究风格摘要”为目标

---

## 10. 推荐的完成标准

每位科学家的档案至少满足以下条件，才算“收全到可用程度”：

1. 有稳定的基本事实信息
2. 至少有 2 类以上可靠来源
3. 能写出一版可信的研究风格摘要
4. 能判断其更像主锚点、备选锚点，还是仅作参考人物
5. 能说明其“不适合”映射哪些类型

注意：

- “收全”不意味着把所有资料都下载完
- “收全”意味着已经足够支持后续画像系统使用

---

## 11. 下一步建议

基于本文，最合理的下一步是：

1. 先定义统一的单人档案模板
2. 再开始批量生成 120 份科学家档案
3. 每完成一批，就做一次“强锚点候选收缩”

---

## 12. 当前最重要的一句话

**后面真正要建的，不是 120 篇传记，而是一套“可比较、可追溯、可用于画像锚点选择”的科学家档案库。**
