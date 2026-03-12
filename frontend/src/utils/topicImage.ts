import { Topic, TopicListItem } from '../api/client'

function stripAngleBrackets(value: string): string {
  const trimmed = value.trim()
  if (trimmed.startsWith('<') && trimmed.endsWith('>')) {
    return trimmed.slice(1, -1).trim()
  }
  return trimmed
}

export function extractFirstMarkdownImage(markdown?: string): string {
  if (!markdown) return ''
  const imagePattern = /!\[[^\]]*]\(([^)\s]+(?:\s+"[^"]*")?)\)/g
  const match = imagePattern.exec(markdown)
  if (!match) return ''
  const raw = match[1].trim()
  const pathOnly = raw.includes('"') ? raw.split('"')[0].trim() : raw
  return stripAngleBrackets(pathOnly)
}

export function resolveTopicImageSrc(topicId: string, src?: string): string {
  if (!src) return ''
  if (/^https?:\/\//.test(src) || src.startsWith('data:')) return src

  const baseUrl = import.meta.env.BASE_URL || '/'
  const normalizedBase = baseUrl === '/' ? '' : baseUrl.replace(/\/$/, '')
  const generatedImagesRelativePattern = /^(?:\.\.\/|\.\/)?generated_images\//

  if (src.startsWith('/api/')) {
    return `${normalizedBase}${src}`
  }

  if (src.startsWith('shared/generated_images/')) {
    const relativePath = src.replace(/^shared\/generated_images\//, '')
    return `${normalizedBase}/api/topics/${topicId}/assets/generated_images/${relativePath}`
  }

  if (generatedImagesRelativePattern.test(src)) {
    const relativePath = src.replace(generatedImagesRelativePattern, '')
    return `${normalizedBase}/api/topics/${topicId}/assets/generated_images/${relativePath}`
  }

  return src
}

export function getTopicPreviewImageSrc(topic: Topic | TopicListItem): string {
  const lightweightPreview = resolveTopicImageSrc(topic.id, topic.preview_image ?? '')
  if (lightweightPreview) return lightweightPreview

  const bodyImage = extractFirstMarkdownImage(topic.body)
  if (bodyImage) return resolveTopicImageSrc(topic.id, bodyImage)

  const summaryImage = extractFirstMarkdownImage((topic as Topic).discussion_result?.discussion_summary)
  if (summaryImage) return resolveTopicImageSrc(topic.id, summaryImage)

  const historyImage = extractFirstMarkdownImage((topic as Topic).discussion_result?.discussion_history)
  if (historyImage) return resolveTopicImageSrc(topic.id, historyImage)

  return ''
}
