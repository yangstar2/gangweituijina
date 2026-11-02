const { api } = require('../../utils/api')

Page({
  data: {
    sessionId: null,
    models: [],
    selectedId: 'mock-qisi-lite',
  },

  onLoad(query) {
    const sessionId = Number(query.sessionId)
    const draft = getApp().globalData.draft
    this.setData({
      sessionId,
      selectedId: draft.modelId || 'mock-qisi-lite',
    })
    api.listModels().then((models) => this.setData({ models }))
  },

  onSelect(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ selectedId: id })
    getApp().globalData.draft.modelId = id
  },

  goPreview() {
    const app = getApp()
    const draft = app.globalData.draft
    draft.modelId = this.data.selectedId
    wx.showLoading({ title: '生成预览…' })
    api
      .createPreview(this.data.sessionId, draft.styleId, draft.modelId)
      .then((preview) => {
        draft.preview = preview
        wx.hideLoading()
        wx.navigateTo({
          url: `/pages/preview/preview?sessionId=${this.data.sessionId}`,
        })
      })
      .catch((err) => {
        wx.hideLoading()
        wx.showToast({ title: (err && err.detail) || '预览失败', icon: 'none' })
      })
  },
})
