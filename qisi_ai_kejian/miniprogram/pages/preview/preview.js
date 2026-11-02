const { api } = require('../../utils/api')

Page({
  data: {
    sessionId: null,
    preview: {
      style_id: '',
      model_id: '',
      pages: [],
    },
    current: 0,
    isExam: false,
  },

  onLoad(query) {
    const sessionId = Number(query.sessionId)
    const draft = getApp().globalData.draft
    this.setData({
      sessionId,
      preview: draft.preview || { style_id: '', model_id: '', pages: [] },
      isExam: draft.contentType === 'exam',
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

  onGenerate() {
    const draft = getApp().globalData.draft
    wx.showLoading({ title: '生成中…' })
    api
      .generate(this.data.sessionId, draft.styleId, draft.modelId)
      .then((artifact) => {
        draft.artifact = artifact
        wx.hideLoading()
        const page =
          artifact.artifact_type === 'exam'
            ? '/pages/result-exam/result-exam'
            : '/pages/result-ppt/result-ppt'
        wx.navigateTo({ url: `${page}?artifactId=${artifact.id}` })
      })
      .catch((err) => {
        wx.hideLoading()
        const d = err && err.detail
        const msg =
          (d && typeof d === 'object' && (d.message || d.msg)) ||
          (typeof d === 'string' ? d : null) ||
          (err && err.message) ||
          '生成失败'
        const code = d && typeof d === 'object' ? d.code : null
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
          return
        }
        wx.showToast({ title: String(msg), icon: 'none' })
      })
  },
})
