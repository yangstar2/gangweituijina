const { api } = require('../../utils/api')

const BASE_STEPS = [
  { id: 'need', title: '理解需求', detail: '对齐主题、对象与课时' },
  { id: 'reason', title: '深度推理', detail: '模型展开思考链' },
  { id: 'outline', title: '结构化大纲', detail: '要点 / 章节 / 注意事项' },
  { id: 'generate', title: '生成 PPT', detail: '调用课件生成工具' },
]

function pagesFromOutline(outline, styleId, modelId) {
  const ol = outline || {}
  const keyPoints = ol.key_points || []
  const sections = ol.outline || []
  const notes = ol.notes || []
  const pages = [
    {
      page_no: 1,
      title: '封面 · 课件预览',
      bullets: [
        `风格：${styleId || 'clean_academic'}`,
        `模型：${modelId || 'mock-qisi-lite'}`,
        '生成中将据此写出完整 PPTX',
      ],
      speaker_note: '开场',
    },
    {
      page_no: 2,
      title: '内容要点',
      bullets: keyPoints.length ? keyPoints.slice(0, 6) : ['（待补充要点）'],
      speaker_note: null,
    },
  ]
  sections.slice(0, 3).forEach((sec, i) => {
    pages.push({
      page_no: 3 + i,
      title: (sec && sec.section) || `章节 ${i + 1}`,
      bullets: (sec && sec.items) || ['要点'],
      speaker_note: null,
    })
  })
  while (pages.length < 5) {
    pages.push({
      page_no: pages.length + 1,
      title: `扩展页 ${pages.length + 1}`,
      bullets: ['根据大纲自动补齐'],
      speaker_note: null,
    })
  }
  pages.push({
    page_no: 6,
    title: '注意事项与收尾',
    bullets: notes.slice(0, 4).length ? notes.slice(0, 4) : ['检查符号与难度', '留足互动时间'],
    speaker_note: null,
  })
  return pages.slice(0, 6).map((p, i) => ({ ...p, page_no: i + 1 }))
}

function pagesFromSlides(slides) {
  return (slides || []).slice(0, 6).map((s, i) => ({
    page_no: i + 1,
    title: s.title || `第 ${i + 1} 页`,
    bullets: s.bullets || [],
    speaker_note: s.speaker_note || null,
    subtitle: s.subtitle || null,
  }))
}

