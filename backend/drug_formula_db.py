#!/usr/bin/env python3
"""
小神农中医AI - 药物/方剂编号体系与疗效数据库
药物编号：DR-类别-序号
方剂编号：FP-主治病位-序号
"""

# 药物类别代码
DRUG_CATEGORIES = {
    'HD': '解表药',
    'QR': '清热药',
    'XZ': '泻下药',
    'HF': '祛风湿药',
    'HL': '化湿药',
    'LS': '利水渗湿药',
    'WY': '温里药',
    'LQ': '理气药',
    'XS': '消食药',
    'QC': '驱虫药',
    'ZH': '止血药',
    'HY': '活血化瘀药',
    'TT': '化痰止咳平喘药',
    'AS': '安神药',
    'PY': '平肝息风药',
    'KS': '开窍药',
    'BY': '补益药',
    'SH': '收涩药',
    'WJ': '外用药',
    'OT': '其他',
}

# 药物数据库
DRUG_DATABASE = {
    # 解表药 (HD)
    'DR-HD-001': {
        'name': '麻黄',
        'properties': {'nature': '辛、微苦', 'taste': '温', 'meridian': '肺、膀胱经'},
        'indications': ['SN-TM-C-001', 'SN-SP-S-005', 'SN-RP-S-002', 'SN-LM-S-002'],
        'contraindications': ['表虚自汗', '阴虚盗汗', '肺肾虚喘', '高血压', '失眠'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '心悸、失眠、血压升高',
        },
        'classic_formulas': ['FP-SP-001', 'FP-SP-002'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·麻黄汤'}],
    },
    'DR-HD-002': {
        'name': '桂枝',
        'properties': {'nature': '辛、甘', 'taste': '温', 'meridian': '心、肺、膀胱经'},
        'indications': ['SN-TM-C-002', 'SN-SP-S-004', 'SN-CV-S-001', 'SN-LM-S-005'],
        'contraindications': ['外感热病', '阴虚火旺', '血热妄行', '孕妇慎用'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见胃肠道不适',
        },
        'classic_formulas': ['FP-SP-001', 'FP-SP-003'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·桂枝汤'}],
    },
    'DR-HD-003': {
        'name': '柴胡',
        'properties': {'nature': '苦、辛', 'taste': '微寒', 'meridian': '肝、胆、肺经'},
        'indications': ['SN-TM-S-008', 'SN-TH-S-007', 'SN-PS-S-001', 'SN-DG-S-001'],
        'contraindications': ['肝阳上亢', '肝风内动', '阴虚火旺', '气机上逆'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见恶心、头晕',
        },
        'classic_formulas': ['FP-TH-002'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·小柴胡汤'}],
    },
    'DR-HD-004': {
        'name': '葛根',
        'properties': {'nature': '甘、辛', 'taste': '凉', 'meridian': '脾、胃经'},
        'indications': ['SN-HD-S-003', 'SN-HD-C-003', 'SN-DG-S-001', 'SN-TM-S-001'],
        'contraindications': ['胃寒呕吐', '表虚多汗'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见腹泻',
        },
        'classic_formulas': ['FP-HD-001'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·葛根汤'}],
    },
    
    # 清热药 (QR)
    'DR-QR-001': {
        'name': '黄连',
        'properties': {'nature': '苦', 'taste': '寒', 'meridian': '心、脾、胃、肝、胆、大肠经'},
        'indications': ['SN-PS-S-001', 'SN-DG-S-001', 'SN-EN-S-009', 'SN-TM-S-001'],
        'contraindications': ['脾胃虚寒', '阴虚津伤', '孕妇慎用'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '胃肠道刺激、恶心',
        },
        'classic_formulas': ['FP-TH-003'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·黄连阿胶汤'}],
    },
    'DR-QR-002': {
        'name': '黄芩',
        'properties': {'nature': '苦', 'taste': '寒', 'meridian': '肺、胆、脾、大肠、小肠经'},
        'indications': ['SN-TM-S-001', 'SN-RP-S-001', 'SN-DG-S-001', 'SN-TH-S-007'],
        'contraindications': ['脾胃虚寒', '食少便溏'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见腹泻',
        },
        'classic_formulas': ['FP-TH-002'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·小柴胡汤'}],
    },
    'DR-QR-003': {
        'name': '石膏',
        'properties': {'nature': '甘、辛', 'taste': '大寒', 'meridian': '肺、胃经'},
        'indications': ['SN-TM-S-001', 'SN-TM-S-009', 'SN-EN-S-008', 'SN-RP-S-002'],
        'contraindications': ['脾胃虚寒', '阴虚内热', '真寒假热'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见腹泻、胃寒',
        },
        'classic_formulas': ['FP-TM-001'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·白虎汤'}],
    },
    'DR-QR-004': {
        'name': '知母',
        'properties': {'nature': '苦、甘', 'taste': '寒', 'meridian': '肺、胃、肾经'},
        'indications': ['SN-TM-S-001', 'SN-TM-S-007', 'SN-EN-S-008', 'SN-PS-S-001'],
        'contraindications': ['脾胃虚寒', '大便溏泄'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见腹泻',
        },
        'classic_formulas': ['FP-TM-001', 'FP-SL-001'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·白虎汤'}],
    },
    'DR-QR-005': {
        'name': '栀子',
        'properties': {'nature': '苦', 'taste': '寒', 'meridian': '心、肺、三焦经'},
        'indications': ['SN-PS-S-001', 'SN-TM-S-001', 'SN-EN-S-008', 'SN-UR-S-001'],
        'contraindications': ['脾虚便溏', '食少'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见腹泻',
        },
        'classic_formulas': ['FP-PS-001'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·栀子豉汤'}],
    },
    
    # 温里药 (WY)
    'DR-WY-001': {
        'name': '附子',
        'properties': {'nature': '辛、甘', 'taste': '大热', 'meridian': '心、肾、脾经'},
        'indications': ['SN-LM-S-005', 'SN-SP-S-010', 'SN-TH-S-004', 'SN-TM-S-010'],
        'contraindications': ['阴虚阳亢', '真热假寒', '孕妇禁用', '半夏、瓜蒌、贝母、白蔹、白及'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '毒性反应（需炮制）',
        },
        'classic_formulas': ['FP-SP-004', 'FP-CV-001'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·四逆汤'}],
    },
    'DR-WY-002': {
        'name': '干姜',
        'properties': {'nature': '辛', 'taste': '热', 'meridian': '脾、胃、心、肺经'},
        'indications': ['SN-LM-S-005', 'SN-DG-S-001', 'SN-TH-S-004', 'SN-SP-S-010'],
        'contraindications': ['阴虚内热', '血热妄行', '实热'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见口干',
        },
        'classic_formulas': ['FP-SP-004', 'FP-TH-003'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·四逆汤'}],
    },
    
    # 补益药 (BY)
    'DR-BY-001': {
        'name': '人参',
        'properties': {'nature': '甘、微苦', 'taste': '微温', 'meridian': '脾、肺、心经'},
        'indications': ['SN-SP-S-010', 'SN-PS-S-008', 'SN-CV-S-004', 'SN-DG-S-012'],
        'contraindications': ['实热证', '气滞', '痰湿', '感冒发热'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见失眠、血压升高等（实证者）',
        },
        'classic_formulas': ['FP-BY-001', 'FP-CV-002'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·四逆加人参汤'}],
    },
    'DR-BY-002': {
        'name': '黄芪',
        'properties': {'nature': '甘', 'taste': '微温', 'meridian': '脾、肺经'},
        'indications': ['SN-SP-S-010', 'SN-SP-S-004', 'SN-OT-S-016', 'SN-LM-S-003'],
        'contraindications': ['表实邪盛', '气滞湿阻', '食积停滞', '阴虚阳亢', '痈疽初起'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见胸闷、头晕（实证者）',
        },
        'classic_formulas': ['FP-BY-002', 'FP-SP-005'],
        'sources': [{'type': 'classic', 'ref': '金匮要略·防己黄芪汤'}],
    },
    'DR-BY-003': {
        'name': '当归',
        'properties': {'nature': '甘、辛', 'taste': '温', 'meridian': '肝、心、脾经'},
        'indications': ['SN-RE-S-002', 'SN-RE-S-003', 'SN-SP-S-010', 'SN-OT-S-009'],
        'contraindications': ['湿盛中满', '大便溏泄', '热盛出血'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见腹泻',
        },
        'classic_formulas': ['FP-BY-003', 'FP-RE-001'],
        'sources': [{'type': 'classic', 'ref': '金匮要略·当归芍药散'}],
    },
    'DR-BY-004': {
        'name': '甘草',
        'properties': {'nature': '甘', 'taste': '平', 'meridian': '心、肺、脾、胃经'},
        'indications': ['SN-TH-S-004', 'SN-RP-S-001', 'SN-SP-S-010', 'SN-PS-S-001'],
        'contraindications': ['湿盛胀满', '水肿', '大戟、芫花、甘遂、海藻'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '长期大量使用可致水肿、高血压',
        },
        'classic_formulas': ['FP-SP-001', 'FP-SP-002', 'FP-TH-002'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·甘草汤'}],
    },
    
    # 安神药 (AS)
    'DR-AS-001': {
        'name': '酸枣仁',
        'properties': {'nature': '甘、酸', 'taste': '平', 'meridian': '心、肝、胆经'},
        'indications': ['SN-SL-S-001', 'SN-PS-S-001', 'SN-PS-S-005', 'SN-SL-S-005'],
        'contraindications': ['实热内盛', '滑泄'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见胃肠道不适',
        },
        'classic_formulas': ['FP-SL-001'],
        'sources': [{'type': 'classic', 'ref': '金匮要略·酸枣仁汤'}],
    },
    'DR-AS-002': {
        'name': '茯苓',
        'properties': {'nature': '甘、淡', 'taste': '平', 'meridian': '心、肺、脾、肾经'},
        'indications': ['SN-PS-S-001', 'SN-SL-S-001', 'SN-PS-S-005', 'SN-SP-S-006'],
        'contraindications': ['阴虚津亏', '肾虚滑精'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见尿频',
        },
        'classic_formulas': ['FP-SL-001', 'FP-SP-005'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·茯苓桂枝白术甘草汤'}],
    },
    
    # 活血化瘀药 (HY)
    'DR-HY-001': {
        'name': '川芎',
        'properties': {'nature': '辛', 'taste': '温', 'meridian': '肝、胆、心包经'},
        'indications': ['SN-HD-S-001', 'SN-HD-S-002', 'SN-RE-S-002', 'SN-OT-S-005'],
        'contraindications': ['阴虚火旺', '舌红口干', '月经过多', '出血性疾病'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见口干、头晕',
        },
        'classic_formulas': ['FP-SL-001', 'FP-RE-001'],
        'sources': [{'type': 'classic', 'ref': '金匮要略·酸枣仁汤'}],
    },
    
    # 利水渗湿药 (LS)
    'DR-LS-001': {
        'name': '泽泻',
        'properties': {'nature': '甘、淡', 'taste': '寒', 'meridian': '肾、膀胱经'},
        'indications': ['SN-UR-S-001', 'SN-SP-S-008', 'SN-TH-S-005', 'SN-EN-S-008'],
        'contraindications': ['肾虚滑精', '无湿热'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见腹泻',
        },
        'classic_formulas': ['FP-LS-001'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·五苓散'}],
    },
    'DR-LS-002': {
        'name': '猪苓',
        'properties': {'nature': '甘、淡', 'taste': '平', 'meridian': '肾、膀胱经'},
        'indications': ['SN-UR-S-001', 'SN-SP-S-008', 'SN-TH-S-005'],
        'contraindications': ['肾虚滑精', '无水湿'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见口干',
        },
        'classic_formulas': ['FP-LS-001'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·猪苓汤'}],
    },
    
    # 化痰止咳平喘药 (TT)
    'DR-TT-001': {
        'name': '半夏',
        'properties': {'nature': '辛', 'taste': '温', 'meridian': '脾、胃、肺经'},
        'indications': ['SN-RP-S-001', 'SN-RP-S-004', 'SN-TH-S-008', 'SN-TH-S-009'],
        'contraindications': ['阴虚燥咳', '血证', '热痰', '孕妇慎用', '乌头'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '生品有毒（需炮制）',
        },
        'classic_formulas': ['FP-RP-001', 'FP-TH-004'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·小半夏汤'}],
    },
    'DR-TT-002': {
        'name': '杏仁',
        'properties': {'nature': '苦', 'taste': '微温', 'meridian': '肺、大肠经'},
        'indications': ['SN-RP-S-001', 'SN-RP-S-002', 'SN-DG-S-002', 'SN-TH-S-008'],
        'contraindications': ['阴虚咳嗽', '大便溏泄', '婴儿慎用'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '生品有小毒（需炮制）',
        },
        'classic_formulas': ['FP-SP-002', 'FP-RP-001'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·麻黄汤'}],
    },
    
    # 理气药 (LQ)
    'DR-LQ-001': {
        'name': '枳实',
        'properties': {'nature': '苦、辛、酸', 'taste': '温', 'meridian': '脾、胃经'},
        'indications': ['SN-TH-S-005', 'SN-DG-S-002', 'SN-TH-S-004', 'SN-TH-O-001'],
        'contraindications': ['脾胃虚弱', '孕妇慎用'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见胃部不适',
        },
        'classic_formulas': ['FP-TH-005'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·枳实栀子豉汤'}],
    },
    'DR-LQ-002': {
        'name': '厚朴',
        'properties': {'nature': '苦、辛', 'taste': '温', 'meridian': '脾、胃、肺、大肠经'},
        'indications': ['SN-TH-S-005', 'SN-DG-S-002', 'SN-RP-S-002', 'SN-TH-S-004'],
        'contraindications': ['气虚津亏', '孕妇慎用'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见口干',
        },
        'classic_formulas': ['FP-TH-005'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·厚朴生姜半夏甘草人参汤'}],
    },
    
    # 消食药 (XS)
    'DR-XS-001': {
        'name': '神曲',
        'properties': {'nature': '甘、辛', 'taste': '温', 'meridian': '脾、胃经'},
        'indications': ['SN-DG-S-012', 'SN-TH-S-005', 'SN-DG-S-006', 'SN-DG-S-007'],
        'contraindications': ['脾阴虚', '胃火亢盛'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '无明显副作用',
        },
        'classic_formulas': [],
        'sources': [{'type': 'classic', 'ref': '本草纲目'}],
    },
    
    # 收涩药 (SH)
    'DR-SH-001': {
        'name': '五味子',
        'properties': {'nature': '酸、甘', 'taste': '温', 'meridian': '肺、心、肾经'},
        'indications': ['SN-RP-S-001', 'SN-RP-S-002', 'SN-SL-S-001', 'SN-SP-S-004'],
        'contraindications': ['表邪未解', '内有实热', '咳嗽初起', '麻疹初起'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见胃部不适',
        },
        'classic_formulas': ['FP-RP-002'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·小青龙汤'}],
    },
    'DR-SH-002': {
        'name': '乌梅',
        'properties': {'nature': '酸、涩', 'taste': '平', 'meridian': '肝、脾、肺、大肠经'},
        'indications': ['SN-DG-S-001', 'SN-TH-S-008', 'SN-TH-S-009', 'SN-SP-S-004'],
        'contraindications': ['表邪未解', '内有实热', '湿热积滞'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见胃酸过多',
        },
        'classic_formulas': ['FP-DG-001'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·乌梅丸'}],
    },
    
    # 平肝息风药 (PY)
    'DR-PY-001': {
        'name': '白芍',
        'properties': {'nature': '苦、酸', 'taste': '微寒', 'meridian': '肝、脾经'},
        'indications': ['SN-HD-S-001', 'SN-TH-S-004', 'SN-LM-S-008', 'SN-RE-S-002'],
        'contraindications': ['虚寒腹痛', '阳虚', '麻疹初起'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见腹泻',
        },
        'classic_formulas': ['FP-SP-003', 'FP-RE-001'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·桂枝汤'}],
    },
    
    # 其他 (OT)
    'DR-OT-001': {
        'name': '生姜',
        'properties': {'nature': '辛', 'taste': '微温', 'meridian': '肺、脾、胃经'},
        'indications': ['SN-TH-S-008', 'SN-TH-S-009', 'SN-LM-S-005', 'SN-DG-S-001'],
        'contraindications': ['阴虚内热', '实热', '目疾', '痔疮', '疮疡'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见胃部灼热感',
        },
        'classic_formulas': ['FP-SP-001', 'FP-TH-004'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·桂枝汤'}],
    },
    'DR-OT-002': {
        'name': '大枣',
        'properties': {'nature': '甘', 'taste': '温', 'meridian': '脾、胃、心经'},
        'indications': ['SN-SP-S-010', 'SN-PS-S-008', 'SN-TH-S-004', 'SN-DG-S-012'],
        'contraindications': ['湿盛', '食滞', '虫积', '齿病', '痰热'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A', 'avg_treatment_duration': 'N/A',
            'side_effects': '偶见腹胀',
        },
        'classic_formulas': ['FP-SP-001', 'FP-TH-002'],
        'sources': [{'type': 'classic', 'ref': '伤寒论·桂枝汤'}],
    },
}

# 方剂数据库
FORMULA_DATABASE = {
    # 表证方剂
    'FP-SP-001': {
        'name': '桂枝汤',
        'source': '伤寒论',
        'composition': {
            'DR-HD-002': '三两',
            'DR-BY-004': '二两',
            'DR-PY-001': '三两',
            'DR-OT-001': '三两',
            'DR-OT-002': '十二枚',
        },
        'indications': ['SN-TM-C-002', 'SN-SP-S-004', 'SN-HD-S-001'],
        'syndrome': '太阳中风表虚证',
        'symptoms': ['发热', '汗出', '恶风', '头痛', '脉浮缓'],
        'contraindications': ['表实无汗', '温病初起', '里热炽盛'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    'FP-SP-002': {
        'name': '麻黄汤',
        'source': '伤寒论',
        'composition': {
            'DR-HD-001': '三两',
            'DR-HD-002': '二两',
            'DR-TT-002': '七十个',
            'DR-BY-004': '一两',
        },
        'indications': ['SN-TM-C-001', 'SN-SP-S-005', 'SN-HD-S-001', 'SN-RP-S-002'],
        'syndrome': '太阳伤寒表实证',
        'symptoms': ['发热', '恶寒', '无汗', '头痛', '身疼痛', '喘', '脉浮紧'],
        'contraindications': ['表虚自汗', '阴虚', '血虚', '疮家', '淋家', '衄家', '亡血家'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    'FP-SP-003': {
        'name': '葛根汤',
        'source': '伤寒论',
        'composition': {
            'DR-HD-004': '四两',
            'DR-HD-001': '三两',
            'DR-HD-002': '二两',
            'DR-BY-004': '二两',
            'DR-PY-001': '二两',
            'DR-OT-001': '三两',
            'DR-OT-002': '十二枚',
        },
        'indications': ['SN-HD-C-003', 'SN-HD-S-001', 'SN-LM-S-002', 'SN-TM-C-001'],
        'syndrome': '太阳病项背强几几',
        'symptoms': ['项背强几几', '无汗', '恶风', '头痛'],
        'contraindications': ['表虚多汗', '阴虚'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    'FP-SP-004': {
        'name': '四逆汤',
        'source': '伤寒论',
        'composition': {
            'DR-WY-001': '一枚',
            'DR-WY-002': '一两半',
            'DR-BY-004': '二两',
        },
        'indications': ['SN-LM-S-005', 'SN-SP-S-010', 'SN-TM-S-010', 'SN-TH-S-004'],
        'syndrome': '少阴病寒化证',
        'symptoms': ['四肢厥冷', '恶寒蜷卧', '呕吐不渴', '腹痛下利', '脉微细'],
        'contraindications': ['真热假寒', '阴虚阳亢', '实热'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    'FP-SP-005': {
        'name': '防己黄芪汤',
        'source': '金匮要略',
        'composition': {
            'DR-BY-002': '一两一分',
            'DR-AS-002': '一两',
            'DR-BY-004': '半两',
            'DR-OT-001': '四片',
            'DR-OT-002': '一枚',
        },
        'indications': ['SN-SP-S-006', 'SN-SP-S-004', 'SN-LM-S-007', 'SN-SP-S-008'],
        'syndrome': '风水表虚证',
        'symptoms': ['汗出恶风', '身重微肿', '肢节疼痛', '小便不利'],
        'contraindications': ['风水表实', '湿热'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    
    # 胸腹方剂
    'FP-TH-002': {
        'name': '小柴胡汤',
        'source': '伤寒论',
        'composition': {
            'DR-HD-003': '半斤',
            'DR-QR-002': '三两',
            'DR-BY-001': '三两',
            'DR-BY-004': '三两',
            'DR-OT-002': '十二枚',
            'DR-OT-001': '三两',
            'DR-TT-001': '半升',
        },
        'indications': ['SN-TM-S-008', 'SN-TH-S-007', 'SN-PS-S-001', 'SN-TH-S-012'],
        'syndrome': '少阳病',
        'symptoms': ['寒热往来', '胸胁苦满', '默默不欲饮食', '心烦喜呕', '口苦咽干', '目眩'],
        'contraindications': ['纯表证', '纯里证', '阴虚血少'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    'FP-TH-003': {
        'name': '黄连阿胶汤',
        'source': '伤寒论',
        'composition': {
            'DR-QR-001': '四两',
            'DR-QR-004': '二两',
            'DR-PY-001': '二两',
            'DR-BY-003': '一两',
            'DR-BY-001': '二枚',
        },
        'indications': ['SN-PS-C-001', 'SN-EN-S-008', 'SN-SL-S-001', 'SN-PS-S-001'],
        'syndrome': '少阴病阴虚火旺证',
        'symptoms': ['心中烦', '不得卧', '口干咽燥', '舌红少苔', '脉细数'],
        'contraindications': ['脾胃虚寒', '痰湿'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    'FP-TH-004': {
        'name': '小半夏汤',
        'source': '金匮要略',
        'composition': {
            'DR-TT-001': '一升',
            'DR-OT-001': '半斤',
        },
        'indications': ['SN-TH-S-009', 'SN-TH-S-008', 'SN-TH-S-012'],
        'syndrome': '痰饮呕吐',
        'symptoms': ['呕吐', '谷不得下', '心下痞', '眩悸'],
        'contraindications': ['胃热呕吐', '阴虚呕吐'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    'FP-TH-005': {
        'name': '厚朴生姜半夏甘草人参汤',
        'source': '伤寒论',
        'composition': {
            'DR-LQ-002': '半斤',
            'DR-OT-001': '半斤',
            'DR-TT-001': '半升',
            'DR-BY-004': '二两',
            'DR-BY-001': '一两',
        },
        'indications': ['SN-TH-S-005', 'SN-TH-O-001', 'SN-SP-S-010', 'SN-DG-S-012'],
        'syndrome': '脾虚气滞腹胀',
        'symptoms': ['腹胀满', '食欲不振', '乏力', '脉缓'],
        'contraindications': ['实热腹胀', '食积腹胀'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    
    # 睡眠方剂
    'FP-SL-001': {
        'name': '酸枣仁汤',
        'source': '金匮要略',
        'composition': {
            'DR-AS-001': '二升',
            'DR-QR-004': '二两',
            'DR-AS-002': '二两',
            'DR-HY-001': '二两',
            'DR-BY-004': '一两',
        },
        'indications': ['SN-SL-S-005', 'SN-PS-S-001', 'SN-EN-S-008', 'SN-HD-S-002'],
        'syndrome': '虚劳虚烦不得眠',
        'symptoms': ['虚烦不得眠', '心悸不安', '头晕目眩', '咽干口燥', '舌红', '脉弦细'],
        'contraindications': ['实热失眠', '痰湿失眠', '食积失眠'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    
    # 妇人方剂
    'FP-RE-001': {
        'name': '当归芍药散',
        'source': '金匮要略',
        'composition': {
            'DR-BY-003': '三两',
            'DR-PY-001': '一斤',
            'DR-BY-002': '三两',
            'DR-AS-002': '四两',
            'DR-HY-001': '半斤',
        },
        'indications': ['SN-RE-S-002', 'SN-TH-S-004', 'SN-TH-S-005', 'SN-RE-S-003'],
        'syndrome': '妇人妊娠肝脾不和',
        'symptoms': ['腹中绞痛', '心悸', '小便不利', '下肢浮肿'],
        'contraindications': ['实热腹痛', '血瘀腹痛'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    
    # 呼吸方剂
    'FP-RP-001': {
        'name': '麻黄杏仁甘草石膏汤',
        'source': '伤寒论',
        'composition': {
            'DR-HD-001': '四两',
            'DR-TT-002': '五十个',
            'DR-BY-004': '二两',
            'DR-QR-003': '半斤',
        },
        'indications': ['SN-RP-S-001', 'SN-RP-S-002', 'SN-TM-S-001', 'SN-TM-S-009'],
        'syndrome': '肺热咳喘',
        'symptoms': ['发热', '喘急', '咳嗽', '口渴', '汗出', '脉浮数'],
        'contraindications': ['风寒咳喘', '痰饮咳喘', '虚喘'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    'FP-RP-002': {
        'name': '小青龙汤',
        'source': '伤寒论',
        'composition': {
            'DR-HD-001': '三两',
            'DR-BY-002': '三两',
            'DR-HD-002': '三两',
            'DR-PY-001': '三两',
            'DR-TT-001': '半升',
            'DR-SH-001': '半升',
            'DR-BY-004': '三两',
            'DR-OT-001': '三两',
        },
        'indications': ['SN-RP-C-001', 'SN-TM-C-001', 'SN-SP-S-005', 'SN-EN-S-005'],
        'syndrome': '外寒内饮',
        'symptoms': ['恶寒发热', '无汗', '咳喘', '痰多清稀', '胸痞', '干呕', '脉浮'],
        'contraindications': ['阴虚咳嗽', '痰热咳嗽', '肺热咳喘'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    
    # 循环方剂
    'FP-CV-001': {
        'name': '四逆加人参汤',
        'source': '伤寒论',
        'composition': {
            'DR-WY-001': '一枚',
            'DR-WY-002': '一两半',
            'DR-BY-004': '二两',
            'DR-BY-001': '一两',
        },
        'indications': ['SN-LM-S-005', 'SN-SP-S-010', 'SN-CV-S-003', 'SN-SP-S-004'],
        'syndrome': '少阴病阳气衰微兼气阴两伤',
        'symptoms': ['四肢厥逆', '恶寒', '脉微细', '下利', '汗出'],
        'contraindications': ['真热假寒', '实热'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    'FP-CV-002': {
        'name': '炙甘草汤',
        'source': '伤寒论',
        'composition': {
            'DR-BY-004': '四两',
            'DR-BY-001': '三两',
            'DR-BY-002': '三两',
            'DR-BY-003': '三两',
            'DR-PY-001': '四两',
            'DR-HD-002': '三两',
            'DR-WY-001': '二两',
            'DR-QR-004': '二两',
            'DR-OT-001': '三两',
            'DR-OT-002': '三十枚',
            'DR-OT-003': '一升',
        },
        'indications': ['SN-CV-O-015', 'SN-CV-S-001', 'SN-CV-S-004', 'SN-SP-S-010'],
        'syndrome': '心动悸脉结代',
        'symptoms': ['心动悸', '脉结代', '虚羸少气', '舌光少苔'],
        'contraindications': ['痰湿内盛', '实热'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    
    # 消化方剂
    'FP-DG-001': {
        'name': '乌梅丸',
        'source': '伤寒论',
        'composition': {
            'DR-SH-002': '三百枚',
            'DR-BY-001': '六两',
            'DR-BY-004': '六两',
            'DR-BY-002': '六两',
            'DR-BY-003': '四两',
            'DR-PY-001': '六两',
            'DR-HD-002': '六两',
            'DR-WY-001': '六两',
            'DR-WY-002': '十两',
            'DR-QR-001': '六两',
            'DR-QR-002': '四两',
            'DR-TT-001': '一升',
        },
        'indications': ['SN-DG-S-001', 'SN-TH-S-004', 'SN-TH-S-008', 'SN-TM-S-008'],
        'syndrome': '蛔厥/上热下寒',
        'symptoms': ['腹痛', '呕吐', '时发时止', '得食而呕', '烦闷', '手足厥冷'],
        'contraindications': ['纯热证', '纯寒证'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    
    # 利水方剂
    'FP-LS-001': {
        'name': '五苓散',
        'source': '伤寒论',
        'composition': {
            'DR-LS-001': '一两六铢',
            'DR-LS-002': '十八铢',
            'DR-BY-002': '十八铢',
            'DR-BY-004': '半两',
            'DR-HD-002': '一两半',
        },
        'indications': ['SN-UR-S-001', 'SN-TH-S-005', 'SN-EN-S-008', 'SN-TM-S-001'],
        'syndrome': '太阳蓄水证',
        'symptoms': ['小便不利', '微热消渴', '水入即吐', '脉浮'],
        'contraindications': ['阴虚津亏', '湿热下注'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    
    # 补益方剂
    'FP-BY-001': {
        'name': '理中丸',
        'source': '伤寒论',
        'composition': {
            'DR-BY-001': '三两',
            'DR-WY-002': '三两',
            'DR-BY-004': '三两',
            'DR-PY-001': '三两',
        },
        'indications': ['SN-LM-S-005', 'SN-DG-S-001', 'SN-TH-S-004', 'SN-SP-S-010'],
        'syndrome': '脾胃虚寒',
        'symptoms': ['脘腹疼痛', '呕吐', '下利', '手足不温', '脉沉细'],
        'contraindications': ['实热', '阴虚', '湿热'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    'FP-BY-002': {
        'name': '小建中汤',
        'source': '伤寒论',
        'composition': {
            'DR-PY-001': '六两',
            'DR-BY-004': '三两',
            'DR-BY-001': '三两',
            'DR-BY-002': '三两',
            'DR-BY-003': '三两',
            'DR-OT-002': '十二枚',
            'DR-OT-003': '一升',
        },
        'indications': ['SN-TH-S-004', 'SN-TH-S-005', 'SN-PS-S-001', 'SN-SP-S-010'],
        'syndrome': '中焦虚寒',
        'symptoms': ['腹中拘急疼痛', '喜温喜按', '心悸', '虚烦', '面色无华'],
        'contraindications': ['实热腹痛', '湿热腹痛'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    'FP-BY-003': {
        'name': '当归生姜羊肉汤',
        'source': '金匮要略',
        'composition': {
            'DR-BY-003': '三两',
            'DR-OT-001': '五两',
            'DR-OT-003': '一斤',
        },
        'indications': ['SN-TH-S-004', 'SN-LM-S-005', 'SN-SP-S-010', 'SN-RE-S-002'],
        'syndrome': '血虚寒疝',
        'symptoms': ['腹中痛', '胁痛', '里急', '产后腹痛', '喜温喜按'],
        'contraindications': ['实热', '湿热', '阴虚火旺'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    
    # 清热方剂
    'FP-TM-001': {
        'name': '白虎汤',
        'source': '伤寒论',
        'composition': {
            'DR-QR-003': '一斤',
            'DR-QR-004': '六两',
            'DR-BY-004': '二两',
            'DR-OT-003': '六合',
        },
        'indications': ['SN-TM-S-001', 'SN-TM-S-009', 'SN-EN-S-008', 'SN-RP-S-002'],
        'syndrome': '阳明经证',
        'symptoms': ['大热', '大汗', '大渴', '脉洪大', '面赤', '气粗'],
        'contraindications': ['表证未解', '真寒假热', '血虚发热', '气虚发热'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    
    # 精神方剂
    'FP-PS-001': {
        'name': '栀子豉汤',
        'source': '伤寒论',
        'composition': {
            'DR-QR-005': '十四个',
            'DR-OT-003': '四合',
        },
        'indications': ['SN-PS-S-001', 'SN-TH-S-012', 'SN-TH-S-009', 'SN-TM-S-001'],
        'syndrome': '热扰胸膈',
        'symptoms': ['虚烦不得眠', '心中懊憹', '反复颠倒', '胸中窒', '心中结痛'],
        'contraindications': ['脾胃虚寒', '大便溏'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
    
    # 头面方剂
    'FP-HD-001': {
        'name': '葛根加半夏汤',
        'source': '伤寒论',
        'composition': {
            'DR-HD-004': '四两',
            'DR-HD-001': '三两',
            'DR-HD-002': '二两',
            'DR-BY-004': '二两',
            'DR-PY-001': '二两',
            'DR-OT-001': '三两',
            'DR-OT-002': '十二枚',
            'DR-TT-001': '半升',
        },
        'indications': ['SN-HD-C-003', 'SN-TH-S-009', 'SN-HD-S-001', 'SN-TM-C-001'],
        'syndrome': '太阳病项背强几几兼呕',
        'symptoms': ['项背强几几', '无汗', '恶风', '呕吐'],
        'contraindications': ['表虚多汗', '阴虚'],
        'effectiveness_stats': {
            'total_cases': 0, 'effective_cases': 0, 'effectiveness_rate': 'N/A',
            'studies_count': 0, 'evidence_level': 'N/A',
        },
    },
}


def get_drug_by_id(drug_id: str) -> dict:
    """根据ID获取药物信息"""
    drug = DRUG_DATABASE.get(drug_id)
    if not drug:
        return None
    return {
        'id': drug_id,
        'name': drug['name'],
        'properties': drug['properties'],
        'contraindications': drug['contraindications'],
        'effectiveness_stats': drug['effectiveness_stats'],
    }


def get_formula_by_id(formula_id: str) -> dict:
    """根据ID获取方剂信息"""
    formula = FORMULA_DATABASE.get(formula_id)
    if not formula:
        return None
    
    # 解析组成药物
    composition = []
    for drug_id, dose in formula['composition'].items():
        drug = DRUG_DATABASE.get(drug_id)
        if drug:
            composition.append({
                'id': drug_id,
                'name': drug['name'],
                'dose': dose,
            })
    
    return {
        'id': formula_id,
        'name': formula['name'],
        'source': formula['source'],
        'composition': composition,
        'syndrome': formula['syndrome'],
        'symptoms': formula['symptoms'],
        'contraindications': formula['contraindications'],
        'effectiveness_stats': formula['effectiveness_stats'],
    }


def find_formulas_by_symptoms(symptom_ids: list) -> list:
    """根据症状ID列表查找匹配的方剂"""
    matched = []
    for formula_id, formula in FORMULA_DATABASE.items():
        # 计算匹配度
        matched_symptoms = [sid for sid in symptom_ids if sid in formula['indications']]
        if matched_symptoms:
            matched.append({
                'id': formula_id,
                'name': formula['name'],
                'source': formula['source'],
                'syndrome': formula['syndrome'],
                'matched_symptoms': matched_symptoms,
                'match_score': len(matched_symptoms) / len(formula['indications']),
            })
    
    # 按匹配度排序
    matched.sort(key=lambda x: x['match_score'], reverse=True)
    return matched


def find_drugs_by_symptoms(symptom_ids: list) -> list:
    """根据症状ID列表查找匹配的药物"""
    matched = []
    for drug_id, drug in DRUG_DATABASE.items():
        matched_indications = [sid for sid in symptom_ids if sid in drug['indications']]
        if matched_indications:
            matched.append({
                'id': drug_id,
                'name': drug['name'],
                'properties': drug['properties'],
                'matched_indications': matched_indications,
                'match_score': len(matched_indications) / len(drug['indications']),
            })
    
    matched.sort(key=lambda x: x['match_score'], reverse=True)
    return matched


def get_drug_contraindications(drug_ids: list) -> list:
    """获取药物禁忌列表"""
    contras = []
    for drug_id in drug_ids:
        drug = DRUG_DATABASE.get(drug_id)
        if drug and drug['contraindications']:
            contras.append({
                'drug_id': drug_id,
                'drug_name': drug['name'],
                'contraindications': drug['contraindications'],
            })
    return contras


if __name__ == "__main__":
    # 测试
    print("=== 药物查询测试 ===")
    drug = get_drug_by_id('DR-HD-001')
    print(f"麻黄: {drug['name']}, 性味: {drug['properties']['nature']}")
    
    print("\n=== 方剂查询测试 ===")
    formula = get_formula_by_id('FP-SP-002')
    print(f"麻黄汤: {formula['name']}")
    print(f"  证型: {formula['syndrome']}")
    print(f"  组成: {', '.join([d['name'] for d in formula['composition']])}")
    
    print("\n=== 症状匹配方剂测试 ===")
    from symptom_codes import find_symptoms_by_text
    symptoms = find_symptoms_by_text("头痛发热，怕冷，没有汗")
    symptom_ids = [s['id'] for s in symptoms]
    formulas = find_formulas_by_symptoms(symptom_ids)
    print(f"匹配方剂: {len(formulas)}个")
    for f in formulas[:3]:
        print(f"  {f['name']} ({f['syndrome']}) - 匹配度: {f['match_score']:.2f}")
