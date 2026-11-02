const { api } = require('../../utils/api')

Page({
  startCourseware() {
    this._start('courseware')
  },

  startExam() {
    this._start('exam')
  },

  goMembership() {
    wx.navigateTo({ url: '/pages/membership/membership' })
  },


  _start(contentType) {
    wx.showLoading({ title: '创建会话…' })
    api
      .createSession(contentType)
      .then((session) => {
        const app = getApp()
        app.globalData.draft = {
          sessionId: session.id,
          contentType,
          outline: null,
          styleId: 'clean_academic',
          modelId: 'mock-qisi-lite',
          preview: null,
          artifact: null,
        }
        wx.hideLoading()
        wx.navigateTo({ url: `/pages/chat/chat?sessionId=${session.id}` })
      })
      .catch((err) => {
        wx.hideLoading()
        wx.showToast({
          title: (err && err.detail) || '后端未启动',
          icon: 'none',
        })
      })
  },
})
