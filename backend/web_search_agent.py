#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小神农联网搜索模块 v1.0
基于OpenAI兼容API实现Agent联网搜索能力
支持：网络搜索、学术数据检索、临床数据验证
"""

import json
import os
import re
import time
from typing import List, Dict, Optional
from datetime import datetime

# 尝试导入openai库
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("[WebSearch] openai库未安装，尝试使用requests")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class WebSearchAgent:
    """联网搜索Agent - 为各Agent提供网络搜索能力"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """
        初始化联网搜索Agent
        
        Args:
            api_key: API密钥，默认从环境变量 WEBSEARCH_API_KEY 获取
            base_url: API基础URL，默认从环境变量 WEBSEARCH_BASE_URL 获取
            model: 使用的模型名称
        """
        self.api_key = api_key or os.environ.get('WEBSEARCH_API_KEY', '')
        self.base_url = base_url or os.environ.get('WEBSEARCH_BASE_URL', 'https://yunwu.ai/v1')
        self.model = model or os.environ.get('WEBSEARCH_MODEL', 'gpt-5.4-pro')  # yunwu.ai可用模型
        
        self.client = None
        self.session = None
        self.last_search_time = 0
        self.search_interval = 1.0  # 搜索间隔（秒）
        self.search_cache = {}  # 搜索缓存
        
        # 初始化客户端
        self._init_client()
    
    def _init_client(self):
        """初始化API客户端"""
        if not self.api_key:
            print("[WebSearch] 警告: 未配置API密钥，联网搜索功能不可用")
            return
        
        if HAS_OPENAI:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                print(f"[WebSearch] OpenAI客户端初始化成功: {self.base_url}")
            except Exception as e:
                print(f"[WebSearch] OpenAI客户端初始化失败: {e}")
        
        if HAS_REQUESTS:
            self.session = requests.Session()
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def is_available(self) -> bool:
        """检查联网搜索是否可用"""
        return bool(self.api_key and (self.client or self.session))
    
    def search(self, query: str, context: str = None, max_results: int = 5) -> List[Dict]:
        """
        执行联网搜索
        
        Args:
            query: 搜索查询词
            context: 搜索上下文（如"中医临床"、"中药研究"等）
            max_results: 最大返回结果数
        
        Returns:
            搜索结果列表，每条包含：title, content, source, credibility_score
        """
        if not self.is_available():
            return self._fallback_search(query, context)
        
        # 检查缓存
        cache_key = f"{query}_{context}"
        if cache_key in self.search_cache:
            cache_time, cache_results = self.search_cache[cache_key]
            if time.time() - cache_time < 3600:  # 缓存1小时
                print(f"[WebSearch] 使用缓存结果: {query}")
                return cache_results
        
        # 速率限制
        elapsed = time.time() - self.last_search_time
        if elapsed < self.search_interval:
            time.sleep(self.search_interval - elapsed)
        
        # 构建搜索提示词
        search_prompt = self._build_search_prompt(query, context)
        
        try:
            results = self._call_api(search_prompt, max_results)
            self.last_search_time = time.time()
            
            # 缓存结果
            self.search_cache[cache_key] = (time.time(), results)
            
            return results
            
        except Exception as e:
            print(f"[WebSearch] 搜索失败: {e}")
            return self._fallback_search(query, context)
    
    def _build_search_prompt(self, query: str, context: str = None) -> str:
        """构建搜索提示词"""
        base_prompt = f"""你是一个专业的中医研究助手。请基于你的知识，针对以下查询提供详细、准确的信息。

查询: {query}
"""
        
        if context:
            base_prompt += f"\n搜索领域: {context}\n"
        
        base_prompt += """
请提供以下格式的回答：
1. 直接回答查询的核心问题
2. 提供相关的中医理论依据
3. 如有临床研究数据，请引用关键数据
4. 标注信息来源的可靠性（高/中/低）
5. 如有不同观点，请列出并分析

