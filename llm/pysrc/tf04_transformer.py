# -*- coding: utf-8 -*-
"""2.4 完整 Transformer 块 —— 从零拼出 Pre-LN Transformer 块（numpy）。

一个块 = 多头注意力 + 前馈网络，各自套「归一化 + 残差」。
Pre-LN（先归一化再进子层）是现代大模型的稳定选择。
"""
import numpy as np
from dl04_regularization import LayerNorm
from tf02_mha import MultiHeadAttention


def gelu(x):
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))


class FeedForward:
    """逐位置前馈：d -> 4d -> d，中间用 GELU。"""

    def __init__(self, d, hidden, seed=0):
        rng = np.random.default_rng(seed)
        self.W1 = rng.standard_normal((d, hidden)) * np.sqrt(2 / d)
        self.b1 = np.zeros(hidden)
        self.W2 = rng.standard_normal((hidden, d)) * np.sqrt(2 / hidden)
        self.b2 = np.zeros(d)

    def __call__(self, x):
        return gelu(x @ self.W1 + self.b1) @ self.W2 + self.b2


class TransformerBlock:
    def __init__(self, d, n_heads, seed=0):
        self.ln1 = LayerNorm(d)
        self.ln2 = LayerNorm(d)
        self.attn = MultiHeadAttention(d, n_heads, seed)
        self.ff = FeedForward(d, 4 * d, seed + 1)

    def __call__(self, x, mask=None):
        x = x + self.attn(self.ln1.forward(x), mask)   # 残差 + Pre-LN 注意力
        x = x + self.ff(self.ln2.forward(x))           # 残差 + Pre-LN 前馈
        return x


if __name__ == "__main__":
    from tf01_attention import causal_mask
    x = np.random.default_rng(0).standard_normal((2, 10, 64))
    blk = TransformerBlock(64, n_heads=8)
    y = blk(x, mask=causal_mask(10))
    print("输入", x.shape, "-> 输出", y.shape, " (形状不变，可无限堆叠)")
    assert y.shape == x.shape
