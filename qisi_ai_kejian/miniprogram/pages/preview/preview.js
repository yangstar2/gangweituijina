Page({
  data: {
    sessionId: null,
    preview: {
      style_id: '',
      model_id: '',
      pages: [],
    },
    current: 0,
  },

  onLoad(query) {
    const sessionId = Number(query.sessionId)
    const draft = getApp().globalData.draft
    this.setData({
      sessionId,
      preview: draft.preview || { style_id: '', model_id: '', pages: [] },
    })
  },

  onChange(e) {
    this.setData({ current: e.detail.current })
  },

  reStyle() {
    wx.navigateTo({
      url: `/pages/style-filter/style-filter?sessionId=${this.data.sessionId}`,
    })
  },

  reModel() {
    wx.navigateTo({
      url: `/pages/model-select/model-select?sessionId=${this.data.sessionId}`,
    })
  },
})
