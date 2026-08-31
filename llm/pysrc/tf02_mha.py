# -*- coding: utf-8 -*-
"""2.2 Multi-Head Attention —— 多头注意力从零实现（numpy）。

把 d_model 拆成 h 个头，每个头在低维子空间独立做注意力，再拼接、过输出投影。
多头让模型在不同子空间关注不同的关系。
"""
import numpy as np
from tf01_attention import scaled_dot_product_attention


class MultiHeadAttention:
    def __init__(self, d_model, n_heads, seed=0):
        assert d_model % n_heads == 0
        rng = np.random.default_rng(seed)
        s = 1.0 / np.sqrt(d_model)
        self.h, self.d, self.dk = n_heads, d_model, d_model // n_heads
        self.Wq = rng.standard_normal((d_model, d_model)) * s
        self.Wk = rng.standard_normal((d_model, d_model)) * s
        self.Wv = rng.standard_normal((d_model, d_model)) * s
        self.Wo = rng.standard_normal((d_model, d_model)) * s

    def _split(self, x):
        B, T, _ = x.shape
        return x.reshape(B, T, self.h, self.dk).transpose(0, 2, 1, 3)  # [B,H,T,dk]

    def __call__(self, x, mask=None):
        B, T, D = x.shape
        q = self._split(x @ self.Wq)
        k = self._split(x @ self.Wk)
        v = self._split(x @ self.Wv)
        out, _ = scaled_dot_product_attention(q, k, v, mask)          # [B,H,T,dk]
        out = out.transpose(0, 2, 1, 3).reshape(B, T, D)             # 拼接各头
        return out @ self.Wo


if __name__ == "__main__":
    x = np.random.default_rng(0).standard_normal((2, 6, 64))
    mha = MultiHeadAttention(64, n_heads=8)
    y = mha(x)
    print("输入", x.shape, "-> 输出", y.shape, " (8 头, 每头 8 维)")
    assert y.shape == x.shape