注意：
- 优先引用权威中医典籍（如《黄帝内经》《伤寒论》《金匮要略》等）
- 优先引用现代中医临床研究
- 对于不确定的信息，明确标注"待验证"
- 避免编造不存在的数据
"""
        return base_prompt
    
    def _call_api(self, prompt: str, max_results: int = 5) -> List[Dict]:
        """调用API获取搜索结果"""
        if self.client and HAS_OPENAI:
            return self._call_openai_api(prompt, max_results)
        elif self.session and HAS_REQUESTS:
            return self._call_requests_api(prompt, max_results)
        else:
            return self._fallback_search(prompt, None)
    
    def _call_openai_api(self, prompt: str, max_results: int = 5) -> List[Dict]:
        """使用OpenAI SDK调用API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的中医研究助手，具备联网搜索能力。请提供准确、有据可查的中医信息。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                stream=False
            )
            
            content = response.choices[0].message.content
            return self._parse_search_results(content)
            
        except Exception as e:
            print(f"[WebSearch] OpenAI API调用失败: {e}")
            raise
    
    def _call_requests_api(self, prompt: str, max_results: int = 5) -> List[Dict]:
        """使用requests调用API"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的中医研究助手，具备联网搜索能力。请提供准确、有据可查的中医信息。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
                "stream": False
            }
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            content = data['choices'][0]['message']['content']
            return self._parse_search_results(content)
            
        except Exception as e:
            print(f"[WebSearch] Requests API调用失败: {e}")
            raise
    
    def _parse_search_results(self, content: str) -> List[Dict]:
        """解析API返回的搜索结果"""
        results = []
        
        # 尝试按段落分割
        paragraphs = content.split('\n\n')
        
        for i, para in enumerate(paragraphs[:5]):  # 最多取5段
            if not para.strip():
                continue
            
            # 提取标题（第一行或前50字）
            lines = para.strip().split('\n')
            title = lines[0][:50] if lines else f"搜索结果 {i+1}"
            
            # 评估可信度
            credibility = self._assess_credibility(para)
            
            result = {
                'id': f'WS-{datetime.now().strftime("%Y%m%d%H%M%S")}-{i}',
                'title': title,
                'content': para[:500],  # 限制长度
                'full_content': para,
                'source': 'AI搜索',
                'credibility_score': credibility['score'],
                'credibility_level': credibility['level'],
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
        
        return results
    
    def _assess_credibility(self, content: str) -> Dict:
        """评估搜索结果的可信度"""
        score = 0.5  # 基础分
        
        # 有典籍引用加分
        classics = ['黄帝内经', '伤寒论', '金匮要略', '本草纲目', '神农本草经', 
                     '温病条辨', '医宗金鉴', '千金方', '外台秘要']
        for classic in classics:
            if classic in content:
                score += 0.1
        
        # 有数据引用加分
        if re.search(r'\d+\.?\d*%|\d+例|\d+人|n=\d+', content):
            score += 0.1
        
        # 有期刊引用加分
        if re.search(r'《[^》]+》|\[\d+\]|doi:|PMID', content):
            score += 0.1
        
        # 有不确定表述减分
        if re.search(r'可能|也许|大概|不确定|待验证|暂无', content):
            score -= 0.1
        
        score = max(0.1, min(1.0, score))
        
        level = '高' if score >= 0.7 else '中' if score >= 0.4 else '低'
        
        return {'score': round(score, 2), 'level': level}
    
    def _fallback_search(self, query: str, context: str = None) -> List[Dict]:
        """降级搜索 - 当API不可用时使用本地知识库"""
        print(f"[WebSearch] 使用降级搜索: {query}")
        
        # 返回一个基本的搜索结果，提示用户API未配置
        return [{
            'id': f'WS-FALLBACK-{int(time.time())}',
            'title': '搜索服务未配置',
            'content': f'联网搜索功能未启用。查询: {query}。请配置API密钥以启用实时搜索功能。',
            'source': '本地系统',
            'credibility_score': 0.0,
            'credibility_level': '低',
            'timestamp': datetime.now().isoformat()
        }]
    
    def verify_fact(self, claim: str, evidence: str = None) -> Dict:
        """
        事实验证 - 验证某个中医论断的真实性
        
        Args:
            claim: 需要验证的论断
            evidence: 已有证据（可选）
        
        Returns:
            验证结果：verified / disputed / unverified
        """
        if not self.is_available():
            return {
                'claim': claim,
                'status': 'unverified',
                'confidence': 0.0,
                'reason': '联网搜索未启用'
            }
        
        prompt = f"""请验证以下中医论断的真实性：

