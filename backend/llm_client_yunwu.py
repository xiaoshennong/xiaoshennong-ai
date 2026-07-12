#!/usr/bin/env python3
"""
小神农中医AI - Yunwu AI API客户端
使用yunwu.ai的API（兼容OpenAI格式）
"""

import os
import json
import time
from typing import Optional, Dict
from dataclasses import dataclass
import urllib.request
import urllib.error


@dataclass
class LLMResponse:
    """LLM响应结构"""
    text: str
    model: str
    usage: Dict
    latency_ms: float


class YunwuAIClient:
    """
    Yunwu AI API客户端
    兼容OpenAI API格式
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("YUNWU_API_KEY", "sk-kGZ5PiMxdpT91QzvvcGPMNk8Sp6Uzkmdmmaq20aE2kEEpzvl")
        self.base_url = base_url or os.getenv("YUNWU_BASE_URL", "https://yunwu.ai/v1")
        self.model = model
        
        print(f"[LLM] Yunwu AI客户端初始化: {self.base_url}, model={model}")
        print(f"[LLM] API Key: {self.api_key[:20]}...")
    
    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """
        调用Yunwu AI API生成回答
        """
        if not self.api_key:
            return "[系统错误：未配置Yunwu AI API Key]"
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个严格的中医知识助手。你只基于用户提供的参考资料回答，绝对不使用自己的知识。对于没有依据的内容必须回答'暂无权威数据支持'。每条结论必须标注出处。"
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            start_time = time.time()
            
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            
            latency = (time.time() - start_time) * 1000
            
            if "choices" in data and len(data["choices"]) > 0:
                result_text = data["choices"][0]["message"]["content"]
                
                usage = data.get("usage", {})
                print(f"[LLM] Yunwu AI调用完成，耗时{latency:.0f}ms, "
                      f"prompt_tokens: {usage.get('prompt_tokens', 0)}, "
                      f"completion_tokens: {usage.get('completion_tokens', 0)}")
                
                return result_text
            else:
                print(f"[LLM] API返回异常: {data}")
                return "[系统错误：API返回异常]"
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"[LLM] Yunwu AI HTTP错误 {e.code}: {error_body}")
            
            if e.code == 401:
                return "[系统错误：API Key无效或已过期]"
            elif e.code == 429:
                return "[系统错误：请求过于频繁，请稍后重试]"
            return f"[系统错误：HTTP {e.code}]"
            
        except Exception as e:
            print(f"[LLM] Yunwu AI调用失败: {e}")
            return "[系统错误：AI服务暂时不可用，请稍后重试]"


class KimiAPIClient:
    """
    Kimi API客户端（开放平台）
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "moonshot-v1-8k"):
        self.api_key = api_key or os.getenv("KIMI_API_KEY", "sk-kimi-dv9yPey41r9gtlv4nyIIZtaeqRCpGjbRR5cz78zF07kveFmx6kDlg4PCE4Dhj6xs")
        self.base_url = "https://api.moonshot.cn/v1"
        self.model = model
        
        print(f"[LLM] Kimi API客户端初始化: {self.base_url}, model={model}")
    
    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """调用Kimi API生成回答"""
        if not self.api_key:
            return "[系统错误：未配置Kimi API Key]"
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个严格的中医知识助手。你只基于用户提供的参考资料回答，绝对不使用自己的知识。对于没有依据的内容必须回答'暂无权威数据支持'。每条结论必须标注出处。"
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            start_time = time.time()
            
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            
            latency = (time.time() - start_time) * 1000
            
            if "choices" in data and len(data["choices"]) > 0:
                result_text = data["choices"][0]["message"]["content"]
                
                usage = data.get("usage", {})
                print(f"[LLM] Kimi API调用完成，耗时{latency:.0f}ms")
                
                return result_text
            else:
                return "[系统错误：API返回异常]"
                
        except Exception as e:
            print(f"[LLM] Kimi API调用失败: {e}")
            return "[系统错误：AI服务暂时不可用]"


def get_llm_client(provider: str = "auto"):
    """
    获取LLM客户端
    
    provider选项：
    - "yunwu": Yunwu AI API（推荐，用户提供的key）
    - "kimi": Kimi开放平台API
    - "kimi-code": Kimi Code CLI内部API
    - "deepseek": DeepSeek API
    - "mock": 模拟客户端
    - "auto": 自动检测
    """
    if provider == "auto":
        # 优先检测Yunwu AI（用户明确提供的key）
        if os.getenv("YUNWU_API_KEY") or True:  # 默认有硬编码的key
            provider = "yunwu"
        elif os.getenv("KIMI_API_KEY"):
            provider = "kimi"
        elif os.getenv("DEEPSEEK_API_KEY"):
            provider = "deepseek"
        else:
            provider = "mock"
    
    if provider == "yunwu":
        return YunwuAIClient()
    elif provider == "kimi":
        return KimiAPIClient()
    elif provider == "kimi-code":
        try:
            from llm_client_v3 import KimiCodeCLIClient
            return KimiCodeCLIClient()
        except ImportError:
            print("[LLM] Kimi Code CLI客户端不可用，回退到Yunwu AI")
            return YunwuAIClient()
    elif provider == "deepseek":
        try:
            from llm_client import DeepSeekClient
            return DeepSeekClient()
        except ImportError:
            pass
    
    # 默认返回Yunwu AI
    print(f"[LLM] 使用Yunwu AI作为默认客户端")
    return YunwuAIClient()


if __name__ == "__main__":
    print("=== 测试Yunwu AI API ===\n")
    
    client = YunwuAIClient()
    
    test_prompt = """你是小神农中医AI助手，必须严格遵守以下规则：

1. 只基于下面提供的【参考资料】回答问题，绝对不能使用你自己的任何知识。
2. 如果【参考资料】中没有相关内容，直接回答："抱歉，暂无权威数据支持该问题。"
3. 每给出一个结论，必须在后面标注对应的出处，格式为：[出处：《书名》·篇章]。

【参考资料】
[参考1]
出处：《伤寒论》·第35条
内容：太阳病，头痛发热，身疼腰痛，骨节疼痛，恶风无汗而喘者，麻黄汤主之。

用户问题：我最近头痛发热，怕冷，没有汗，应该怎么办？

请基于以上参考资料，给出体质辨识和调理建议。"""
    
    print("调用Yunwu AI API...")
    result = client.generate(test_prompt, temperature=0.3)
    print("\n=== 结果 ===")
    print(result[:500])
