# 完整画像量表、维度、Skill 与心理学依据审计

## 1. 文档目标

本文用于审计 TopicLab / Resonnet 当前“完整画像”系统中与以下内容相关的真实实现与理论依据：

1. 当前活跃使用的三套量表是什么
2. 每套量表具体测哪些维度，怎么计分
3. 完整画像链路里的 Skill 栈是怎么组织的
4. 这些量表各自的心理学依据强弱如何
5. 当前实现里有哪些结构性脱节或风险

本文只记录本轮实际核验到的内容，不把项目内未验证设想当成既成事实。

---

## 2. 一句话结论

当前完整画像的“心理测量”核心由三部分组成：

- `Mini-IPIP`：标准短版大五人格量表，心理测量依据最稳
- `AMS-GSR 28`：基于经典 `AMS` 改写的研究生/科研版，理论根基稳，但当前项目内版本属于情境改编版，仍需单独验证
- `RCSS`：项目自定义“科研认知风格量表”，有理论灵感，但在当前仓库和本轮外部核验中未见已发表的正式信效度证据

同时，当前系统存在一个关键实现差异：

- `LLM/Skill 路径` 会把量表结果写进 `profile.md`
- `前端量表页路径` 目前只把结果存进 `scales.json`
- `结构化画像页` 读的是 `profile.md`，不是 `scales.json`

这意味着：**现在“前端量表测试页”和“完整画像展示页”还不是完全打通的一条链。**

---

## 3. 当前完整画像的实际结构

### 3.1 结构化画像的数据面

当前完整画像在前端展示的结构，定义在：

- [types.ts](../../frontend/src/modules/profile-helper/types.ts)

其中与心理维度最相关的部分是：

- `cognitive_style`
- `motivation`
- `personality`
- `interpretation`

此外还包括：

- `identity`
- `capability`
- `needs`

所以完整画像并不只是“三个心理量表”，而是：

1. 基础身份
2. 能力
3. 当前需求
4. 认知风格
5. 学术动机
6. 人格
7. 综合解读

### 3.2 结构化画像的真实解析入口

结构化画像接口是：

- [profile_helper.py](../../../Resonnet/app/api/profile_helper.py)
  - `GET /profile/{session_id}/structured`

这个接口实际调用：

- [profile_parser.py](../../../Resonnet/app/services/profile_helper/profile_parser.py)

也就是说，当前画像页看到的结构化结果，本质上是从：

- `session["profile"]`
- 即磁盘上的 `profile.md`

解析出来的，而不是从 `scales.json` 动态拼出来的。

---

## 4. 三套量表的真实实现

前端量表定义在：

- [scales.ts](../../frontend/src/modules/profile-helper/data/scales.ts)

计分逻辑在：

- [scoring.ts](../../frontend/src/modules/profile-helper/utils/scoring.ts)

当前前端暴露给用户的三套量表是：

1. `RCSS`
2. `Mini-IPIP`
3. `AMS-GSR 28`

### 4.1 RCSS：科研认知风格量表

定义位置：

- [scales.ts](../../frontend/src/modules/profile-helper/data/scales.ts)
- [researcher-cognitive-style.md](../../../Resonnet/libs/profile_helper/docs/researcher-cognitive-style.md)
- [administer-rcss/SKILL.md](../../../Resonnet/libs/profile_helper/skills/administer-rcss/SKILL.md)

#### 测量维度

RCSS 当前只有 2 个维度：

- `integration`：横向整合
- `depth`：垂直深度

共 8 题：

- A1-A4：横向整合
- B1-B4：垂直深度

#### 计分方式

- 7 分制 Likert
- 每个维度 4 题求和
- `I = A1 + A2 + A3 + A4`
- `D = B1 + B2 + B3 + B4`
- `CSI = I - D`
- CSI 范围：`-24 ~ +24`

类型阈值当前写死在：

- [scoring.ts](../../frontend/src/modules/profile-helper/utils/scoring.ts)

具体区间：

- `+17 ~ +24`：强整合型
- `+8 ~ +16`：倾向整合型
- `-7 ~ +7`：平衡型
- `-16 ~ -8`：倾向深度型
- `-24 ~ -17`：强深度型

