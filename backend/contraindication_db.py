#!/usr/bin/env python3
"""
小神农中医AI - 十八反/十九畏/七情配伍禁忌规则库
编码格式：RL-规则组-序号
"""

from code_system import RULE_GROUP_CODES

# ========== 十八反规则库 ==========
RULE_18FAN = {
    'rule_group': '十八反',
    'rule_group_id': 'RL-18F',
    'source': '《神农本草经》· 十八反歌诀',
    'verse': '本草明言十八反，半蒌贝蔹及攻乌，藻戟遂芫俱战草，诸参辛芍叛藜芦。',
    
    'rules': [
        {
            'rule_id': 'RL-18F-001',
            'type': '相反',
            'drug_a': 'DR-QT-004',  # 乌头（川乌/草乌/附子）
            'drug_a_name': '乌头',
            'drug_a_aliases': ['川乌', '草乌', '附子'],
            'drug_b_list': ['DR-HQ-001', 'DR-HQ-002', 'DR-LS-001', 'DR-WY-001'],
            'drug_b_names': ['半夏', '瓜蒌', '贝母', '白蔹'],
            'drug_b_aliases': {
                'DR-HQ-001': ['半夏', '法半夏', '姜半夏', '清半夏'],
                'DR-HQ-002': ['瓜蒌', '瓜蒌皮', '瓜蒌仁', '天花粉'],
                'DR-LS-001': ['贝母', '川贝母', '浙贝母'],
                'DR-WY-001': ['白蔹'],
            },
            'severity': '剧毒',
            'mechanism': '乌头碱与这些药物的生物碱相互作用，增强毒性，可致心律失常、呼吸麻痹',
            'clinical_evidence': '有中毒案例报告，可致死',
            'verse_line': '半蒌贝蔹及攻乌',
            'symptoms': ['恶心呕吐', '口舌麻木', '四肢抽搐', '心律失常', '呼吸困难'],
            'antidote': '立即停用，洗胃，对症支持，阿托品',
        },
        {
            'rule_id': 'RL-18F-002',
            'type': '相反',
            'drug_a': 'DR-QT-004',
            'drug_a_name': '乌头',
            'drug_b_list': ['DR-WY-002'],
            'drug_b_names': ['白及'],
            'drug_b_aliases': {
                'DR-WY-002': ['白及'],
            },
            'severity': '剧毒',
            'mechanism': '同RL-18F-001',
            'clinical_evidence': '有中毒案例报告',
            'verse_line': '半蒌贝蔹及攻乌（续）',
            'symptoms': ['恶心呕吐', '口舌麻木', '四肢抽搐', '心律失常', '呼吸困难'],
            'antidote': '立即停用，洗胃，对症支持',
        },
        {
            'rule_id': 'RL-18F-003',
            'type': '相反',
            'drug_a': 'DR-QT-005',  # 甘草
            'drug_a_name': '甘草',
            'drug_a_aliases': ['甘草', '生甘草', '炙甘草', '甘草梢'],
            'drug_b_list': ['DR-LS-002', 'DR-LS-003', 'DR-LS-004', 'DR-LS-005'],
            'drug_b_names': ['海藻', '大戟', '甘遂', '芫花'],
            'drug_b_aliases': {
                'DR-LS-002': ['海藻', '海带'],
                'DR-LS-003': ['大戟', '红大戟', '京大戟'],
                'DR-LS-004': ['甘遂'],
                'DR-LS-005': ['芫花'],
            },
            'severity': '剧毒',
            'mechanism': '甘草酸与这些药物的毒性成分相互作用，增强毒性',
            'clinical_evidence': '动物实验显示毒性增强',
            'verse_line': '藻戟遂芫俱战草',
            'symptoms': ['腹痛腹泻', '恶心呕吐', '脱水', '电解质紊乱'],
            'antidote': '立即停用，补液，对症支持',
        },
        {
            'rule_id': 'RL-18F-004',
            'type': '相反',
            'drug_a': 'DR-BY-001',  # 人参
            'drug_a_name': '人参',
            'drug_a_aliases': ['人参', '生晒参', '红参', '西洋参', '党参', '太子参', '丹参', '玄参', '沙参', '苦参', '细辛', '白芍', '赤芍'],
            'drug_b_list': ['DR-LS-006'],
            'drug_b_names': ['藜芦'],
            'drug_b_aliases': {
                'DR-LS-006': ['藜芦'],
            },
            'severity': '剧毒',
            'mechanism': '藜芦碱与人参皂苷相互作用，产生毒性',
            'clinical_evidence': '有中毒案例报告',
            'verse_line': '诸参辛芍叛藜芦',
            'note': '诸参包括：人参、丹参、玄参、沙参、苦参、党参；辛指细辛；芍指白芍、赤芍',
            'symptoms': ['恶心呕吐', '腹痛', '头晕', '心悸', '血压下降'],
            'antidote': '立即停用，洗胃，对症支持',
        },
    ],
}

