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

  _localPptxPath(artifact) {
    const id = (artifact && artifact.id) || 'ppt'
    // Force .pptx under USER_DATA_PATH — WeChat temp paths often lack an
    // extension, so openDocument/Keynote treat the file as corrupt.
    const root = (wx.env && wx.env.USER_DATA_PATH) || ''
    if (!root) return ''
    return `${root}/artifact_${id}.pptx`
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

    const filePath = this._localPptxPath(this.data.artifact)
    const req = {
      url,
      success: (res) => {
        wx.hideLoading()
        this.setData({ downloadBusy: false })
        const ok =
          res.statusCode >= 200 &&
          res.statusCode < 300 &&
          (res.filePath || res.tempFilePath)
        if (!ok) {
          this._copyLinkFallback(url)
          return
        }
        const path = res.filePath || res.tempFilePath
        // Guard: tiny bodies are almost always HTML/JSON error pages saved as pptx
        const fs = wx.getFileSystemManager && wx.getFileSystemManager()
        const openIt = () => {
          wx.openDocument({
            filePath: path,
            fileType: 'pptx',
            showMenu: true,
            fail: () => this._copyLinkFallback(url),
          })
        }
        if (fs && fs.getFileInfo) {
          fs.getFileInfo({
            filePath: path,
            success: (info) => {
              if (!info || !info.size || info.size < 1000) {
                wx.showToast({ title: '文件异常，已复制链接', icon: 'none' })
                this._copyLinkFallback(url)
                return
              }
              openIt()
            },
            fail: openIt,
          })
        } else {
          openIt()
        }
      },
      fail: () => {
        wx.hideLoading()
        this.setData({ downloadBusy: false })
        this._copyLinkFallback(url)
      },
    }
    if (filePath) req.filePath = filePath

    wx.downloadFile(req)
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
