#!/usr/bin/env python3
"""
小神农中医AI - 对话式问诊引擎 v1.0
多轮对话收集症状，智能追问，达到阈值后触发辨证
"""

import json
import re
import time
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

from symptom_codes import find_symptoms_by_text, SYMPTOM_MAP, BODY_PARTS
from drug_formula_db import find_formulas_by_symptoms
from syndrome_db import find_syndromes_by_symptoms


class DialoguePhase(Enum):
    """对话阶段"""
    GREETING = "greeting"           # 欢迎/初始
    COLLECTING = "collecting"       # 收集症状
    CLARIFYING = "clarifying"       # 澄清/确认
    DIFFERENTIATING = "differentiating"  # 鉴别诊断
    CONFIRMING = "confirming"       # 确认信息
    READY = "ready"                 # 准备辨证
    DIAGNOSING = "diagnosing"       # 辨证中


@dataclass
class CollectedSymptom:
    """已收集的症状信息"""
    symptom_id: str
    name: str
    source: str  # 'user_explicit', 'inferred', 'confirmed', 'denied'
    confidence: float  # 0-1
    first_mentioned: float  # timestamp
    mentions: int = 1
    details: str = ""  # 用户描述的细节


@dataclass
class DialogueState:
    """对话状态"""
    session_id: str
    phase: DialoguePhase = DialoguePhase.GREETING
    turn_count: int = 0
    collected_symptoms: Dict[str, CollectedSymptom] = field(default_factory=dict)
    pending_questions: List[str] = field(default_factory=list)
    asked_questions: Set[str] = field(default_factory=set)
    user_profile: Dict = field(default_factory=dict)  # age, gender, etc.
    last_user_input: str = ""
    last_bot_response: str = ""
    diagnosis_triggered: bool = False
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "phase": self.phase.value,
            "turn_count": self.turn_count,
            "collected_symptoms": {
                k: {
                    "symptom_id": v.symptom_id,
                    "name": v.name,
                    "source": v.source,
                    "confidence": v.confidence,
                    "mentions": v.mentions,
                    "details": v.details
                }
                for k, v in self.collected_symptoms.items()
            },
            "pending_questions": self.pending_questions,
            "asked_questions": list(self.asked_questions),
            "user_profile": self.user_profile,
            "diagnosis_triggered": self.diagnosis_triggered,
        }