# ========== 十九畏规则库 ==========
RULE_19WEI = {
    'rule_group': '十九畏',
    'rule_group_id': 'RL-19W',
    'source': '《神农本草经》· 十九畏歌诀',
    'verse': '硫黄原是火中精，朴硝一见便相争。水银莫与砒霜见，狼毒最怕密陀僧。巴豆性烈最为上，偏与牵牛不顺情。丁香莫与郁金见，川乌草乌不顺犀。牙硝难合京三棱，官桂善能调冷气，若逢石脂便相欺。人参最怕五灵脂。',
    
    'rules': [
        {
            'rule_id': 'RL-19W-001',
            'type': '相畏',
            'drug_a': 'DR-XY-001',  # 硫黄
            'drug_a_name': '硫黄',
            'drug_b': 'DR-XY-002',  # 朴硝
            'drug_b_name': '朴硝',
            'drug_b_aliases': ['朴硝', '芒硝', '玄明粉'],
            'severity': '严重',
            'mechanism': '硫黄性温，朴硝性寒，寒热相激，可致腹泻、腹痛',
            'clinical_evidence': '传统经验禁忌',
            'verse_line': '硫黄原是火中精，朴硝一见便相争',
            'symptoms': ['腹痛', '腹泻', '恶心'],
        },
        {
            'rule_id': 'RL-19W-002',
            'type': '相畏',
            'drug_a': 'DR-QT-006',  # 水银
            'drug_a_name': '水银',
            'drug_b': 'DR-QT-007',  # 砒霜
            'drug_b_name': '砒霜',
            'drug_b_aliases': ['砒霜', '信石', '砒石'],
            'severity': '剧毒',
            'mechanism': '两者均为剧毒重金属，合用毒性叠加',
            'clinical_evidence': '有致死案例',
            'verse_line': '水银莫与砒霜见',
            'symptoms': ['急性中毒', '多器官衰竭'],
            'antidote': '立即就医，二巯丙醇',
        },
        {
            'rule_id': 'RL-19W-003',
            'type': '相畏',
            'drug_a': 'DR-QT-008',  # 狼毒
            'drug_a_name': '狼毒',
            'drug_b': 'DR-QT-009',  # 密陀僧
            'drug_b_name': '密陀僧',
            'drug_b_aliases': ['密陀僧', '铅黄'],
            'severity': '严重',
            'mechanism': '两者毒性叠加',
            'clinical_evidence': '传统经验禁忌',
            'verse_line': '狼毒最怕密陀僧',
            'symptoms': ['中毒反应'],
        },
        {
            'rule_id': 'RL-19W-004',
            'type': '相畏',
            'drug_a': 'DR-XY-003',  # 巴豆
            'drug_a_name': '巴豆',
            'drug_b': 'DR-LS-007',  # 牵牛子
            'drug_b_name': '牵牛子',
            'drug_b_aliases': ['牵牛子', '黑丑', '白丑', '二丑'],
            'severity': '严重',
            'mechanism': '两者均为峻下之品，合用致泻作用过强，可致脱水、电解质紊乱',
            'clinical_evidence': '动物实验显示腹泻加重',
            'verse_line': '巴豆性烈最为上，偏与牵牛不顺情',
            'symptoms': ['剧烈腹泻', '脱水', '电解质紊乱', '腹痛'],
        },
        {
            'rule_id': 'RL-19W-005',
            'type': '相畏',
            'drug_a': 'DR-LQ-001',  # 丁香
            'drug_a_name': '丁香',
            'drug_b': 'DR-LQ-002',  # 郁金
            'drug_b_name': '郁金',
            'drug_b_aliases': ['郁金', '川郁金', '广郁金'],
            'severity': '中等',
            'mechanism': '丁香性温，郁金性寒，功效相反，合用降低药效',
            'clinical_evidence': '传统经验禁忌',
            'verse_line': '丁香莫与郁金见',
            'symptoms': ['药效降低'],
        },
        {
            'rule_id': 'RL-19W-006',
            'type': '相畏',
            'drug_a': 'DR-QT-004',  # 川乌/草乌
            'drug_a_name': '川乌/草乌',
            'drug_a_aliases': ['川乌', '草乌', '附子'],
            'drug_b': 'DR-QT-010',  # 犀角（现代用水牛角代替）
            'drug_b_name': '犀角',
            'drug_b_aliases': ['犀角', '水牛角'],
            'severity': '严重',
            'mechanism': '乌头辛热，犀角咸寒，寒热相激',
            'clinical_evidence': '传统经验禁忌',
            'verse_line': '川乌草乌不顺犀',
            'symptoms': ['药效降低', '可能毒性增强'],
        },
        {
            'rule_id': 'RL-19W-007',
            'type': '相畏',
            'drug_a': 'DR-XY-004',  # 牙硝
            'drug_a_name': '牙硝',
            'drug_a_aliases': ['牙硝', '芒硝'],
            'drug_b': 'DR-HY-003',  # 三棱
            'drug_b_name': '三棱',
            'drug_b_aliases': ['三棱', '京三棱'],
            'severity': '中等',
            'mechanism': '功效相反，合用降低药效',
            'clinical_evidence': '传统经验禁忌',
            'verse_line': '牙硝难合京三棱',
            'symptoms': ['药效降低'],
        },
        {
            'rule_id': 'RL-19W-008',
            'type': '相畏',
            'drug_a': 'DR-WL-003',  # 官桂
            'drug_a_name': '官桂',
            'drug_a_aliases': ['官桂', '肉桂', '桂枝'],
            'drug_b': 'DR-SS-001',  # 石脂
            'drug_b_name': '石脂',
            'drug_b_aliases': ['赤石脂', '白石脂'],
            'severity': '中等',
            'mechanism': '官桂辛热，石脂酸涩收敛，功效相反',
            'clinical_evidence': '传统经验禁忌',
            'verse_line': '官桂善能调冷气，若逢石脂便相欺',
            'symptoms': ['药效降低'],
        },
        {
            'rule_id': 'RL-19W-009',
            'type': '相畏',
            'drug_a': 'DR-BY-001',  # 人参
            'drug_a_name': '人参',
            'drug_b': 'DR-SS-002',  # 五灵脂
            'drug_b_name': '五灵脂',
            'drug_b_aliases': ['五灵脂'],
            'severity': '严重',
            'mechanism': '五灵脂破坏人参有效成分，降低药效',
            'clinical_evidence': '传统经验禁忌，现代研究证实',
            'verse_line': '人参最怕五灵脂',
            'symptoms': ['药效降低', '可能产生不良反应'],
        },
    ],
}

