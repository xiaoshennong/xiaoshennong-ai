#!/usr/bin/env python3
"""
小神农中医AI - LLM客户端
支持多种大模型API：DeepSeek、OpenAI、通义千问等
"""

import os
import time
import json
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """LLM响应结构"""
    text: str
    model: str
    usage: Dict
    latency_ms: float


class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek-chat"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.model = model
        self.base_url = "https://api.deepseek.com/v1"
        
        if not self.api_key:
            print("[LLM] 警告：未设置DeepSeek API Key")
    
    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """
        调用DeepSeek API生成回答
        temperature=0.3：降低随机性，减少幻觉
        """
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个严格的中医知识助手，只基于提供的参考资料回答，不编造任何内容。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9
            )
            
            latency = (time.time() - start_time) * 1000
            
            result = LLMResponse(
                text=response.choices[0].message.content,
                model=self.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                latency_ms=latency
            )
            
            print(f"[LLM] DeepSeek调用完成，耗时{latency:.0f}ms，token用量：{result.usage['total_tokens']}")
            return result.text
            
        except Exception as e:
            print(f"[LLM] DeepSeek调用失败: {e}")
            return "[系统错误：AI服务暂时不可用，请稍后重试]"


class MockLLMClient:
    """模拟LLM客户端（用于测试，无需API Key）"""
    
    def __init__(self):
        print("[LLM] 使用模拟LLM客户端（无需API Key）")
    
    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """模拟生成：从提示词中提取参考资料内容，格式化输出"""
        
        # 提取参考资料部分
        ref_match = re.search(r'【参考资料】\n(.+?)\n\n用户问题：', prompt, re.DOTALL)
        
        if ref_match:
            references = ref_match.group(1)
            
            # 简单格式化输出
            lines = references.split('\n')
            output_lines = []
            
            for line in lines:
                if line.startswith('出处：'):
                    output_lines.append(f"\n{line}")
                elif line.startswith('内容：'):
                    content = line.replace('内容：', '').strip()
                    if content:
                        output_lines.append(f"根据古籍记载：{content}")
            
            output = '\n'.join(output_lines)
            
            # 添加体质辨识（简化）
            output += "\n\n【体质辨识】\n"
            if '恶寒' in prompt and '无汗' in prompt:
                output += "初步判断：风寒表实证\n"
                output += "【调理建议】\n"
                output += "建议采用辛温解表之法，可考虑麻黄汤类方剂。"
                output += "[出处：《伤寒论》·第35条]\n"
            elif '汗出' in prompt:
                output += "初步判断：风寒表虚证\n"
                output += "【调理建议】\n"
                output += "建议采用解肌发表之法，可考虑桂枝汤类方剂。"
                output += "[出处：《伤寒论》·第12条]\n"
            else:
                output += "根据现有资料，暂无法明确辨识体质类型。\n"
            
            output += "\n【重要提示】本结果仅供参考，不能替代专业医生诊断。如有不适，请及时就医。"
            
            return output
        
        return "抱歉，暂无权威数据支持该问题。"


import re


def get_llm_client(provider: str = "mock"):
    """
    获取LLM客户端
    
    provider选项：
    - "mock": 模拟客户端，无需API Key，用于测试
    - "deepseek": DeepSeek API，需要设置DEEPSEEK_API_KEY
    - "openai": OpenAI API，需要设置OPENAI_API_KEY
    """
    if provider == "deepseek":
        return DeepSeekClient()
    elif provider == "mock":
        return MockLLMClient()
    else:
        raise ValueError(f"不支持的LLM提供商: {provider}")


if __name__ == "__main__":
    # 测试
    client = MockLLMClient()
    
    test_prompt = """你是小神农中医AI助手...

【参考资料】
[参考1]
出处：《伤寒论》·第35条
内容：太阳病，头痛发热，身疼腰痛，骨节疼痛，恶风无汗而喘者，麻黄汤主之。
原文：太阳病，头痛发热，身疼腰痛，骨节疼痛，恶风无汗而喘者，麻黄汤主之。

用户问题：我最近头痛发热，怕冷，没有汗，应该怎么办？

请基于以上参考资料，给出体质辨识和调理建议。"""
    
    result = client.generate(test_prompt)
    print("\n=== LLM输出 ===")
    print(result)