class SymptomQuestionBank:
    """症状追问问题库"""
    
    # 按部位分类的追问模板
    FOLLOW_UP_TEMPLATES = {
        # 全身症状
        "SN-QT": {
            "fever": [
                "您发热的情况是怎样的？是低热（37.3-38℃）还是高热（38℃以上）？",
                "发热有没有规律？比如上午轻下午重，或者持续不退？",
                "发热时有没有怕冷或怕热的感觉？"
            ],
            "chills": [
                "怕冷的情况是持续的还是一阵阵的？",
                "怕冷时有没有发热？还是只怕冷不发热？",
                "加衣服或盖被子能不能缓解怕冷？"
            ],
            "sweat": [
                "出汗的情况是怎样的？是白天出汗还是晚上睡觉时出汗？",
                "出汗后感觉舒服一些还是更不舒服？",
                "出汗多不多？是微微出汗还是大汗淋漓？"
            ],
            "fatigue": [
                "乏力的情况持续多久了？是最近才出现还是已经有一段时间？",
                "休息后能不能缓解？",
                "除了乏力，有没有气短、不想说话的情况？"
            ],
        },
        # 头部症状
        "SN-TB": {
            "headache": [
                "头痛是哪个部位？前额、两侧、后脑勺还是整个头都痛？",
                "头痛的性质是怎样的？胀痛、刺痛、隐痛还是跳痛？",
                "什么情况下头痛会加重？比如风吹、情绪激动、睡眠不足？"
            ],
            "dizziness": [
                "头晕是天旋地转的感觉，还是头重脚轻、昏昏沉沉？",
                "头晕和体位变化有没有关系？比如站起来时加重？",
                "头晕时有没有恶心、呕吐？"
            ],
        },
        # 胸腹部
        "SN-XB": {
            "chest_pain": [
                "胸闷胸痛是刺痛、胀痛还是隐痛？",
                "疼痛和呼吸、情绪有没有关系？",
                "有没有心悸、心慌的感觉？"
            ],
        },
        "SN-FB": {
            "abdominal_pain": [
                "腹痛是哪个部位？上腹部、肚脐周围还是下腹部？",
                "疼痛是隐痛、绞痛还是胀痛？",
                "按压时疼痛加重还是减轻？"
            ],
            "bloating": [
                "腹胀是饭后加重还是一直都有？",
                "有没有嗳气、打嗝？",
                "排气（放屁）后能不能缓解？"
            ],
            "appetite": [
                "食欲不好是最近才有的还是持续一段时间了？",
                "有没有口苦、口淡或口黏的感觉？",
                "看到油腻的食物有没有恶心？"
            ],
        },
        # 二便
        "SN-DB": {
            "stool": [
                "大便一天几次？成形还是稀溏？",
                "大便有没有黏液、脓血？",
                "排便时有没有肛门灼热感？"
            ],
            "urine": [
                "小便颜色是怎样的？清长还是黄赤？",
                "小便次数有没有增多或减少？",
                "排尿时有没有灼热感或疼痛？"
            ],
        },
        # 睡眠
        "SN-SM": {
            "insomnia": [
                "失眠是入睡困难、多梦易醒还是早醒？",
                "失眠多久了？有没有特定原因？",
                "失眠时有没有心烦、焦虑？"
            ],
        },
        # 情志
        "SN-QZ": {
            "mood": [
                "最近情绪怎么样？有没有烦躁、焦虑或抑郁？",
                "情绪波动大不大？容易生气还是容易悲伤？",
                "情绪不好时身体症状会不会加重？"
            ],
        },
    }
    
    # 通用追问问题（当症状不够时）
    GENERAL_QUESTIONS = [
        "除了刚才提到的，身体还有其他不舒服的地方吗？",
        "这种情况持续多久了？",
        "最近饮食、睡眠怎么样？",
        "有没有怕冷或怕热？",
        "精神状态怎么样？容易累吗？",
        "大小便正常吗？",
        "口不干？口苦吗？",
        "有没有出汗？白天还是晚上？",
    ]
    
    # 鉴别诊断问题（当多个证型可能时）
    DIFFERENTIATION_QUESTIONS = {
        "wind_cold_vs_wind_heat": {
            "trigger": ["SN-TB-S-001", "SN-QT-Z-001"],  # 头痛 + 发热
            "questions": [
                "您怕冷明显还是怕热明显？",
                "有没有出汗？有汗还是无汗？",
                "口渴吗？想喝热水还是凉水？",
                "咽喉痛不痛？红肿吗？"
            ]
        },
        "qi_deficiency_vs_yang_deficiency": {
            "trigger": ["SN-QT-Z-018"],  # 乏力
            "questions": [
                "怕冷的情况严重吗？手脚冰凉吗？",
                "喜欢喝热水还是常温水？",
                "腹泻时有没有未消化的食物？"
            ]
        },
        "yin_deficiency_vs_blood_deficiency": {
            "trigger": ["SN-SM-Z-001"],  # 失眠
            "questions": [
                "手心脚心热吗？",
                "下午或晚上有没有潮热感？",
                "皮肤干燥吗？嘴唇颜色淡吗？"
            ]
        },
        "damp_heat_vs_phlegm_damp": {
            "trigger": ["SN-FB-T-003"],  # 口苦
            "questions": [
                "身体感觉沉重吗？",
                "舌苔厚吗？白腻还是黄腻？",
                "大便黏马桶吗？"
            ]
        },
    }