# ========== 七情配伍规则库 ==========
RULE_7QING = {
    'rule_group': '七情配伍',
    'rule_group_id': 'RL-7Q',
    'source': '《神农本草经》· 七情配伍',
    'description': '单行、相须、相使、相畏、相杀、相恶、相反',
    
    'rules': [
        {
            'rule_id': 'RL-7Q-001',
            'type': '相须',
            'drug_a': 'DR-JB-001',  # 麻黄
            'drug_a_name': '麻黄',
            'drug_b': 'DR-JB-002',  # 桂枝
            'drug_b_name': '桂枝',
            'effect': '协同增效',
            'mechanism': '麻黄发汗解表，桂枝温经通阳，合用增强发汗解表之力',
            'example_formula': 'FP-TY-002',  # 麻黄汤
            'example_formula_name': '麻黄汤',
            'alert': '🟢 优良配伍',
        },
        {
            'rule_id': 'RL-7Q-002',
            'type': '相使',
            'drug_a': 'DR-JB-001',  # 麻黄
            'drug_a_name': '麻黄',
            'drug_b': 'DR-HQ-001',  # 杏仁
            'drug_b_name': '杏仁',
            'effect': '辅助增效',
            'mechanism': '麻黄宣肺平喘，杏仁降肺止咳，一宣一降，增强平喘效果',
            'example_formula': 'FP-TY-002',  # 麻黄汤
            'example_formula_name': '麻黄汤',
            'alert': '🟢 优良配伍',
        },
        {
            'rule_id': 'RL-7Q-003',
            'type': '相畏',
            'drug_a': 'DR-JB-001',  # 麻黄
            'drug_a_name': '麻黄',
            'drug_b': 'DR-BY-002',  # 甘草
            'drug_b_name': '甘草',
            'effect': '缓和烈性',
            'mechanism': '甘草缓和麻黄发汗之力，防止过汗伤正',
            'example_formula': 'FP-TY-002',  # 麻黄汤
            'example_formula_name': '麻黄汤',
            'alert': '🟡 注意：降低麻黄发汗力',
        },
        {
            'rule_id': 'RL-7Q-004',
            'type': '相杀',
            'drug_a': 'DR-BY-002',  # 甘草
            'drug_a_name': '甘草',
            'drug_b': 'DR-QT-004',  # 附子
            'drug_b_name': '附子',
            'effect': '制约毒性',
            'mechanism': '甘草可降低附子毒性，延长煎煮时间也可减毒',
            'example_formula': 'FP-SY2-001',  # 四逆汤
            'example_formula_name': '四逆汤',
            'alert': '🟢 安全配伍：甘草制约附子毒性',
        },
        {
            'rule_id': 'RL-7Q-005',
            'type': '相恶',
            'drug_a': 'DR-BY-001',  # 人参
            'drug_a_name': '人参',
            'drug_b': 'DR-XY-002',  # 莱菔子（萝卜子）
            'drug_b_name': '莱菔子',
            'effect': '降低药效',
            'mechanism': '莱菔子行气破气，削弱人参补气作用',
            'alert': '🔴 避免同用：莱菔子削弱人参补气功效',
        },
    ],
}


