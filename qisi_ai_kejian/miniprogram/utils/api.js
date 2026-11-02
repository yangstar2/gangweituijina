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
          const payload = res.data || { detail: `HTTP ${res.statusCode}` }
          if (payload && typeof payload === 'object') payload.statusCode = res.statusCode
          reject(payload)
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
  generate(sessionId, styleId, modelId, title) {
    return request(`/api/sessions/${sessionId}/generate`, 'POST', {
      style_id: styleId,
      model_id: modelId,
      title: title || null,
    })
  },
  getArtifact(artifactId) {
    return request(`/api/artifacts/${artifactId}`)
  },
  listPlans() {
    return request('/api/membership/plans')
  },
  getMembership(userId) {
    return request(`/api/membership/me?user_id=${userId}`)
  },
  createOrder(userId, planId) {
    return request('/api/pay/orders', 'POST', { user_id: userId, plan_id: planId })
  },
  mockPayNotify(orderId) {
    return request(`/api/pay/notify/mock`, 'POST', { order_id: orderId })
  },
}

module.exports = { api, request }
