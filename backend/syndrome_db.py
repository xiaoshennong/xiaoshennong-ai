#!/usr/bin/env python3
"""
小神农中医AI - 证型数据库（SY编码体系）
编码格式：SY-体系-序号
"""

from code_system import SYNDROME_SYSTEM_CODES

# 证型数据库
SYNDROME_DATABASE = {
    # 太阳病 (TY)
    'SY-TY-001': {
        'name': '太阳中风',
        'system': '六经辨证',
        'system_code': 'TY',
        'key_symptoms': ['SN-SP-S-003', 'SN-SP-S-002', 'SN-SP-S-004', 'SN-CV-O-001'],
        'key_signs': {
            'pulse': '浮缓',
            'tongue': '舌苔薄白',
        },
        'pathogenesis': '风邪袭表，卫强营弱，营卫失调',
        'treatment_principle': '解肌发表，调和营卫',
        'main_formula': {'formula_id': 'FP-TY-001', 'formula_name': '桂枝汤'},
        'variations': [
            {'condition': '兼项背强几几', 'modified_formula': 'FP-TY-003', 'formula_name': '桂枝加葛根汤'},
            {'condition': '兼喘', 'modified_formula': 'FP-HX-001', 'formula_name': '桂枝加厚朴杏子汤'},
            {'condition': '兼阳虚', 'modified_formula': 'FP-TY-005', 'formula_name': '桂枝加附子汤'},
        ],
        'contraindications': {
            'pulse_float_tight': '脉浮紧无汗者禁用（表实，非中风）',
            'alcoholics': '酒客不喜甘者禁用',
        },
        'differentiation': [
            '与太阳伤寒鉴别：伤寒无汗脉紧，中风汗出脉缓',
            '与风热表证鉴别：风热有咽痛口渴，中风无',
        ],
        'severity': '轻',
        'source': '伤寒论',
    },
    'SY-TY-002': {
        'name': '太阳伤寒',
        'system': '六经辨证',
        'system_code': 'TY',
        'key_symptoms': ['SN-SP-S-001', 'SN-SP-S-003', 'SN-SP-S-005', 'SN-HD-S-001', 'SN-HD-S-003'],
        'key_signs': {
            'pulse': '浮紧',
            'tongue': '舌苔薄白',
        },
        'pathogenesis': '寒邪束表，卫阳被郁，营阴凝滞',
        'treatment_principle': '发汗解表，宣肺平喘',
        'main_formula': {'formula_id': 'FP-TY-002', 'formula_name': '麻黄汤'},
        'variations': [
            {'condition': '兼烦躁', 'modified_formula': 'FP-TY-006', 'formula_name': '大青龙汤'},
            {'condition': '兼项背强几几', 'modified_formula': 'FP-TY-007', 'formula_name': '葛根汤'},
        ],
        'contraindications': {
            'sweating': '有汗者禁用（表虚，非伤寒）',
            'weak_pulse': '尺中脉迟者禁用（荣气不足）',
            'special_groups': '疮家、淋家、衄家、亡血家、汗家禁用',
        },
        'differentiation': [
            '与太阳中风鉴别：中风汗出脉缓，伤寒无汗脉紧',
            '与温病鉴别：温病发热重恶寒轻，口渴咽痛',
        ],
        'severity': '轻-中',
        'source': '伤寒论',
    },
    'SY-TY-003': {
        'name': '太阳蓄水',
        'system': '六经辨证',
        'system_code': 'TY',
        'key_symptoms': ['SN-SP-S-003', 'SN-UR-S-001', 'SN-SP-S-002', 'SN-DG-S-001'],
        'key_signs': {
            'pulse': '浮',
            'tongue': '舌苔白',
        },
        'pathogenesis': '太阳表邪未解，邪热入里，与水互结于膀胱',
        'treatment_principle': '化气行水，兼以解表',
        'main_formula': {'formula_id': 'FP-TY-008', 'formula_name': '五苓散'},
        'variations': [],
        'contraindications': {
            'yin_deficiency': '阴虚津亏者慎用',
        },
        'differentiation': [
            '与太阳蓄血鉴别：蓄水小便不利，蓄血小便自利',
        ],
        'severity': '中',
        'source': '伤寒论',
    },
    
    # 阳明病 (YM)
    'SY-YM-001': {
        'name': '阳明经证',
        'system': '六经辨证',
        'system_code': 'YM',
        'key_symptoms': ['SN-SP-S-003', 'SN-EN-S-008', 'SN-SP-S-002', 'SN-SL-S-001'],
        'key_signs': {
            'pulse': '洪大',
            'tongue': '舌红苔黄',
        },
        'pathogenesis': '邪热入里，充斥阳明，里热炽盛',
        'treatment_principle': '清热生津',
        'main_formula': {'formula_id': 'FP-YM-001', 'formula_name': '白虎汤'},
        'variations': [
            {'condition': '兼气阴两伤', 'modified_formula': 'FP-YM-002', 'formula_name': '白虎加人参汤'},
        ],
        'contraindications': {
            'surface_syndrome': '表证未解者禁用',
            'false_cold': '真寒假热者禁用',
            'blood_deficiency': '血虚发热者禁用',
        },
        'differentiation': [
            '与阳明腑证鉴别：经证无燥屎，腑证有燥屎',
            '与少阳证鉴别：少阳寒热往来，阳明但热不寒',
        ],
        'severity': '中-重',
        'source': '伤寒论',
    },
    'SY-YM-002': {
        'name': '阳明腑证',
        'system': '六经辨证',
        'system_code': 'YM',
        'key_symptoms': ['SN-TH-S-009', 'SN-TH-S-001', 'SN-TH-S-005', 'SN-DG-S-002'],
        'key_signs': {
            'pulse': '沉实',
            'tongue': '舌红苔黄燥/黑燥',
        },
        'pathogenesis': '邪热入里，与肠中糟粕相结，燥屎内结',
        'treatment_principle': '峻下热结',
        'main_formula': {'formula_id': 'FP-YM-003', 'formula_name': '大承气汤'},
        'variations': [
            {'condition': '痞满实而燥结不甚', 'modified_formula': 'FP-YM-004', 'formula_name': '小承气汤'},
            {'condition': '燥结而痞满不甚', 'modified_formula': 'FP-YM-005', 'formula_name': '调胃承气汤'},
        ],
        'contraindications': {
            'surface_syndrome': '表证未解者禁用',
            'fluid_depletion': '津液亏耗者禁用',
            'pregnant': '孕妇禁用',
            'elderly_weak': '年老体虚者禁用',
        },
        'differentiation': [
            '与阳明经证鉴别：腑证有燥屎，腹满痛拒按',
        ],
        'severity': '重',
        'source': '伤寒论',
    },
    
    # 少阳病 (SY)
    'SY-SY-001': {
        'name': '少阳病',
        'system': '六经辨证',
        'system_code': 'SY',
        'key_symptoms': ['SN-SP-S-013', 'SN-TH-S-001', 'SN-HD-O-012', 'SN-SL-S-001', 'SN-EN-S-008', 'SN-EN-S-008'],
        'key_signs': {
            'pulse': '弦',
            'tongue': '舌苔薄白或薄黄',
        },
        'pathogenesis': '邪犯少阳，正邪分争，枢机不利',
        'treatment_principle': '和解少阳',
        'main_formula': {'formula_id': 'FP-SY-001', 'formula_name': '小柴胡汤'},
        'variations': [
            {'condition': '兼大便秘结', 'modified_formula': 'FP-SY-002', 'formula_name': '大柴胡汤'},
        ],
        'contraindications': {
            'pure_surface': '纯表证者不宜',
            'pure_interior': '纯里证者不宜',
            'yin_deficiency': '阴虚血少者慎用',
        },
        'differentiation': [
            '与太阳病鉴别：太阳病恶寒明显，少阳寒热往来',
            '与阳明病鉴别：阳明病但热不寒，少阳寒热往来',
        ],
        'severity': '中',
        'source': '伤寒论',
    },
    
    # 太阴病 (TY2)
    'SY-TY2-001': {
        'name': '太阴病',
        'system': '六经辨证',
        'system_code': 'TY2',
        'key_symptoms': ['SN-DG-S-001', 'SN-TH-S-009', 'SN-TH-S-001', 'SN-SP-S-001'],
        'key_signs': {
            'pulse': '沉迟',
            'tongue': '舌淡苔白',
        },
        'pathogenesis': '脾阳虚弱，寒湿内盛',
        'treatment_principle': '温中散寒，健脾燥湿',
        'main_formula': {'formula_id': 'FP-TY2-001', 'formula_name': '理中丸'},
        'variations': [
            {'condition': '兼表证', 'modified_formula': 'FP-TY2-002', 'formula_name': '桂枝人参汤'},
        ],
        'contraindications': {
            'heat_syndrome': '热证禁用',
            'damp_heat': '湿热禁用',
        },
        'differentiation': [
            '与阳明腑证鉴别：太阴腹满时痛，阳明腹满痛拒按',
        ],
        'severity': '中',
        'source': '伤寒论',
    },
    
    # 少阴病 (SY2)
    'SY-SY2-001': {
        'name': '少阴寒化证',
        'system': '六经辨证',
        'system_code': 'SY2',
        'key_symptoms': ['SN-SP-S-001', 'SN-LM-S-006', 'SN-SP-S-010', 'SN-DG-S-001'],
        'key_signs': {
            'pulse': '微细',
            'tongue': '舌淡苔白',
        },
        'pathogenesis': '心肾阳衰，阴寒内盛',
        'treatment_principle': '回阳救逆',
        'main_formula': {'formula_id': 'FP-SY2-001', 'formula_name': '四逆汤'},
        'variations': [
            {'condition': '兼气阴两伤', 'modified_formula': 'FP-SY2-002', 'formula_name': '四逆加人参汤'},
            {'condition': '阴盛格阳', 'modified_formula': 'FP-SY2-003', 'formula_name': '通脉四逆汤'},
        ],
        'contraindications': {
            'heat_syndrome': '热证禁用',
            'yang_hyperactivity': '阴虚阳亢禁用',
        },
        'differentiation': [
            '与少阴热化证鉴别：寒化肢冷脉微，热化心烦不眠',
        ],
        'severity': '危重',
        'source': '伤寒论',
    },
    'SY-SY2-002': {
        'name': '少阴热化证',
        'system': '六经辨证',
        'system_code': 'SY2',
        'key_symptoms': ['SN-SL-S-001', 'SN-PS-S-001', 'SN-EN-S-008', 'SN-SP-S-003'],
        'key_signs': {
            'pulse': '细数',
            'tongue': '舌红少苔',
        },
        'pathogenesis': '肾阴不足，心火偏亢',
        'treatment_principle': '滋阴降火',
        'main_formula': {'formula_id': 'FP-SY2-004', 'formula_name': '黄连阿胶汤'},
        'variations': [],
        'contraindications': {
            'spleen_stomach_deficiency': '脾胃虚寒者慎用',
            'phlegm_damp': '痰湿内盛者慎用',
        },
        'differentiation': [
            '与少阴寒化证鉴别：热化心烦不眠，寒化肢冷脉微',
        ],
        'severity': '中',
        'source': '伤寒论',
    },
    
    # 厥阴病 (JY)
    'SY-JY-001': {
        'name': '厥阴病',
        'system': '六经辨证',
        'system_code': 'JY',
        'key_symptoms': ['SN-SP-S-013', 'SN-DG-S-001', 'SN-TH-S-001', 'SN-DG-S-001'],
        'key_signs': {
            'pulse': '弦',
            'tongue': '舌苔白或黄',
        },
        'pathogenesis': '阴阳交争，寒热错杂',
        'treatment_principle': '清上温下，和胃降逆',
        'main_formula': {'formula_id': 'FP-JY-001', 'formula_name': '乌梅丸'},
        'variations': [],
        'contraindications': {
            'pure_heat': '纯热证禁用',
            'pure_cold': '纯寒证禁用',
        },
        'differentiation': [
            '与少阳病鉴别：少阳寒热往来，厥阴上热下寒',
        ],
        'severity': '重',
        'source': '伤寒论',
    },
    
    # 气血津液 (QB)
    'SY-QB-001': {
        'name': '气虚证',
        'system': '气血津液辨证',
        'system_code': 'QB',
        'key_symptoms': ['SN-SP-S-010', 'SN-SP-S-006', 'SN-SP-S-007', 'SN-TH-S-012'],
        'key_signs': {
            'pulse': '弱',
            'tongue': '舌淡苔白',
        },
        'pathogenesis': '元气不足，脏腑功能减退',
        'treatment_principle': '益气健脾',
        'main_formula': {'formula_id': 'FP-QB-001', 'formula_name': '四君子汤'},
        'variations': [
            {'condition': '兼血虚', 'modified_formula': 'FP-QB-002', 'formula_name': '八珍汤'},
        ],
        'contraindications': {
            'excess_heat': '实热证禁用',
            'qi_stagnation': '气滞证慎用',
        },
        'severity': '轻-中',
        'source': '中医基础理论',
    },
    'SY-QB-002': {
        'name': '血虚证',
        'system': '气血津液辨证',
        'system_code': 'QB',
        'key_symptoms': ['SN-HD-S-002', 'SN-HD-S-004', 'SN-SP-S-010', 'SN-PS-S-004'],
        'key_signs': {
            'pulse': '细',
            'tongue': '舌淡白',
        },
        'pathogenesis': '血液亏虚，脏腑失养',
        'treatment_principle': '补血养血',
        'main_formula': {'formula_id': 'FP-QB-003', 'formula_name': '四物汤'},
        'variations': [
            {'condition': '兼气虚', 'modified_formula': 'FP-QB-002', 'formula_name': '八珍汤'},
        ],
        'contraindications': {
            'blood_stasis': '血瘀证慎用',
            'dampness': '湿盛中满者慎用',
        },
        'severity': '轻-中',
        'source': '中医基础理论',
    },
    'SY-QB-003': {
        'name': '阴虚证',
        'system': '气血津液辨证',
        'system_code': 'QB',
        'key_symptoms': ['SN-SP-S-003', 'SN-EN-S-008', 'SN-SL-S-001', 'SN-LM-S-001'],
        'key_signs': {
            'pulse': '细数',
            'tongue': '舌红少苔',
        },
        'pathogenesis': '阴液不足，虚热内生',
        'treatment_principle': '滋阴清热',
        'main_formula': {'formula_id': 'FP-QB-004', 'formula_name': '六味地黄丸'},
        'variations': [
            {'condition': '兼火旺', 'modified_formula': 'FP-QB-005', 'formula_name': '知柏地黄丸'},
        ],
        'contraindications': {
            'spleen_deficiency': '脾虚便溏者慎用',
            'yang_deficiency': '阳虚者禁用',
        },
        'severity': '中',
        'source': '中医基础理论',
    },
    'SY-QB-004': {
        'name': '阳虚证',
        'system': '气血津液辨证',
        'system_code': 'QB',
        'key_symptoms': ['SN-SP-S-001', 'SN-LM-S-006', 'SN-SP-S-010', 'SN-DG-S-001'],
        'key_signs': {
            'pulse': '沉迟',
            'tongue': '舌淡胖苔白',
        },
        'pathogenesis': '阳气不足，温煦功能减退',
        'treatment_principle': '温阳补肾',
        'main_formula': {'formula_id': 'FP-QB-006', 'formula_name': '金匮肾气丸'},
        'variations': [],
        'contraindications': {
            'heat_syndrome': '热证禁用',
            'yin_deficiency': '阴虚者禁用',
        },
        'severity': '中',
        'source': '中医基础理论',
    },
    'SY-QB-005': {
        'name': '痰湿证',
        'system': '气血津液辨证',
        'system_code': 'QB',
        'key_symptoms': ['SN-SP-S-010', 'SN-TH-S-005', 'SN-TH-S-012', 'SN-EN-S-013'],
        'key_signs': {
            'pulse': '滑',
            'tongue': '舌胖苔腻',
        },
        'pathogenesis': '脾失健运，水湿内停，聚湿成痰',
        'treatment_principle': '健脾燥湿，化痰理气',
        'main_formula': {'formula_id': 'FP-QB-007', 'formula_name': '二陈汤'},
        'variations': [
            {'condition': '兼热', 'modified_formula': 'FP-QB-008', 'formula_name': '温胆汤'},
        ],
        'contraindications': {
            'fluid_depletion': '津液亏虚者慎用',
            'dryness': '燥证慎用',
        },
        'severity': '中',
        'source': '中医基础理论',
    },
    'SY-QB-006': {
        'name': '血瘀证',
        'system': '气血津液辨证',
        'system_code': 'QB',
        'key_symptoms': ['SN-SP-C-003', 'SN-HD-S-001', 'SN-TH-S-001', 'SN-SK-S-001'],
        'key_signs': {
            'pulse': '涩',
            'tongue': '舌紫暗或有瘀斑',
        },
        'pathogenesis': '血行不畅，瘀阻脉络',
        'treatment_principle': '活血化瘀',
        'main_formula': {'formula_id': 'FP-QB-009', 'formula_name': '血府逐瘀汤'},
        'variations': [],
        'contraindications': {
            'bleeding': '出血倾向者慎用',
            'pregnant': '孕妇禁用',
        },
        'severity': '中',
        'source': '中医基础理论',
    },
    'SY-QB-007': {
        'name': '湿热证',
        'system': '气血津液辨证',
        'system_code': 'QB',
        'key_symptoms': ['SN-SP-S-003', 'SN-TH-S-005', 'SN-TH-S-012', 'SN-EN-S-013', 'SN-SK-S-002'],
        'key_signs': {
            'pulse': '滑数',
            'tongue': '舌红苔黄腻',
        },
        'pathogenesis': '湿热蕴结，气机不畅',
        'treatment_principle': '清热利湿',
        'main_formula': {'formula_id': 'FP-QB-010', 'formula_name': '三仁汤'},
        'variations': [
            {'condition': '肝胆湿热', 'modified_formula': 'FP-QB-011', 'formula_name': '龙胆泻肝汤'},
        ],
        'contraindications': {
            'spleen_deficiency': '脾胃虚寒者慎用',
            'yin_deficiency': '阴虚者慎用',
        },
        'severity': '中',
        'source': '中医基础理论',
    },
    
    # 脏腑辨证 - 心 (YN)
    'SY-YN-001': {
        'name': '心阴虚',
        'system': '脏腑辨证',
        'system_code': 'YN',
        'key_symptoms': ['SN-PS-S-001', 'SN-SL-S-001', 'SN-EN-S-008', 'SN-CV-S-001'],
        'key_signs': {
            'pulse': '细数',
            'tongue': '舌红少苔',
        },
        'pathogenesis': '心阴不足，虚热内扰',
        'treatment_principle': '滋阴养心，清热安神',
        'main_formula': {'formula_id': 'FP-SJ-001', 'formula_name': '酸枣仁汤'},
        'variations': [
            {'condition': '兼火旺', 'modified_formula': 'FP-SY2-004', 'formula_name': '黄连阿胶汤'},
        ],
        'contraindications': {
            'spleen_stomach_deficiency': '脾胃虚寒者慎用',
        },
        'differentiation': [
            '与心气虚鉴别：气虚乏力自汗，阴虚口干烦热',
        ],
        'severity': '中',
        'source': '中医基础理论',
    },
    'SY-YN-002': {
        'name': '心阳虚',
        'system': '脏腑辨证',
        'system_code': 'YN',
        'key_symptoms': ['SN-CV-S-001', 'SN-SP-S-001', 'SN-SP-S-010', 'SN-LM-S-006'],
        'key_signs': {
            'pulse': '微弱',
            'tongue': '舌淡胖',
        },
        'pathogenesis': '心阳不足，温运无力',
        'treatment_principle': '温补心阳',
        'main_formula': {'formula_id': 'FP-XH-001', 'formula_name': '桂枝甘草汤'},
        'variations': [],
        'contraindications': {
            'heat_syndrome': '热证禁用',
        },
        'severity': '中-重',
        'source': '中医基础理论',
    },
    
    # 脏腑辨证 - 肝 (YG)
    'SY-YG-001': {
        'name': '肝郁气滞',
        'system': '脏腑辨证',
        'system_code': 'YG',
        'key_symptoms': ['SN-TH-S-007', 'SN-PS-S-001', 'SN-SL-S-001', 'SN-DG-S-002'],
        'key_signs': {
            'pulse': '弦',
            'tongue': '舌苔薄白',
        },
        'pathogenesis': '情志不遂，肝气郁结，气机不畅',
        'treatment_principle': '疏肝理气',
        'main_formula': {'formula_id': 'FP-YG-001', 'formula_name': '柴胡疏肝散'},
        'variations': [],
        'contraindications': {
            'yin_deficiency': '阴虚火旺者慎用',
        },
        'severity': '轻-中',
        'source': '中医基础理论',
    },
    'SY-YG-002': {
        'name': '肝阳上亢',
        'system': '脏腑辨证',
        'system_code': 'YG',
        'key_symptoms': ['SN-HD-S-001', 'SN-HD-S-002', 'SN-HD-O-006', 'SN-PS-S-001'],
        'key_signs': {
            'pulse': '弦有力',
            'tongue': '舌红',
        },
        'pathogenesis': '肝肾阴虚，肝阳上亢',
        'treatment_principle': '平肝潜阳',
        'main_formula': {'formula_id': 'FP-YG-002', 'formula_name': '天麻钩藤饮'},
        'variations': [],
        'contraindications': {
            'yang_deficiency': '阳虚者禁用',
        },
        'severity': '中',
        'source': '中医基础理论',
    },
    
    # 脏腑辨证 - 脾 (YN)
    'SY-YN-003': {
        'name': '脾虚湿困',
        'system': '脏腑辨证',
        'system_code': 'YN',
        'key_symptoms': ['SN-TH-S-012', 'SN-TH-S-005', 'SN-SP-S-010', 'SN-DG-S-001'],
        'key_signs': {
            'pulse': '濡',
            'tongue': '舌淡胖苔白腻',
        },
        'pathogenesis': '脾失健运，水湿内停',
        'treatment_principle': '健脾利湿',
        'main_formula': {'formula_id': 'FP-YN-001', 'formula_name': '参苓白术散'},
        'variations': [],
        'contraindications': {
            'fluid_depletion': '津液亏虚者慎用',
        },
        'severity': '中',
        'source': '中医基础理论',
    },
    
    # 脏腑辨证 - 肾 (YN)
    'SY-YN-004': {
        'name': '肾阴虚',
        'system': '脏腑辨证',
        'system_code': 'YN',
        'key_symptoms': ['SN-BK-S-001', 'SN-UR-S-001', 'SN-SL-S-001', 'SN-SP-S-003'],
        'key_signs': {
            'pulse': '细数',
            'tongue': '舌红少苔',
        },
        'pathogenesis': '肾阴不足，虚热内生',
        'treatment_principle': '滋补肾阴',
        'main_formula': {'formula_id': 'FP-QB-004', 'formula_name': '六味地黄丸'},
        'variations': [
            {'condition': '兼火旺', 'modified_formula': 'FP-QB-005', 'formula_name': '知柏地黄丸'},
            {'condition': '兼肝阴虚', 'modified_formula': 'FP-YN-002', 'formula_name': '杞菊地黄丸'},
        ],
        'contraindications': {
            'spleen_deficiency': '脾虚便溏者慎用',
        },
        'severity': '中',
        'source': '中医基础理论',
    },
    'SY-YN-005': {
        'name': '肾阳虚',
        'system': '脏腑辨证',
        'system_code': 'YN',
        'key_symptoms': ['SN-BK-S-001', 'SN-SP-S-001', 'SN-UR-S-002', 'SN-LM-S-006'],
        'key_signs': {
            'pulse': '沉迟',
            'tongue': '舌淡胖苔白',
        },
        'pathogenesis': '肾阳不足，温煦功能减退',
        'treatment_principle': '温补肾阳',
        'main_formula': {'formula_id': 'FP-QB-006', 'formula_name': '金匮肾气丸'},
        'variations': [],
        'contraindications': {
            'heat_syndrome': '热证禁用',
            'yin_deficiency': '阴虚者禁用',
        },
        'severity': '中',
        'source': '中医基础理论',
    },
    
    # 卫气营血 (WS)
    'SY-WS-001': {
        'name': '卫分证',
        'system': '卫气营血辨证',
        'system_code': 'WS',
        'key_symptoms': ['SN-SP-S-003', 'SN-SP-S-001', 'SN-EN-S-008', 'SN-HD-S-001'],
        'key_signs': {
            'pulse': '浮数',
            'tongue': '舌边尖红，苔薄白',
        },
        'pathogenesis': '温邪犯表，卫气失和',
        'treatment_principle': '辛凉解表',
        'main_formula': {'formula_id': 'FP-WS-001', 'formula_name': '银翘散'},
        'variations': [],
        'contraindications': {
            'cold_syndrome': '风寒表证禁用',
        },
        'severity': '轻',
        'source': '温病条辨',
    },
    'SY-WS-002': {
        'name': '气分证',
        'system': '卫气营血辨证',
        'system_code': 'WS',
        'key_symptoms': ['SN-SP-S-003', 'SN-EN-S-008', 'SN-TH-S-001', 'SN-DG-S-001'],
        'key_signs': {
            'pulse': '洪大',
            'tongue': '舌红苔黄',
        },
        'pathogenesis': '邪热入里，正邪剧争',
        'treatment_principle': '清气泄热',
        'main_formula': {'formula_id': 'FP-YM-001', 'formula_name': '白虎汤'},
        'variations': [],
        'contraindications': {
            'surface_syndrome': '表证未解者慎用',
        },
        'severity': '中',
        'source': '温病条辨',
    },
    'SY-WS-003': {
        'name': '营分证',
        'system': '卫气营血辨证',
        'system_code': 'WS',
        'key_symptoms': ['SN-SP-S-003', 'SN-SL-S-001', 'SN-PS-S-010', 'SN-SK-S-001'],
        'key_signs': {
            'pulse': '细数',
            'tongue': '舌红绛',
        },
        'pathogenesis': '邪热入营，营阴受损',
        'treatment_principle': '清营透热',
        'main_formula': {'formula_id': 'FP-WS-002', 'formula_name': '清营汤'},
        'variations': [],
        'contraindications': {
            'qi_deficiency': '气虚者慎用',
        },
        'severity': '重',
        'source': '温病条辨',
    },
    'SY-WS-004': {
        'name': '血分证',
        'system': '卫气营血辨证',
        'system_code': 'WS',
        'key_symptoms': ['SN-SP-S-003', 'SN-PS-S-010', 'SN-SK-S-001', 'SN-SP-O-004'],
        'key_signs': {
            'pulse': '细数或弦数',
            'tongue': '舌深绛或紫暗',
        },
        'pathogenesis': '邪热入血，耗血动血',
        'treatment_principle': '凉血散血',
        'main_formula': {'formula_id': 'FP-WS-003', 'formula_name': '犀角地黄汤'},
        'variations': [],
        'contraindications': {
            'spleen_deficiency': '脾虚者慎用',
        },
        'severity': '危重',
        'source': '温病条辨',
    },
}


