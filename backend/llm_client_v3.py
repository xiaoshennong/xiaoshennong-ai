#!/usr/bin/env python3
"""
小神农中医AI - Kimi Code CLI API客户端
直接使用Kimi Code CLI的OAuth token调用内部API
API地址: https://api.kimi.com/coding/v1
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


class KimiCodeCLIClient:
    """
    Kimi Code CLI API客户端
    使用Kimi Code CLI的OAuth token直接调用内部API
    """
    
    def __init__(self, access_token: Optional[str] = None, model: str = "kimi-for-coding"):
        self.model = model
        self.base_url = "https://api.kimi.com/coding/v1"
        
        # 获取access token
        self.access_token = access_token or self._load_token_from_credentials()
        
        if not self.access_token:
            print("[LLM] 警告：无法获取Kimi Code CLI的access token")
            print("[LLM] 请确保已登录Kimi Code CLI")
        else:
            print(f"[LLM] Kimi Code CLI token已加载: {self.access_token[:20]}...")
    
    def _load_token_from_credentials(self) -> Optional[str]:
        """从Kimi Code CLI的凭据文件加载token"""
        credential_paths = [
            os.path.expanduser("~/.kimi-code/credentials/kimi-code.json"),
            os.path.expanduser("~/.kimi/credentials/kimi-code.json"),
        ]
        
        for path in credential_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    access_token = data.get("access_token")
                    expires_at = data.get("expires_at", 0)
                    
                    # 检查token是否过期
                    if expires_at and expires_at < time.time():
                        print(f"[LLM] Token已过期，尝试刷新...")
                        refresh_token = data.get("refresh_token")
                        if refresh_token:
                            return self._refresh_token(refresh_token)
                        return None
                    
                    return access_token
                    
                except Exception as e:
                    print(f"[LLM] 读取凭据失败: {e}")
                    continue
        
        return None
    
    def _refresh_token(self, refresh_token: str) -> Optional[str]:
        """刷新token"""
        # 简化实现：实际应该调用Kimi的token刷新接口
        print("[LLM] Token刷新未实现，请重新登录Kimi Code CLI")
        return None
    
    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """
        调用Kimi Code CLI API生成回答
        
        使用OpenAI兼容的chat completions接口
        """
        if not self.access_token:
            return "[系统错误：未配置Kimi Code CLI，请登录后再试]"
        
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
            "max_tokens": max_tokens
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
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
                print(f"[LLM] Kimi Code调用完成，耗时{latency:.0f}ms, "
                      f"prompt_tokens: {usage.get('prompt_tokens', 0)}, "
                      f"completion_tokens: {usage.get('completion_tokens', 0)}")
                
                return result_text
            else:
                print(f"[LLM] API返回异常: {data}")
                return "[系统错误：API返回异常]"
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"[LLM] Kimi Code HTTP错误 {e.code}: {error_body}")
            
            if e.code == 401:
                return "[系统错误：Kimi Code CLI token已过期，请重新登录]"
            return f"[系统错误：HTTP {e.code}]"
            
        except Exception as e:
            print(f"[LLM] Kimi Code调用失败: {e}")
            return "[系统错误：AI服务暂时不可用，请稍后重试]"


def get_llm_client(provider: str = "auto"):
    """
    获取LLM客户端
    
    provider选项：
    - "kimi-code": Kimi Code CLI内部API（推荐）
    - "kimi": Kimi开放平台API
    - "deepseek": DeepSeek API
    - "mock": 模拟客户端（无需API Key）
    - "auto": 自动检测（优先Kimi Code CLI）
    """
    if provider == "auto":
        # 优先检测Kimi Code CLI
        token = KimiCodeCLIClient().access_token
        if token:
            provider = "kimi-code"
        elif os.getenv("KIMI_API_KEY"):
            provider = "kimi"
        elif os.getenv("DEEPSEEK_API_KEY"):
            provider = "deepseek"
        else:
            provider = "mock"
    
    if provider == "kimi-code":
        return KimiCodeCLIClient()
    elif provider == "kimi":
        # 使用Kimi开放平台API
        try:
            from llm_client_v2 import KimiCodeClient
            return KimiCodeClient()
        except ImportError:
            from llm_client import get_llm_client as old_get
            return old_get("kimi")
    elif provider == "deepseek":
        try:
            from llm_client import DeepSeekClient
            return DeepSeekClient()
        except ImportError:
            pass
    elif provider == "mock":
        try:
            from llm_client_v2 import MockLLMClient
            return MockLLMClient()
        except ImportError:
            from llm_client import MockLLMClient
            return MockLLMClient()
    
    # 默认返回Mock
    print(f"[LLM] 无法加载{provider}客户端，使用Mock")
    try:
        from llm_client_v2 import MockLLMClient
        return MockLLMClient()
    except ImportError:
        from llm_client import MockLLMClient
        return MockLLMClient()


if __name__ == "__main__":
    print("=== 测试Kimi Code CLI API ===\n")
    
    client = KimiCodeCLIClient()
    
    if client.access_token:
        print(f"Token已获取: {client.access_token[:30]}...")
        
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
        
        print("\n调用API...")
        result = client.generate(test_prompt, temperature=0.3)
        print("\n=== 结果 ===")
        print(result[:500])
    else:
        print("无法获取token，请确保已登录Kimi Code CLI")
        print("登录命令: kimi login")
