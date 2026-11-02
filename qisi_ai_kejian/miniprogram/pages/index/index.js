const { api } = require('../../utils/api')

Page({
  /** AI生成PPT → 详情页（主题对话 / 粘贴 / 上传） */
  startCourseware() {
    wx.navigateTo({ url: '/pages/ai-ppt-detail/ai-ppt-detail' })
  },

  /** AI生成试卷 → existing exam ask-teacher flow */
  startExam() {
    this._start('exam')
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
