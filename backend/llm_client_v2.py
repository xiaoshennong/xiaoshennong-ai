#!/usr/bin/env python3
"""
小神农中医AI - Kimi Code API客户端
直接使用Kimi Code的API能力作为LLM生成层
"""

import os
import time
import json
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """LLM响应结构"""
    text: str
    model: str
    usage: Dict
    latency_ms: float


class KimiCodeClient:
    """
    Kimi Code API客户端
    使用OpenAI兼容接口调用Kimi Code
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "kimi-latest"):
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
        self.model = model
        # Kimi Code使用OpenAI兼容接口
        self.base_url = "https://api.moonshot.cn/v1"
        
        if not self.api_key:
            print("[LLM] 警告：未设置Kimi API Key，尝试从环境变量获取")
            # 尝试读取Kimi Code配置文件
            self._try_load_from_config()
    
    def _try_load_from_config(self):
        """尝试从Kimi Code配置文件中读取API Key"""
        config_paths = [
            os.path.expanduser("~/.kimi-code/config.toml"),
            os.path.expanduser("~/.kimi/config.toml"),
            os.path.expanduser("~/.config/kimi-code/config.toml"),
        ]
        
        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 简单解析TOML查找api_key
                        for line in content.split('\n'):
                            if 'api_key' in line and '=' in line:
                                key = line.split('=')[1].strip().strip('"').strip("'")
                                if key and key != 'YOUR_API_KEY':
                                    self.api_key = key
                                    print(f"[LLM] 从配置文件读取API Key: {path}")
                                    return
                except Exception:
                    pass
    
    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """
        调用Kimi Code API生成回答
        
        参数：
            prompt: 完整的提示词（已包含参考资料和约束）
            temperature: 0.3（低随机性，减少幻觉）
            max_tokens: 最大输出长度
        
        返回：
            生成的文本内容
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
                    {
                        "role": "system", 
                        "content": "你是一个严格的中医知识助手。你只基于用户提供的参考资料回答，绝对不使用自己的知识。对于没有依据的内容必须回答'暂无权威数据支持'。每条结论必须标注出处。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9,
                # 降低重复惩罚，避免截断古籍原文
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            latency = (time.time() - start_time) * 1000
            
            result = LLMResponse(
                text=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                latency_ms=latency
            )
            
            print(f"[LLM] Kimi调用完成，模型: {result.model}, 耗时{latency:.0f}ms, token用量: {result.usage['total_tokens']}")
            return result.text
            
        except Exception as e:
            print(f"[LLM] Kimi调用失败: {e}")
            # 失败时返回错误提示，不编造内容
            return "[系统错误：AI服务暂时不可用，请稍后重试]"


class MockLLMClient:
    """模拟LLM客户端（用于测试，无需API Key）"""
    
    def __init__(self):
        print("[LLM] 使用模拟LLM客户端（无需API Key）")
    
    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """模拟生成：从提示词中提取参考资料内容，格式化输出"""
        
        import re
        
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


def get_llm_client(provider: str = "mock"):
    """
    获取LLM客户端
    
    provider选项：
    - "mock": 模拟客户端，无需API Key，用于测试
    - "kimi": Kimi Code API，需要设置KIMI_API_KEY
    - "deepseek": DeepSeek API，需要设置DEEPSEEK_API_KEY
    """
    if provider == "kimi":
        return KimiCodeClient()
    elif provider == "deepseek":
        # 兼容旧的DeepSeek配置
        from llm_client import DeepSeekClient
        return DeepSeekClient()
    elif provider == "mock":
        return MockLLMClient()
    else:
        raise ValueError(f"不支持的LLM提供商: {provider}")


if __name__ == "__main__":
    # 测试Kimi Code API
    print("=== 测试Kimi Code API ===")
    
    # 尝试初始化
    client = KimiCodeClient()
    
    if client.api_key:
        print(f"API Key已配置: {client.api_key[:10]}...")
        
        # 测试调用
        test_prompt = """你是小神农中医AI助手，必须严格遵守以下规则：

1. 只基于下面提供的【参考资料】回答问题，绝对不能使用你自己的任何知识。
2. 如果【参考资料】中没有相关内容，直接回答："抱歉，暂无权威数据支持该问题。"

【参考资料】
[参考1]
出处：《伤寒论》·第35条
内容：太阳病，头痛发热，身疼腰痛，骨节疼痛，恶风无汗而喘者，麻黄汤主之。

用户问题：我最近头痛发热，怕冷，没有汗，应该怎么办？

请基于以上参考资料，给出体质辨识和调理建议。"""
        
        result = client.generate(test_prompt, temperature=0.3)
        print("\n=== LLM输出 ===")
        print(result[:500])
    else:
        print("API Key未配置，跳过测试")
        print("设置方式：")
        print("  1. 环境变量: set KIMI_API_KEY=your-key")
        print("  2. 配置文件: ~/.kimi-code/config.toml")
