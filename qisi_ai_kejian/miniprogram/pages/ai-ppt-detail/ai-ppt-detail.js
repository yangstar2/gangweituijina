const { api } = require('../../utils/api')

const THEME_STARTERS = [
  '人工智能与未来教育',
  '安全生产培训课件',
  '新员工入职培训',
]

const MOCK_DOCS = [
  {
    name: '安全生产培训大纲.pdf',
    content:
      '[文档] 安全生产培训大纲：覆盖隐患排查、应急演练、个人防护与事故案例复盘，面向一线班组，建议 45 分钟课件。',
  },
  {
    name: '新员工入职手册.docx',
    content:
      '[文档] 新员工入职手册摘要：公司文化、组织架构、制度流程、岗位职责与试用期目标，适合入职首日培训 PPT。',
  },
  {
    name: 'AI教育专题讲稿.txt',
    content:
      '[文档] 人工智能与未来教育讲稿：教育场景中的大模型应用、教师角色变化、课堂互动设计与伦理边界。',
  },
]

Page({
  data: {
    mode: 'theme',
    sessionId: null,
    messages: [],
    input: '',
    sending: false,
    starting: false,
    clarifyingDone: false,
    suggestedReplies: [],
    displayChips: THEME_STARTERS,
    scrollInto: '',
    pasteText: '',
    pasteLen: 0,
    uploadName: '',
    uploadContent: '',
    canStart: false,
  },

  onLoad() {
    this._ensureThemeSession()
  },

  onSelectMode(e) {
    const mode = e.currentTarget.dataset.mode
    if (!mode || mode === this.data.mode) return
    this.setData({ mode }, () => {
      this._refreshCanStart()
      this._refreshChips()
      if (mode === 'theme' && !this.data.sessionId) {
        this._ensureThemeSession()
      }
    })
  },

  _refreshChips() {
    const { mode, suggestedReplies } = this.data
    if (mode !== 'theme') return
    this.setData({
      displayChips: suggestedReplies.length ? suggestedReplies : THEME_STARTERS,
    })
  },

  _refreshCanStart() {
    const { mode, clarifyingDone, pasteText, uploadContent, starting } = this.data
    let canStart = false
    if (mode === 'theme') canStart = !!clarifyingDone
    else if (mode === 'paste') canStart = !!(pasteText || '').trim()
    else if (mode === 'upload') canStart = !!uploadContent
    if (starting) canStart = false
    this.setData({ canStart })
  },

  _ensureThemeSession() {
    if (this._sessionPromise) return this._sessionPromise
    wx.showLoading({ title: '准备对话…', mask: true })
    this._sessionPromise = api
      .createSession('courseware', 'AI PPT 主题澄清')
      .then((session) => {
        const app = getApp()
        app.globalData.draft = {
          sessionId: session.id,
          contentType: 'courseware',
          outline: null,
          styleId: 'clean_academic',
          modelId: 'mock-qisi-lite',
          preview: null,
          artifact: null,
          sourceMode: 'theme',
        }
        this.setData({ sessionId: session.id })
        return api.getMessages(session.id).then((msgs) => {
          const last = msgs[msgs.length - 1]
          this.setData({
            messages: msgs,
            scrollInto: last ? `msg-${last.id}` : '',
            clarifyingDone: false,
            suggestedReplies: [],
            displayChips: THEME_STARTERS,
          })
          this._refreshCanStart()
          wx.hideLoading()
        })
      })
      .catch((err) => {
        this._sessionPromise = null
        wx.hideLoading()
        wx.showToast({
          title: (err && err.detail) || '后端未启动',
          icon: 'none',
        })
      })
    return this._sessionPromise
  },

  onInput(e) {
    this.setData({ input: e.detail.value })
  },

  onPasteInput(e) {
    const pasteText = e.detail.value || ''
    this.setData({ pasteText, pasteLen: pasteText.length }, () => this._refreshCanStart())
  },

  onSuggest(e) {
    const text = e.currentTarget.dataset.text
    if (!text) return
    this.setData({ input: text }, () => this.onSend())
  },

  onSend() {
    const content = (this.data.input || '').trim()
    if (!content || this.data.sending || this.data.mode !== 'theme') return

    const run = () => {
      this.setData({ sending: true, input: '' })
      api
        .sendMessage(this.data.sessionId, content)
        .then((reply) => {
          const app = getApp()
          if (reply.outline) {
            app.globalData.draft.outline = reply.outline
          }
          return api.getMessages(this.data.sessionId).then((msgs) => {
            const last = msgs[msgs.length - 1]
            this.setData({
              messages: msgs,
              clarifyingDone: !!reply.teacher.clarifying_done,
              suggestedReplies: reply.teacher.suggested_replies || [],
              scrollInto: last ? `msg-${last.id}` : '',
              sending: false,
            })
            this._refreshChips()
            this._refreshCanStart()
          })
        })
        .catch((err) => {
          this.setData({ sending: false })
          wx.showToast({
            title: (err && err.detail) || '发送失败',
            icon: 'none',
          })
        })
    }

    if (!this.data.sessionId) {
      this._ensureThemeSession().then(() => {
        if (this.data.sessionId) run()
      })
      return
    }
    run()
  },

  onPickDoc() {
    wx.showActionSheet({
      itemList: MOCK_DOCS.map((d) => d.name),
      success: (res) => {
        const doc = MOCK_DOCS[res.tapIndex]
        if (!doc) return
        this.setData(
          {
            uploadName: doc.name,
            uploadContent: doc.content,
          },
          () => this._refreshCanStart()
        )
      },
    })
  },

  onStartCreate() {
    if (!this.data.canStart || this.data.starting) {
      if (this.data.mode === 'theme' && !this.data.clarifyingDone) {
        wx.showToast({ title: '先和 AI 对齐目标再创作', icon: 'none' })
      } else if (this.data.mode === 'paste') {
        wx.showToast({ title: '请先粘贴文本', icon: 'none' })
      } else if (this.data.mode === 'upload') {
        wx.showToast({ title: '请先选择文档', icon: 'none' })
      }
      return
    }

    if (this.data.mode === 'theme') {
      this._goOutline(this.data.sessionId)
      return
    }

    if (this.data.mode === 'paste') {
      this._startFromMaterial((this.data.pasteText || '').trim(), 'paste')
      return
    }

    this._startFromMaterial(this.data.uploadContent, 'upload')
  },

  _startFromMaterial(rawText, sourceMode) {
    const text = (rawText || '').trim()
    if (!text) return
    this.setData({ starting: true, canStart: false })
    wx.showLoading({ title: '整理大纲…', mask: true })

    api
      .createSession('courseware', sourceMode === 'upload' ? '文档转PPT' : '文本转PPT')
      .then((session) => {
        const app = getApp()
        app.globalData.draft = {
          sessionId: session.id,
          contentType: 'courseware',
          outline: null,
          styleId: 'clean_academic',
          modelId: 'mock-qisi-lite',
          preview: null,
          artifact: null,
          sourceMode,
        }
        // Prefix helps mock_ai one-shot outline for long material
        const payload =
          sourceMode === 'upload'
            ? text
            : text.startsWith('[粘贴]')
              ? text
              : `[粘贴]\n${text}`
        return api.sendMessage(session.id, payload).then((reply) => {
          if (reply.outline) {
            app.globalData.draft.outline = reply.outline
          }
          // If mock still wants more turns, nudge once with a confirm
          if (!reply.teacher.clarifying_done) {
            return api
              .sendMessage(session.id, '按上述材料直接生成课件大纲，对象为培训学员，约45分钟。')
              .then((r2) => {
                if (r2.outline) app.globalData.draft.outline = r2.outline
                if (!r2.teacher.clarifying_done) {
                  return api
                    .sendMessage(session.id, '确认：突出核心要点与案例，难度适中。')
                    .then((r3) => {
                      if (r3.outline) app.globalData.draft.outline = r3.outline
                      return session.id
                    })
                }
                return session.id
              })
          }
          return session.id
        })
      })
      .then((sessionId) => {
        wx.hideLoading()
        this.setData({ starting: false })
        this._refreshCanStart()
        this._goOutline(sessionId)
      })
      .catch((err) => {
        wx.hideLoading()
        this.setData({ starting: false })
        this._refreshCanStart()
        wx.showToast({
          title: (err && err.detail) || '创作失败',
          icon: 'none',
        })
      })
  },

  _goOutline(sessionId) {
    if (!sessionId) {
      wx.showToast({ title: '会话无效', icon: 'none' })
      return
    }
    wx.navigateTo({
      url: `/pages/outline/outline?sessionId=${sessionId}`,
    })
  },
})
