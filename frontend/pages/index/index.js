// 小神农中医AI - 首页逻辑
const API_BASE = 'http://localhost:5000'; // 生产环境应使用HTTPS域名

Page({
  data: {
    hotProducts: []
  },

  onLoad() {
    this.loadHotProducts();
  },

  // 加载热门商品
  loadHotProducts() {
    // 本地数据（MVP阶段），后续对接API
    this.setData({
      hotProducts: [
        {
          id: 'sour_plum_soup',
          name: '小神农·酸梅汤',
          source: '《本草纲目》·梅',
          price: 3990,
          originalPrice: 5990,
          image: '/assets/products/sour_plum.jpg',
          expert: '中医科学院监制'
        },
        {
          id: 'dampness_tea',
          name: '小神农·祛湿茶',
          source: '《食疗本草》',
          price: 4990,
          originalPrice: 6990,
          image: '/assets/products/dampness.jpg',
          expert: '中医科学院监制'
        }
      ]
    });
  },

  // 跳转到AI辨证
  goToDiagnosis() {
    wx.navigateTo({
      url: '/pages/diagnosis/diagnosis'
    });
  },

  // 跳转到商品列表
  goToProducts() {
    wx.navigateTo({
      url: '/pages/products/products'
    });
  },

  // 跳转到古籍查询
  goToKnowledge() {
    wx.navigateTo({
      url: '/pages/knowledge/knowledge'
    });
  },

  // 跳转到健康档案
  goToHealth() {
    wx.navigateTo({
      url: '/pages/health/health'
    });
  },

  // 商品详情
  goToProductDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/product-detail/product-detail?id=${id}`
    });
  }
});
