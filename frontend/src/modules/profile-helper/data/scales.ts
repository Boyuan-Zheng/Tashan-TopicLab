export interface ScaleDimension {
  id: string
  name: string
  questionIds: string[]
}

export interface ScaleQuestion {
  id: string
  text: string
  dimensionId: string
}

export interface ScaleDefinition {
  id: string
  name: string
  description: string
  instructions: string
  minVal: number
  maxVal: number
  minLabel: string
  maxLabel: string
  dimensions: ScaleDimension[]
  questions: ScaleQuestion[]
}

export const ALL_SCALES: ScaleDefinition[] = [
  {
    id: 'rcss',
    name: '科研认知风格量表（RCSS）',
    description: '评估横向整合与垂直深度倾向，辅助形成科研认知风格画像。',
    instructions: '请根据你的真实习惯打分：1 表示非常不符合，5 表示非常符合。',
    minVal: 1,
    maxVal: 5,
    minLabel: '非常不符合',
    maxLabel: '非常符合',
    dimensions: [
      { id: 'integration', name: '横向整合', questionIds: ['rcss_1', 'rcss_3', 'rcss_5'] },
      { id: 'depth', name: '垂直深度', questionIds: ['rcss_2', 'rcss_4', 'rcss_6'] },
    ],
    questions: [
      { id: 'rcss_1', text: '我会主动把不同学科的方法组合到同一个课题中。', dimensionId: 'integration' },
      { id: 'rcss_2', text: '我倾向在单一方向持续深挖，直到形成体系。', dimensionId: 'depth' },
      { id: 'rcss_3', text: '遇到问题时，我会先建立跨领域关联图谱。', dimensionId: 'integration' },
      { id: 'rcss_4', text: '我更喜欢把一个核心问题拆解到足够细的层级。', dimensionId: 'depth' },
      { id: 'rcss_5', text: '我经常关注邻近领域的新工具并尝试迁移应用。', dimensionId: 'integration' },
      { id: 'rcss_6', text: '我对理论细节和边界条件会投入大量时间核验。', dimensionId: 'depth' },
    ],
  },
  {
    id: 'ams',
    name: '学术动机量表（AMS）',
    description: '测量内在动机与外在动机倾向，帮助校对数字分身动机维度。',
    instructions: '请根据最近半年状态作答：1 表示非常不同意，5 表示非常同意。',
    minVal: 1,
    maxVal: 5,
    minLabel: '非常不同意',
    maxLabel: '非常同意',
    dimensions: [
      { id: 'intrinsic', name: '内在动机', questionIds: ['ams_1', 'ams_3', 'ams_5'] },
      { id: 'extrinsic', name: '外在动机', questionIds: ['ams_2', 'ams_4', 'ams_6'] },
    ],
    questions: [
      { id: 'ams_1', text: '我做科研主要因为对问题本身好奇。', dimensionId: 'intrinsic' },
      { id: 'ams_2', text: '论文发表数量是我持续投入的重要驱动力。', dimensionId: 'extrinsic' },
      { id: 'ams_3', text: '即使没有明确回报，我也愿意继续探索有价值的问题。', dimensionId: 'intrinsic' },
      { id: 'ams_4', text: '职称、项目与资源获取会显著影响我的投入强度。', dimensionId: 'extrinsic' },
      { id: 'ams_5', text: '我享受从混乱信息中构建清晰解释的过程。', dimensionId: 'intrinsic' },
      { id: 'ams_6', text: '外部评价对我是否继续推进课题有很大影响。', dimensionId: 'extrinsic' },
    ],
  },
]

export function getScaleById(scaleId: string): ScaleDefinition | undefined {
  return ALL_SCALES.find((scale) => scale.id === scaleId)
}
