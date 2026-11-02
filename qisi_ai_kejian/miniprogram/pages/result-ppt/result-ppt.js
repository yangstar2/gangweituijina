const { api } = require('../../utils/api')

Page({
  data: { artifact: null },

  onLoad(query) {
    const id = Number(query.artifactId)
    const draft = getApp().globalData.draft
    if (draft.artifact && draft.artifact.id === id) {
      this.setData({ artifact: draft.artifact })
      return
    }
    api.getArtifact(id).then((a) => this.setData({ artifact: a }))
  },

  goHome() {
    wx.reLaunch({ url: '/pages/index/index' })
  },
})
