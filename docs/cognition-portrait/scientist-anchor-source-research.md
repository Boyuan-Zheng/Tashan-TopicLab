# 科学人物锚点资料源调研：已故科学家人物池、来源分层与候选策略

## 1. 文档目标

本文用于回答轻测试 / 画像系统中一个关键问题：

如果我们不受当前本地科学家库限制，想从历史上更大范围的、已故的科学家中挑选“画像原型人物”，那么：

1. 网上是否已经存在可直接拿来用的“科学家画像 / 人格分析总库”
2. 哪些资料源最适合建立人物锚点池
3. 后续该如何构建“类型命名 + 科学人物锚点”的系统

---

## 2. 一句话结论

本轮调研后的核心结论是：

**我没有找到一个现成、权威、覆盖全学科、并且已经把“所有已故科学家”做成结构化人格画像的公共数据库。**

目前最现实、也最可靠的路径不是“直接找到现成总库”，而是：

1. 用 `权威人物资料库` 建科学家候选池
2. 用 `历史影响力 / 知名度数据集` 做优先级筛选
3. 用 `创造力与科学人格研究` 作为群体层参考框架
4. 再由 TopicLab 自己完成“人物锚点画像化”

也就是说：

- `人物素材库` 可以外部获取
- `人物画像化` 最终仍然要自己做

---

## 3. 这次调研最重要的发现

## 3.1 没有找到“现成全量科学家画像数据库”

目前能找到的资料，要么是：

- 人物生平数据库
- 奖项与成就数据库
- 历史影响力排名
- 某些学科的专门传记库

但没有发现一个成熟公共资源同时满足：

- 只收科学家
- 可筛已故人物
- 覆盖多学科
- 有足够详细的传记资料
- 直接给出结构化人格 / 工作风格画像

所以后续最合理的结构不是“找现成数据库导入”，而是：

- **用多个资料源拼出一个自己的锚点池**

---

## 3.2 可以分成三类资料源

本轮调研后，外部资料最适合分成三层：

### A 层：人物真实性与生平事实来源

回答：

- 这个人是谁
- 做了什么
- 生卒年
- 研究领域
- 代表贡献

这是建立人物池的第一层。

### B 层：影响力 / 知名度 / 候选优先级来源

回答：

- 这个人是否足够有代表性
- 是否值得优先进入画像候选池
- 是否具备较高公众识别度

这是建立“先选谁”的第二层。

### C 层：群体人格与创造力研究来源

回答：

- 科学创造者整体更可能具备哪些性格特征
- 这些心理学变量与科学创造有什么关系

这是做“人物画像化”的参考框架，但**不是单个人物的直接证据**。

## 3.3 更实用的理解：发现层和验证层要分开

如果目标不是只挑十几位名人，而是希望从“历史上已故科学家的大池子”里系统筛选，那么更实用的结构其实是两层：

### 发现层（discovery layer）

回答：

- 能不能先把候选人尽可能拉全
- 哪些人值得先看
- 哪些人物在多学科、多时代下仍然有识别度

这一层可以接受：

- 覆盖很广但不一定是最终证据的资源
- 榜单、索引、百科、开放知识图谱

### 验证层（validation layer）

回答：

- 这个人的基本事实是否可靠
- 他的研究风格、工作路径、气质线索是否有可引文本
- 是否足够支持我们写“人物锚点摘要”

这一层应优先使用：

- 官方机构传记
- 学术机构 biographical memoir
- 高质量历史科学参考工具书

结论：

- **“全量拉候选” 和 “给人物定画像” 不能用同一种来源做。**
- 前者更重覆盖，后者更重可信度。

---

## 4. A 层：最适合建立人物池的权威资料源

## 4.1 Nobel Prize 官方站

来源：

- <https://www.nobelprize.org/>

为什么重要：

- 官方权威
- 每位 laureate 都有标准化的人物页
- 生平、机构、领域、贡献描述清晰
- 对近现代科学家尤其好用