论断: {claim}

{evidence if evidence else ''}

请分析：
1. 该论断是否有经典中医典籍支持？
2. 是否有现代临床研究支持？
3. 是否有争议或反对观点？
4. 你的结论和置信度（高/中/低）

请基于你的知识库回答，不要编造数据。"""
        
        try:
            results = self.search(prompt, context="中医事实验证")
            
            if results:
                content = results[0].get('full_content', '')
                
                # 简单判断验证状态
                status = 'unverified'
                if '支持' in content or '正确' in content or '有依据' in content:
                    status = 'verified'
                elif '错误' in content or '不支持' in content or '无依据' in content:
                    status = 'disputed'
                
                return {
                    'claim': claim,
                    'status': status,
                    'confidence': results[0].get('credibility_score', 0.5),
                    'evidence': content[:300],
                    'source': results[0].get('source', 'AI验证')
                }
            
        except Exception as e:
            print(f"[WebSearch] 事实验证失败: {e}")
        
        return {
            'claim': claim,
            'status': 'unverified',
            'confidence': 0.0,
            'reason': '验证失败'
        }
    
    def search_clinical_data(self, symptom: str, treatment: str = None) -> List[Dict]:
        """
        搜索临床数据 - 查找症状相关的临床研究
        
        Args:
            symptom: 症状名称
            treatment: 治疗方法（可选）
        
        Returns:
            临床研究数据列表
        """
        query = f"{symptom} 临床研究 中医治疗"
        if treatment:
            query += f" {treatment}"
        
        return self.search(query, context="中医临床研究")
    
    def search_herb_data(self, herb_name: str) -> List[Dict]:
        """
        搜索中药数据 - 查找中药的现代研究
        
        Args:
            herb_name: 中药名称
        
        Returns:
            中药研究数据列表
        """
        query = f"{herb_name} 中药 现代研究 药理 临床"
        return self.search(query, context="中药现代研究")
    
    def search_formula_evidence(self, formula_name: str) -> List[Dict]:
        """
        搜索方剂证据 - 查找方剂的临床证据
        
        Args:
            formula_name: 方剂名称
        
        Returns:
            方剂临床证据列表
        """
        query = f"{formula_name} 方剂 临床研究 疗效"
        return self.search(query, context="方剂临床研究")


# ========== 全局搜索Agent实例 ==========
_web_search_agent = None

def get_web_search_agent() -> WebSearchAgent:
    """获取全局联网搜索Agent实例"""
    global _web_search_agent
    if _web_search_agent is None:
        _web_search_agent = WebSearchAgent()
    return _web_search_agent

def init_web_search(api_key: str = None, base_url: str = None, model: str = None):
    """初始化联网搜索Agent"""
    global _web_search_agent
    _web_search_agent = WebSearchAgent(api_key, base_url, model)
    return _web_search_agent


# ========== 测试 ==========
if __name__ == '__main__':
    # 测试联网搜索
    print("=" * 60)
    print("小神农联网搜索模块测试")
    print("=" * 60)
    
    # 从环境变量获取配置
    agent = get_web_search_agent()
    
    if agent.is_available():
        print("\n[测试1] 搜索中药数据")
        results = agent.search_herb_data("黄芪")
        for r in results:
            print(f"  - {r['title']} (可信度: {r['credibility_level']})")
        
        print("\n[测试2] 搜索临床数据")
        results = agent.search_clinical_data("失眠")
        for r in results:
            print(f"  - {r['title']} (可信度: {r['credibility_level']})")
        
        print("\n[测试3] 事实验证")
        result = agent.verify_fact("黄芪具有补气升阳的功效")
        print(f"  验证结果: {result['status']} (置信度: {result['confidence']})")
    else:
        print("\n联网搜索未配置，请设置环境变量:")
        print("  WEBSEARCH_API_KEY=your_api_key")
        print("  WEBSEARCH_BASE_URL=https://yunwu.ai/v1")
