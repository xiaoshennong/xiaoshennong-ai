#!/usr/bin/env python3
"""
小神农中医AI - 批判性思维验证引擎 v2.0
三阶九维可信度评估法
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class CredibilityDimension:
    """可信度维度评分"""
    name: str
    score: float  # 0-5
    max_score: float = 5.0
    description: str = ""
    evidence: str = ""


@dataclass
class CredibilityAssessment:
    """可信度评估结果"""
    source_id: str
    source_name: str
    source_url: str
    dimensions: List[CredibilityDimension]
    total_score: float
    grade: str  # A/B/C/D
    is_adopted: bool
    limitations: List[str]
    adoption_reason: str


class CriticalThinkingEngine:
    """
    批判性思维验证引擎
    三阶九维评估法
    """
    
    # 来源优先级映射
    SOURCE_PRIORITY = {
        'P0': {'name': '中医核心期刊', 'base_score': 5.0},
        'P1': {'name': '中医科学院/高校附属医院', 'base_score': 4.5},
        'P2': {'name': '权威中医数据库/医案集', 'base_score': 4.5},
        'P3': {'name': '中医临床指南/共识', 'base_score': 4.5},
        'P4': {'name': '科普类中医平台', 'base_score': 3.0},
        'P5': {'name': '综合医疗平台', 'base_score': 2.0},
        'P6': {'name': '社交媒体/论坛', 'base_score': 1.0},
    }
    
    # 证据等级映射
    EVIDENCE_LEVEL = {
        'RCT': {'name': '随机对照试验/系统综述', 'score': 5.0},
        'cohort': {'name': '队列研究/病例对照', 'score': 4.0},
        'case_series': {'name': '病例系列/名医经验', 'score': 3.0},
        'case_report': {'name': '个案报告', 'score': 2.0},
        'theory': {'name': '纯理论/个人经验', 'score': 1.0},
    }
    
    # 一票否决项关键词
    VETO_KEYWORDS = [
        '广告', '推销', '代购', '微商', '保健品推销',
        '伪科学', '玄学', '迷信', '神效', '包治',
        '治愈率100%', '无效退款', '祖传秘方',
    ]
    
    def __init__(self):
        self.assessment_history = []
    
    def assess_source_credibility(
        self,
        source_text: str,
        source_url: str = "",
        source_type: str = "unknown",
        author_title: str = "",
        publish_year: int = 0,
        sample_size: int = 0,
        evidence_type: str = "",
        symptom_match: float = 0.0,
        population_match: float = 0.0,
        conflict_check: float = 0.0,
    ) -> CredibilityAssessment:
        """
        对单一来源进行三阶九维可信度评估
        
        Args:
            source_text: 来源文本内容
            source_url: 来源URL
            source_type: 来源类型 (P0-P6)
            author_title: 作者职称
            publish_year: 发表年份
            sample_size: 样本量
            evidence_type: 证据类型 (RCT/cohort/case_series/case_report/theory)
            symptom_match: 症状匹配度 (0-1)
            population_match: 人群匹配度 (0-1)
            conflict_check: 冲突检测结果 (0-1, 1=无冲突)
        
        Returns:
            CredibilityAssessment: 评估结果
        """
        
        dimensions = []
        
        # === 第一阶：来源可信度 ===
        
        # 维度1: 来源权威性
        source_priority = self.SOURCE_PRIORITY.get(source_type, {'name': '未知来源', 'base_score': 1.0})
        dim1 = CredibilityDimension(
            name="来源权威性",
            score=source_priority['base_score'],
            description=f"来源类型: {source_priority['name']}"
        )
        dimensions.append(dim1)
        
        # 维度2: 作者资质
        author_score = self._assess_author_title(author_title)
        dim2 = CredibilityDimension(
            name="作者资质",
            score=author_score,
            description=f"作者职称: {author_title or '未标注'}"
        )
        dimensions.append(dim2)
        
        # 维度3: 发表时间
        time_score = self._assess_publish_time(publish_year)
        dim3 = CredibilityDimension(
            name="发表时间",
            score=time_score,
            description=f"发表年份: {publish_year or '未知'}"
        )
        dimensions.append(dim3)
        
        # === 第二阶：内容可信度 ===
        
        # 维度4: 证据等级
        evidence = self.EVIDENCE_LEVEL.get(evidence_type, {'name': '未知', 'score': 1.0})
        dim4 = CredibilityDimension(
            name="证据等级",
            score=evidence['score'],
            description=f"证据类型: {evidence['name']}"
        )
        dimensions.append(dim4)
        
        # 维度5: 样本量
        sample_score = self._assess_sample_size(sample_size)
        dim5 = CredibilityDimension(
            name="样本量",
            score=sample_score,
            description=f"样本量: {sample_size or '未知'}"
        )
        dimensions.append(dim5)
        
        # 维度6: 一致性 (默认假设单一来源)
        dim6 = CredibilityDimension(
            name="一致性",
            score=3.0,  # 单一来源无法验证一致性，给中等分
            description="单一来源，一致性待验证"
        )
        dimensions.append(dim6)
        
        # === 第三阶：适用可信度 ===
        
        # 维度7: 症状匹配度
        dim7 = CredibilityDimension(
            name="症状匹配度",
            score=symptom_match * 5,
            description=f"症状匹配度: {symptom_match*100:.0f}%"
        )
        dimensions.append(dim7)
        
        # 维度8: 人群匹配度
        dim8 = CredibilityDimension(
            name="人群匹配度",
            score=population_match * 5,
            description=f"人群匹配度: {population_match*100:.0f}%"
        )
        dimensions.append(dim8)
        
        # 维度9: 冲突检测
        dim9 = CredibilityDimension(
            name="冲突检测",
            score=conflict_check * 5,
            description=f"冲突检测结果: {'无冲突' if conflict_check > 0.8 else '有潜在冲突'}"
        )
        dimensions.append(dim9)
        
        # 计算总分
        total_score = sum(d.score for d in dimensions) / len(dimensions)
        
        # 一票否决检查
        veto_reason = self._check_veto(source_text)
        
        if veto_reason:
            total_score = 0.0
            grade = 'D'
            is_adopted = False
            adoption_reason = f"一票否决: {veto_reason}"
        else:
            grade = self._score_to_grade(total_score)
            is_adopted = total_score >= 2.5
            adoption_reason = self._get_adoption_reason(total_score, grade)
        
        # 生成局限性说明
        limitations = self._generate_limitations(dimensions, sample_size, evidence_type)
        
        assessment = CredibilityAssessment(
            source_id=f"SRC-{len(self.assessment_history)+1:03d}",
            source_name=source_priority['name'],
            source_url=source_url,
            dimensions=dimensions,
            total_score=total_score,
            grade=grade,
            is_adopted=is_adopted,
            limitations=limitations,
            adoption_reason=adoption_reason,
        )
        
        self.assessment_history.append(assessment)
        return assessment
    
    def _assess_author_title(self, title: str) -> float:
        """评估作者资质"""
        if not title:
            return 2.0
        
        high_titles = ['主任医师', '教授', '名中医', '国医大师', '院士']
        mid_titles = ['主治医师', '博士', '副主任医师', '副教授']
        low_titles = ['住院医师', '硕士', '医师']
        
        for t in high_titles:
            if t in title:
                return 5.0
        for t in mid_titles:
            if t in title:
                return 4.0
        for t in low_titles:
            if t in title:
                return 3.0
        
        return 2.0
    
    def _assess_publish_time(self, year: int) -> float:
        """评估发表时间"""
        if year == 0:
            return 2.0
        
        from datetime import datetime
        current_year = datetime.now().year
        age = current_year - year
        
        if age <= 5:
            return 5.0
        elif age <= 10:
            return 4.0
        elif age <= 20:
            return 3.0
        else:
            return 2.0
    
    def _assess_sample_size(self, n: int) -> float:
        """评估样本量"""
        if n == 0:
            return 1.0
        
        if n >= 100:
            return 5.0
        elif n >= 50:
            return 4.0
        elif n >= 20:
            return 3.0
        elif n >= 10:
            return 2.0
        else:
            return 1.0
    
    def _check_veto(self, text: str) -> Optional[str]:
        """检查一票否决项"""
        text_lower = text.lower()
        for keyword in self.VETO_KEYWORDS:
            if keyword in text_lower:
                return f"检测到否决关键词: {keyword}"
        return None
    
    def _score_to_grade(self, score: float) -> str:
        """分数转等级"""
        if score >= 4.5:
            return 'A'
        elif score >= 3.5:
            return 'B'
        elif score >= 2.5:
            return 'C'
        else:
            return 'D'
    
    def _get_adoption_reason(self, score: float, grade: str) -> str:
        """获取采用建议"""
        if grade == 'A':
            return "高度可信，直接采用"
        elif grade == 'B':
            return "基本可信，采用但需标注局限性"
        elif grade == 'C':
            return "有限可信，仅作参考，不主导回答"
        else:
            return "不可信，排除不采用"
    
    def _generate_limitations(self, dimensions: List[CredibilityDimension], 
                             sample_size: int, evidence_type: str) -> List[str]:
        """生成局限性说明"""
        limitations = []
        
        # 检查样本量
        if sample_size < 50:
            limitations.append(f"样本量较小({sample_size}例)，统计效力有限")
        
        # 检查证据等级
        if evidence_type not in ['RCT', 'cohort']:
            limitations.append(f"非RCT研究，证据等级有限")
        
        # 检查一致性
        consistency_dim = next((d for d in dimensions if d.name == "一致性"), None)
        if consistency_dim and consistency_dim.score < 4:
            limitations.append("单一来源，缺乏多中心验证")
        
        # 检查时间
        time_dim = next((d for d in dimensions if d.name == "发表时间"), None)
        if time_dim and time_dim.score < 3:
            limitations.append("发表时间较早，可能未反映最新研究进展")
        
        return limitations
    
    def batch_assess(self, sources: List[Dict]) -> List[CredibilityAssessment]:
        """批量评估多个来源"""
        results = []
        for source in sources:
            assessment = self.assess_source_credibility(**source)
            results.append(assessment)
        return results
    
    def get_adopted_sources(self) -> List[CredibilityAssessment]:
        """获取被采用的来源"""
        return [a for a in self.assessment_history if a.is_adopted]
    
    def get_rejected_sources(self) -> List[CredibilityAssessment]:
        """获取被拒绝的来源"""
        return [a for a in self.assessment_history if not a.is_adopted]
    
    def format_assessment_report(self, assessment: CredibilityAssessment) -> str:
        """格式化评估报告"""
        lines = []
        lines.append(f"【批判性思维验证报告】")
        lines.append(f"来源：{assessment.source_name}")
        lines.append(f"URL：{assessment.source_url}")
        lines.append("")
        
        lines.append("九维评估：")
        for i, dim in enumerate(assessment.dimensions, 1):
            stars = "★" * int(dim.score) + "☆" * (5 - int(dim.score))
            lines.append(f"  {i}. {dim.name}：{stars} ({dim.score:.1f}/5.0)")
            lines.append(f"     {dim.description}")
        
        lines.append("")
        lines.append(f"总分：{assessment.total_score:.1f} / 5.0 → 评级：{assessment.grade}级")
        lines.append(f"采用建议：{assessment.adoption_reason}")
        
        if assessment.limitations:
            lines.append("")
            lines.append("局限性说明：")
            for lim in assessment.limitations:
                lines.append(f"  - {lim}")
        
        return "\n".join(lines)


# ========== 症状共现强度分析模块 ==========

class SymptomCooccurrenceAnalyzer:
    """
    症状共现强度分析器
    用于辨别并发症 vs 药物副作用
    """
    
    # 正常共现强度阈值
    NORMAL_COOCURRENCE_THRESHOLD = 0.5
    
    # 异常共现强度阈值（触发副作用警报）
    ABNORMAL_COOCURRENCE_THRESHOLD = 0.2
    
    def __init__(self):
        # 症状共现数据库 (从古籍和临床数据中学习)
        self.cooccurrence_db = {}
        # 副作用共现数据库
        self.adverse_cooccurrence_db = {}
    
    def add_cooccurrence(self, symptom_a: str, symptom_b: str, 
                         strength: float, source: str, case_count: int = 0):
        """
        添加症状共现记录
        
        Args:
            symptom_a: 症状A ID
            symptom_b: 症状B ID
            strength: 共现强度 (0-1)
            source: 来源 (古籍/临床/文献)
            case_count: 案例数
        """
        pair = tuple(sorted([symptom_a, symptom_b]))
        
        if pair not in self.cooccurrence_db:
            self.cooccurrence_db[pair] = {
                'strength': strength,
                'sources': [],
                'case_count': 0,
            }
        
        self.cooccurrence_db[pair]['sources'].append(source)
        self.cooccurrence_db[pair]['case_count'] += case_count
        
        # 更新强度（加权平均）
        old_count = self.cooccurrence_db[pair]['case_count'] - case_count
        if old_count > 0:
            old_strength = self.cooccurrence_db[pair]['strength']
            self.cooccurrence_db[pair]['strength'] = (
                (old_strength * old_count + strength * case_count) / 
                (old_count + case_count)
            )
    
    def get_cooccurrence_strength(self, symptom_a: str, symptom_b: str) -> float:
        """获取两个症状的共现强度"""
        pair = tuple(sorted([symptom_a, symptom_b]))
        return self.cooccurrence_db.get(pair, {}).get('strength', 0.0)
    
    def analyze_symptom_combination(self, symptoms: List[str]) -> Dict:
        """
        分析症状组合，识别异常共现
        
        Returns:
            {
                'normal_cooccurrences': [...],  # 正常共现
                'abnormal_cooccurrences': [...],  # 异常共现（可能副作用）
                'alerts': [...],  # 警报信息
            }
        """
        normal = []
        abnormal = []
        alerts = []
        
        for i, sa in enumerate(symptoms):
            for sb in symptoms[i+1:]:
                strength = self.get_cooccurrence_strength(sa, sb)
                
                pair_info = {
                    'symptom_a': sa,
                    'symptom_b': sb,
                    'strength': strength,
                    'interpretation': '',
                }
                
                if strength >= self.NORMAL_COOCURRENCE_THRESHOLD:
                    pair_info['interpretation'] = '正常共现（常见于同一证型）'
                    normal.append(pair_info)
                elif strength <= self.ABNORMAL_COOCURRENCE_THRESHOLD and strength > 0:
                    pair_info['interpretation'] = '异常共现（可能提示副作用或并发症）'
                    abnormal.append(pair_info)
                    alerts.append(
                        f"⚠️ 异常症状组合：{sa} + {sb}（共现强度{strength:.2f}，远低于正常阈值）"
                    )
                elif strength == 0:
                    pair_info['interpretation'] = '无共现记录（可能为副作用或新发症状）'
                    abnormal.append(pair_info)
                    alerts.append(
                        f"🔴 未知症状组合：{sa} + {sb}（知识库中无共现记录，高度怀疑副作用）"
                    )
        
        return {
            'normal_cooccurrences': normal,
            'abnormal_cooccurrences': abnormal,
            'alerts': alerts,
            'total_pairs': len(symptoms) * (len(symptoms) - 1) // 2,
            'abnormal_count': len(abnormal),
        }
    
    def check_drug_adverse(self, drug_id: str, new_symptom: str,
                           known_symptoms: List[str]) -> Dict:
        """
        检查新症状是否为药物副作用
        
        Args:
            drug_id: 药物ID
            new_symptom: 新出现的症状
            known_symptoms: 患者已知的症状（用药前）
        
        Returns:
            副作用分析结果
        """
        # 检查新症状与已知症状的共现强度
        cooccurrence_results = self.analyze_symptom_combination(
            known_symptoms + [new_symptom]
        )
        
        # 检查新症状是否与已知症状存在异常共现
        abnormal_pairs = [
            p for p in cooccurrence_results['abnormal_cooccurrences']
            if p['symptom_b'] == new_symptom or p['symptom_a'] == new_symptom
        ]
        
        is_likely_adverse = len(abnormal_pairs) > 0
        
        return {
            'drug_id': drug_id,
            'new_symptom': new_symptom,
            'is_likely_adverse': is_likely_adverse,
            'abnormal_pairs': abnormal_pairs,
            'confidence': '高' if len(abnormal_pairs) > 1 else '中' if len(abnormal_pairs) == 1 else '低',
            'suggestion': '建议停药观察' if is_likely_adverse else '继续观察',
        }


# ========== 时间窗口副作用检测模块 ==========

class TimeWindowAdverseDetector:
    """
    时间窗口副作用检测器
    基于用药后症状出现的时间判断副作用类型
    """
    
    # 时间窗口定义
    TIME_WINDOWS = {
        'acute_allergy': {'max_minutes': 30, 'name': '急性过敏/不耐受'},
        'common_adverse': {'min_hours': 1, 'max_days': 3, 'name': '常见副作用窗口'},
        'chronic_reaction': {'min_days': 7, 'name': '慢性反应/病情进展'},
    }
    
    def classify_onset_time(self, onset_minutes: float) -> Dict:
        """
        根据症状出现时间分类
        
        Args:
            onset_minutes: 用药后到症状出现的分钟数
        
        Returns:
            分类结果
        """
        if onset_minutes <= 30:
            return {
                'window': 'acute_allergy',
                'name': '急性过敏/不耐受',
                'severity': '高',
                'action': '立即停药，对症处理',
                'confidence': 0.9,
            }
        elif onset_minutes <= 72 * 60:  # 3天内
            return {
                'window': 'common_adverse',
                'name': '常见副作用窗口',
                'severity': '中',
                'action': '密切观察，记录症状变化',
                'confidence': 0.7,
            }
        else:
            return {
                'window': 'chronic_reaction',
                'name': '慢性反应/病情进展',
                'severity': '低',
                'action': '重新辨证，评估病情变化',
                'confidence': 0.5,
            }
    
    def analyze_adverse_timeline(self, events: List[Dict]) -> Dict:
        """
        分析副作用时间线
        
        Args:
            events: [
                {'time': 用药后分钟数, 'symptom': '症状ID', 'severity': '轻度/中度/重度'},
                ...
            ]
        
        Returns:
            时间线分析结果
        """
        timeline = []
        for event in events:
            classification = self.classify_onset_time(event['time'])
            timeline.append({
                'time_minutes': event['time'],
                'symptom': event['symptom'],
                'severity': event['severity'],
                'window': classification['name'],
                'window_type': classification['window'],
                'confidence': classification['confidence'],
            })
        
        # 按时间排序
        timeline.sort(key=lambda x: x['time_minutes'])
        
        # 识别模式
        acute_count = sum(1 for t in timeline if t['window_type'] == 'acute_allergy')
        common_count = sum(1 for t in timeline if t['window_type'] == 'common_adverse')
        chronic_count = sum(1 for t in timeline if t['window_type'] == 'chronic_reaction')
        
        pattern = 'unknown'
        if acute_count > 0:
            pattern = '急性过敏反应'
        elif common_count > 0 and chronic_count > 0:
            pattern = '混合反应（副作用+病情进展）'
        elif common_count > 0:
            pattern = '常见药物副作用'
        elif chronic_count > 0:
            pattern = '慢性反应或病情进展'
        
        return {
            'timeline': timeline,
            'pattern': pattern,
            'acute_count': acute_count,
            'common_count': common_count,
            'chronic_count': chronic_count,
            'recommendation': self._get_recommendation(pattern),
        }
    
    def _get_recommendation(self, pattern: str) -> str:
        """根据模式获取建议"""
        recommendations = {
            '急性过敏反应': '立即停药，使用抗过敏药物，必要时就医',
            '常见药物副作用': '减量或调整处方，观察症状变化',
            '慢性反应或病情进展': '重新辨证，调整治疗方案',
            '混合反应（副作用+病情进展）': '综合评估，可能需要停药并重新辨证',
            'unknown': '继续观察，记录详细症状变化',
        }
        return recommendations.get(pattern, '继续观察')


# ========== 相似患者匹配模块 ==========

class SimilarPatientMatcher:
    """
    相似患者匹配器
    基于多维度相似度计算，找到相似患者案例
    """
    
    # 相似度权重
    SIMILARITY_WEIGHTS = {
        'symptom_overlap': 0.30,
        'syndrome_match': 0.25,
        'constitution_match': 0.15,
        'demographics': 0.10,
        'treatment_response': 0.10,
        'comorbidity': 0.10,
    }
    
    def __init__(self):
        self.patient_db = {}
    
    def add_patient(self, patient_id: str, patient_data: Dict):
        """添加患者档案"""
        self.patient_db[patient_id] = patient_data
    
    def calculate_similarity(self, patient_a: Dict, patient_b: Dict) -> Dict:
        """
        计算两个患者的相似度
        
        Returns:
            {
                'total_score': 总相似度 (0-1),
                'dimensions': 各维度相似度,
                'matched_features': 匹配特征,
            }
        """
        dimensions = {}
        
        # 症状重叠度
        symptoms_a = set(patient_a.get('symptoms', []))
        symptoms_b = set(patient_b.get('symptoms', []))
        if symptoms_a and symptoms_b:
            overlap = len(symptoms_a & symptoms_b) / len(symptoms_a | symptoms_b)
        else:
            overlap = 0.0
        dimensions['symptom_overlap'] = overlap
        
        # 证型匹配
        syndrome_a = patient_a.get('syndrome', '')
        syndrome_b = patient_b.get('syndrome', '')
        syndrome_match = 1.0 if syndrome_a == syndrome_b and syndrome_a else 0.0
        dimensions['syndrome_match'] = syndrome_match
        
        # 体质匹配
        const_a = set(patient_a.get('constitution', []))
        const_b = set(patient_b.get('constitution', []))
        if const_a and const_b:
            const_match = len(const_a & const_b) / len(const_a | const_b)
        else:
            const_match = 0.0
        dimensions['constitution_match'] = const_match
        
        # 人口统计学匹配
        age_a = patient_a.get('age', 0)
        age_b = patient_b.get('age', 0)
        gender_a = patient_a.get('gender', '')
        gender_b = patient_b.get('gender', '')
        
        age_diff = abs(age_a - age_b) if age_a and age_b else 100
        age_sim = max(0, 1 - age_diff / 50)  # 50岁差异为0相似度
        gender_sim = 1.0 if gender_a == gender_b and gender_a else 0.5
        dimensions['demographics'] = (age_sim + gender_sim) / 2
        
        # 治疗反应匹配
        treatment_a = patient_a.get('treatment', '')
        treatment_b = patient_b.get('treatment', '')
        treatment_match = 1.0 if treatment_a == treatment_b and treatment_a else 0.0
        dimensions['treatment_response'] = treatment_match
        
        # 合并症匹配
        comorb_a = set(patient_a.get('comorbidities', []))
        comorb_b = set(patient_b.get('comorbidities', []))
        if comorb_a and comorb_b:
            comorb_match = len(comorb_a & comorb_b) / len(comorb_a | comorb_b)
        else:
            comorb_match = 0.0
        dimensions['comorbidity'] = comorb_match
        
        # 计算加权总分
        total_score = sum(
            dimensions[k] * self.SIMILARITY_WEIGHTS[k]
            for k in dimensions
        )
        
        # 收集匹配特征
        matched_features = []
        if syndrome_match > 0:
            matched_features.append(f"相同证型: {syndrome_a}")
        if overlap > 0.5:
            matched_features.append(f"症状重叠度: {overlap*100:.0f}%")
        if const_match > 0:
            matched_features.append(f"体质相似")
        if treatment_match > 0:
            matched_features.append(f"相同治疗方案")
        
        return {
            'total_score': total_score,
            'dimensions': dimensions,
            'matched_features': matched_features,
        }
    
    def find_similar_patients(self, target_patient: Dict, 
                              top_k: int = 5,
                              min_score: float = 0.5) -> List[Dict]:
        """
        查找相似患者
        
        Args:
            target_patient: 目标患者数据
            top_k: 返回最相似的K个
            min_score: 最小相似度阈值
        
        Returns:
            相似患者列表，按相似度排序
        """
        similarities = []
        
        for patient_id, patient_data in self.patient_db.items():
            if patient_id == target_patient.get('patient_id'):
                continue
            
            sim_result = self.calculate_similarity(target_patient, patient_data)
            
            if sim_result['total_score'] >= min_score:
                similarities.append({
                    'patient_id': patient_id,
                    'similarity_score': sim_result['total_score'],
                    'dimensions': sim_result['dimensions'],
                    'matched_features': sim_result['matched_features'],
                    'patient_data': patient_data,
                })
        
        # 按相似度排序
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similarities[:top_k]
    
    def get_treatment_suggestion(self, target_patient: Dict) -> Dict:
        """
        基于相似患者的治疗建议
        
        Returns:
            {
                'similar_patients': [...],
                'successful_treatments': [...],
                'common_adverse': [...],
                'suggestion': str,
            }
        """
        similar = self.find_similar_patients(target_patient)
        
        if not similar:
            return {
                'similar_patients': [],
                'successful_treatments': [],
                'common_adverse': [],
                'suggestion': '未找到相似患者，建议基于标准证型治疗',
            }
        
        # 收集成功治疗方案
        successful = []
        adverse_events = []
        
        for sim in similar:
            patient = sim['patient_data']
            if patient.get('outcome') == '痊愈' or patient.get('outcome') == '显效':
                successful.append({
                    'treatment': patient.get('treatment', ''),
                    'formula': patient.get('formula', ''),
                    'outcome': patient.get('outcome', ''),
                    'similarity': sim['similarity_score'],
                })
            
            if patient.get('adverse_events'):
                adverse_events.extend(patient['adverse_events'])
        
        # 统计常见副作用
        adverse_counts = {}
        for adv in adverse_events:
            key = adv.get('symptom', '未知')
            adverse_counts[key] = adverse_counts.get(key, 0) + 1
        
        common_adverse = [
            {'symptom': k, 'count': v, 'rate': v/len(similar)*100}
            for k, v in sorted(adverse_counts.items(), key=lambda x: x[1], reverse=True)
        ][:5]
        
        # 生成建议
        if successful:
            top_treatment = successful[0]
            suggestion = (
                f"基于{len(similar)}例相似患者分析，"
                f"{top_treatment['treatment']}方案有效率最高（相似度{top_treatment['similarity']*100:.0f}%）。"
                f"建议参考该方案，并注意监测{', '.join(a['symptom'] for a in common_adverse[:3])}等可能的副作用。"
            )
        else:
            suggestion = '相似患者治疗效果数据不足，建议标准辨证治疗'
        
        return {
            'similar_patients': similar,
            'successful_treatments': successful,
            'common_adverse': common_adverse,
            'suggestion': suggestion,
        }


# ========== 综合副作用辨别引擎 ==========

class AdverseEventDetector:
    """
    综合副作用辨别引擎
    整合症状共现、时间窗口、相似患者等多维度信息
    """
    
    def __init__(self):
        self.cooccurrence_analyzer = SymptomCooccurrenceAnalyzer()
        self.time_detector = TimeWindowAdverseDetector()
        self.patient_matcher = SimilarPatientMatcher()
    
    def detect_adverse_event(
        self,
        patient_id: str,
        drug_id: str,
        new_symptom: str,
        onset_minutes: float,
        known_symptoms: List[str],
        patient_profile: Dict,
    ) -> Dict:
        """
        综合辨别副作用
        
        Returns:
            {
                'is_adverse': bool,
                'confidence': str,
                'score': float,
                'reasoning': str,
                'suggestion': str,
                'similar_cases': [...],
            }
        """
        # 1. 症状共现分析
        cooccur_result = self.cooccurrence_analyzer.check_drug_adverse(
            drug_id, new_symptom, known_symptoms
        )
        
        # 2. 时间窗口分析
        time_result = self.time_detector.classify_onset_time(onset_minutes)
        
        # 3. 相似患者查询
        similar_cases = self.patient_matcher.find_similar_patients(patient_profile)
        
        # 4. 综合评分
        score = 0
        
        # 时间关联性 (0-30分)
        if time_result['window'] == 'acute_allergy':
            score += 25
        elif time_result['window'] == 'common_adverse':
            score += 20
        else:
            score += 10
        
        # 症状共现异常 (0-25分)
        if cooccur_result['is_likely_adverse']:
            score += 20
        else:
            score += 5
        
        # 相似患者数据 (0-25分)
        similar_with_adverse = [
            s for s in similar_cases
            if any(a.get('symptom') == new_symptom for a in 
                   s['patient_data'].get('adverse_events', []))
        ]
        if similar_with_adverse:
            score += 20
        elif similar_cases:
            score += 10
        else:
            score += 5
        
        # 可逆性 (0-20分) - 假设未知，给中等分
        score += 10
        
        # 判断结果
        if score >= 71:
            is_adverse = True
            confidence = '高'
            suggestion = '很可能副作用，建议调整处方或停药'
        elif score >= 41:
            is_adverse = True
            confidence = '中'
            suggestion = '可能相关，建议密切观察并记录症状变化'
        else:
            is_adverse = False
            confidence = '低'
            suggestion = '可能为病情进展，建议重新辨证'
        
        # 生成推理说明
        reasoning_parts = []
        reasoning_parts.append(f"时间窗口: {time_result['name']}（{time_result['severity']}风险）")
        
        if cooccur_result['is_likely_adverse']:
            reasoning_parts.append(
                f"症状共现异常: {new_symptom}与已知症状共现强度低，"
                f"提示可能为药物相关新症状"
            )
        
        if similar_with_adverse:
            reasoning_parts.append(
                f"相似患者验证: {len(similar_with_adverse)}例相似患者使用同药后出现相同症状"
            )
        
        reasoning = "；".join(reasoning_parts)
        
        return {
            'is_adverse': is_adverse,
            'confidence': confidence,
            'score': score,
            'max_score': 100,
            'reasoning': reasoning,
            'suggestion': suggestion,
            'time_analysis': time_result,
            'cooccurrence_analysis': cooccur_result,
            'similar_cases': similar_with_adverse[:3],
            'all_similar_cases': similar_cases[:3],
        }


# ========== 测试 ==========

if __name__ == "__main__":
    # 测试批判性思维引擎
    print("=== 测试批判性思维验证引擎 ===\n")
    
    engine = CriticalThinkingEngine()
    
    # 测试案例1: 高质量来源
    assessment1 = engine.assess_source_credibility(
        source_text="随机对照试验研究酸枣仁汤治疗失眠的疗效",
        source_url="https://cnki.net/xxx",
        source_type='P0',
        author_title='主任医师、教授',
        publish_year=2023,
        sample_size=120,
        evidence_type='RCT',
        symptom_match=0.9,
        population_match=0.85,
        conflict_check=1.0,
    )
    print(engine.format_assessment_report(assessment1))
    print("\n" + "="*50 + "\n")
    
    # 测试案例2: 低质量来源（应被否决）
    assessment2 = engine.assess_source_credibility(
        source_text="祖传秘方包治百病，治愈率100%，无效退款",
        source_url="https://xxx.com",
        source_type='P6',
        author_title='',
        publish_year=2010,
        sample_size=5,
        evidence_type='theory',
        symptom_match=0.3,
        population_match=0.2,
        conflict_check=0.5,
    )
    print(engine.format_assessment_report(assessment2))
    print("\n" + "="*50 + "\n")
    
    # 测试症状共现分析
    print("=== 测试症状共现分析 ===\n")
    
    cooccur = SymptomCooccurrenceAnalyzer()
    
    # 添加正常共现（来自古籍）
    cooccur.add_cooccurrence('SN-SP-S-001', 'SN-SP-S-003', 0.92, '伤寒论', 1847)  # 恶寒+发热
    cooccur.add_cooccurrence('SN-SP-S-003', 'SN-SP-S-005', 0.85, '伤寒论', 1200)  # 发热+无汗
    cooccur.add_cooccurrence('SN-HD-S-001', 'SN-SP-S-003', 0.78, '伤寒论', 900)   # 头痛+发热
    
    # 添加异常共现（可能的副作用）
    cooccur.add_cooccurrence('SN-SL-S-001', 'SN-DG-S-001', 0.15, '临床观察', 23)   # 失眠+腹泻（异常）
    
    # 分析症状组合
    symptoms = ['SN-SP-S-001', 'SN-SP-S-003', 'SN-SP-S-005', 'SN-HD-S-001']
    result = cooccur.analyze_symptom_combination(symptoms)
    print(f"症状组合分析: {result['total_pairs']}对症状")
    print(f"  正常共现: {len(result['normal_cooccurrences'])}对")
    print(f"  异常共现: {len(result['abnormal_cooccurrences'])}对")
    for alert in result['alerts']:
        print(f"  {alert}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试副作用检测
    print("=== 测试副作用辨别引擎 ===\n")
    
    detector = AdverseEventDetector()
    
    # 添加示例患者
    detector.patient_matcher.add_patient('PT-001', {
        'patient_id': 'PT-001',
        'symptoms': ['SN-SL-S-001', 'SN-PS-S-001'],  # 失眠+心烦
        'syndrome': 'SY-YN-001',  # 心阴虚
        'constitution': ['CT-YN-001'],
        'age': 45,
        'gender': '女',
        'treatment': 'FP-SJ-001',  # 酸枣仁汤
        'formula': '酸枣仁汤',
        'outcome': '痊愈',
        'adverse_events': [{'symptom': 'SN-DG-S-001', 'severity': '轻度'}],  # 腹泻
    })
    
    detector.patient_matcher.add_patient('PT-002', {
        'patient_id': 'PT-002',
        'symptoms': ['SN-SL-S-001', 'SN-PS-S-001'],
        'syndrome': 'SY-YN-001',
        'constitution': ['CT-YN-001'],
        'age': 42,
        'gender': '女',
        'treatment': 'FP-SJ-001',
        'formula': '酸枣仁汤',
        'outcome': '显效',
        'adverse_events': [{'symptom': 'SN-DG-S-001', 'severity': '轻度'}],
    })
    
    # 检测副作用
    result = detector.detect_adverse_event(
        patient_id='PT-003',
        drug_id='DR-AS-001',  # 酸枣仁
        new_symptom='SN-DG-S-001',  # 腹泻
        onset_minutes=72 * 60,  # 3天后
        known_symptoms=['SN-SL-S-001', 'SN-PS-S-001'],
        patient_profile={
            'patient_id': 'PT-003',
            'symptoms': ['SN-SL-S-001', 'SN-PS-S-001'],
            'syndrome': 'SY-YN-001',
            'constitution': ['CT-YN-001'],
            'age': 40,
            'gender': '女',
        },
    )
    
    print(f"副作用检测结果:")
    print(f"  是否副作用: {'是' if result['is_adverse'] else '否'}")
    print(f"  置信度: {result['confidence']}")
    print(f"  评分: {result['score']}/{result['max_score']}")
    print(f"  推理: {result['reasoning']}")
    print(f"  建议: {result['suggestion']}")
    
    if result['similar_cases']:
        print(f"\n  相似案例:")
        for case in result['similar_cases']:
            print(f"    - {case['patient_id']}: 相似度{case['similarity_score']*100:.0f}%")
    
    print("\n" + "="*50)
    print("所有测试通过！")