本轮看到的典型页面：

- Marie Curie Facts：
  <https://www.nobelprize.org/prizes/chemistry/1911/marie-curie/>
- Richard Feynman Facts：
  <https://www.nobelprize.org/laureate/86>

优点：

- 可靠
- 易引用
- 适合做已故科学家基本事实验证

局限：

- 只覆盖 Nobel 体系人物
- 对数学、计算机、工程史人物覆盖不足
- 不是人格画像资料库

结论：

- **适合当 A 层核心来源之一**

---

## 4.2 MacTutor History of Mathematics

来源：

- <https://mathshistory.st-andrews.ac.uk/>

为什么重要：

- 圣安德鲁斯大学长期维护
- 对数学、理论计算、部分物理史人物覆盖非常好
- 生平叙事密度高

本轮核验：

- MacTutor 由 University of St Andrews 维护
- 页面明确说明项目长期运行且获得奖项认可

优点：

- 数学家、逻辑学家、理论科学家特别强
- 很适合找“深挖型”“抽象型”人物锚点

局限：

- 数学偏强
- 不是全科学史通用数据库

结论：

- **适合补足 Nobel 不覆盖的数学 / 理论人物**

---

## 4.3 Science History Institute

来源：

- <https://www.sciencehistory.org/education/scientific-biographies/>

为什么重要：

- 对化学、材料、生命科学、生物技术、分子生物学史人物覆盖好
- 传记写法比较适合做“人物气质提炼”

本轮核验：

- 官方 Scientific Biographies 页面明确是机构自建传记项目

优点：

- 对实验科学人物尤其有价值
- 对“工作方式”和“研究生涯路径”的叙事更友好

局限：

- 学科覆盖不如全学科百科全

结论：

- **适合补足实验科学与生命科学人物池**

---

## 4.4 Royal Society 档案与历史内容

来源：

- <https://royalsociety.org/news/2023/04/science-in-the-making/>
- <https://royalsociety.org/videos/people-of-science-videos/>

为什么重要：

- 对近代科学史人物很权威
- 对手稿、历史物件、科学故事背景有加成

优点：

- 适合做更深的二次研究
- 可以补人物的研究语境和历史氛围

局限：

- 不像 Nobel 那样是统一传记索引
- 更适合深挖，不适合第一轮大规模建池

结论：

- **适合二轮补充，不适合做第一层主索引**

---

## 4.5 Profiles in Science（美国国家医学图书馆）

来源：

- <https://profiles.nlm.nih.gov/>

为什么重要：

- 这是 U.S. National Library of Medicine 的数字历史资源
- 不只是短传记，而是围绕档案材料组织的人物专题
- 对医学、生命科学、公共卫生相关人物尤其有价值

本轮核验：

- 数据页说明该项目通过档案整理、策展和数字化来呈现科学家与医学创新者的生平与工作

优点：

- 适合补“实验室工作风格”“公共角色”“职业路径”
- 对生命科学和医学类锚点很有帮助

局限：

- 覆盖面不是“所有科学家”
- 更像精选深档案人物库

结论：

- **适合作为生命科学 / 医学人物的高质量验证层来源**

---

## 4.6 National Academy of Sciences Biographical Memoirs

来源：

- <https://www.nasonline.org/publications/biographical-memoirs/>

为什么重要：

- 官方说明该系列自 1877 年起出版
- 专门记录已故 NAS 成员的生平和代表著作
- 文本通常由熟悉其工作的人撰写

本轮核验到的关键信息：

- NAS 官方页明确写明：该系列提供已故 National Academy of Sciences members 的 life histories 和 selected bibliographies
- 在线馆藏约有 1,900 篇 memoir

优点：

- 非常适合做“人物锚点摘要”的事实和风格验证
- 对 19-20 世纪美国及相关学术网络人物特别有帮助

局限：

- 只覆盖 NAS 成员
- 仍不是全量科学家数据库

结论：

- **非常适合做高可信度人物验证层**

---