Page({
  data: {
    sessionId: null,
    phase: 'boot', // boot | thinking | typing | ready | generating | done | error
    phaseTitle: '准备开始',
    phaseSub: '将调用推理模型梳理课件结构',
    providerLabel: 'DeepSeek',
    uiSteps: BASE_STEPS.map((s, i) => ({
      ...s,
      status: i === 0 ? 'active' : 'pending',
      detail: s.detail,
    })),
    thinkingOpen: true,
    fullThinking: '',
    displayedThinking: '',
    thinkingPreview: '等待推理…',
    scrollAnchor: '',
    outline: { key_points: [], outline: [], notes: [] },
    outlineReady: false,
    previewPages: [],
    previewCurrent: 0,
    showSlidePreview: false,
    artifactId: null,
    errorMsg: '',
    autoGenerate: true,
  },

  onLoad(query) {
    const sessionId = Number(query.sessionId)
    const autoGenerate = query.autoGenerate !== '0'
    this.setData({ sessionId, autoGenerate })
    this._runThink()
  },

  onUnload() {
    this._clearTypewriter()
  },

  toggleThinking() {
    this.setData({ thinkingOpen: !this.data.thinkingOpen })
  },

  onPreviewChange(e) {
    this.setData({ previewCurrent: e.detail.current })
  },

  _setStepStatus(activeId, doneIds) {
    const done = new Set(doneIds || [])
    const uiSteps = BASE_STEPS.map((s) => {
      let status = 'pending'
      if (done.has(s.id)) status = 'done'
      if (s.id === activeId) status = 'active'
      return { ...s, status, detail: s.detail }
    })
    this.setData({ uiSteps })
  },

  _applyServerSteps(steps) {
    if (!steps || !steps.length) return
    const uiSteps = this.data.uiSteps.map((s, i) => {
      const remote = steps[i]
      if (!remote) return s
      return {
        ...s,
        detail: remote.detail || s.detail,
        title: i === 1 ? remote.title || s.title : s.title,
      }
    })
    this.setData({ uiSteps })
  },

  _clearTypewriter() {
    if (this._typeTimer) {
      clearInterval(this._typeTimer)
      this._typeTimer = null
    }
  },

  _typeThinking(text, onDone) {
    this._clearTypewriter()
    const full = text || ''
    let i = 0
    const chunk = Math.max(2, Math.ceil(full.length / 80))
    this.setData({
      phase: 'typing',
      fullThinking: full,
      displayedThinking: '',
      thinkingPreview: full.slice(0, 48) + (full.length > 48 ? '…' : ''),
      scrollAnchor: '',
    })
    this._typeTimer = setInterval(() => {
      i = Math.min(full.length, i + chunk)
      this.setData({
        displayedThinking: full.slice(0, i),
        scrollAnchor: 'think-end',
      })
      if (i >= full.length) {
        this._clearTypewriter()
        if (onDone) onDone()
      }
    }, 32)
  },

  _loadPreview(outline) {
    const draft = getApp().globalData.draft || {}
    const styleId = draft.styleId || 'clean_academic'
    const modelId = draft.modelId || 'mock-qisi-lite'
    // Instant local preview from outline so UI is never blank while generating
    const local = pagesFromOutline(outline, styleId, modelId)
    this.setData({
      previewPages: local,
      showSlidePreview: true,
      previewCurrent: 0,
    })
    draft.preview = {
      style_id: styleId,
      model_id: modelId,
      pages: local,
    }
    // Prefer server ~6-page preview when available
    return api
      .createPreview(this.data.sessionId, styleId, modelId)
      .then((preview) => {
        const pages = (preview && preview.pages) || local
        draft.preview = preview
        this.setData({
          previewPages: pages,
          showSlidePreview: true,
        })
        return pages
      })
      .catch(() => local)
  },

  _runThink() {
    const draft = getApp().globalData.draft || {}
    this.setData({
      phase: 'thinking',
      phaseTitle: 'AI 正在思考',
      phaseSub: '推理课件结构，稍后生成 PPT',
      errorMsg: '',
      outlineReady: false,
      showSlidePreview: false,
      previewPages: [],
    })
    this._setStepStatus('reason', ['need'])

    api
      .pptThink(this.data.sessionId, {
        style_id: draft.styleId || 'clean_academic',
        model_id: draft.modelId || 'mock-qisi-lite',
        title: draft.title || null,
        auto_generate: false,
      })
      .then((res) => {
        draft.outline = res.outline
        draft.thinking = {
          provider: res.provider,
          model: res.model,
          text: res.thinking,
          steps: res.thinking_steps,
        }
        const label =
          res.provider === 'deepseek'
            ? `DeepSeek · ${res.model}`
            : `Mock 推理${res.deepseek_configured ? '' : '（未配置密钥）'}`
        this.setData({
          providerLabel: label,
          outline: res.outline,
        })
        this._applyServerSteps(res.thinking_steps)
        this._setStepStatus('outline', ['need', 'reason'])
        this._typeThinking(res.thinking || '', () => {
          this.setData({
            outlineReady: true,
            phase: 'ready',
            phaseTitle: '大纲已就绪',
            phaseSub: this.data.autoGenerate
              ? 'teacher-prep 大纲就绪，预览后生成 PPTX'
              : '可先滑动预览，再生成 PPT',
          })
          this._setStepStatus('generate', ['need', 'reason', 'outline'])
          this._loadPreview(res.outline).then(() => {
            if (this.data.autoGenerate) {
              setTimeout(() => this.onGenerate(), 450)
            }
          })
        })
      })
      .catch((err) => {
        const d = err && err.detail
        const msg =
          (d && typeof d === 'object' && (d.message || d.msg)) ||
          (typeof d === 'string' ? d : null) ||
          (err && err.message) ||
          '思考失败'
        this.setData({
          phase: 'error',
          phaseTitle: '思考中断',
          phaseSub: '可重试或先查看已有大纲',
          errorMsg: String(msg),
        })
      })
  },

  retry() {
    this._runThink()
  },

  goOutline() {
    wx.navigateTo({
      url: `/pages/outline/outline?sessionId=${this.data.sessionId}`,
    })
  },

  goResult() {
    if (!this.data.artifactId) return
    wx.redirectTo({
      url: `/pages/result-ppt/result-ppt?artifactId=${this.data.artifactId}`,
    })
  },

  onGenerate() {
    if (this.data.phase === 'generating') return
    const draft = getApp().globalData.draft || {}
    // Ensure preview is visible during file build
    if (!this.data.showSlidePreview || !this.data.previewPages.length) {
      this._loadPreview(this.data.outline || draft.outline)
    }
    this.setData({
      phase: 'generating',
      phaseTitle: '正在生成 PPT',
      phaseSub: 'teacher-prep-skill 驱动内容；下方可预览并写出 .pptx',
      errorMsg: '',
      thinkingOpen: false,
      showSlidePreview: true,
    })
    this._setStepStatus('generate', ['need', 'reason', 'outline'])

    api
      .generate(
        this.data.sessionId,
        draft.styleId || 'clean_academic',
        draft.modelId || 'mock-qisi-lite'
      )
      .then((artifact) => {
        draft.artifact = artifact
        const slides = (artifact.content || {}).slides || []
        const fromArtifact = pagesFromSlides(slides)
        if (fromArtifact.length) {
          this.setData({ previewPages: fromArtifact, showSlidePreview: true })
          draft.preview = {
            style_id: artifact.style_id,
            model_id: artifact.model_id,
            pages: fromArtifact,
          }
        }
        this.setData({
          phase: 'done',
          phaseTitle: 'PPT 已生成',
          phaseSub: `共 ${((artifact.content || {}).slide_count) || '-'} 页，可下载或继续预览`,
          artifactId: artifact.id,
        })
        this._setStepStatus(null, ['need', 'reason', 'outline', 'generate'])
      })
      .catch((err) => {
        const d = err && err.detail
        const msg =
          (d && typeof d === 'object' && (d.message || d.msg)) ||
          (typeof d === 'string' ? d : null) ||
          (err && err.message) ||
          '生成失败'
        const code = d && typeof d === 'object' ? d.code : null
        this.setData({
          phase: 'ready',
          phaseTitle: '大纲已就绪',
          phaseSub: '生成未完成，可重试',
          errorMsg: String(msg),
        })
        if (code === 'membership_required' || String(msg).indexOf('会员') >= 0) {
          wx.showModal({
            title: '需要会员',
            content: String(msg),
            confirmText: '去开通',
            success(res) {
              if (res.confirm) {
                wx.navigateTo({ url: '/pages/membership/membership' })
              }
            },
          })
        }
      })
  },
})
