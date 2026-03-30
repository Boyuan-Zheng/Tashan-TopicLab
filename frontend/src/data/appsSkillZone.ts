export interface ResearchSkillDiscipline {
  key: string
  name: string
  summary: string
}

export interface ResearchSkillCluster {
  key: string
  title: string
  summary: string
}

export const RESEARCH_SKILL_DISCIPLINES: ResearchSkillDiscipline[] = [
  { key: '01', name: '哲学', summary: '问题定义、方法反思与概念辨析。' },
  { key: '02', name: '经济学', summary: '政策、博弈、产业与量化分析。' },
  { key: '03', name: '法学', summary: '法规条文、案例研究与制度比较。' },
  { key: '04', name: '教育学', summary: '教学设计、学习分析与评估反馈。' },
  { key: '05', name: '文学', summary: '文本细读、语义分析与写作辅助。' },
  { key: '06', name: '历史学', summary: '史料梳理、脉络追踪与叙事校对。' },
  { key: '07', name: '理学', summary: '理论推导、数据分析与实验解释。' },
  { key: 'ast', name: '天文学', summary: '观测资料、星表与天体研究辅助。' },
  { key: '08', name: '工学', summary: '工程实现、系统设计与实验优化。' },
  { key: '09', name: '农学', summary: '农业数据、育种、生态与田间研究。' },
  { key: '10', name: '医学', summary: '临床、影像、生信与医学研究支持。' },
  { key: '11', name: '军事学', summary: '战略推演、情报研判与体系分析。' },
  { key: '12', name: '管理学', summary: '组织、运营、决策与管理评估。' },
  { key: '13', name: '艺术学', summary: '风格研究、策展叙事与创作辅助。' },
]

export const RESEARCH_SKILL_CLUSTERS: ResearchSkillCluster[] = [
  { key: 'bio', title: '生物与生命科学', summary: '覆盖单细胞、多组学、基因组学、蛋白质组学等研究型技能。' },
  { key: 'pharma', title: '药物研发', summary: '围绕分子对接、化学信息学、药理分析与药物设计展开。' },
  { key: 'med', title: '医学与临床', summary: '适合临床研究、医学影像、精准医疗与疾病分析。' },
  { key: 'labos', title: '实验室自动化', summary: '实验协议、机器人控制、LabOS 与实验流程编排。' },
  { key: 'vision', title: '视觉与 XR', summary: '图像分割、姿态估计、手势追踪与空间感知能力。' },
  { key: 'general', title: '数据科学', summary: '统计学、机器学习、数据清洗、可视化与模型分析。' },
  { key: 'literature', title: '文献检索', summary: '学术搜索、数据库访问、文献筛选与知识整理。' },
]