def get_syndrome_by_id(syndrome_id: str) -> dict:
    """根据ID获取证型信息"""
    syndrome = SYNDROME_DATABASE.get(syndrome_id)
    if not syndrome:
        return None
    return {
        'id': syndrome_id,
        'name': syndrome['name'],
        'system': syndrome['system'],
        'system_code': syndrome['system_code'],
        'key_symptoms': syndrome['key_symptoms'],
        'key_signs': syndrome['key_signs'],
        'pathogenesis': syndrome['pathogenesis'],
        'treatment_principle': syndrome['treatment_principle'],
        'main_formula': syndrome['main_formula'],
        'variations': syndrome['variations'],
        'contraindications': syndrome['contraindications'],
        'differentiation': syndrome.get('differentiation', []),
        'severity': syndrome['severity'],
        'source': syndrome['source'],
    }


def find_syndromes_by_symptoms(symptom_ids: list) -> list:
    """根据症状ID列表查找匹配的证型"""
    matched = []
    for syndrome_id, syndrome in SYNDROME_DATABASE.items():
        key_symptoms = set(syndrome['key_symptoms'])
        matched_symptoms = [sid for sid in symptom_ids if sid in key_symptoms]
        if matched_symptoms:
            matched.append({
                'id': syndrome_id,
                'name': syndrome['name'],
                'system': syndrome['system'],
                'matched_symptoms': matched_symptoms,
                'match_score': len(matched_symptoms) / len(key_symptoms),
                'severity': syndrome['severity'],
                'main_formula': syndrome['main_formula'],
            })
    
    matched.sort(key=lambda x: x['match_score'], reverse=True)
    return matched