class DialogueEngine:
    """对话式问诊引擎"""
    
    # 触发辨证的最小症状数
    MIN_SYMPTOMS_FOR_DIAGNOSIS = 3
    # 最大对话轮数
    MAX_TURNS = 8
    # 症状置信度阈值
    CONFIDENCE_THRESHOLD = 0.6
    
    def __init__(self):
        self.question_bank = SymptomQuestionBank()
        self.sessions: Dict[str, DialogueState] = {}
        print("[DialogueEngine] 对话式问诊引擎初始化完成")
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """创建新对话会话"""
        if session_id is None:
            session_id = f"dialogue_{int(time.time() * 1000)}"
        
        self.sessions[session_id] = DialogueState(session_id=session_id)
        print(f"[DialogueEngine] 创建会话: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[DialogueState]:
        """获取会话状态"""
        return self.sessions.get(session_id)
    
    def process_turn(self, session_id: str, user_input: str) -> Dict:
        """
        处理一轮对话
        
        Returns:
            {
                "session_id": str,
                "phase": str,
                "bot_response": str,  # AI回复（打字机效果展示）
                "thinking_steps": List[Dict],  # 思考过程（供前端展示）
                "collected_symptoms": List[Dict],
                "symptom_count": int,
                "is_ready_for_diagnosis": bool,
                "diagnosis_query": str,  # 如果ready，生成辨证查询
                "suggested_questions": List[str],  # 建议的追问问题
                "progress_percent": int,  # 收集进度
            }
        """
        state = self.sessions.get(session_id)
        if not state:
            return {
                "session_id": session_id,
                "error": "会话不存在，请重新开始",
                "phase": "error"
            }
        
        state.turn_count += 1
        state.last_user_input = user_input
        state.last_activity = time.time()
        
        thinking_steps = []
        
        # Step 1: 解析用户输入，提取症状
        step1_start = time.time()
        extracted_symptoms = find_symptoms_by_text(user_input)
        new_symptoms = []
        
        for s in extracted_symptoms:
            sid = s['id']
            if sid not in state.collected_symptoms:
                state.collected_symptoms[sid] = CollectedSymptom(
                    symptom_id=sid,
                    name=s['name'],
                    source='user_explicit',
                    confidence=1.0,
                    first_mentioned=time.time(),
                    details=user_input
                )
                new_symptoms.append(s)
            else:
                # 更新已有症状
                state.collected_symptoms[sid].mentions += 1
                state.collected_symptoms[sid].confidence = min(1.0, state.collected_symptoms[sid].confidence + 0.1)
        
        thinking_steps.append({
            "step": 1,
            "name": "症状提取",
            "description": f"从用户输入中提取到 {len(new_symptoms)} 个新症状，累计 {len(state.collected_symptoms)} 个",
            "time_ms": round((time.time() - step1_start) * 1000, 2),
            "details": {
                "new_symptoms": [s['name'] for s in new_symptoms],
                "total_symptoms": len(state.collected_symptoms)
            }
        })
        
        # Step 2: 判断对话阶段，生成追问
        step2_start = time.time()
        
        symptom_ids = list(state.collected_symptoms.keys())
        symptom_count = len(symptom_ids)
        
        # 计算进度
        progress = min(100, int(symptom_count / self.MIN_SYMPTOMS_FOR_DIAGNOSIS * 100))
        
        # 判断阶段
        if state.turn_count == 1:
            state.phase = DialoguePhase.COLLECTING
        elif symptom_count >= self.MIN_SYMPTOMS_FOR_DIAGNOSIS:
            # 检查是否需要鉴别诊断
            need_diff = self._need_differentiation(state)
            if need_diff and state.turn_count < self.MAX_TURNS:
                state.phase = DialoguePhase.DIFFERENTIATING
            else:
                state.phase = DialoguePhase.READY
        elif state.turn_count >= self.MAX_TURNS:
            state.phase = DialoguePhase.READY
        else:
            state.phase = DialoguePhase.CLARIFYING
        
        thinking_steps.append({
            "step": 2,
            "name": "阶段判断",
            "description": f"当前阶段: {state.phase.value}, 已收集 {symptom_count} 个症状",
            "time_ms": round((time.time() - step2_start) * 1000, 2),
            "details": {
                "phase": state.phase.value,
                "symptom_count": symptom_count,
                "turn_count": state.turn_count,
                "need_differentiation": state.phase == DialoguePhase.DIFFERENTIATING
            }
        })
        
        # Step 3: 生成回复和追问
        step3_start = time.time()
        
        bot_response = ""
        suggested_questions = []
        is_ready = False
        diagnosis_query = ""
        
        if state.phase == DialoguePhase.GREETING:
            bot_response = self._generate_greeting()
            suggested_questions = ["我最近头痛发热，怕冷", "失眠多梦，口干舌燥"]
            
        elif state.phase == DialoguePhase.COLLECTING:
            bot_response = self._generate_collecting_response(state, new_symptoms)
            suggested_questions = self._generate_follow_up_questions(state)
            
        elif state.phase == DialoguePhase.CLARIFYING:
            bot_response = self._generate_clarifying_response(state)
            suggested_questions = self._generate_follow_up_questions(state)
            
        elif state.phase == DialoguePhase.DIFFERENTIATING:
            bot_response = self._generate_differentiation_response(state)
            suggested_questions = self._generate_differentiation_questions(state)
            
        elif state.phase == DialoguePhase.READY:
            is_ready = True
            bot_response = self._generate_ready_response(state)
            diagnosis_query = self._build_diagnosis_query(state)
            state.diagnosis_triggered = True
            suggested_questions = []
        
        thinking_steps.append({
            "step": 3,
            "name": "生成回复",
            "description": f"生成{state.phase.value}阶段回复，推荐 {len(suggested_questions)} 个追问",
            "time_ms": round((time.time() - step3_start) * 1000, 2),
            "details": {
                "response_length": len(bot_response),
                "suggested_questions_count": len(suggested_questions)
            }
        })
        
        return {
            "session_id": session_id,
            "phase": state.phase.value,
            "bot_response": bot_response,
            "thinking_steps": thinking_steps,
            "collected_symptoms": [
                {
                    "id": s.symptom_id,
                    "name": s.name,
                    "confidence": s.confidence,
                    "source": s.source,
                    "mentions": s.mentions
                }
                for s in state.collected_symptoms.values()
            ],
            "symptom_count": symptom_count,
            "is_ready_for_diagnosis": is_ready,
            "diagnosis_query": diagnosis_query,
            "suggested_questions": suggested_questions[:3],  # 最多3个
            "progress_percent": progress,
            "turn_count": state.turn_count,
        }
    
    def _generate_greeting(self) -> str:
        """生成欢迎语"""
        return """您好！我是小神农AI助手，专门帮助您分析身体状况。

为了给您更准确的分析，我会先问您几个问题。请尽量详细描述您的不适，比如：
• 哪里不舒服？（头痛、腹痛、关节痛等）
• 持续多久了？
• 有没有其他伴随症状？

您现在最不舒服的地方是什么？"""
    
    def _generate_collecting_response(self, state: DialogueState, new_symptoms: List[Dict]) -> str:
        """生成收集阶段的回复"""
        if new_symptoms:
            symptom_names = "、".join([s['name'] for s in new_symptoms])
            response = f"我注意到您提到了{symptom_names}。"
            
            # 如果有多个症状，简单关联分析
            if len(new_symptoms) >= 2:
                response += "这些症状同时出现，"
                # 查找可能的证型
                sids = [s['id'] for s in new_symptoms]
                syndromes = find_syndromes_by_symptoms(sids)
                if syndromes:
                    top = syndromes[0]
                    response += f"可能与{top['name']}相关。"
            
            response += "\n\n"
        else:
            response = ""
        
        response += "还有其他不舒服的地方吗？比如饮食、睡眠、大小便、精神状态等方面？"
        return response
    
    def _generate_clarifying_response(self, state: DialogueState) -> str:
        """生成澄清阶段的回复"""
        symptoms = list(state.collected_symptoms.values())
        symptom_names = "、".join([s.name for s in symptoms])
        
        return f"目前我了解到您有{symptom_names}的情况。为了更准确地分析，我还需要了解一些细节。"
    
    def _generate_differentiation_response(self, state: DialogueState) -> str:
        """生成鉴别诊断阶段的回复"""
        return "根据您描述的症状，有几种可能的方向。为了缩小范围，想再确认几个关键点："
    
    def _generate_ready_response(self, state: DialogueState) -> str:
        """生成准备辨证的回复"""
        symptoms = list(state.collected_symptoms.values())
        symptom_names = "、".join([s.name for s in symptoms])
        
        return f"感谢您提供的详细信息！我已收集到您{len(symptoms)}个症状（{symptom_names}），现在为您进行AI辨证分析..."
    
    def _generate_follow_up_questions(self, state: DialogueState) -> List[str]:
        """生成追问问题"""
        questions = []
        collected_ids = set(state.collected_symptoms.keys())
        
        # 1. 根据已有症状的部位，生成相关追问
        for sid in collected_ids:
            prefix = sid[:5]  # SN-XX
            templates = self.question_bank.FOLLOW_UP_TEMPLATES.get(prefix, {})
            
            # 找到匹配的症状类型
            for symptom_type, qs in templates.items():
                # 避免重复提问
                for q in qs:
                    if q not in state.asked_questions:
                        questions.append(q)
                        break  # 每种类型只问一个
        
        # 2. 补充通用问题
        for q in self.question_bank.GENERAL_QUESTIONS:
            if q not in state.asked_questions and q not in questions:
                questions.append(q)
        
        # 记录已问问题
        for q in questions[:2]:
            state.asked_questions.add(q)
        
        return questions[:3]
    
    def _need_differentiation(self, state: DialogueState) -> bool:
        """判断是否需要鉴别诊断"""
        symptom_ids = set(state.collected_symptoms.keys())
        
        for diff_name, diff_info in self.question_bank.DIFFERENTIATION_QUESTIONS.items():
            triggers = set(diff_info["trigger"])
            if triggers & symptom_ids:  # 有交集
                # 检查是否已经问过鉴别问题
                asked_diff = any(q in state.asked_questions for q in diff_info["questions"])
                if not asked_diff:
                    return True
        
        return False
    
    def _generate_differentiation_questions(self, state: DialogueState) -> List[str]:
        """生成鉴别诊断问题"""
        symptom_ids = set(state.collected_symptoms.keys())
        questions = []
        
        for diff_name, diff_info in self.question_bank.DIFFERENTIATION_QUESTIONS.items():
            triggers = set(diff_info["trigger"])
            if triggers & symptom_ids:
                for q in diff_info["questions"]:
                    if q not in state.asked_questions:
                        questions.append(q)
                        state.asked_questions.add(q)
        
        return questions[:3]
    
    def _build_diagnosis_query(self, state: DialogueState) -> str:
        """构建辨证查询"""
        symptoms = list(state.collected_symptoms.values())
        symptom_desc = "，".join([s.name for s in symptoms])
        
        query = f"症状：{symptom_desc}"
        
        # 添加用户画像信息
        if state.user_profile.get("age"):
            query += f"，年龄：{state.user_profile['age']}岁"
        if state.user_profile.get("gender"):
            query += f"，性别：{state.user_profile['gender']}"
        
        return query
    
    def add_user_profile(self, session_id: str, key: str, value: str) -> bool:
        """添加用户画像信息"""
        state = self.sessions.get(session_id)
        if not state:
            return False
        state.user_profile[key] = value
        return True
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """获取会话摘要"""
        state = self.sessions.get(session_id)
        if not state:
            return None
        
        return {
            "session_id": session_id,
            "turn_count": state.turn_count,
            "phase": state.phase.value,
            "symptom_count": len(state.collected_symptoms),
            "symptoms": [s.name for s in state.collected_symptoms.values()],
            "diagnosis_triggered": state.diagnosis_triggered,
            "duration_seconds": int(time.time() - state.created_at),
        }
    
    def cleanup_old_sessions(self, max_age_hours: float = 24):
        """清理过期会话"""
        cutoff = time.time() - max_age_hours * 3600
        to_remove = [
            sid for sid, state in self.sessions.items()
            if state.last_activity < cutoff
        ]
        for sid in to_remove:
            del self.sessions[sid]
        return len(to_remove)


# ========== 单例 ==========
_dialogue_engine = None

def get_dialogue_engine() -> DialogueEngine:
    global _dialogue_engine
    if _dialogue_engine is None:
        _dialogue_engine = DialogueEngine()
    return _dialogue_engine


if __name__ == "__main__":
    # 测试对话引擎
    engine = DialogueEngine()
    session = engine.create_session()
    
    print("=" * 50)
    print("对话式问诊引擎测试")
    print("=" * 50)
    
    # 模拟对话
    test_inputs = [
        "我最近头痛",
        "还有发热，怕冷",
        "没有汗，已经三天了",
        "口干，想喝水",
        "不想吃饭，有点恶心",
    ]
    
    for user_input in test_inputs:
        print(f"\n[用户] {user_input}")
        result = engine.process_turn(session, user_input)
        print(f"[AI] {result['bot_response']}")
        print(f"  阶段: {result['phase']}, 症状数: {result['symptom_count']}, 进度: {result['progress_percent']}%")
        if result['suggested_questions']:
            print(f"  追问: {result['suggested_questions']}")
        if result['is_ready_for_diagnosis']:
            print(f"  ✅ 准备辨证: {result['diagnosis_query']}")
            break
    
    print("\n" + "=" * 50)
    print("会话摘要:")
    print(json.dumps(engine.get_session_summary(session), ensure_ascii=False, indent=2))