#### 心理学依据判断

RCSS 当前不是我能确认到的标准已发表量表。

项目内文档声称其理论基础来自：

- 认知风格理论
- Mode 1 / Mode 2 知识生产模式

但需要注意：

- 当前仓库内没有引用已发表的 RCSS 原始论文
- 当前仓库内没有真实样本上的验证报告
- [researcher-cognitive-style.md](../../../Resonnet/libs/profile_helper/docs/researcher-cognitive-style.md) 自己就把“信效度说明”标成了 `草案`

所以更准确的表述是：

- `RCSS 是项目自建量表`
- `有概念框架，但当前未见成熟心理测量学验证证据`

#### 结论

RCSS 适合被当作：

- `研究型画像维度`
- `内部产品化工具`

不适合当前阶段被表述为：

- `已经完成正式心理测量学验证的标准量表`

---

### 4.2 Mini-IPIP：大五人格量表

定义位置：

- [scales.ts](../../frontend/src/modules/profile-helper/data/scales.ts)
- [mini-ipip-scale.md](../../../Resonnet/libs/profile_helper/docs/mini-ipip-scale.md)
- [administer-mini-ipip/SKILL.md](../../../Resonnet/libs/profile_helper/skills/administer-mini-ipip/SKILL.md)

#### 测量维度

Mini-IPIP 当前测 5 个维度：

- `E`：外向性 Extraversion
- `A`：宜人性 Agreeableness
- `C`：尽责性 Conscientiousness
- `N`：神经质 Neuroticism
- `I`：开放性/智力 Intellect/Imagination

共 20 题，每维度 4 题。

#### 计分方式

- 5 分制
- 11 个反向题
- 反向计分公式：`6 - 原始分`
- 每维度取 4 题平均分

反向题当前写在：

- [scales.ts](../../frontend/src/modules/profile-helper/data/scales.ts)

评分逻辑在：

- [scoring.ts](../../frontend/src/modules/profile-helper/utils/scoring.ts)

人格高低分段用于展示，写在：

- [PersonalitySection.tsx](../../frontend/src/modules/profile-helper/components/profile/PersonalitySection.tsx)

#### 心理学依据判断

Mini-IPIP 是当前三套里依据最稳的一套。

项目内引用的原始来源是：

- Donnellan, Oswald, Baird, & Lucas (2006)

本轮外部核验到的权威来源包括：

- PubMed 条目：<https://pubmed.ncbi.nlm.nih.gov/16768595/>
- IPIP 权限页：<https://ipip.ori.org/newPermission.htm>

可以确认的事实：

- Mini-IPIP 是标准短版 Big Five 工具
- 它基于公共领域的 IPIP 题库
- IPIP 官方明确说明材料已进入 public domain，可用于商业或非商业用途

因此，当前项目里：

- `理论基础强`
- `题目来源清晰`
- `版权边界相对清楚`

#### 结论

如果要保留一套最“正”的标准人格测量，Mini-IPIP 是当前系统里最可靠的一套。

---

### 4.3 AMS-GSR 28：学术动机量表（研究生/科研版）

定义位置：

- [scales.ts](../../frontend/src/modules/profile-helper/data/scales.ts)
- [academic-motivation-scale.md](../../../Resonnet/libs/profile_helper/docs/academic-motivation-scale.md)
- [administer-ams/SKILL.md](../../../Resonnet/libs/profile_helper/skills/administer-ams/SKILL.md)

#### 测量维度

AMS-GSR 28 当前测 7 个维度：

- `know`：求知内在动机
- `accomplishment`：成就内在动机
- `stimulation`：体验刺激内在动机
- `identified`：认同调节
- `introjected`：内摄调节
- `external`：外部调节
- `amotivation`：无动机

共 28 题，每维度 4 题。

#### 计分方式

- 7 分制
- 全部正向计分
- 每个维度取 4 题平均分

综合指标：

- `intrinsic_total = know + accomplishment + stimulation`
- `extrinsic_total = identified + introjected + external`
- `RAI = 3×know + 3×accomplishment + 3×stimulation + 2×identified - introjected - 2×external - 3×amotivation`

