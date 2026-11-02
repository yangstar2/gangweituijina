const { api } = require('../../utils/api')

Page({
  data: {
    sessionId: null,
    messages: [],
    input: '',
    suggestedReplies: [],
    clarifyingDone: false,
    scrollInto: '',
    sending: false,
  },

  onLoad(query) {
    const sessionId = Number(query.sessionId)
    this.setData({ sessionId })
    this._loadMessages()
  },

  _loadMessages() {
    api.getMessages(this.data.sessionId).then((msgs) => {
      const last = msgs[msgs.length - 1]
      this.setData({
        messages: msgs,
        scrollInto: last ? `msg-${last.id}` : '',
      })
    })
  },

  onInput(e) {
    this.setData({ input: e.detail.value })
  },

  onSuggest(e) {
    this.setData({ input: e.currentTarget.dataset.text }, () => this.onSend())
  },

  onSend() {
    const content = (this.data.input || '').trim()
    if (!content || this.data.sending) return
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
        })
      })
      .catch((err) => {
        this.setData({ sending: false })
        wx.showToast({ title: (err && err.detail) || '发送失败', icon: 'none' })
      })
  },

  goOutline() {
    wx.navigateTo({
      url: `/pages/outline/outline?sessionId=${this.data.sessionId}`,
    })
  },
})
