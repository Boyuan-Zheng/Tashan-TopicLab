import type { ScaleDefinition } from '../data/scales'

export function calculateScores(
  scale: ScaleDefinition,
  answers: Record<string, number>
): Record<string, number> {
  const scores: Record<string, number> = {}

  for (const dimension of scale.dimensions) {
    const values = dimension.questionIds
      .map((id) => answers[id])
      .filter((v): v is number => typeof v === 'number')
    const sum = values.reduce((acc, v) => acc + v, 0)
    scores[dimension.id] = values.length ? sum / values.length : 0
  }

  return scores
}

export function calculateRCSS(scores: Record<string, number>) {
  const I = Number((scores.integration ?? 0).toFixed(2))
  const D = Number((scores.depth ?? 0).toFixed(2))
  const CSI = Number((I - D).toFixed(2))
  const type = CSI >= 0 ? '整合偏好型' : '深挖偏好型'
  return { I, D, CSI, type }
}

export function calculateAMSRAI(scores: Record<string, number>) {
  const intrinsicTotal = Number((scores.intrinsic ?? 0).toFixed(2))
  const extrinsicTotal = Number((scores.extrinsic ?? 0).toFixed(2))
  const RAI = Number((intrinsicTotal - extrinsicTotal).toFixed(2))
  return { intrinsicTotal, extrinsicTotal, RAI }
}
