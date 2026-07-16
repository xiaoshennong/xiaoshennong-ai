#!/usr/bin/env python3
"""
小神农中医AI - Yunwu AI API客户端（统一入口）
所有 LLM 调用均通过 yunwu.ai（OpenAI 兼容格式）。
"""

import os
import json
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
import urllib.request
import urllib.error


@dataclass
class LLMResponse:
    """LLM响应结构"""
    text: str
    model: str
    usage: Dict[str, Any]
    latency_ms: float


class YunwuAIClient:
    """
    Yunwu AI API 客户端（OpenAI 兼容格式）
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 model: str = "gpt-4o-mini"):
        # 优先使用传入参数，其次环境变量，不再内置任何硬编码 key
        self.api_key = api_key or os.getenv("YUNWU_API_KEY", "")
        self.base_url = base_url or os.getenv("YUNWU_API_BASE") or os.getenv(
            "YUNWU_BASE_URL", "https://yunwu.ai/v1"
        )
        self.model = model or os.getenv("YUNWU_MODEL", "gpt-4o-mini")

        print(f"[LLM] Yunwu AI 客户端初始化: {self.base_url}, model={self.model}")
        if self.api_key:
            print(f"[LLM] API Key: {self.api_key[:20]}...")
        else:
            print("[LLM] 警告：未配置 YUNWU_API_KEY")

    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """
        调用 Yunwu AI API 生成回答。
        """
        if not self.api_key:
            return "[系统错误：未配置Yunwu AI API Key]"

        url = f"{self.base_url}/chat/completions"

        system_content = system_prompt or (
            "你是一个严格的中医知识助手。你只基于用户提供的参考资料回答，"
            "绝对不使用自己的知识。对于没有依据的内容必须回答'暂无权威数据支持'。"
            "每条结论必须标注出处。"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_content},
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
                data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                headers=headers,
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode('utf-8'))

            latency = (time.time() - start_time) * 1000

            if data.get("choices"):
                result_text = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                print(
                    f"[LLM] Yunwu AI 调用完成，耗时{latency:.0f}ms, "
                    f"prompt_tokens: {usage.get('prompt_tokens', 0)}, "
                    f"completion_tokens: {usage.get('completion_tokens', 0)}"
                )
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
            print(f"[LLM] Yunwu AI 调用失败: {e}")
            return "[系统错误：AI服务暂时不可用，请稍后重试]"

    def chat(self, messages: list, temperature: float = 0.3,
             max_tokens: int = 2000, response_format: Optional[Dict] = None) -> str:
        """
        通用 chat/completions 调用，支持自定义 messages 和 response_format。
        """
        if not self.api_key:
            raise RuntimeError("未配置 YUNWU_API_KEY")

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if response_format:
            payload["response_format"] = response_format

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        if data.get("choices"):
            return data["choices"][0]["message"]["content"]
        raise RuntimeError(f"Yunwu API 返回异常: {data}")


def get_llm_client(provider: str = "auto") -> YunwuAIClient:
    """
    获取 LLM 客户端。
    无论传入什么 provider，均返回 YunwuAIClient，确保所有调用走 yunwu.ai。
    """
    if provider != "yunwu" and provider != "auto":
        print(f"[LLM] 忽略 provider={provider}，统一使用 Yunwu AI")
    return YunwuAIClient()


# 保留旧别名，确保导入兼容性
KimiAPIClient = YunwuAIClient


if __name__ == "__main__":
    print("=== 测试 Yunwu AI API ===\n")

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

    print("调用 Yunwu AI API...")
    result = client.generate(test_prompt, temperature=0.3)
    print("\n=== 结果 ===")
    print(result[:500])