def find_syndromes_by_system(system_code: str) -> list:
    """根据体系代码查找证型"""
    return [
        {'id': sid, 'name': s['name'], 'severity': s['severity']}
        for sid, s in SYNDROME_DATABASE.items()
        if s['system_code'] == system_code
    ]


if __name__ == "__main__":
    # 测试
    print("=== 证型数据库测试 ===")
    print(f"总证型数: {len(SYNDROME_DATABASE)}")
    
    # 测试查询
    syndrome = get_syndrome_by_id('SY-TY-001')
    print(f"\n太阳中风: {syndrome['name']}")
    print(f"  主方: {syndrome['main_formula']['formula_name']}")
    print(f"  治则: {syndrome['treatment_principle']}")
    
    # 测试症状匹配
    print("\n=== 症状匹配测试 ===")
    symptoms = ['SN-SP-S-001', 'SN-SP-S-003', 'SN-SP-S-005', 'SN-HD-S-001']
    matched = find_syndromes_by_symptoms(symptoms)
    print(f"症状: 恶寒+发热+无汗+头痛")
    for m in matched[:5]:
        print(f"  {m['name']} [{m['id']}] - 匹配度: {m['match_score']:.2f}")
    
    # 测试体系查询
    print("\n=== 六经辨证证型 ===")
    six_jing = find_syndromes_by_system('TY') + find_syndromes_by_system('YM') + \
               find_syndromes_by_system('SY') + find_syndromes_by_system('TY2') + \
               find_syndromes_by_system('SY2') + find_syndromes_by_system('JY')
    for s in six_jing:
        print(f"  {s['name']} [{s['id']}] - 严重程度: {s['severity']}")
