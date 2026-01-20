"""Token 计数工具"""

import tiktoken


class TokenCounter:
    """Token 计数器"""

    def __init__(self, encoding_name: str = "cl100k_base"):
        """
        初始化 Token 计数器

        Args:
            encoding_name: tiktoken 编码名称，默认为 cl100k_base（GPT-4）
        """
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception:
            # 如果无法加载指定编码，使用默认编码
            self.encoding = tiktoken.encoding_for_model("gpt-4")

    def count_tokens(self, text: str) -> int:
        """
        计算文本的 token 数量

        Args:
            text: 要计算的文本

        Returns:
            token 数量
        """
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception:
            # 如果编码失败，使用近似估算（1 token ≈ 4 字符）
            return len(text) // 4

    def count_messages_tokens(self, messages: list) -> int:
        """
        计算消息列表的 token 数量

        Args:
            messages: 消息列表，格式为 [{"role": "...", "content": "..."}, ...]

        Returns:
            token 数量
        """
        try:
            # 近似计算消息的 token 数
            num_tokens = 0
            for message in messages:
                # 每个消息的格式开销
                num_tokens += 4
                for key, value in message.items():
                    num_tokens += self.count_tokens(str(value))
                    if key == "name":
                        num_tokens -= 1  # name 字段有特殊处理
            num_tokens += 2  # 每个回复的格式开销
            return num_tokens
        except Exception:
            # 如果计算失败，估算所有文本的总 token 数
            total_text = "\n".join([str(m) for m in messages])
            return self.count_tokens(total_text)

    def truncate_text(self, text: str, max_tokens: int) -> str:
        """
        截断文本以适应最大 token 限制

        Args:
            text: 要截断的文本
            max_tokens: 最大 token 数

        Returns:
            截断后的文本
        """
        try:
            tokens = self.encoding.encode(text)
            if len(tokens) <= max_tokens:
                return text

            truncated_tokens = tokens[:max_tokens]
            return self.encoding.decode(truncated_tokens)
        except Exception:
            # 如果编码失败，按字符数截断
            max_chars = max_tokens * 4
            return text[:max_chars]

    def estimate_cost(
        self, input_tokens: int, output_tokens: int, input_price: float = 0.0001, output_price: float = 0.0002
    ) -> float:
        """
        估算 API 调用成本

        Args:
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
            input_price: 每 1K 输入 token 的价格（美元）
            output_price: 每 1K 输出 token 的价格（美元）

        Returns:
            估算成本（美元）
        """
        input_cost = (input_tokens / 1000) * input_price
        output_cost = (output_tokens / 1000) * output_price
        return input_cost + output_cost


# 全局实例
_token_counter = None


def get_token_counter() -> TokenCounter:
    """获取 Token 计数器单例"""
    global _token_counter
    if _token_counter is None:
        _token_counter = TokenCounter()
    return _token_counter