## 4.7 Royal Society Fellows 历史名录 / Biographical Memoirs

来源：

- <https://catalogues.royalsociety.org/calmview/what.aspx>
- Royal Society journals catalogue 中的 Biographical Memoirs 说明

为什么重要：

- Royal Society 官方目录明确说明：提供 past Fellows and Foreign Members 的名单
- 官方文字还特别指出：该列表只包含 deceased Fellows
- 同时还可进一步接到传记性 memoir 资料

优点：

- 对英国科学传统与近代科学史人物特别强
- 很适合补足物理、化学、自然史、工程相关人物

局限：

- 结构不如“统一人物库”那样直接
- 更适合“定人后深挖”，不是最轻量的第一步列表

结论：

- **适合做英国系 / Royal Society 传统人物的验证层补充**

---

## 4.8 Complete Dictionary of Scientific Biography / Britannica 等广覆盖工具书与百科

来源：

- University of Chicago Library 对 Complete Dictionary of Scientific Biography 的介绍：
  <https://www.lib.uchicago.edu/about/news/complete-dictionary-of-scientific-biography/>
- Britannica sciences biographies：
  <https://www.britannica.com/browse/biographies/sciences>

为什么重要：

- `Complete Dictionary of Scientific Biography` 是历史科学研究里非常重要的参考工具，芝加哥大学图书馆说明其包含来自不同时代、不同国家的数学家和自然科学家 biographies，并强调其 narrative scientific biographies 会涉及 achievements and personalities
- Britannica 的 sciences biography 入口则适合做宽覆盖、快速初筛和公众识别度校准

优点：

- 适合弥补官方机构站点的学科断层
- 对古代、近代、跨时代人物特别有帮助
- Britannica 很适合快速扫广度

局限：

- `Complete Dictionary of Scientific Biography` 多通过高校图书馆 / 订阅访问
- Britannica 是百科型，不等于深度传记

结论：

- **适合做广覆盖参考层；其中 DSB 更像高质量参考工具，Britannica 更像宽口径发现层辅助**

---

## 5. B 层：最适合做“优先挑谁”的影响力来源

## 5.1 Pantheon 1.0 / Historical Popularity Index

来源：

- Nature / Scientific Data：
  <https://www.nature.com/articles/sdata201575>

为什么重要：

- 这是一个经过人工校验的全球历史人物数据集
- 提供跨语言覆盖和历史影响力指标

本轮确认到的关键信息：

- 数据集包含 manually verified biographies
- 提供 `HPI`（Historical Popularity Index）
- 适合衡量“全球可识别度”

优点：

- 很适合做“谁更适合作为主锚点”的优先级排序
- 比单纯拍脑袋选人物更稳

局限：

- 不是纯科学家数据库
- 也不提供人格画像

结论：

- **非常适合做锚点优先级排序器**

---

## 5.2 Nobel Laureates 全量索引

来源：

- <https://www.nobelprize.org/prizes/lists/all-nobel-prizes>

为什么重要：

- 对 20 世纪之后的高识别科学人物非常实用
- 适合快速建立第一批“公众高认知科学人物池”

局限：

- 天生偏 Nobel 体系
- 对数学 / 工程 / 早期科学史不够

结论：

- **适合做近现代高认知人物的第一批名单**

---

## 5.3 Asimov’s Biographical Encyclopedia / Hart / Human Accomplishment 这类榜单

本轮检索里，能看到这类资源被频繁引用，但大多不是开放、统一、可直接结构化抓取的官方在线数据库。

例如：

- Asimov’s Biographical Encyclopedia of Science and Technology
- Michael Hart《The 100》
- Human Accomplishment 对照分析（被 Pantheon 论文引用）

结论：

- 它们可以作为“辅助参考”
- 但不适合当第一优先级数据源

原因：

- 权威性与可用性不如官方传记库
- 对产品工程落地帮助有限

---

## 5.4 Wikidata Query Service / 开放知识图谱

来源：

- Wikidata SPARQL Query Service：
  <https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service>
