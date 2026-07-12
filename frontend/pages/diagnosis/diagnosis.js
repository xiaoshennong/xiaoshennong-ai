// 小神农中医AI - 辨证页面逻辑
const API_BASE = 'http://localhost:5000';

// 标准化问诊问题（20-30题）
const QUESTIONS = [
  {
    id: 'symptoms',
    text: '您目前最主要的不适症状是什么？',
    type: 'multiple',
    options: [
      { value: 'headache', label: '头痛' },
      { value: 'fever', label: '发热' },
      { value: 'chills', label: '怕冷/恶寒' },
      { value: 'sweating', label: '出汗' },
      { value: 'cough', label: '咳嗽' },
      { value: 'insomnia', label: '失眠' },
      { value: 'fatigue', label: '乏力' },
      { value: 'appetite_loss', label: '食欲不振' },
      { value: 'bloating', label: '腹胀' },
      { value: 'diarrhea', label: '腹泻' },
      { value: 'constipation', label: '便秘' },
      { value: 'dry_mouth', label: '口干' },
      { value: 'bitter_taste', label: '口苦' },
      { value: 'sore_throat', label: '咽痛' },
      { value: 'back_pain', label: '腰痛' }
    ]
  },
  {
    id: 'sweat_type',
    text: '您的出汗情况如何？',
    type: 'single',
    options: [
      { value: 'no_sweat', label: '无汗' },
      { value: 'little_sweat', label: '少汗' },
      { value: 'normal_sweat', label: '正常' },
      { value: 'night_sweat', label: '盗汗（夜间出汗）' },
      { value: 'spontaneous_sweat', label: '自汗（白天易出汗）' },
      { value: 'excessive_sweat', label: '多汗' }
    ]
  },
  {
    id: 'body_temp',
    text: '您对温度的感受？',
    type: 'single',
    options: [
      { value: 'cold_intolerant', label: '怕冷，喜热' },
      { value: 'heat_intolerant', label: '怕热，喜凉' },
      { value: 'cold_limbs', label: '手脚冰凉' },
      { value: 'hot_palms', label: '手心发热' },
      { value: 'normal_temp', label: '正常' }
    ]
  },
  {
    id: 'digestion',
    text: '您的消化情况？',
    type: 'single',
    options: [
      { value: 'good', label: '食欲好，消化正常' },
      { value: 'poor_appetite', label: '食欲不振' },
      { value: 'bloating', label: '饭后腹胀' },
      { value: 'acid_reflux', label: '反酸烧心' },
      { value: 'loose_stool', label: '大便溏稀' },
      { value: 'dry_stool', label: '大便干结' }
    ]
  },
  {
    id: 'sleep',
    text: '您的睡眠情况？',
    type: 'single',
    options: [
      { value: 'good', label: '睡眠好' },
      { value: 'difficulty_falling', label: '入睡困难' },
      { value: 'frequent_waking', label: '易醒' },
      { value: 'dream_disturbed', label: '多梦' },
      { value: 'early_waking', label: '早醒' }
    ]
  },
  {
    id: 'emotion',
    text: '您的情绪状态？',
    type: 'single',
    options: [
      { value: 'calm', label: '平和' },
      { value: 'irritable', label: '易怒' },
      { value: 'anxious', label: '焦虑' },
      { value: 'depressed', label: '抑郁' },
      { value: 'worried', label: '多思多虑' }
    ]
  },
  {
    id: 'complexion',
    text: '您的面色？',
    type: 'single',
    options: [
      { value: 'normal', label: '正常红润' },
      { value: 'pale', label: '苍白' },
      { value: 'sallow', label: '萎黄' },
      { value: 'flushed', label: '潮红' },
      { value: 'dark', label: '晦暗' },
      { value: 'oily', label: '油腻' }
    ]
  },
  {
    id: 'tongue',
    text: '您的舌象（可选）？',
    type: 'single',
    options: [
      { value: 'unknown', label: '不清楚' },
      { value: 'pale', label: '舌淡' },
      { value: 'red', label: '舌红' },
      { value: 'dark_red', label: '舌暗红' },
      { value: 'white_coating', label: '白苔' },
      { value: 'yellow_coating', label: '黄苔' },
      { value: 'thick_coating', label: '厚腻苔' }
    ]
  },
  {
    id: 'age_gender',
    text: '请补充基本信息',
    type: 'info',
    fields: [
      { id: 'age', label: '年龄', type: 'number', placeholder: '例如：35' },
      { id: 'gender', label: '性别', type: 'single', options: [
        { value: 'male', label: '男' },
        { value: 'female', label: '女' }
      ]}
    ]
  }
];

