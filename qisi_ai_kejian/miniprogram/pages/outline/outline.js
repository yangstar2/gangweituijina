const { api } = require('../../utils/api')

Page({
  data: {
    sessionId: null,
    outline: {
      key_points: [],
      outline: [],
      notes: [],
    },
  },

  onLoad(query) {
    const sessionId = Number(query.sessionId)
    this.setData({ sessionId })
    const draft = getApp().globalData.draft
    if (draft.outline && draft.sessionId === sessionId) {
      this.setData({ outline: draft.outline })
      return
    }
    api
      .getOutline(sessionId)
      .then((ol) => {
        getApp().globalData.draft.outline = ol
        this.setData({ outline: ol })
      })
      .catch(() => {
        wx.showToast({ title: '大纲尚未生成', icon: 'none' })
      })
  },

  backChat() {
    wx.navigateBack()
  },

  goStyle() {
    wx.navigateTo({
      url: `/pages/style-filter/style-filter?sessionId=${this.data.sessionId}`,
    })
  },
})