# ========== 查询接口 ==========

def check_18fan(drug_a: str, drug_b: str) -> dict:
    """检查两药是否属于十八反"""
    for rule in RULE_18FAN['rules']:
        if rule['drug_a'] == drug_a:
            if drug_b in rule['drug_b_list']:
                return {
                    'is_contraindicated': True,
                    'rule_id': rule['rule_id'],
                    'rule_group': '十八反',
                    'severity': rule['severity'],
                    'drug_a': rule['drug_a_name'],
                    'drug_b': rule['drug_b_names'][rule['drug_b_list'].index(drug_b)],
                    'mechanism': rule['mechanism'],
                    'symptoms': rule.get('symptoms', []),
                    'verse': rule['verse_line'],
                }
        # 反向检查
        if drug_b == rule['drug_a']:
            if drug_a in rule['drug_b_list']:
                return {
                    'is_contraindicated': True,
                    'rule_id': rule['rule_id'],
                    'rule_group': '十八反',
                    'severity': rule['severity'],
                    'drug_a': rule['drug_b_names'][rule['drug_b_list'].index(drug_a)],
                    'drug_b': rule['drug_a_name'],
                    'mechanism': rule['mechanism'],
                    'symptoms': rule.get('symptoms', []),
                    'verse': rule['verse_line'],
                }
    return {'is_contraindicated': False}


def check_19wei(drug_a: str, drug_b: str) -> dict:
    """检查两药是否属于十九畏"""
    for rule in RULE_19WEI['rules']:
        if rule['drug_a'] == drug_a and rule['drug_b'] == drug_b:
            return {
                'is_contraindicated': True,
                'rule_id': rule['rule_id'],
                'rule_group': '十九畏',
                'severity': rule['severity'],
                'drug_a': rule['drug_a_name'],
                'drug_b': rule['drug_b_name'],
                'mechanism': rule['mechanism'],
                'symptoms': rule.get('symptoms', []),
                'verse': rule['verse_line'],
            }
        if rule['drug_a'] == drug_b and rule['drug_b'] == drug_a:
            return {
                'is_contraindicated': True,
                'rule_id': rule['rule_id'],
                'rule_group': '十九畏',
                'severity': rule['severity'],
                'drug_a': rule['drug_b_name'],
                'drug_b': rule['drug_a_name'],
                'mechanism': rule['mechanism'],
                'symptoms': rule.get('symptoms', []),
                'verse': rule['verse_line'],
            }
    return {'is_contraindicated': False}