前端实现位于：

- [scoring.ts](../../frontend/src/modules/profile-helper/utils/scoring.ts)

前端展示说明位于：

- [MotivationSection.tsx](../../frontend/src/modules/profile-helper/components/profile/MotivationSection.tsx)

#### 心理学依据判断

AMS 的理论根是明确的：

- 自我决定理论（Self-Determination Theory, SDT）
- 其中尤其对应外在动机内化连续谱

本轮核验到的外部来源包括：

- SAGE 原始条目：<https://journals.sagepub.com/doi/10.1177/0013164492052004025>
- SDT 官方理论页：<https://selfdeterminationtheory.org/the-theory/>

SAGE 页面可确认：

- 原始 AMS 是 28 题
- 它区分 3 类内在动机、3 类外在动机和无动机

但当前项目里真正使用的不是原始 AMS-C 28，而是：

- `AMS-GSR 28`
- 即为研究生/科研场景改写后的版本

这个改写版在项目文档中已经明确写了：

- 它是 `adapted version`
- 使用前应重新做内容效度、CFA、内部一致性与效标验证

这意味着：

- `原始 AMS 的理论基础是稳的`
- `当前项目正在使用的 AMS-GSR 28 是场景改编版`
- `改编版本身的心理测量学证据，在当前仓库中尚未完成闭环`

#### 版权与使用边界

需要注意，SDT 官方问卷页面写得很明确：

- <https://www.selfdeterminationtheory.org/questionnaires>

它说明：

- 站内问卷为 copyrighted
- academic use 通常允许
- commercial use 需要获取 permission

所以相较于 IPIP：

- AMS 这条线的版权边界更敏感
- AMS-GSR 28 作为改编版，后续如果对外商用，需要再单独过法务与授权判断

#### 结论

AMS-GSR 28 适合作为：

- `有明确理论根基的研究型动机结构工具`

但不宜当前就表述为：

- `已经完成正式验证的研究生科研专用标准量表`

---

## 5. 额外存在但未进入当前“三量表主流程”的量表

仓库中还存在：

- [multidimensional-work-motivation-scale.md](../../../Resonnet/libs/profile_helper/docs/multidimensional-work-motivation-scale.md)

对应的是：

- `MWMS 19`

原始来源可在 SDT 官方站核验：

- 论文 PDF：<https://selfdeterminationtheory.org/wp-content/uploads/2014/04/2015_GagneForestEtAl_MultidimensionalWork.pdf>
- 问卷页：<https://selfdeterminationtheory.org/wp-content/uploads/2022/02/MWMS_Complete.pdf>

但从当前前端三量表定义来看：

- `MWMS 不在现行用户量表页`
- 它更像是项目里的参考理论文档，而不是当前主施测量表

这说明项目的动机建模在概念上参考了：

- 教育场景的 AMS
- 工作场景的 MWMS

但当前落地主流程仍然是：

- `AMS-GSR 28`

---

## 6. 完整画像 Skill 栈

Skill 装载入口在：

- [tools.py](../../../Resonnet/app/services/profile_helper/tools.py)

系统提示词路由在：

- [prompts.py](../../../Resonnet/app/services/profile_helper/prompts.py)

项目内实际可读到的主 Skill 包括：

1. `collect-basic-info`
2. `administer-ams`
3. `administer-rcss`
4. `administer-mini-ipip`
5. `infer-profile-dimensions`
6. `review-profile`
7. `update-profile`
8. `generate-forum-profile`
9. `generate-ai-memory-prompt`
10. `import-ai-memory`
11. `modify-profile-schema`

从完整画像主流程看，最核心的是前 7 个。

### 6.1 主流程 Skill

主流程由 [implementation-guide.md](../../../Resonnet/libs/profile_helper/docs/implementation-guide.md) 说明得比较清楚：

1. `collect-basic-info`
   - 采基础身份、能力、需求
2. 分叉：
   - `infer-profile-dimensions`
   - 或三套量表施测 `administer-ams / administer-rcss / administer-mini-ipip`
3. `review-profile`
   - 审核展示
4. `update-profile`
   - 后续修改

### 6.2 推断路径 Skill

