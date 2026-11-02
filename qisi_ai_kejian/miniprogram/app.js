const { api } = require('./utils/api')

App({
  globalData: {
    user: null,
    apiBase: 'http://127.0.0.1:8000',
    // Carried across clarification → style → model → preview
    draft: {
      sessionId: null,
      contentType: null,
      outline: null,
      styleId: 'clean_academic',
      modelId: 'mock-qisi-lite',
      preview: null,
    },
  },

  onLaunch() {
    api
      .login('mock_code')
      .then((user) => {
        this.globalData.user = user
      })
      .catch((err) => {
        console.warn('mock login failed (backend down?)', err)
      })
  },
})
