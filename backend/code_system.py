#!/usr/bin/env python3
"""
小神农中医AI - 统一编码体系 v2.1
对齐文档标准：
- 症状：SN-部位-类别-序号（QT=全身, Z=自觉, T=体征, F=复合）
- 药物：DR-功效类别-序号（JB=解表, QR=清热, AS=安神, BY=补益等）
- 证型：SY-体系-序号（TY=太阳, YM=阳明, QB=气血津液等）
- 方剂：FP-主治病位-序号（TY=太阳, SJ=精神, XG=消化等）
- 禁忌规则：RL-规则组-序号（18F=十八反, 19W=十九畏, 7Q=七情）
- 古籍条文：CL-来源-序号
"""

# ========== 部位代码（症状SN）==========
BODY_PART_CODES = {
    'QT': '全身/一般',
    'HD': '头面',
    'TH': '胸腹',
    'YB': '腰背',
    'SZ': '四肢',
    'XG': '消化',
    'HX': '呼吸',
    'XH': '循环',
    'MN': '泌尿生殖',
    'SJ': '精神神经',
    'WG': '五官',
    'PF': '皮肤',
}

# 类别代码（症状SN）
SYMPTOM_TYPE_CODES = {
    'Z': '自觉症状（主观）',
    'T': '体征（客观）',
    'F': '复合症状（组合）',
}

# ========== 功效类别代码（药物DR）==========
DRUG_CATEGORY_CODES = {
    'JB': '解表药',
    'QR': '清热药',
    'XY': '泻下药',
    'XS': '祛风湿药',
    'HS': '化湿药',
    'LS': '利水渗湿药',
    'WL': '温里药',
    'LQ': '理气药',
    'XY2': '消食药',
    'QC': '驱虫药',
    'ZX': '止血药',
    'HY': '活血化瘀药',
    'HQ': '化痰止咳平喘药',
    'AS': '安神药',
    'PG': '平肝息风药',
    'KQ': '开窍药',
    'BY': '补益药',
    'SS': '收涩药',
    'WY': '外用药',
    'QT': '其他',
}

# ========== 体系代码（证型SY）==========
SYNDROME_SYSTEM_CODES = {
    'TY': '太阳病',
    'YM': '阳明病',
    'SY': '少阳病',
    'TY2': '太阴病',
    'SY2': '少阴病',
    'JY': '厥阴病',
    'QB': '气血津液',
    'YG': '脏腑（阳）',
    'YN': '脏腑（阴）',
    'WS': '卫气营血',
    'SL': '三焦',
    'QT': '其他',
}

# ========== 主治病位代码（方剂FP）==========
FORMULA_TARGET_CODES = {
    'TY': '太阳',
    'YM': '阳明',
    'SY': '少阳',
    'TY2': '太阴',
    'SY2': '少阴',
    'JY': '厥阴',
    'QT': '全身',
    'HD': '头面',
    'TH': '胸腹',
    'XG': '消化',
    'HX': '呼吸',
    'SJ': '精神',
    'SZ': '四肢',
    'MN': '泌尿生殖',
}

# ========== 规则组代码（禁忌RL）==========
RULE_GROUP_CODES = {
    '18F': '十八反',
    '19W': '十九畏',
    '7Q': '七情配伍',
    'JC': '妊娠禁忌',
    'SY': '食忌',
}

# ========== 关系类型代码 ==========
RELATIONSHIP_TYPES = {
    'treats': '药物治疗',
    'treated_by': '被治疗',
    'in_formula': '组成方剂',
    'contains': '包含药物',
    'interacts': '药物相互作用',
    'contraindicated': '禁忌配伍',
    'indicates': '主治证型',
    'indicated_by': '对应方剂',
    'documents': '古籍记载',
    'co_occurs': '症状共现',
    'complicates': '并发症',
    'has_syndrome': '患有证型',
    'takes': '服用',
    'reports': '反馈',
    'causes_adverse': '引起副作用',
    'similar_to': '相似于',
}


def validate_symptom_id(symptom_id: str) -> bool:
    """验证症状编号格式：SN-部位-类别-序号"""
    parts = symptom_id.split('-')
    if len(parts) != 4 or parts[0] != 'SN':
        return False
    if parts[1] not in BODY_PART_CODES:
        return False
    if parts[2] not in SYMPTOM_TYPE_CODES:
        return False
    try:
        int(parts[3])
        return True
    except ValueError:
        return False