`infer-profile-dimensions` 很重要，因为它体现了系统对“量表”和“推断”的关系定位：

- 量表是优先的标准测量
- AI 推断是快速估算
- 推断结果必须标注 `AI推断`

它会尝试估算：

- RCSS
- AMS 全 7 维
- Mini-IPIP 全 5 维

所以从产品定位上，当前系统不是“只有实测画像”，而是：

- `量表实测 + AI推断` 混合体系

---

## 7. 当前评分标准与解释逻辑

### 7.1 RCSS

来源：

- [scoring.ts](../../frontend/src/modules/profile-helper/utils/scoring.ts)

规则：

- 两个维度先求和
- 再用差值 `CSI = I - D`
- 再按固定阈值判定 5 类风格

这个标准是项目自己定义的展示型阈值，不是我在本轮核验里确认到的外部常模。

### 7.2 Mini-IPIP

来源：

- [scoring.ts](../../frontend/src/modules/profile-helper/utils/scoring.ts)
- [PersonalitySection.tsx](../../frontend/src/modules/profile-helper/components/profile/PersonalitySection.tsx)

规则：

- 先做反向计分
- 再求 5 维平均
- 展示层按区间映射为：
  - 极高
  - 偏高
  - 中等
  - 偏低
  - 极低

注意：

- 这些“高/中/低”标签是当前产品展示逻辑
- 不是正式常模百分位解释

### 7.3 AMS-GSR 28

来源：

- [scoring.ts](../../frontend/src/modules/profile-helper/utils/scoring.ts)
- [MotivationSection.tsx](../../frontend/src/modules/profile-helper/components/profile/MotivationSection.tsx)

规则：

- 7 个子维度各自取均分
- 再计算 `intrinsic_total / extrinsic_total / RAI`

RAI 本质上是一个加权综合指标，用来表达：

- 越高：越自主
- 越低：越受控或越接近无动机

需要注意：

- 当前前端展示里没有常模百分位
- 主要是结构解释，不是标准诊断

---

## 8. 一个关键实现发现：量表页与画像页没有完全打通

这次代码核验里最关键的工程发现是：

### 8.1 前端量表页怎么存

量表页在：

- [ScaleTestPage.tsx](../../frontend/src/modules/profile-helper/pages/ScaleTestPage.tsx)

它提交到：

- [profileHelperApi.ts](../../frontend/src/modules/profile-helper/profileHelperApi.ts)
  - `POST /profile-helper/scales/submit`

后端接收在：

- [profile_helper.py](../../../Resonnet/app/api/profile_helper.py)

然后保存逻辑是：

- [sessions.py](../../../Resonnet/app/services/profile_helper/sessions.py)
  - `save_scales()`

这个函数只做了两件事：

- 写进 `session["scales"]`
- 持久化为 `scales.json`

### 8.2 画像页怎么读

结构化画像页走的是：

- `GET /profile/{session_id}/structured`

它只解析：

- `session["profile"]`
- 即 `profile.md`

而不是读取 `scales.json`

### 8.3 这意味着什么

这意味着现在存在两条并行链：

1. `Skill / LLM 对话施测链`
   - 量表结果写进 `profile.md`
   - 画像页能直接读到

2. `前端量表测试页链`
   - 量表结果写进 `scales.json`
   - 画像页默认读不到

所以从工程角度，当前最准确的判断是：

- `量表测试功能已经存在`
- `完整画像展示功能已经存在`
- `但两者还没有在所有路径上彻底合并成一个统一事实源`

这是后续必须优先处理的架构问题之一。

---

## 9. 心理学依据强弱分级

结合本轮代码核验与外部来源核验，可以把当前系统里的三套量表粗略分成三档：

### 9.1 强依据

- `Mini-IPIP`

原因：

- 标准短版 Big Five
- 原始文献清晰
- IPIP 公共领域可用性清晰
- 当前项目中题目与结构基本沿用了标准形式

### 9.2 中等依据

- `AMS-GSR 28`

原因：

- 原始 AMS 理论基础明确
- SDT / OIT 理论根清楚
- 但当前项目使用的是研究生/科研场景改编版
- 改编版尚未在仓库中看到完成的独立验证报告

