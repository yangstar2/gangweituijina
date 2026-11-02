const { api, getBase } = require('../../utils/api')

Page({
  data: {
    artifact: null,
    outlineSummary: null,
    downloadUrl: '',
    downloadBusy: false,
  },

  onLoad(query) {
    const id = Number(query.artifactId)
    const draft = getApp().globalData.draft || {}
    if (draft.artifact && draft.artifact.id === id) {
      this._applyArtifact(draft.artifact)
      return
    }
    api.getArtifact(id).then((a) => this._applyArtifact(a))
  },

  _applyArtifact(artifact) {
    const content = (artifact && artifact.content) || {}
    const outline =
      content.outline_summary ||
      (getApp().globalData.draft && getApp().globalData.draft.outline) ||
      null
    const downloadUrl =
      artifact.download_url ||
      content.download_url ||
      (artifact.id ? `/api/artifacts/${artifact.id}/download` : '')
    this.setData({
      artifact,
      outlineSummary: outline,
      downloadUrl,
    })
  },

  _fullDownloadUrl() {
    const rel = this.data.downloadUrl || ''
    if (!rel) return ''
    if (/^https?:\/\//i.test(rel)) return rel
    return `${getBase()}${rel}`
  },

  onDownload() {
    if (this.data.downloadBusy) return
    const url = this._fullDownloadUrl()
    if (!url) {
      wx.showToast({ title: '暂无下载地址', icon: 'none' })
      return
    }
    this.setData({ downloadBusy: true })
    wx.showLoading({ title: '下载中…', mask: true })

    wx.downloadFile({
      url,
      success: (res) => {
        wx.hideLoading()
        this.setData({ downloadBusy: false })
        if (res.statusCode >= 200 && res.statusCode < 300 && res.tempFilePath) {
          wx.openDocument({
            filePath: res.tempFilePath,
            fileType: 'pptx',
            showMenu: true,
            fail: () => {
              wx.setClipboardData({
                data: url,
                success: () =>
                  wx.showToast({ title: '链接已复制，可在浏览器打开', icon: 'none' }),
              })
            },
          })
        } else {
          this._copyLinkFallback(url)
        }
      },
      fail: () => {
        wx.hideLoading()
        this.setData({ downloadBusy: false })
        this._copyLinkFallback(url)
      },
    })
  },

  _copyLinkFallback(url) {
    wx.setClipboardData({
      data: url,
      success: () =>
        wx.showModal({
          title: '下载链接',
          content: '已复制下载链接，可在系统浏览器中打开保存 .pptx',
          showCancel: false,
        }),
    })
  },

  copyLink() {
    const url = this._fullDownloadUrl()
    if (!url) return
    wx.setClipboardData({
      data: url,
      success: () => wx.showToast({ title: '已复制链接', icon: 'success' }),
    })
  },

  goHome() {
    wx.reLaunch({ url: '/pages/index/index' })
  },
})