def validate_drug_id(drug_id: str) -> bool:
    """验证药物编号格式：DR-类别-序号"""
    parts = drug_id.split('-')
    if len(parts) != 3 or parts[0] != 'DR':
        return False
    if parts[1] not in DRUG_CATEGORY_CODES:
        return False
    try:
        int(parts[2])
        return True
    except ValueError:
        return False


def validate_syndrome_id(syndrome_id: str) -> bool:
    """验证证型编号格式：SY-体系-序号"""
    parts = syndrome_id.split('-')
    if len(parts) != 3 or parts[0] != 'SY':
        return False
    if parts[1] not in SYNDROME_SYSTEM_CODES:
        return False
    try:
        int(parts[2])
        return True
    except ValueError:
        return False


def validate_formula_id(formula_id: str) -> bool:
    """验证方剂编号格式：FP-主治病位-序号"""
    parts = formula_id.split('-')
    if len(parts) != 3 or parts[0] != 'FP':
        return False
    if parts[1] not in FORMULA_TARGET_CODES:
        return False
    try:
        int(parts[2])
        return True
    except ValueError:
        return False


def validate_rule_id(rule_id: str) -> bool:
    """验证规则编号格式：RL-规则组-序号"""
    parts = rule_id.split('-')
    if len(parts) != 3 or parts[0] != 'RL':
        return False
    if parts[1] not in RULE_GROUP_CODES:
        return False
    try:
        int(parts[2])
        return True
    except ValueError:
        return False


def get_id_description(entity_id: str) -> str:
    """获取编号的人类可读描述"""
    parts = entity_id.split('-')
    
    if parts[0] == 'SN' and len(parts) == 4:
        part = BODY_PART_CODES.get(parts[1], '未知部位')
        stype = SYMPTOM_TYPE_CODES.get(parts[2], '未知类别')
        return f"症状：{part}/{stype} #{parts[3]}"
    
    elif parts[0] == 'DR' and len(parts) == 3:
        cat = DRUG_CATEGORY_CODES.get(parts[1], '未知类别')
        return f"药物：{cat} #{parts[2]}"
    
    elif parts[0] == 'SY' and len(parts) == 3:
        sys = SYNDROME_SYSTEM_CODES.get(parts[1], '未知体系')
        return f"证型：{sys} #{parts[2]}"
    
    elif parts[0] == 'FP' and len(parts) == 3:
        target = FORMULA_TARGET_CODES.get(parts[1], '未知病位')
        return f"方剂：主治{target} #{parts[2]}"
    
    elif parts[0] == 'RL' and len(parts) == 3:
        group = RULE_GROUP_CODES.get(parts[1], '未知规则')
        return f"禁忌：{group} #{parts[2]}"
    
    return f"未知：{entity_id}"


if __name__ == "__main__":
    # 测试验证
    test_ids = [
        'SN-QT-Z-001',  # 恶寒
        'SN-HD-Z-001',  # 头痛
        'DR-JB-001',    # 麻黄
        'DR-AS-001',    # 酸枣仁
        'SY-TY-001',    # 太阳中风
        'SY-TY-002',    # 太阳伤寒
        'FP-TY-001',    # 桂枝汤
        'FP-TY-002',    # 麻黄汤
        'RL-18F-001',   # 十八反第1条
        'RL-19W-001',   # 十九畏第1条
    ]
    
    for tid in test_ids:
        print(f"{tid}: {get_id_description(tid)}")
    
    # 测试验证
    print("\n验证测试:")
    print(f"SN-QT-Z-001 valid: {validate_symptom_id('SN-QT-Z-001')}")
    print(f"SN-INVALID-001 valid: {validate_symptom_id('SN-INVALID-001')}")
    print(f"DR-JB-001 valid: {validate_drug_id('DR-JB-001')}")
    print(f"SY-TY-001 valid: {validate_syndrome_id('SY-TY-001')}")
    print(f"FP-TY-001 valid: {validate_formula_id('FP-TY-001')}")
    print(f"RL-18F-001 valid: {validate_rule_id('RL-18F-001')}")