- Scholia and scientometrics with Wikidata：
  <https://arxiv.org/abs/1703.04222>

为什么重要：

- 如果我们真的想“先全量摸一遍历史已故科学家”，开放知识图谱是很现实的 discovery 工具
- Wikidata 官方提供 query service，可按 occupation、出生/死亡时间、国籍、领域等条件先拉大池子

优点：

- 非常适合做第一步候选发现
- 可以把“已故 + 科学家 + 时代 / 国别 / 学科”的粗筛自动化
- 对后续批量构建候选池很有工程价值

局限：

- 它是开放知识图谱，不是终局事实裁判
- 人物条目质量不均
- 不适合直接拿来写最终锚点画像

结论：

- **适合做 discovery layer 的大池抓取工具，不适合单独作为验证层证据**

---

## 6. C 层：科学人格 / 创造力研究能提供什么

## 6.1 Gregory Feist 的研究线索

来源：

- Feist (1998) meta-analysis PDF：
  <https://andymatuschak.org/files/papers/Feist%20-%201998%20-%20A%20Meta-Analysis%20of%20Personality%20in%20Scientific%20and%20Artistic%20Creativity.pdf>

这条线很重要，因为它回答的是：

- 科学创造者群体通常具备什么人格倾向

这类研究能够给出的不是：

- “费曼的大五精确分数是多少”

而是：

- 在群体层面，科学创造者更常见哪些特征

这对画像设计的意义是：

- 可以用来约束我们不要乱写人物锚点

但它不能直接替代单个人物的画像证据。

结论：

- **适合做群体层理论校正，不适合直接给人物贴标签**

---

## 6.2 Nobel Strengths / banquet speech CAVE 研究

来源：

- <https://repository.upenn.edu/entities/publication/20c17a35-77fd-4673-95c4-eefef1bbcb15>

这类研究尝试从 Nobel Laureates 的公开文本中提取心理特征倾向。

这很有意思，但要注意：

- 它是文本推断
- 不是标准化人格测量
- 更适合做启发，不适合当唯一人物定性依据

结论：

- **可做辅助灵感来源，但不应单独决定人物锚点画像**

---

## 7. 关键结论：后续不能指望“找现成科学家画像库”

结合以上三层资料源，本轮最重要的现实判断是：

**后续不能把希望放在“找到一个现成网站，上面已经把所有已故科学家都做成结构化画像”。**

更现实的做法是 TopicLab 自己建立三层系统：

1. `候选人物池`
   - 先决定有哪些人值得考虑
2. `锚点画像摘要`
   - 为每个人写一个结构化“研究气质摘要”
3. `类型映射层`
   - 再把这些人物映射到画像类型

---

## 8. 推荐的数据构建策略

## 8.1 第一步：先建 60-120 人候选池

来源组合建议：

- `Discovery layer`
  - Pantheon / HPI
  - Wikidata Query Service
  - Britannica sciences biographies
- `Validation layer`
  - Nobel Prize 官方人物
  - MacTutor 数学 / 理论人物
  - Science History Institute 实验科学人物
  - Profiles in Science
  - NAS Biographical Memoirs
  - 少量 Royal Society / 学科史补充

筛选标准：

- 已故
- 公众相对可识别
- 研究风格有叙事辨识度
- 至少有 2 个以上可靠来源
- 最好能覆盖不同学科、时代、性别与研究路径

---

## 8.2 第二步：先做“画像锚点”而不是“人格定量”

不要一开始就强行给每个人打完整大五分数。

更稳的做法是先提炼：

- 研究气质
- 问题处理方式
- 组织方式
- 对外风格
- 是否偏整合 / 深挖

也就是先做：

- `结构化定性画像`

再考虑是否需要进一步量化。

---

## 8.3 第三步：主锚点和备选锚点并存

每种类型建议至少准备：

- `1 个主锚点`
- `1-2 个备选锚点`

原因：

