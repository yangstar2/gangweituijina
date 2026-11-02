const { api } = require('../../utils/api')

Page({
  data: {
    sessionId: null,
    styles: [],
    selectedId: 'clean_academic',
  },

  onLoad(query) {
    const sessionId = Number(query.sessionId)
    const draft = getApp().globalData.draft
    this.setData({
      sessionId,
      selectedId: draft.styleId || 'clean_academic',
    })
    api.listStyles().then((styles) => this.setData({ styles }))
  },

  onSelect(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ selectedId: id })
    getApp().globalData.draft.styleId = id
  },

  goModel() {
    getApp().globalData.draft.styleId = this.data.selectedId
    wx.navigateTo({
      url: `/pages/model-select/model-select?sessionId=${this.data.sessionId}`,
    })
  },
})
