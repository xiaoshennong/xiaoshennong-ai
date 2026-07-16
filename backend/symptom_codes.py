#!/usr/bin/env python3
"""
小神农中医AI - 症状编号体系 (SN: Symptom Number)
编号格式：SN-部位-类别-序号
"""

# 部位代码（2位）
BODY_PARTS = {
    'HD': '头面',
    'TH': '胸腹',
    'BK': '腰背',
    'LM': '四肢',
    'SP': '全身',
    'PS': '精神',
    'DG': '消化',
    'RP': '呼吸',
    'CV': '循环',
    'UR': '泌尿',
    'RE': '生殖',
    'SK': '皮肤',
    'EN': '五官',
    'TM': '体温',
    'SL': '睡眠',
    'OT': '其他',
}

# 类别代码（1位）
CATEGORY_CODES = {
    'S': '主观症状（患者感觉）',
    'O': '客观体征（医师观察）',
    'C': '复合症状（多个症状组合）',
}

# 症状编号映射表
SYMPTOM_MAP = {
    # 头面 (HD)
    'SN-HD-S-001': {'name': '头痛', 'aliases': ['头痛', '头疼', '头风', '头胀痛', '偏头痛'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-HD-S-002': {'name': '头晕', 'aliases': ['头晕', '头昏', '眩晕', '头眩'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-HD-S-003': {'name': '头胀', 'aliases': ['头胀', '头重', '头胀满'], 'classic_refs': ['内经']},
    'SN-HD-S-004': {'name': '耳鸣', 'aliases': ['耳鸣', '耳中鸣', '耳内鸣响'], 'classic_refs': ['内经']},
    'SN-HD-O-001': {'name': '面色发红', 'aliases': ['面红', '面色红', '面赤', '面色潮红'], 'classic_refs': ['伤寒论']},
    'SN-HD-O-002': {'name': '面色发白', 'aliases': ['面白', '面色苍白', '面色无华'], 'classic_refs': ['内经']},
    'SN-HD-O-003': {'name': '面色发黄', 'aliases': ['面黄', '面色黄', '萎黄'], 'classic_refs': ['金匮要略']},
    'SN-HD-O-004': {'name': '面色发黑', 'aliases': ['面黑', '面色黑', '黧黑'], 'classic_refs': ['金匮要略']},
    'SN-HD-O-005': {'name': '面色发青', 'aliases': ['面青', '面色青', '青黑'], 'classic_refs': ['内经']},
    'SN-HD-O-006': {'name': '目赤', 'aliases': ['目赤', '眼红', '眼睛红', '白睛红'], 'classic_refs': ['伤寒论']},
    'SN-HD-O-007': {'name': '目黄', 'aliases': ['目黄', '眼黄', '巩膜黄'], 'classic_refs': ['金匮要略']},
    'SN-HD-O-008': {'name': '鼻塞', 'aliases': ['鼻塞', '鼻堵', '鼻不通'], 'classic_refs': ['伤寒论']},
    'SN-HD-O-009': {'name': '流涕', 'aliases': ['流涕', '鼻涕', '鼻流清涕', '鼻流浊涕'], 'classic_refs': ['伤寒论']},
    'SN-HD-O-010': {'name': '咽干', 'aliases': ['咽干', '咽喉干', '喉咙干'], 'classic_refs': ['伤寒论']},
    'SN-HD-O-011': {'name': '咽痛', 'aliases': ['咽痛', '喉咙痛', '咽喉痛', '嗓子痛'], 'classic_refs': ['伤寒论']},
    'SN-HD-O-012': {'name': '口苦', 'aliases': ['口苦', '口中有苦味'], 'classic_refs': ['伤寒论']},
    'SN-HD-O-013': {'name': '口臭', 'aliases': ['口臭', '口气重', '口中有异味'], 'classic_refs': ['内经']},
    'SN-HD-O-014': {'name': '齿痛', 'aliases': ['齿痛', '牙痛', '牙齿痛'], 'classic_refs': ['内经']},
    'SN-HD-O-015': {'name': '齿槁', 'aliases': ['齿槁', '牙齿枯槁', '齿干'], 'classic_refs': ['内经']},
    'SN-HD-O-016': {'name': '发堕', 'aliases': ['发堕', '脱发', '头发脱落', '发落'], 'classic_refs': ['内经']},
    'SN-HD-O-017': {'name': '发白', 'aliases': ['发白', '头发白', '白发', '鬓发斑白'], 'classic_refs': ['内经']},
    'SN-HD-C-001': {'name': '头痛伴发热', 'aliases': ['头痛发热', '头疼发烧'], 'classic_refs': ['伤寒论']},
    'SN-HD-C-002': {'name': '头痛伴恶寒', 'aliases': ['头痛怕冷', '头疼恶寒'], 'classic_refs': ['伤寒论']},
    'SN-HD-C-003': {'name': '头项强痛', 'aliases': ['头项强痛', '脖子僵硬', '项背强'], 'classic_refs': ['伤寒论']},
    
    # 胸腹 (TH)
    'SN-TH-S-001': {'name': '胸闷', 'aliases': ['胸闷', '胸满', '胸中窒', '胸痞'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-S-002': {'name': '胸痛', 'aliases': ['胸痛', '胸疼', '胸背痛', '心痛'], 'classic_refs': ['金匮要略']},
    'SN-TH-S-003': {'name': '心悸', 'aliases': ['心悸', '心慌', '心下悸', '心动悸'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-S-004': {'name': '胃脘痛', 'aliases': ['胃脘痛', '胃痛', '胃疼', '心下痛', '脘腹痛', '胃不舒服', '胃不适', '胃难受', '胃有点不舒服', '胃胀痛', '胃隐痛'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-S-005': {'name': '腹胀', 'aliases': ['腹胀', '腹满', '肚子胀', '脘腹胀满', '胃胀', '胃满', '肚子鼓鼓'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-S-006': {'name': '腹痛', 'aliases': ['腹痛', '肚子疼', '腹疼', '少腹痛', '小腹痛'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-S-007': {'name': '胁痛', 'aliases': ['胁痛', '胁肋痛', '两胁痛', '肋痛'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-S-008': {'name': '恶心', 'aliases': ['恶心', '欲吐', '想吐', '干呕'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-S-009': {'name': '呕吐', 'aliases': ['呕吐', '吐', '呕', '哕'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-S-010': {'name': '呃逆', 'aliases': ['呃逆', '打嗝', '嗳气', '噫气'], 'classic_refs': ['伤寒论']},
    'SN-TH-S-011': {'name': '烧心', 'aliases': ['烧心', '心下热', '胃中灼热', '反酸'], 'classic_refs': ['伤寒论']},
    'SN-TH-S-012': {'name': '食欲不振', 'aliases': ['食欲不振', '不欲食', '不能食', '纳呆', '纳差', '没胃口', '吃不下', '不想吃饭', '饭量减少'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-S-013': {'name': '消谷善饥', 'aliases': ['消谷善饥', '多食易饥', '易饿', '食量大'], 'classic_refs': ['金匮要略']},
    'SN-TH-S-014': {'name': '吞酸', 'aliases': ['吞酸', '吐酸', '泛酸', '酸水'], 'classic_refs': ['伤寒论']},
    'SN-TH-O-001': {'name': '心下痞', 'aliases': ['心下痞', '胃痞', '痞满', '心下痞硬'], 'classic_refs': ['伤寒论']},
    'SN-TH-O-002': {'name': '心下硬', 'aliases': ['心下硬', '心下硬满', '心下坚'], 'classic_refs': ['伤寒论']},
    'SN-TH-O-003': {'name': '腹满', 'aliases': ['腹满', '腹部胀满', '腹胀满'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-O-004': {'name': '腹水', 'aliases': ['腹水', '鼓胀', '水鼓', '腹部肿大'], 'classic_refs': ['金匮要略']},
    'SN-TH-O-005': {'name': '肠鸣', 'aliases': ['肠鸣', '腹中雷鸣', '腹中鸣'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-C-001': {'name': '胸胁苦满', 'aliases': ['胸胁苦满', '胸胁满', '胸胁胀满'], 'classic_refs': ['伤寒论']},
    'SN-TH-C-002': {'name': '胃脘痛伴呕吐', 'aliases': ['胃痛呕吐', '胃疼想吐'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-C-003': {'name': '腹痛伴腹泻', 'aliases': ['腹痛腹泻', '肚子疼拉肚子'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TH-C-004': {'name': '心下痞硬伴呕吐', 'aliases': ['胃痞呕吐', '心下痞硬呕'], 'classic_refs': ['伤寒论']},
    
    # 腰背 (BK)
    'SN-BK-S-001': {'name': '腰痛', 'aliases': ['腰痛', '腰疼', '腰脊痛', '腰背痛'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-BK-S-002': {'name': '背痛', 'aliases': ['背痛', '背疼', '肩背痛'], 'classic_refs': ['伤寒论']},
    'SN-BK-S-003': {'name': '颈痛', 'aliases': ['颈痛', '脖子痛', '颈项痛', '项强'], 'classic_refs': ['伤寒论']},
    'SN-BK-S-004': {'name': '腰膝酸软', 'aliases': ['腰膝酸软', '腰膝无力', '腰酸腿软'], 'classic_refs': ['内经', '金匮要略']},
    'SN-BK-O-001': {'name': '脊柱畸形', 'aliases': ['脊柱畸形', '驼背', '脊柱侧弯'], 'classic_refs': ['内经']},
    'SN-BK-C-001': {'name': '腰痛伴下肢放射痛', 'aliases': ['腰痛腿痛', '腰疼腿麻', '坐骨神经痛'], 'classic_refs': ['金匮要略']},
    
    # 四肢 (LM)
    'SN-LM-S-001': {'name': '关节痛', 'aliases': ['关节痛', '关节疼痛', '骨节痛', '骨节疼痛'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-LM-S-002': {'name': '肌肉酸痛', 'aliases': ['肌肉酸痛', '身疼', '身体疼痛', '身痛', '体痛'], 'classic_refs': ['伤寒论']},
    'SN-LM-S-003': {'name': '四肢乏力', 'aliases': ['四肢乏力', '四肢无力', '手足无力', '乏力', '无力'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-LM-S-004': {'name': '手足心热', 'aliases': ['手足心热', '手心热', '脚心热', '五心烦热'], 'classic_refs': ['内经', '金匮要略']},
    'SN-LM-S-005': {'name': '手足冷', 'aliases': ['手足冷', '手脚冰凉', '手足不温', '四肢冷', '手足逆冷'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-LM-S-006': {'name': '肢体麻木', 'aliases': ['肢体麻木', '麻木', '不仁', '肌肤不仁'], 'classic_refs': ['金匮要略']},
    'SN-LM-S-007': {'name': '肢体浮肿', 'aliases': ['肢体浮肿', '四肢肿', '手脚肿', '浮肿'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-LM-S-008': {'name': '抽筋', 'aliases': ['抽筋', '转筋', '筋脉拘急', '挛急'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-LM-S-009': {'name': '震颤', 'aliases': ['震颤', '颤抖', '振颤', '身瞤动'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-LM-O-001': {'name': '关节肿胀', 'aliases': ['关节肿胀', '关节肿', '关节肿大'], 'classic_refs': ['金匮要略']},
    'SN-LM-O-002': {'name': '关节变形', 'aliases': ['关节变形', '关节畸形', '关节僵硬'], 'classic_refs': ['金匮要略']},
    'SN-LM-O-003': {'name': '下肢水肿', 'aliases': ['下肢水肿', '腿肿', '脚肿', '足肿'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-LM-C-001': {'name': '关节痛伴肿胀', 'aliases': ['关节肿痛', '关节红肿热痛'], 'classic_refs': ['金匮要略']},
    'SN-LM-C-002': {'name': '四肢冷伴腹痛', 'aliases': ['手脚冷肚子疼', '四肢厥冷腹痛'], 'classic_refs': ['伤寒论', '金匮要略']},
    
    # 全身 (SP)
    'SN-SP-S-001': {'name': '恶寒', 'aliases': ['恶寒', '怕冷', '畏寒', '恶风寒', '怕冷怕风'], 'classic_refs': ['伤寒论']},
    'SN-SP-S-002': {'name': '恶风', 'aliases': ['恶风', '怕风', '畏风', '风吹难受'], 'classic_refs': ['伤寒论']},
    'SN-SP-S-003': {'name': '发热', 'aliases': ['发热', '发烧', '身热', '潮热', '壮热', '微热', '低热', '高热'], 'classic_refs': ['伤寒论']},
    'SN-SP-S-004': {'name': '汗出', 'aliases': ['汗出', '出汗', '自汗', '盗汗', '多汗', '流汗'], 'classic_refs': ['伤寒论']},
    'SN-SP-S-005': {'name': '无汗', 'aliases': ['无汗', '不出汗', '汗不出', '不得汗'], 'classic_refs': ['伤寒论']},
    'SN-SP-S-006': {'name': '身重', 'aliases': ['身重', '身体沉重', '身体重', '身重如裹'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SP-S-007': {'name': '消瘦', 'aliases': ['消瘦', '瘦', '羸瘦', '身体瘦', '形瘦'], 'classic_refs': ['金匮要略']},
    'SN-SP-S-008': {'name': '浮肿', 'aliases': ['浮肿', '水肿', '肿胀', '肿'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SP-S-009': {'name': '肥胖', 'aliases': ['肥胖', '胖', '形体丰腴', '体重超标'], 'classic_refs': ['内经']},
    'SN-SP-S-010': {'name': '乏力', 'aliases': ['乏力', '疲倦', '疲劳', '倦怠', '困乏', '没力气'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SP-S-011': {'name': '畏寒肢冷', 'aliases': ['畏寒肢冷', '怕冷手脚凉', '全身怕冷'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SP-S-012': {'name': '潮热', 'aliases': ['潮热', '午后热', '日晡发热', '定时发热'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SP-S-013': {'name': '寒热往来', 'aliases': ['寒热往来', '忽冷忽热', '冷热交替', '一阵冷一阵热'], 'classic_refs': ['伤寒论']},
    'SN-SP-O-001': {'name': '体温升高', 'aliases': ['体温升高', '体温高', '量体温高'], 'classic_refs': ['伤寒论']},
    'SN-SP-O-002': {'name': '皮肤黄染', 'aliases': ['皮肤黄', '身黄', '发黄', '黄疸'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SP-O-003': {'name': '皮肤斑疹', 'aliases': ['皮肤斑疹', '斑疹', '皮疹', '出疹', '红斑'], 'classic_refs': ['伤寒论']},
    'SN-SP-O-004': {'name': '皮肤瘀斑', 'aliases': ['皮肤瘀斑', '瘀斑', '紫癜', '皮下出血'], 'classic_refs': ['金匮要略']},
    'SN-SP-C-001': {'name': '发热恶寒无汗', 'aliases': ['发烧怕冷不出汗', '发热恶寒无汗'], 'classic_refs': ['伤寒论']},
    'SN-SP-C-002': {'name': '发热汗出恶风', 'aliases': ['发烧出汗怕风', '发热汗出恶风'], 'classic_refs': ['伤寒论']},
    'SN-SP-C-003': {'name': '身疼痛', 'aliases': ['身疼痛', '浑身疼', '全身疼', '身体疼痛'], 'classic_refs': ['伤寒论']},
    'SN-SP-C-004': {'name': '身重乏力', 'aliases': ['身体沉重没力气', '身重乏力'], 'classic_refs': ['伤寒论', '金匮要略']},
    
    # 精神 (PS)
    'SN-PS-S-001': {'name': '心烦', 'aliases': ['心烦', '烦躁', '心中烦', '烦乱'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-PS-S-002': {'name': '失眠', 'aliases': ['失眠', '不寐', '不得眠', '目不瞑', '睡不着', '难入睡'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-PS-S-003': {'name': '多梦', 'aliases': ['多梦', '梦多', '睡眠不安', '易醒'], 'classic_refs': ['内经', '金匮要略']},
    'SN-PS-S-004': {'name': '健忘', 'aliases': ['健忘', '记忆力差', '忘事', '善忘'], 'classic_refs': ['内经']},
    'SN-PS-S-005': {'name': '焦虑', 'aliases': ['焦虑', '紧张', '不安', '坐卧不宁'], 'classic_refs': ['金匮要略']},
    'SN-PS-S-006': {'name': '抑郁', 'aliases': ['抑郁', '情绪低落', '闷闷不乐', '悲伤欲哭'], 'classic_refs': ['金匮要略']},
    'SN-PS-S-007': {'name': '易怒', 'aliases': ['易怒', '烦躁易怒', '暴怒', '容易生气'], 'classic_refs': ['内经', '金匮要略']},
    'SN-PS-S-008': {'name': '精神萎靡', 'aliases': ['精神萎靡', '没精神', '精神差', '萎靡不振'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-PS-S-009': {'name': '嗜睡', 'aliases': ['嗜睡', '困倦', '昏昏欲睡', '多眠'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-PS-S-010': {'name': '谵语', 'aliases': ['谵语', '说胡话', '神志不清', '意识模糊'], 'classic_refs': ['伤寒论']},
    'SN-PS-S-011': {'name': '喜悲伤', 'aliases': ['喜悲伤', '想哭', '情绪低落', '悲伤'], 'classic_refs': ['金匮要略']},
    'SN-PS-S-012': {'name': '恐惧', 'aliases': ['恐惧', '害怕', '惊恐', '易惊'], 'classic_refs': ['内经', '金匮要略']},
    'SN-PS-S-013': {'name': '神疲', 'aliases': ['神疲', '精神疲惫', '神疲乏力'], 'classic_refs': ['金匮要略']},
    'SN-PS-O-001': {'name': '表情淡漠', 'aliases': ['表情淡漠', '表情呆滞', '神情淡漠'], 'classic_refs': ['金匮要略']},
    'SN-PS-O-002': {'name': '目光呆滞', 'aliases': ['目光呆滞', '眼神呆滞', '目光无神'], 'classic_refs': ['金匮要略']},
    'SN-PS-C-001': {'name': '虚烦不得眠', 'aliases': ['虚烦失眠', '心烦睡不着'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-PS-C-002': {'name': '喜悲伤欲哭', 'aliases': ['想哭', '悲伤欲哭', '情绪低落想哭'], 'classic_refs': ['金匮要略']},
    
    # 消化 (DG)
    'SN-DG-S-001': {'name': '泄泻', 'aliases': ['泄泻', '腹泻', '拉肚子', '溏泄', '便溏', '下利'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-DG-S-002': {'name': '便秘', 'aliases': ['便秘', '便闭', '大便难', '大便不通', '排便困难'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-DG-S-003': {'name': '里急后重', 'aliases': ['里急后重', '便意频繁', '排便不尽'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-DG-S-004': {'name': '大便黏滞', 'aliases': ['大便黏滞', '大便粘', '黏腻不爽', '大便不爽'], 'classic_refs': ['金匮要略']},
    'SN-DG-S-005': {'name': '完谷不化', 'aliases': ['完谷不化', '食物不消化', '消化不良', '食不消化'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-DG-S-006': {'name': '嗳气', 'aliases': ['嗳气', '打嗝', '噫气', '打饱嗝'], 'classic_refs': ['伤寒论']},
    'SN-DG-S-007': {'name': '矢气', 'aliases': ['矢气', '放屁', '排气多', '肠鸣矢气'], 'classic_refs': ['伤寒论']},
    'SN-DG-O-001': {'name': '大便色黑', 'aliases': ['大便黑', '黑便', '柏油样便'], 'classic_refs': ['金匮要略']},
    'SN-DG-O-002': {'name': '大便带血', 'aliases': ['便血', '大便带血', '血便'], 'classic_refs': ['金匮要略']},
    'SN-DG-O-003': {'name': '大便色白', 'aliases': ['大便白', '白便', '陶土色便'], 'classic_refs': ['伤寒论']},
    'SN-DG-O-004': {'name': '大便色黄', 'aliases': ['大便黄', '黄便'], 'classic_refs': ['伤寒论']},
    'SN-DG-O-005': {'name': '大便干结', 'aliases': ['大便干', '干结', '燥结', '硬便'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-DG-C-001': {'name': '下利清谷', 'aliases': ['下利清谷', '拉肚子不消化', '完谷不化腹泻'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-DG-C-002': {'name': '便秘伴腹胀', 'aliases': ['便秘肚子胀', '大便不通腹胀'], 'classic_refs': ['伤寒论', '金匮要略']},
    
    # 呼吸 (RP)
    'SN-RP-S-001': {'name': '咳嗽', 'aliases': ['咳嗽', '咳', '咳逆', '嗽'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-RP-S-002': {'name': '气喘', 'aliases': ['气喘', '喘', '喘息', '呼吸急促', '气短', '气促'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-RP-S-003': {'name': '呼吸困难', 'aliases': ['呼吸困难', '呼吸不畅', '胸闷气短', '憋气'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-RP-S-004': {'name': '咳痰', 'aliases': ['咳痰', '痰多', '吐痰', '咯痰'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-RP-S-005': {'name': '痰中带血', 'aliases': ['痰中带血', '咯血', '咳血', '吐血'], 'classic_refs': ['金匮要略']},
    'SN-RP-S-006': {'name': '胸痛伴咳嗽', 'aliases': ['胸痛咳嗽', '咳嗽胸疼'], 'classic_refs': ['金匮要略']},
    'SN-RP-S-007': {'name': '声音嘶哑', 'aliases': ['声音嘶哑', '声哑', '失音', '声音低微'], 'classic_refs': ['金匮要略']},
    'SN-RP-O-001': {'name': '呼吸音粗', 'aliases': ['呼吸音粗', '呼吸粗重'], 'classic_refs': ['伤寒论']},
    'SN-RP-O-002': {'name': '喉中痰鸣', 'aliases': ['喉中痰鸣', '痰鸣', '喉中水鸡声'], 'classic_refs': ['金匮要略']},
    'SN-RP-O-003': {'name': '胸廓变形', 'aliases': ['胸廓变形', '桶状胸', '鸡胸'], 'classic_refs': ['金匮要略']},
    'SN-RP-C-001': {'name': '咳喘痰多', 'aliases': ['咳嗽气喘痰多', '咳喘痰多'], 'classic_refs': ['金匮要略']},
    'SN-RP-C-002': {'name': '喘息不得卧', 'aliases': ['喘不能躺', '喘息不得卧', '呼吸困难不能平卧'], 'classic_refs': ['金匮要略']},
    
    # 循环 (CV)
    'SN-CV-S-001': {'name': '心悸', 'aliases': ['心悸', '心慌', '心跳快', '心动悸'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-S-002': {'name': '胸闷', 'aliases': ['胸闷', '胸满', '胸中窒', '胸痞'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-S-003': {'name': '胸痛', 'aliases': ['胸痛', '胸疼', '胸背痛', '心痛', '心下痛'], 'classic_refs': ['金匮要略']},
    'SN-CV-S-004': {'name': '气短', 'aliases': ['气短', '气不足', '少气', '气息短'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-O-001': {'name': '脉浮', 'aliases': ['脉浮', '浮脉'], 'classic_refs': ['伤寒论']},
    'SN-CV-O-002': {'name': '脉沉', 'aliases': ['脉沉', '沉脉'], 'classic_refs': ['伤寒论']},
    'SN-CV-O-003': {'name': '脉数', 'aliases': ['脉数', '数脉', '脉快'], 'classic_refs': ['伤寒论']},
    'SN-CV-O-004': {'name': '脉迟', 'aliases': ['脉迟', '迟脉', '脉慢'], 'classic_refs': ['伤寒论']},
    'SN-CV-O-005': {'name': '脉细', 'aliases': ['脉细', '细脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-O-006': {'name': '脉弦', 'aliases': ['脉弦', '弦脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-O-007': {'name': '脉滑', 'aliases': ['脉滑', '滑脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-O-008': {'name': '脉涩', 'aliases': ['脉涩', '涩脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-O-009': {'name': '脉紧', 'aliases': ['脉紧', '紧脉'], 'classic_refs': ['伤寒论']},
    'SN-CV-O-010': {'name': '脉微', 'aliases': ['脉微', '微脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-O-011': {'name': '脉弱', 'aliases': ['脉弱', '弱脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-O-012': {'name': '脉虚', 'aliases': ['脉虚', '虚脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-O-013': {'name': '脉实', 'aliases': ['脉实', '实脉'], 'classic_refs': ['伤寒论']},
    'SN-CV-O-014': {'name': '脉洪', 'aliases': ['脉洪', '洪脉', '脉洪大'], 'classic_refs': ['伤寒论']},
    'SN-CV-O-015': {'name': '脉结代', 'aliases': ['脉结代', '结代脉', '脉结'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-O-016': {'name': '脉促', 'aliases': ['脉促', '促脉'], 'classic_refs': ['伤寒论']},
    'SN-CV-O-017': {'name': '脉芤', 'aliases': ['脉芤', '芤脉'], 'classic_refs': ['金匮要略']},
    'SN-CV-O-018': {'name': '脉革', 'aliases': ['脉革', '革脉'], 'classic_refs': ['金匮要略']},
    'SN-CV-C-001': {'name': '脉浮紧', 'aliases': ['脉浮紧', '浮紧脉'], 'classic_refs': ['伤寒论']},
    'SN-CV-C-002': {'name': '脉浮缓', 'aliases': ['脉浮缓', '浮缓脉'], 'classic_refs': ['伤寒论']},
    'SN-CV-C-003': {'name': '脉浮数', 'aliases': ['脉浮数', '浮数脉'], 'classic_refs': ['伤寒论']},
    'SN-CV-C-004': {'name': '脉沉迟', 'aliases': ['脉沉迟', '沉迟脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-C-005': {'name': '脉沉细', 'aliases': ['脉沉细', '沉细脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-C-006': {'name': '脉弦细', 'aliases': ['脉弦细', '弦细脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-C-007': {'name': '脉细数', 'aliases': ['脉细数', '细数脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-C-008': {'name': '脉滑数', 'aliases': ['脉滑数', '滑数脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-C-009': {'name': '脉弦数', 'aliases': ['脉弦数', '弦数脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-CV-C-010': {'name': '脉微弱', 'aliases': ['脉微弱', '微弱脉'], 'classic_refs': ['伤寒论', '金匮要略']},
    
    # 泌尿 (UR)
    'SN-UR-S-001': {'name': '小便不利', 'aliases': ['小便不利', '排尿困难', '尿不畅', '尿少'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-UR-S-002': {'name': '尿频', 'aliases': ['尿频', '小便频数', '尿多', '小便多'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-UR-S-003': {'name': '尿急', 'aliases': ['尿急', '尿急迫', '憋不住尿'], 'classic_refs': ['伤寒论']},
    'SN-UR-S-004': {'name': '尿痛', 'aliases': ['尿痛', '小便痛', '排尿痛', '尿道痛'], 'classic_refs': ['伤寒论']},
    'SN-UR-S-005': {'name': '遗尿', 'aliases': ['遗尿', '尿床', '小便失禁', '遗溺'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-UR-S-006': {'name': '夜尿多', 'aliases': ['夜尿多', '夜尿频', '夜间多尿'], 'classic_refs': ['金匮要略']},
    'SN-UR-O-001': {'name': '尿色黄', 'aliases': ['尿黄', '小便黄', '尿色深'], 'classic_refs': ['伤寒论']},
    'SN-UR-O-002': {'name': '尿色白', 'aliases': ['尿白', '小便白', '尿色清'], 'classic_refs': ['伤寒论']},
    'SN-UR-O-003': {'name': '尿血', 'aliases': ['尿血', '血尿', '小便带血', '尿中带血'], 'classic_refs': ['金匮要略']},
    'SN-UR-O-004': {'name': '尿浊', 'aliases': ['尿浊', '小便浑浊', '白浊'], 'classic_refs': ['金匮要略']},
    'SN-UR-O-005': {'name': '尿中有砂石', 'aliases': ['尿砂石', '尿中有石', '砂淋'], 'classic_refs': ['金匮要略']},
    'SN-UR-C-001': {'name': '小便不利伴口渴', 'aliases': ['尿少口渴', '小便不利口渴'], 'classic_refs': ['伤寒论', '金匮要略']},
    
    # 生殖 (RE)
    'SN-RE-S-001': {'name': '月经不调', 'aliases': ['月经不调', '月经不准', '经期紊乱', '经行不调'], 'classic_refs': ['金匮要略']},
    'SN-RE-S-002': {'name': '痛经', 'aliases': ['痛经', '经行腹痛', '月经痛'], 'classic_refs': ['金匮要略']},
    'SN-RE-S-003': {'name': '闭经', 'aliases': ['闭经', '月经不来', '经闭', '停经'], 'classic_refs': ['金匮要略']},
    'SN-RE-S-004': {'name': '崩漏', 'aliases': ['崩漏', '月经量多', '经量过多', '漏下'], 'classic_refs': ['金匮要略']},
    'SN-RE-S-005': {'name': '带下异常', 'aliases': ['带下异常', '白带异常', '带下病', '带下多'], 'classic_refs': ['金匮要略']},
    'SN-RE-S-006': {'name': '不孕', 'aliases': ['不孕', '不育', '无子'], 'classic_refs': ['金匮要略']},
    'SN-RE-S-007': {'name': '阳痿', 'aliases': ['阳痿', '阳事不举', '勃起障碍'], 'classic_refs': ['金匮要略']},
    'SN-RE-S-008': {'name': '早泄', 'aliases': ['早泄', '遗精', '滑精', '梦遗'], 'classic_refs': ['金匮要略']},
    'SN-RE-S-009': {'name': '性欲减退', 'aliases': ['性欲减退', '性欲低下', '性冷淡'], 'classic_refs': ['金匮要略']},
    'SN-RE-O-001': {'name': '经血色暗', 'aliases': ['经血暗', '月经色暗', '经血紫暗'], 'classic_refs': ['金匮要略']},
    'SN-RE-O-002': {'name': '经血有血块', 'aliases': ['经血块', '月经有血块', '血块'], 'classic_refs': ['金匮要略']},
    'SN-RE-C-001': {'name': '月经量少色暗', 'aliases': ['月经少色暗', '经量少色暗'], 'classic_refs': ['金匮要略']},
    
    # 皮肤 (SK)
    'SN-SK-S-001': {'name': '皮肤瘙痒', 'aliases': ['皮肤瘙痒', '皮肤痒', '身痒', '痒疹'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SK-S-002': {'name': '皮肤干燥', 'aliases': ['皮肤干燥', '皮肤干', '肌肤甲错'], 'classic_refs': ['金匮要略']},
    'SN-SK-S-003': {'name': '皮肤油腻', 'aliases': ['皮肤油腻', '面油', '头油', '油脂分泌多'], 'classic_refs': ['内经']},
    'SN-SK-O-001': {'name': '皮肤红斑', 'aliases': ['皮肤红斑', '红斑', '红疹', '疹子'], 'classic_refs': ['伤寒论']},
    'SN-SK-O-002': {'name': '皮肤丘疹', 'aliases': ['皮肤丘疹', '丘疹', '小疙瘩'], 'classic_refs': ['伤寒论']},
    'SN-SK-O-003': {'name': '皮肤水疱', 'aliases': ['皮肤水疱', '水疱', '疱疹', '水泡'], 'classic_refs': ['伤寒论']},
    'SN-SK-O-004': {'name': '皮肤脓疱', 'aliases': ['皮肤脓疱', '脓疱', '化脓'], 'classic_refs': ['金匮要略']},
    'SN-SK-O-005': {'name': '皮肤溃疡', 'aliases': ['皮肤溃疡', '溃疡', '溃烂', '疮疡'], 'classic_refs': ['金匮要略']},
    'SN-SK-O-006': {'name': '皮肤瘢痕', 'aliases': ['皮肤瘢痕', '疤痕', '瘢痕'], 'classic_refs': ['金匮要略']},
    'SN-SK-O-007': {'name': '皮肤脱屑', 'aliases': ['皮肤脱屑', '皮屑', '脱屑', '脱皮'], 'classic_refs': ['金匮要略']},
    'SN-SK-O-008': {'name': '皮肤色素沉着', 'aliases': ['皮肤色素沉着', '色斑', '黑斑', '黄褐斑'], 'classic_refs': ['金匮要略']},
    'SN-SK-O-009': {'name': '皮肤水肿', 'aliases': ['皮肤水肿', '皮肤肿', '浮肿'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SK-O-010': {'name': '皮肤汗出', 'aliases': ['皮肤汗出', '自汗', '盗汗', '汗出'], 'classic_refs': ['伤寒论']},
    'SN-SK-C-001': {'name': '皮肤瘙痒伴红斑', 'aliases': ['皮肤痒红', '瘙痒红斑'], 'classic_refs': ['伤寒论']},
    
    # 五官 (EN)
    'SN-EN-S-001': {'name': '目干涩', 'aliases': ['目干涩', '眼干', '眼睛干涩', '目干'], 'classic_refs': ['金匮要略']},
    'SN-EN-S-002': {'name': '视物模糊', 'aliases': ['视物模糊', '视力模糊', '眼花', '目昏'], 'classic_refs': ['金匮要略']},
    'SN-EN-S-003': {'name': '耳鸣', 'aliases': ['耳鸣', '耳中鸣', '耳内鸣响', '耳聋'], 'classic_refs': ['内经', '金匮要略']},
    'SN-EN-S-004': {'name': '听力下降', 'aliases': ['听力下降', '耳聋', '听力减退', '耳背'], 'classic_refs': ['金匮要略']},
    'SN-EN-S-005': {'name': '鼻塞', 'aliases': ['鼻塞', '鼻堵', '鼻不通', '鼻窒'], 'classic_refs': ['伤寒论']},
    'SN-EN-S-006': {'name': '流涕', 'aliases': ['流涕', '鼻涕', '鼻流清涕', '鼻流浊涕'], 'classic_refs': ['伤寒论']},
    'SN-EN-S-007': {'name': '嗅觉减退', 'aliases': ['嗅觉减退', '闻不到味', '嗅觉失灵'], 'classic_refs': ['金匮要略']},
    'SN-EN-S-008': {'name': '口干', 'aliases': ['口干', '口渴', '咽干', '舌燥', '口中干'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-EN-S-009': {'name': '口苦', 'aliases': ['口苦', '口中有苦味', '嘴里苦'], 'classic_refs': ['伤寒论']},
    'SN-EN-S-010': {'name': '口淡', 'aliases': ['口淡', '口淡无味', '口中淡'], 'classic_refs': ['伤寒论']},
    'SN-EN-S-011': {'name': '口甜', 'aliases': ['口甜', '口中有甜味', '嘴里甜'], 'classic_refs': ['内经']},
    'SN-EN-S-012': {'name': '口黏', 'aliases': ['口黏', '口黏腻', '口中黏'], 'classic_refs': ['金匮要略']},
    'SN-EN-S-013': {'name': '咽痛', 'aliases': ['咽痛', '喉咙痛', '咽喉痛', '嗓子痛', '咽痛'], 'classic_refs': ['伤寒论']},
    'SN-EN-S-014': {'name': '吞咽困难', 'aliases': ['吞咽困难', '咽不下', '吞咽不利'], 'classic_refs': ['金匮要略']},
    'SN-EN-O-001': {'name': '目赤', 'aliases': ['目赤', '眼红', '眼睛红', '白睛红'], 'classic_refs': ['伤寒论']},
    'SN-EN-O-002': {'name': '目黄', 'aliases': ['目黄', '眼黄', '巩膜黄', '黄疸'], 'classic_refs': ['金匮要略']},
    'SN-EN-O-003': {'name': '目陷', 'aliases': ['目陷', '眼窝凹陷', '眼眶深陷'], 'classic_refs': ['金匮要略']},
    'SN-EN-O-004': {'name': '舌苔白', 'aliases': ['舌苔白', '白苔', '苔白'], 'classic_refs': ['伤寒论']},
    'SN-EN-O-005': {'name': '舌苔黄', 'aliases': ['舌苔黄', '黄苔', '苔黄'], 'classic_refs': ['伤寒论']},
    'SN-EN-O-006': {'name': '舌苔腻', 'aliases': ['舌苔腻', '腻苔', '苔腻', '苔厚腻'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-EN-O-007': {'name': '舌苔燥', 'aliases': ['舌苔燥', '燥苔', '苔燥', '苔干'], 'classic_refs': ['伤寒论']},
    'SN-EN-O-008': {'name': '舌红', 'aliases': ['舌红', '舌质红', '舌红绛'], 'classic_refs': ['伤寒论']},
    'SN-EN-O-009': {'name': '舌淡', 'aliases': ['舌淡', '舌质淡', '舌淡白'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-EN-O-010': {'name': '舌紫', 'aliases': ['舌紫', '舌质紫', '舌紫暗', '舌有瘀斑'], 'classic_refs': ['金匮要略']},
    'SN-EN-O-011': {'name': '舌胖大', 'aliases': ['舌胖大', '舌体胖大', '舌胖', '齿痕舌'], 'classic_refs': ['金匮要略']},
    'SN-EN-O-012': {'name': '舌瘦薄', 'aliases': ['舌瘦薄', '舌体瘦', '瘦薄舌'], 'classic_refs': ['金匮要略']},
    'SN-EN-O-013': {'name': '舌裂纹', 'aliases': ['舌裂纹', '舌有裂纹', '裂纹舌'], 'classic_refs': ['金匮要略']},
    'SN-EN-O-014': {'name': '舌震颤', 'aliases': ['舌震颤', '舌体颤动', '舌抖'], 'classic_refs': ['金匮要略']},
    'SN-EN-O-015': {'name': '齿痕舌', 'aliases': ['齿痕舌', '舌边齿痕', '舌有齿印'], 'classic_refs': ['金匮要略']},
    'SN-EN-C-001': {'name': '口干口苦', 'aliases': ['口干口苦', '嘴里干苦'], 'classic_refs': ['伤寒论']},
    'SN-EN-C-002': {'name': '目赤咽痛', 'aliases': ['眼红喉咙痛', '目赤咽痛'], 'classic_refs': ['伤寒论']},
    
    # 体温 (TM)
    'SN-TM-S-001': {'name': '发热', 'aliases': ['发热', '发烧', '身热', '壮热', '高热', '微热', '低热', '潮热'], 'classic_refs': ['伤寒论']},
    'SN-TM-S-002': {'name': '恶寒', 'aliases': ['恶寒', '怕冷', '畏寒', '恶风寒', '怕冷怕风'], 'classic_refs': ['伤寒论']},
    'SN-TM-S-003': {'name': '恶风', 'aliases': ['恶风', '怕风', '畏风', '风吹难受'], 'classic_refs': ['伤寒论']},
    'SN-TM-S-004': {'name': '汗出', 'aliases': ['汗出', '出汗', '自汗', '盗汗', '多汗', '流汗'], 'classic_refs': ['伤寒论']},
    'SN-TM-S-005': {'name': '无汗', 'aliases': ['无汗', '不出汗', '汗不出', '不得汗'], 'classic_refs': ['伤寒论']},
    'SN-TM-S-006': {'name': '手足心热', 'aliases': ['手足心热', '手心热', '脚心热', '五心烦热'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TM-S-007': {'name': '潮热', 'aliases': ['潮热', '午后热', '日晡发热', '定时发热'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-TM-S-008': {'name': '寒热往来', 'aliases': ['寒热往来', '忽冷忽热', '冷热交替', '一阵冷一阵热'], 'classic_refs': ['伤寒论']},
    'SN-TM-S-009': {'name': '但热不寒', 'aliases': ['但热不寒', '只热不冷', '发热不恶寒'], 'classic_refs': ['伤寒论']},
    'SN-TM-S-010': {'name': '但寒不热', 'aliases': ['但寒不热', '只冷不热', '恶寒不发热'], 'classic_refs': ['伤寒论']},
    'SN-TM-S-011': {'name': '身热不扬', 'aliases': ['身热不扬', '身热不热', '身热不扬'], 'classic_refs': ['伤寒论']},
    'SN-TM-O-001': {'name': '体温升高', 'aliases': ['体温升高', '体温高', '量体温高', '体温计显示高'], 'classic_refs': ['伤寒论']},
    'SN-TM-O-002': {'name': '体温降低', 'aliases': ['体温降低', '体温低', '体温低', '四肢冰冷'], 'classic_refs': ['伤寒论']},
    'SN-TM-C-001': {'name': '发热恶寒无汗', 'aliases': ['发烧怕冷不出汗', '发热恶寒无汗'], 'classic_refs': ['伤寒论']},
    'SN-TM-C-002': {'name': '发热汗出恶风', 'aliases': ['发烧出汗怕风', '发热汗出恶风'], 'classic_refs': ['伤寒论']},
    'SN-TM-C-003': {'name': '发热口渴汗出', 'aliases': ['发烧口渴出汗', '发热口渴汗出'], 'classic_refs': ['伤寒论']},
    'SN-TM-C-004': {'name': '恶寒发热体痛', 'aliases': ['怕冷发烧身体疼', '恶寒发热体痛'], 'classic_refs': ['伤寒论']},
    
    # 睡眠 (SL)
    'SN-SL-S-001': {'name': '失眠', 'aliases': ['失眠', '不寐', '不得眠', '目不瞑', '睡不着', '难入睡', '入睡困难'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SL-S-002': {'name': '多梦', 'aliases': ['多梦', '梦多', '睡眠不安', '易醒', '夜梦多'], 'classic_refs': ['内经', '金匮要略']},
    'SN-SL-S-003': {'name': '易醒', 'aliases': ['易醒', '睡眠浅', '醒后难入睡', '早醒'], 'classic_refs': ['金匮要略']},
    'SN-SL-S-004': {'name': '嗜睡', 'aliases': ['嗜睡', '困倦', '昏昏欲睡', '多眠', '睡不醒'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SL-S-005': {'name': '虚烦不得眠', 'aliases': ['虚烦失眠', '心烦睡不着', '虚烦不得眠'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SL-S-006': {'name': '梦魇', 'aliases': ['梦魇', '噩梦', '梦中惊醒', '夜惊'], 'classic_refs': ['金匮要略']},
    'SN-SL-S-007': {'name': '梦游', 'aliases': ['梦游', '睡中行走', '夜行'], 'classic_refs': ['金匮要略']},
    'SN-SL-O-001': {'name': '睡眠时间减少', 'aliases': ['睡眠少', '睡眠时间不足', '睡眠时间短'], 'classic_refs': ['金匮要略']},
    'SN-SL-O-002': {'name': '睡眠时间增多', 'aliases': ['睡眠多', '睡眠时间过长', '嗜睡多眠'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SL-C-001': {'name': '失眠伴心烦', 'aliases': ['失眠心烦', '睡不着心烦'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SL-C-002': {'name': '失眠伴口干', 'aliases': ['失眠口干', '睡不着口干'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SL-C-003': {'name': '失眠伴心悸', 'aliases': ['失眠心悸', '睡不着心慌'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-SL-C-004': {'name': '嗜睡伴乏力', 'aliases': ['嗜睡乏力', '困乏无力'], 'classic_refs': ['伤寒论', '金匮要略']},
    
    # 其他 (OT)
    'SN-OT-S-001': {'name': '体重下降', 'aliases': ['体重下降', '消瘦', '体重减轻', '体重降低'], 'classic_refs': ['金匮要略']},
    'SN-OT-S-002': {'name': '体重增加', 'aliases': ['体重增加', '发胖', '体重上升', '肥胖'], 'classic_refs': ['内经']},
    'SN-OT-S-003': {'name': '水肿', 'aliases': ['水肿', '浮肿', '肿胀', '肿'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-OT-S-004': {'name': '出血', 'aliases': ['出血', '流血', '衄血', '吐血', '便血', '尿血', '崩漏'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-OT-S-005': {'name': '瘀血', 'aliases': ['瘀血', '血瘀', '血滞', '血凝'], 'classic_refs': ['金匮要略']},
    'SN-OT-S-006': {'name': '痰多', 'aliases': ['痰多', '痰饮', '痰湿', '痰浊'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-OT-S-007': {'name': '气滞', 'aliases': ['气滞', '气郁', '气机不畅', '胸闷气短'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-OT-S-008': {'name': '气虚', 'aliases': ['气虚', '气不足', '少气', '乏力', '倦怠'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-OT-S-009': {'name': '血虚', 'aliases': ['血虚', '血不足', '面色无华', '唇甲色淡'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-OT-S-010': {'name': '阴虚', 'aliases': ['阴虚', '阴不足', '口干咽燥', '五心烦热'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-OT-S-011': {'name': '阳虚', 'aliases': ['阳虚', '阳不足', '畏寒肢冷', '面色苍白'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-OT-S-012': {'name': '津液不足', 'aliases': ['津液不足', '津液亏虚', '口干咽燥', '皮肤干燥'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-OT-S-013': {'name': '精亏', 'aliases': ['精亏', '肾精不足', '精髓亏虚', '腰膝酸软'], 'classic_refs': ['内经', '金匮要略']},
    'SN-OT-S-014': {'name': '神疲乏力', 'aliases': ['神疲乏力', '精神疲惫', '神疲', '乏力倦怠'], 'classic_refs': ['金匮要略']},
    'SN-OT-S-015': {'name': '少气懒言', 'aliases': ['少气懒言', '气短懒言', '言语低微'], 'classic_refs': ['金匮要略']},
    'SN-OT-S-016': {'name': '自汗', 'aliases': ['自汗', '白天出汗', '动辄汗出'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-OT-S-017': {'name': '盗汗', 'aliases': ['盗汗', '夜间出汗', '睡中汗出', '醒后汗止'], 'classic_refs': ['伤寒论', '金匮要略']},
    'SN-OT-S-018': {'name': '战汗', 'aliases': ['战汗', '先战栗后汗出', '寒战后出汗'], 'classic_refs': ['伤寒论']},
    'SN-OT-S-019': {'name': '绝汗', 'aliases': ['绝汗', '脱汗', '大汗不止', '汗出如油'], 'classic_refs': ['伤寒论']},
    'SN-OT-S-020': {'name': '黄汗', 'aliases': ['黄汗', '汗出沾衣色黄', '汗出色黄'], 'classic_refs': ['金匮要略']},
}


def find_symptoms_by_text(text: str) -> list:
    """
    从用户输入文本中识别症状编号
    返回匹配的症状列表
    """
    text = text.lower()
    matched = []
    seen_ids = set()
    
    for symptom_id, info in SYMPTOM_MAP.items():
        if symptom_id in seen_ids:
            continue
        for alias in info['aliases']:
            if alias in text:
                matched.append({
                    'id': symptom_id,
                    'name': info['name'],
                    'part': BODY_PARTS.get(symptom_id.split('-')[1], '未知'),
                    'category': CATEGORY_CODES.get(symptom_id.split('-')[2], '未知'),
                    'classic_refs': info['classic_refs']
                })
                seen_ids.add(symptom_id)
                break
    
    return matched


def get_symptom_by_id(symptom_id: str) -> dict:
    """根据ID获取症状信息"""
    info = SYMPTOM_MAP.get(symptom_id)
    if not info:
        return None
    return {
        'id': symptom_id,
        'name': info['name'],
        'part': BODY_PARTS.get(symptom_id.split('-')[1], '未知'),
        'category': CATEGORY_CODES.get(symptom_id.split('-')[2], '未知'),
        'aliases': info['aliases'],
        'classic_refs': info['classic_refs']
    }


def get_symptoms_by_part(part_code: str) -> list:
    """根据部位代码获取症状列表"""
    results = []
    for symptom_id, info in SYMPTOM_MAP.items():
        if symptom_id.split('-')[1] == part_code:
            results.append({
                'id': symptom_id,
                'name': info['name'],
                'aliases': info['aliases']
            })
    return results


def format_symptom_list(symptoms: list) -> str:
    """格式化症状列表为可读文本"""
    if not symptoms:
        return "未识别到症状"
    
    lines = []
    for s in symptoms:
        lines.append(f"  • {s['name']} [{s['id']}] ({s['part']}/{s['category']})")
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    test_inputs = [
        "我最近头痛发热，怕冷，没有汗",
        "失眠多梦，口干舌燥，手心发热",
        "腹胀腹泻，食欲不振，乏力",
        "咳嗽，咽痛，发热",
        "腰痛，关节痛，乏力",
    ]
    
    for text in test_inputs:
        print(f"\n输入: {text}")
        symptoms = find_symptoms_by_text(text)
        print(f"识别到 {len(symptoms)} 个症状:")
        print(format_symptom_list(symptoms))