def check_7qing(drug_a: str, drug_b: str) -> dict:
    """检查两药的七情配伍关系"""
    for rule in RULE_7QING['rules']:
        if (rule['drug_a'] == drug_a and rule['drug_b'] == drug_b) or \
           (rule['drug_a'] == drug_b and rule['drug_b'] == drug_a):
            return {
                'has_relation': True,
                'rule_id': rule['rule_id'],
                'type': rule['type'],
                'drug_a': rule['drug_a_name'],
                'drug_b': rule['drug_b_name'],
                'effect': rule['effect'],
                'mechanism': rule['mechanism'],
                'example_formula': rule.get('example_formula_name', ''),
                'alert': rule.get('alert', ''),
            }
    return {'has_relation': False}


def check_all_contraindications(drug_list: list) -> list:
    """检查药物列表中的所有禁忌关系"""
    results = []
    checked_pairs = set()
    
    for i, drug_a in enumerate(drug_list):
        for drug_b in drug_list[i+1:]:
            pair = tuple(sorted([drug_a, drug_b]))
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)
            
            # 检查十八反
            fan = check_18fan(drug_a, drug_b)
            if fan['is_contraindicated']:
                results.append({
                    'type': '十八反',
                    'severity': fan['severity'],
                    'drug_a': fan['drug_a'],
                    'drug_b': fan['drug_b'],
                    'rule_id': fan['rule_id'],
                    'mechanism': fan['mechanism'],
                    'symptoms': fan['symptoms'],
                    'verse': fan['verse'],
                    'alert': '🔴 禁忌配伍：不可同用！',
                })
                continue
            
            # 检查十九畏
            wei = check_19wei(drug_a, drug_b)
            if wei['is_contraindicated']:
                results.append({
                    'type': '十九畏',
                    'severity': wei['severity'],
                    'drug_a': wei['drug_a'],
                    'drug_b': wei['drug_b'],
                    'rule_id': wei['rule_id'],
                    'mechanism': wei['mechanism'],
                    'symptoms': wei['symptoms'],
                    'verse': wei['verse'],
                    'alert': '🟠 相畏配伍：慎用！',
                })
                continue
            
            # 检查七情配伍
            qing = check_7qing(drug_a, drug_b)
            if qing['has_relation']:
                results.append({
                    'type': '七情配伍',
                    'relation_type': qing['type'],
                    'drug_a': qing['drug_a'],
                    'drug_b': qing['drug_b'],
                    'effect': qing['effect'],
                    'mechanism': qing['mechanism'],
                    'example_formula': qing['example_formula'],
                    'alert': qing['alert'],
                })
    
    return results


if __name__ == "__main__":
    # 测试
    print("=== 十八反测试 ===")
    result = check_18fan('DR-QT-004', 'DR-HQ-001')
    print(f"乌头+半夏: {'禁忌' if result['is_contraindicated'] else '安全'}")
    if result['is_contraindicated']:
        print(f"  严重程度: {result['severity']}")
        print(f"  机制: {result['mechanism']}")
        print(f"  歌诀: {result['verse']}")
    
    print("\n=== 十九畏测试 ===")
    result = check_19wei('DR-BY-001', 'DR-SS-002')
    print(f"人参+五灵脂: {'禁忌' if result['is_contraindicated'] else '安全'}")
    if result['is_contraindicated']:
        print(f"  严重程度: {result['severity']}")
        print(f"  歌诀: {result['verse']}")
    
    print("\n=== 七情配伍测试 ===")
    result = check_7qing('DR-JB-001', 'DR-JB-002')
    print(f"麻黄+桂枝: {'有配伍关系' if result['has_relation'] else '无特殊关系'}")
    if result['has_relation']:
        print(f"  类型: {result['type']}")
        print(f"  效果: {result['effect']}")
        print(f"  {result['alert']}")
    
    print("\n=== 方剂禁忌检查测试 ===")
    # 麻黄汤组成：麻黄、桂枝、杏仁、甘草
    formula_drugs = ['DR-JB-001', 'DR-JB-002', 'DR-HQ-001', 'DR-BY-002']
    contras = check_all_contraindications(formula_drugs)
    print(f"麻黄汤组成药物禁忌检查: {len(contras)}条")
    for c in contras:
        print(f"  {c['alert']} - {c.get('type', c.get('relation_type', ''))}")
    
    # 四逆汤组成：附子、干姜、甘草
    print("\n四逆汤组成药物禁忌检查:")
    sini_drugs = ['DR-WL-001', 'DR-WL-002', 'DR-BY-002']
    contras = check_all_contraindications(sini_drugs)
    print(f"  {len(contras)}条")
    for c in contras:
        print(f"  {c['alert']} - {c.get('type', c.get('relation_type', ''))}")