Page({
  data: {
    currentStep: 0,
    totalSteps: QUESTIONS.length,
    currentQuestion: null,
    selectedAnswers: {},
    canProceed: false,
    isLoading: false,
    result: null,
    recommendations: []
  },

  onLoad() {
    this.setData({ totalSteps: QUESTIONS.length });
  },

  // 开始辨证
  startDiagnosis() {
    this.setData({ currentStep: 1 });
    this.updateQuestion();
  },

  // 更新当前问题
  updateQuestion() {
    const { currentStep } = this.data;
    const question = QUESTIONS[currentStep - 1];
    
    this.setData({
      currentQuestion: question,
      canProceed: false
    });

    // 检查是否已有答案
    this.checkCanProceed();
  },

  // 单选
  selectOption(e) {
    const { value } = e.currentTarget.dataset;
    const { currentQuestion, selectedAnswers } = this.data;
    
    this.setData({
      selectedAnswers: {
        ...selectedAnswers,
        [currentQuestion.id]: value
      }
    });
    
    this.checkCanProceed();
  },

  // 多选切换
  toggleOption(e) {
    const { value } = e.currentTarget.dataset;
    const { currentQuestion, selectedAnswers } = this.data;
    const current = selectedAnswers[currentQuestion.id] || [];
    
    let updated;
    if (current.includes(value)) {
      updated = current.filter(v => v !== value);
    } else {
      updated = [...current, value];
    }
    
    this.setData({
      selectedAnswers: {
        ...selectedAnswers,
        [currentQuestion.id]: updated
      }
    });
    
    this.checkCanProceed();
  },

  // 文本输入
  onTextInput(e) {
    const { currentQuestion, selectedAnswers } = this.data;
    
    this.setData({
      selectedAnswers: {
        ...selectedAnswers,
        [currentQuestion.id]: e.detail.value
      }
    });
    
    this.checkCanProceed();
  },

  // 检查是否可以继续
  checkCanProceed() {
    const { currentQuestion, selectedAnswers } = this.data;
    const answer = selectedAnswers[currentQuestion.id];
    
    let canProceed = false;
    if (currentQuestion.type === 'single') {
      canProceed = !!answer;
    } else if (currentQuestion.type === 'multiple') {
      canProceed = Array.isArray(answer) && answer.length > 0;
    } else if (currentQuestion.type === 'text') {
      canProceed = !!answer && answer.length > 0;
    } else if (currentQuestion.type === 'info') {
      canProceed = true; // 信息字段可选
    }
    
    this.setData({ canProceed });
  },

  // 下一步
  nextStep() {
    const { currentStep, totalSteps, canProceed } = this.data;
    
    if (!canProceed) return;
    
    if (currentStep >= totalSteps) {
      this.submitDiagnosis();
    } else {
      this.setData({ currentStep: currentStep + 1 });
      this.updateQuestion();
    }
  },

  // 上一步
  prevStep() {
    const { currentStep } = this.data;
    if (currentStep > 1) {
      this.setData({ currentStep: currentStep - 1 });
      this.updateQuestion();
    }
  },

  // 提交辨证
  submitDiagnosis() {
    const { selectedAnswers } = this.data;
    
    // 构建症状描述
    const symptoms = [];
    if (selectedAnswers.symptoms) {
      symptoms.push(...selectedAnswers.symptoms.map(v => {
        const opt = QUESTIONS[0].options.find(o => o.value === v);
        return opt ? opt.label : v;
      }));
    }
    
    // 其他信息
    const symptomText = symptoms.join('、');
    const age = selectedAnswers.age || '';
    const gender = selectedAnswers.gender || '';
    
    this.setData({ isLoading: true });
    
    // 调用API
    wx.request({
      url: `${API_BASE}/api/diagnosis`,
      method: 'POST',
      header: { 'Content-Type': 'application/json' },
      data: {
        symptoms: symptomText,
        age: age,
        gender: gender
      },
      success: (res) => {
        if (res.data.success) {
          this.setData({
            result: res.data.data,
            isLoading: false
          });
          
          // 加载推荐商品
          this.loadRecommendations(res.data.data.constitution);
        } else {
          this.handleError(res.data.error || '辨证失败');
        }
      },
      fail: (err) => {
        // 模拟数据（MVP阶段无后端时）
        this.mockResult(symptomText);
      }
    });
  },

  // 模拟结果（开发测试用）
  mockResult(symptoms) {
    setTimeout(() => {
      const isCold = symptoms.includes('怕冷') || symptoms.includes('恶寒');
      const isFever = symptoms.includes('发热') || symptoms.includes('头痛');
      
      let constitution, syndrome, advice;
      
      if (isCold && isFever) {
        constitution = '风寒表实证';
        syndrome = '外感风寒，卫阳被郁，腠理闭塞';
        advice = '建议采用辛温解表之法。可考虑麻黄汤类方剂发汗解表。注意保暖，多饮温水，避风寒。';
      } else if (symptoms.includes('出汗')) {
        constitution = '风寒表虚证';
        syndrome = '外感风寒，营卫不和';
        advice = '建议采用解肌发表之法。可考虑桂枝汤类方剂调和营卫。注意休息，饮食清淡。';
      } else {
        constitution = '待进一步辨识';
        syndrome = '根据现有症状，暂无法明确辨证';
        advice = '建议详细描述症状，或咨询专业医师。';
      }
      
      this.setData({
        result: {
          constitution,
          syndrome,
          advice,
          sources: [
            {
              book: '伤寒论',
              section: '太阳病篇',
              text: '太阳之为病，脉浮，头项强痛而恶寒。',
              original_text: '太阳之为病，脉浮，头项强痛而恶寒。'
            }
          ],
          warning: '【重要提示】本结果仅供参考，不能替代专业医生诊断。如有不适，请及时就医。'
        },
        isLoading: false
      });
      
      this.loadRecommendations(constitution);
    }, 2000);
  },

  // 加载推荐商品
  loadRecommendations(constitution) {
    // 根据体质推荐
    const allProducts = [
      { id: 'sour_plum_soup', name: '酸梅汤', price: 3990, image: '/assets/products/sour_plum.jpg', constitutions: ['阴虚质', '湿热质'] },
      { id: 'dampness_tea', name: '祛湿茶', price: 4990, image: '/assets/products/dampness.jpg', constitutions: ['痰湿质', '湿热质'] },
      { id: 'qing_bu_liang', name: '清补凉', price: 2990, image: '/assets/products/qingbu.jpg', constitutions: ['阴虚质', '气虚质'] },
      { id: 'sishen_tang', name: '四神汤', price: 3990, image: '/assets/products/sishen.jpg', constitutions: ['气虚质', '阳虚质'] },
      { id: 'chrysanthemum_tea', name: '菊花枸杞茶', price: 2990, image: '/assets/products/chrysanthemum.jpg', constitutions: ['阴虚质', '气郁质'] }
    ];
    
    // 简单匹配（实际应调用API）
    const matched = allProducts.slice(0, 3);
    
    this.setData({ recommendations: matched });
  },

  // 处理错误
  handleError(msg) {
    this.setData({ isLoading: false });
    wx.showToast({ title: msg, icon: 'none' });
  },

  // 重新辨证
  restart() {
    this.setData({
      currentStep: 0,
      selectedAnswers: {},
      result: null,
      recommendations: []
    });
  },

  // 找医师确认
  goToConsult() {
    wx.showToast({ title: '医师对接功能即将上线', icon: 'none' });
  },

  // 跳转到商品
  goToProduct(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/product-detail/product-detail?id=${id}` });
  }
});