- 单一人物太容易被贴死
- 也容易因为争议或认知偏差影响整类气质

---

## 9. 第一版候选池建议

以下不是最终定稿，而是适合进入“锚点候选池”的第一版方向。

### 9.1 跨界整合 / 宏观联结类

- Leonardo da Vinci
- Richard Feynman
- Herbert Simon
- John von Neumann
- James Clerk Maxwell
- Charles Darwin

### 9.2 深度专精 / 长期深挖类

- Marie Curie
- Barbara McClintock
- Rosalind Franklin
- Santiago Ramón y Cajal
- Paul Dirac
- Emmy Noether

### 9.3 理论抽象 / 结构发现类

- Alan Turing
- Emmy Noether
- Paul Dirac
- James Clerk Maxwell
- Claude Shannon
- Niels Bohr

### 9.4 观察-实验-耐心积累类

- Charles Darwin
- Jane Goodall
- Rosalind Franklin
- Santiago Ramón y Cajal
- Tu Youyou

### 9.5 工程 / 转化 / 系统落地类

- Qian Xuesen
- Thomas Edison
- Tim Berners-Lee（若后续继续允许在世人物则可考虑，但当前应排除）

说明：

- 这里只是“候选池方向”
- 不是说这些人已经完成了一致口径的画像建模

---

## 10. 当前最推荐的策略

如果只保留一句最实用的建议，那就是：

**先不要追求“全量所有已故科学家”，而应该先建立一个 60-120 人的高质量候选池。**

原因：

- 命名系统最终不需要 500 个锚点
- 每种类型真正能稳定承载的代表人物其实很有限
- 先做高质量池，比先做大全更重要

---

## 11. 这轮调研后我建议的下一步

最适合继续做的不是直接写满所有类型，而是按这个顺序推进：

1. 先用 discovery layer 拉出一个更宽的已故科学家候选清单
2. 定“锚点科学家候选池”的准入标准
3. 收缩成第一版 60-120 人名单
4. 给每个人写结构化画像摘要
5. 再映射到 `4+1` 类型系统

也就是说：

- **先建人物池**
- **再建类型名**
- **最后才做一一映射**

---

## 12. 本轮主要来源

- Nobel Prize 官方站：
  <https://www.nobelprize.org/>
- Marie Curie Facts：
  <https://www.nobelprize.org/prizes/chemistry/1911/marie-curie/>
- Richard Feynman Facts：
  <https://www.nobelprize.org/laureate/86>
- MacTutor History of Mathematics：
  <https://mathshistory.st-andrews.ac.uk/>
- Science History Institute Scientific Biographies：
  <https://www.sciencehistory.org/education/scientific-biographies/>
- Royal Society Science in the Making：
  <https://royalsociety.org/news/2023/04/science-in-the-making/>
- Profiles in Science：
  <https://profiles.nlm.nih.gov/>
- NAS Biographical Memoirs：
  <https://www.nasonline.org/publications/biographical-memoirs/>
- Pantheon 1.0 / Scientific Data：
  <https://www.nature.com/articles/sdata201575>
- Wikidata SPARQL Query Service：
  <https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service>
- Complete Dictionary of Scientific Biography（University of Chicago Library 介绍页）：
  <https://www.lib.uchicago.edu/about/news/complete-dictionary-of-scientific-biography/>
- Britannica sciences biographies：
  <https://www.britannica.com/browse/biographies/sciences>
- Feist (1998) meta-analysis：
  <https://andymatuschak.org/files/papers/Feist%20-%201998%20-%20A%20Meta-Analysis%20of%20Personality%20in%20Scientific%20and%20Artistic%20Creativity.pdf>
- Nobel Strengths / CAVE：
  <https://repository.upenn.edu/entities/publication/20c17a35-77fd-4673-95c4-eefef1bbcb15>

---

## 13. 当前最重要的一句话

**“科学家人物锚点”不是一个现成数据库问题，而是一个“资料源拼接 + 候选池构建 + 人物画像化”的系统设计问题。**
