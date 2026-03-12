import { useState, useEffect } from 'react'
import { TopicExpert, topicExpertsApi } from '../api/client'
import { authApi, DigitalTwinRecord, tokenManager } from '../api/auth'
import { handleApiError, handleApiSuccess } from '../utils/errorHandler'
import ExpertSelector from './ExpertSelector'

interface ExpertManagementProps {
  topicId: string
  onExpertsChange?: () => void
  fillHeight?: boolean
}

const inputClass = 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-serif focus:border-black focus:outline-none'
const labelClass = 'block text-sm font-serif font-medium text-black mb-2'

export default function ExpertManagement({ topicId, onExpertsChange, fillHeight = false }: ExpertManagementProps) {
  const [experts, setExperts] = useState<TopicExpert[]>([])
  const [loading, setLoading] = useState(true)
  const [expertListRefreshTrigger, setExpertListRefreshTrigger] = useState(0)
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [selectedExpert, setSelectedExpert] = useState<TopicExpert | null>(null)
  const [editContent, setEditContent] = useState('')
  const [digitalTwins, setDigitalTwins] = useState<DigitalTwinRecord[]>([])
  const [loadingTwins, setLoadingTwins] = useState(false)
  const [selectedTwinName, setSelectedTwinName] = useState('')
  const [importingTwin, setImportingTwin] = useState(false)

  const [customName, setCustomName] = useState('')
  const [customLabel, setCustomLabel] = useState('')
  const [customDescription, setCustomDescription] = useState('')
  const [customContent, setCustomContent] = useState('')
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    loadExperts()
  }, [topicId])

  const loadExperts = async () => {
    try {
      const res = await topicExpertsApi.list(topicId)
      setExperts(res.data)
    } catch (err) {
      handleApiError(err, '加载角色列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAddPreset = async (name: string) => {
    await topicExpertsApi.add(topicId, { source: 'preset', preset_name: name })
    await loadExperts()
    onExpertsChange?.()
    handleApiSuccess('角色添加成功')
  }

  const handleRemove = async (name: string) => {
    await topicExpertsApi.delete(topicId, name)
    await loadExperts()
    onExpertsChange?.()
    handleApiSuccess('角色删除成功')
  }

  const handleEdit = async (expert: TopicExpert) => {
    setSelectedExpert(expert)
    setEditContent('')
    setShowEditDialog(true)
    try {
      const res = await topicExpertsApi.getContent(topicId, expert.name)
      setEditContent(res.data.role_content)
    } catch (err) {
      handleApiError(err, '加载角色内容失败')
    }
  }

  const handleSaveEdit = async () => {
    if (!selectedExpert || !editContent) return
    try {
      await topicExpertsApi.update(topicId, selectedExpert.name, { role_content: editContent })
      setShowEditDialog(false)
      setSelectedExpert(null)
      setEditContent('')
      await loadExperts()
      onExpertsChange?.()
      handleApiSuccess('角色更新成功')
    } catch (err: any) {
      handleApiError(err, '更新失败')
    }
  }

  const handleShare = async (expert: TopicExpert) => {
    if (!confirm(`将「${expert.label}」分享到平台预设库？所有用户均可添加此角色。`)) return
    try {
      await topicExpertsApi.share(topicId, expert.name)
      await loadExperts()
      setExpertListRefreshTrigger((v) => v + 1)
      handleApiSuccess(`「${expert.label}」已共享到平台`)
    } catch (err: any) {
      handleApiError(err, '分享失败')
    }
  }

  const handleAddCustom = async () => {
    if (!customName || !customLabel || !customDescription || !customContent) {
      alert('请先生成角色信息或填写所有字段')
      return
    }
    try {
      await topicExpertsApi.add(topicId, {
        source: 'custom',
        name: customName,
        label: customLabel,
        description: customDescription,
        role_content: customContent,
      })
      setShowAddDialog(false)
      setCustomName(''); setCustomLabel(''); setCustomDescription(''); setCustomContent('')
      await loadExperts()
      onExpertsChange?.()
      handleApiSuccess('自定义角色创建成功')
    } catch (err: any) {
      handleApiError(err, '创建角色失败')
    }
  }

  const sanitizeExpertName = (input: string): string => {
    const normalized = input
      .trim()
      .toLowerCase()
      .replace(/[^\w]+/g, '_')
      .replace(/^_+|_+$/g, '')
    return normalized || `digital_twin_${Date.now().toString(36)}`
  }

  const buildMaskedRoleContent = (displayName: string, description: string) => {
    return [
      `# ${displayName}`,
      '',
      '> 此角色来源于私密数字分身，内容已脱敏。',
      '',
      '## 可公开信息',
      '',
      description ? `- 简介：${description}` : '- 简介：未提供',
      '',
      '## 使用说明',
      '',
      '- 可参与话题讨论，但不暴露原始私密分身全文。',
    ].join('\n')
  }

  const openImportDialog = async () => {
    const token = tokenManager.get()
    if (!token) {
      handleApiError(new Error('未登录'), '请先登录后再导入数字分身')
      return
    }
    setShowImportDialog(true)
    setLoadingTwins(true)
    try {
      const res = await authApi.getDigitalTwins(token)
      setDigitalTwins(res.digital_twins || [])
      setSelectedTwinName((res.digital_twins?.[0]?.agent_name ?? ''))
    } catch (err) {
      handleApiError(err, '加载数字分身失败')
    } finally {
      setLoadingTwins(false)
    }
  }

  const handleImportTwin = async () => {
    const token = tokenManager.get()
    if (!token || !selectedTwinName) return
    setImportingTwin(true)
    try {
      const detailRes = await authApi.getDigitalTwinDetail(token, selectedTwinName)
      const twin = detailRes.digital_twin
      const displayName = twin.display_name || twin.expert_name || twin.agent_name || '我的数字分身'
      const expertName = sanitizeExpertName(twin.expert_name || twin.agent_name || displayName)
      const isPrivate = twin.visibility === 'private'
      const roleContent = isPrivate
        ? buildMaskedRoleContent(displayName, `来自私密分身「${displayName}」`)
        : (twin.role_content || buildMaskedRoleContent(displayName, '导入时未提供详情'))

      await topicExpertsApi.add(topicId, {
        source: 'custom',
        name: expertName,
        label: displayName,
        description: isPrivate ? '来自私密数字分身（已脱敏）' : '来自数字分身导入',
        role_content: roleContent,
        origin_type: 'digital_twin',
        origin_visibility: twin.visibility || 'private',
        masked: isPrivate,
      })
      setShowImportDialog(false)
      await loadExperts()
      onExpertsChange?.()
      handleApiSuccess(isPrivate ? '私密分身已脱敏导入' : '数字分身导入成功')
    } catch (err) {
      handleApiError(err, '导入数字分身失败')
    } finally {
      setImportingTwin(false)
    }
  }

  const handleGenerateExpert = async () => {
    if (!customLabel.trim()) { handleApiError({ message: '请输入角色标签' }, '请输入角色标签'); return }
    if (!customDescription.trim()) { handleApiError({ message: '请输入角色简介' }, '请输入角色简介'); return }
    if (!customDescription.trim()) { handleApiError({ message: '请输入角色简介' }, '请输入角色简介'); return }

    setGenerating(true)
    try {
      const res = await topicExpertsApi.generate(topicId, {
        expert_name: customName.trim() || undefined,
        expert_label: customLabel.trim(),
        description: customDescription.trim(),
      })
      if (res.data.expert_name && !customName) setCustomName(res.data.expert_name)
      setCustomContent(res.data.role_content)
      handleApiSuccess('AI 生成成功！请检查并编辑信息')
    } catch (err: any) {
      handleApiError(err, 'AI 生成失败')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <p className="text-gray-500 text-sm">加载中...</p>

  return (
    <div className={fillHeight ? 'h-full flex flex-col min-h-0 overflow-hidden' : 'space-y-4'}>
      <p className="text-xs text-gray-500 mb-2 flex-shrink-0">
        点击 + 将角色加入话题，选中的角色会参与讨论。也可创建新角色。
      </p>
      <div className="flex gap-2 flex-shrink-0 mb-2">
        <button
          onClick={() => setShowAddDialog(true)}
          className="bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-4 py-1.5 rounded-lg text-sm font-medium transition-colors"
        >
          创建新角色
        </button>
        <button
          onClick={openImportDialog}
          className="bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-4 py-1.5 rounded-lg text-sm font-medium transition-colors"
        >
          导入我的数字分身
        </button>
      </div>
      <div className={fillHeight ? 'flex-1 min-h-0 overflow-hidden' : ''}>
        <ExpertSelector
          value={experts.map((e) => e.name)}
          selectedExperts={experts.map((e) => ({
            name: e.name,
            label: e.label,
            source: e.source,
            masked: e.masked,
            origin_visibility: e.origin_visibility,
          }))}
          onChange={() => {}}
          onAdd={handleAddPreset}
          onRemove={handleRemove}
          onEdit={(name) => {
            const e = experts.find((x) => x.name === name)
            if (e) handleEdit(e)
          }}
          onShare={(name) => {
            const e = experts.find((x) => x.name === name)
            if (e) handleShare(e)
          }}
          fillHeight={fillHeight}
          refreshTrigger={expertListRefreshTrigger}
        />
      </div>

      {showAddDialog && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setShowAddDialog(false)}
        >
          <div
            className="bg-white p-6 max-w-lg w-[90%] max-h-[80vh] overflow-auto border border-gray-200 rounded-lg"
            onClick={e => e.stopPropagation()}
          >
            <h3 className="font-serif font-semibold text-black mb-6">创建新角色</h3>

            <div className="mb-4">
              <label className={labelClass}>角色标签（中文）*</label>
              <input className={inputClass} placeholder="例如：经济学家" value={customLabel} onChange={e => setCustomLabel(e.target.value)} />
            </div>
            <div className="mb-4">
              <label className={labelClass}>角色简介*</label>
              <input className={inputClass} placeholder="例如：专注于 AI 对经济的影响" value={customDescription} onChange={e => setCustomDescription(e.target.value)} />
            </div>

            <div className="mb-4">
              <button
                onClick={handleGenerateExpert}
                className="w-full bg-black text-white px-4 py-2 text-sm font-serif hover:bg-gray-900 transition-colors disabled:opacity-50"
                disabled={generating || !customLabel || !customDescription}
              >
                {generating ? 'AI 生成中...' : 'AI 自动生成完整信息'}
              </button>
            </div>

            <div className="mb-4">
              <label className={labelClass}>角色名称（英文）</label>
              <input className={inputClass} placeholder="AI 自动生成，也可手动输入" value={customName} onChange={e => setCustomName(e.target.value)} />
            </div>
            <div className="mb-4">
              <label className={labelClass}>角色定义（Markdown）</label>
              <textarea
                className={`${inputClass} min-h-[200px] font-mono resize-y`}
                placeholder="AI 自动生成，也可手动输入..."
                value={customContent}
                onChange={e => setCustomContent(e.target.value)}
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleAddCustom}
                className="bg-black text-white px-4 py-2 text-sm font-serif hover:bg-gray-900 transition-colors disabled:opacity-50"
                disabled={!customName || !customLabel || !customDescription || !customContent}
              >
                创建角色
              </button>
              <button onClick={() => setShowAddDialog(false)} className="border border-gray-200 rounded-lg px-4 py-2 text-sm font-serif text-black hover:border-black transition-colors">取消</button>
            </div>
          </div>
        </div>
      )}

      {showImportDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowImportDialog(false)}>
          <div className="bg-white p-6 max-w-lg w-[90%] border border-gray-200 rounded-lg" onClick={e => e.stopPropagation()}>
            <h3 className="font-serif font-semibold text-black mb-2">导入我的数字分身</h3>
            <p className="text-xs text-gray-500 mb-4">私密分身会自动脱敏后导入，其他用户无法获取原始内容。</p>
            {loadingTwins ? (
              <p className="text-sm text-gray-500">加载中...</p>
            ) : digitalTwins.length === 0 ? (
              <p className="text-sm text-gray-500">暂无可导入分身</p>
            ) : (
              <div className="space-y-2 max-h-72 overflow-auto border border-gray-100 rounded-lg p-2 mb-4">
                {digitalTwins.map((twin) => (
                  <label key={twin.agent_name} className="flex items-start gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer">
                    <input
                      type="radio"
                      name="selectedTwin"
                      className="mt-1"
                      checked={selectedTwinName === twin.agent_name}
                      onChange={() => setSelectedTwinName(twin.agent_name)}
                    />
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-black truncate">
                        {twin.display_name || twin.expert_name || twin.agent_name}
                      </div>
                      <div className="text-xs text-gray-500">
                        可见性：{twin.visibility === 'private' ? '私密（将脱敏导入）' : '公开'}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <button
                onClick={handleImportTwin}
                disabled={importingTwin || loadingTwins || !selectedTwinName}
                className="bg-black text-white px-4 py-2 text-sm font-serif hover:bg-gray-900 transition-colors disabled:opacity-50"
              >
                {importingTwin ? '导入中...' : '确认导入'}
              </button>
              <button
                onClick={() => setShowImportDialog(false)}
                className="border border-gray-200 rounded-lg px-4 py-2 text-sm font-serif text-black hover:border-black transition-colors"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {showEditDialog && selectedExpert && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setShowEditDialog(false)}
        >
          <div
            className="bg-white p-6 max-w-xl w-[90%] max-h-[80vh] overflow-auto border border-gray-200 rounded-lg"
            onClick={e => e.stopPropagation()}
          >
            <h3 className="font-serif font-semibold text-black mb-4">编辑角色：{selectedExpert.label}</h3>
            {selectedExpert.masked && (
              <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2 mb-3">
                此角色来源于私密数字分身，当前展示内容已脱敏。
              </p>
            )}

            <label className={labelClass}>角色定义（Markdown）</label>
            <textarea
              className={`${inputClass} min-h-[300px] font-mono resize-y mb-4`}
              value={editContent}
              onChange={e => setEditContent(e.target.value)}
              placeholder="在此输入新的角色定义..."
            />

            <div className="flex gap-2">
              <button onClick={handleSaveEdit} className="bg-black text-white px-4 py-2 text-sm font-serif hover:bg-gray-900 transition-colors">保存</button>
              <button onClick={() => setShowEditDialog(false)} className="border border-gray-200 rounded-lg px-4 py-2 text-sm font-serif text-black hover:border-black transition-colors">取消</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