### 9.3 弱依据 / 内部工具

- `RCSS`

原因：

- 是当前项目自建量表
- 有理论灵感，但未见成熟发表或正式验证
- 当前更适合作为画像型内部工具，而非标准心理量表

---

## 10. 产品与研究上的建议

### 10.1 对外表述要分层

如果后续对外写文案，建议严格区分：

- `标准短量表`：Mini-IPIP
- `理论改编量表`：AMS-GSR 28
- `项目自建画像维度工具`：RCSS

不要把三者都说成同一种“标准心理测量”。

### 10.2 先统一事实源

当前最需要的不是再加新量表，而是统一：

- `profile.md`
- `scales.json`
- 结构化画像接口

否则用户会出现：

- “我明明测过了，为什么画像页没变”

### 10.3 RCSS 需要重新命名定位

如果 RCSS 继续使用，建议在产品层的默认说法更接近：

- `科研认知风格画像`
- `研究策略偏好测量`

而不是直接把它包装成已成熟标准量表。

### 10.4 AMS-GSR 28 需要补验证

如果未来要更严肃地对外使用 AMS-GSR 28，至少需要：

1. 内容效度审阅
2. 探索/验证性因素分析
3. 内部一致性检验
4. 与科研满意度、坚持度、产出等变量的效标关系验证

这些要求其实项目内文档已经自己写出来了，只是还没有看到闭环证据。

---

## 11. 本轮核验使用的主要来源

### 11.1 项目内实现

- [scales.ts](../../frontend/src/modules/profile-helper/data/scales.ts)
- [scoring.ts](../../frontend/src/modules/profile-helper/utils/scoring.ts)
- [ScaleTestPage.tsx](../../frontend/src/modules/profile-helper/pages/ScaleTestPage.tsx)
- [types.ts](../../frontend/src/modules/profile-helper/types.ts)
- [profile_parser.py](../../../Resonnet/app/services/profile_helper/profile_parser.py)
- [profile_helper.py](../../../Resonnet/app/api/profile_helper.py)
- [sessions.py](../../../Resonnet/app/services/profile_helper/sessions.py)
- [tools.py](../../../Resonnet/app/services/profile_helper/tools.py)
- [prompts.py](../../../Resonnet/app/services/profile_helper/prompts.py)
- [implementation-guide.md](../../../Resonnet/libs/profile_helper/docs/implementation-guide.md)
- [researcher-cognitive-style.md](../../../Resonnet/libs/profile_helper/docs/researcher-cognitive-style.md)
- [academic-motivation-scale.md](../../../Resonnet/libs/profile_helper/docs/academic-motivation-scale.md)
- [mini-ipip-scale.md](../../../Resonnet/libs/profile_helper/docs/mini-ipip-scale.md)
- [multidimensional-work-motivation-scale.md](../../../Resonnet/libs/profile_helper/docs/multidimensional-work-motivation-scale.md)

### 11.2 外部核验来源

- Mini-IPIP PubMed：<https://pubmed.ncbi.nlm.nih.gov/16768595/>
- IPIP 权限说明：<https://ipip.ori.org/newPermission.htm>
- AMS 原始论文页：<https://journals.sagepub.com/doi/10.1177/0013164492052004025>
- SDT 理论页：<https://selfdeterminationtheory.org/the-theory/>
- SDT 问卷版权说明：<https://www.selfdeterminationtheory.org/questionnaires>
- MWMS 原始论文 PDF：<https://selfdeterminationtheory.org/wp-content/uploads/2014/04/2015_GagneForestEtAl_MultidimensionalWork.pdf>
- MWMS 官方问卷页：<https://selfdeterminationtheory.org/wp-content/uploads/2022/02/MWMS_Complete.pdf>

---

## 12. 当前最重要的结论

如果只保留一句最关键的话，那就是：

**当前完整画像并不是“三个都同等成熟的标准心理量表系统”，而是“一个标准人格量表 + 一个理论改编动机量表 + 一个项目自建认知画像量表”组成的混合系统。**

而且从工程上看，这三套量表在“前端量表页”和“画像主文档”之间还没有完全统一成一个数据闭环。
