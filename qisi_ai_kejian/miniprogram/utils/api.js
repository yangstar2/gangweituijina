function getBase() {
  const app = getApp()
  return (app && app.globalData && app.globalData.apiBase) || 'http://127.0.0.1:8000'
}

function request(path, method, data) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${getBase()}${path}`,
      method: method || 'GET',
      data: data || {},
      header: { 'Content-Type': 'application/json' },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          reject(res.data || { detail: `HTTP ${res.statusCode}` })
        }
      },
      fail: reject,
    })
  })
}

const api = {
  health() {
    return request('/api/health')
  },
  login(code) {
    return request('/api/auth/login', 'POST', { code: code || 'mock_code' })
  },
  createSession(contentType, title) {
    return request('/api/sessions', 'POST', {
      content_type: contentType,
      title: title || null,
    })
  },
  getMessages(sessionId) {
    return request(`/api/sessions/${sessionId}/messages`)
  },
  sendMessage(sessionId, content) {
    return request(`/api/sessions/${sessionId}/messages`, 'POST', { content })
  },
  getOutline(sessionId) {
    return request(`/api/sessions/${sessionId}/outline`)
  },
  listStyles() {
    return request('/api/catalog/styles')
  },
  listModels() {
    return request('/api/catalog/models')
  },
  createPreview(sessionId, styleId, modelId) {
    const q = `style_id=${encodeURIComponent(styleId)}&model_id=${encodeURIComponent(modelId)}`
    return request(`/api/sessions/${sessionId}/preview?${q}`, 'POST')
  },
}

module.exports = { api, request }
