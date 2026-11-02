const { api } = require('../../utils/api')

Page({
  data: {
    plans: [],
    membership: null,
    selectedId: 'pro_month',
    userId: null,
  },

  onShow() {
    const user = getApp().globalData.user
    const userId = user && user.user_id
    this.setData({ userId })
    api.listPlans().then((plans) => {
      const mapped = plans.map((p) => ({
        ...p,
        price_yuan: (p.price_fen / 100).toFixed(2),
      }))
      this.setData({ plans: mapped })
    })
    if (userId) {
      api.getMembership(userId).then((m) => this.setData({ membership: m }))
    } else {
      api.login('mock_code').then((u) => {
        getApp().globalData.user = u
        this.setData({ userId: u.user_id })
        return api.getMembership(u.user_id)
      }).then((m) => this.setData({ membership: m }))
    }
  },

  onSelect(e) {
    this.setData({ selectedId: e.currentTarget.dataset.id })
  },

  onBuy() {
    const userId = this.data.userId
    if (!userId) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      return
    }
    wx.showLoading({ title: '下单…' })
    api
      .createOrder(userId, this.data.selectedId)
      .then((order) => {
        // Real: wx.requestPayment(order.pay_sign_package)
        return api.mockPayNotify(order.id)
      })
      .then(() => api.getMembership(userId))
      .then((m) => {
        wx.hideLoading()
        this.setData({ membership: m })
        wx.showToast({ title: '开通成功（mock）', icon: 'success' })
      })
      .catch((err) => {
        wx.hideLoading()
        wx.showToast({
          title: (err && (err.detail || err.message)) || '支付失败',
          icon: 'none',
        })
      })
  },
})
