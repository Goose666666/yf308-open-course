# -*- coding: utf-8 -*-
"""2.5 手写 GPT —— 从零拼一个最小 GPT 前向 + 自回归生成（numpy）。

GPT = 词嵌入 + 位置编码 → 若干因果 Transformer 块 → 归一化 → 输出头（映回词表）。
生成时逐个 token：取最后位置的 logits、选下一个、拼回序列、再前向。
"""
import numpy as np
from tf04_transformer import TransformerBlock
from tf01_attention import causal_mask
from tf03_posenc import sinusoidal_encoding
from dl04_regularization import LayerNorm


class MiniGPT:
    def __init__(self, vocab, d, n_heads, n_layers, max_seq, seed=0):
        rng = np.random.default_rng(seed)
        self.tok_emb = rng.standard_normal((vocab, d)) * 0.02
        self.pos = sinusoidal_encoding(max_seq, d)
        self.blocks = [TransformerBlock(d, n_heads, seed + i) for i in range(n_layers)]
        self.lnf = LayerNorm(d)
        self.head = rng.standard_normal((d, vocab)) * 0.02
        self.vocab = vocab

    def forward(self, idx):
        """idx: [B, T] 整数 token。返回 logits [B, T, vocab]。"""
        B, T = idx.shape
        x = self.tok_emb[idx] + self.pos[:T]        # 词嵌入 + 位置
        mask = causal_mask(T)
        for blk in self.blocks:
            x = blk(x, mask)
        return self.lnf.forward(x) @ self.head

    def generate(self, idx, n_new):
        """贪心自回归生成 n_new 个 token。"""
        for _ in range(n_new):
            logits = self.forward(idx)
            nxt = logits[:, -1].argmax(-1, keepdims=True)   # 取最后位置最大概率 token
            idx = np.concatenate([idx, nxt], axis=1)
        return idx


if __name__ == "__main__":
    gpt = MiniGPT(vocab=50, d=64, n_heads=4, n_layers=2, max_seq=32, seed=0)
    idx = np.array([[1, 2, 3]])
    logits = gpt.forward(idx)
    print("前向 logits 形状", logits.shape, " (B, T, vocab)")
    out = gpt.generate(idx, n_new=5)
    print("生成序列 (未训练, 仅演示自回归流程):", out[0].tolist())
