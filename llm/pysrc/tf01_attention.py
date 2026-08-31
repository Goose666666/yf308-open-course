# -*- coding: utf-8 -*-
"""2.1 Attention 机制 —— 缩放点积注意力从零实现（numpy）。

注意力用查询 Q、键 K、值 V 三个角色，按 Q 与 K 的相关程度加权聚合 V。
核心公式：Attention(Q,K,V) = softmax(QKᵀ/√d) V。
"""
import numpy as np


def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)      # 数值稳定
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


def scaled_dot_product_attention(Q, K, V, mask=None):
    """Q,K,V 形状 [..., seq, d]。mask 为 True 处允许注意。返回 (输出, 注意力权重)。"""
    d = Q.shape[-1]
    scores = Q @ K.swapaxes(-1, -2) / np.sqrt(d)  # [..., seq_q, seq_k]
    if mask is not None:
        scores = np.where(mask, scores, -1e9)     # 屏蔽处置为极小值
    weights = softmax(scores, axis=-1)
    return weights @ V, weights


def causal_mask(seq):
    """下三角为 True：位置 i 只能看到 ≤ i 的位置（自回归所需）。"""
    return np.tril(np.ones((seq, seq), dtype=bool))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    Q = rng.standard_normal((1, 4, 8))
    K = rng.standard_normal((1, 4, 8))
    V = rng.standard_normal((1, 4, 8))
    out, w = scaled_dot_product_attention(Q, K, V)
    print("输出形状", out.shape, " 注意力权重每行和 =", np.round(w[0].sum(-1), 3))
    out_c, w_c = scaled_dot_product_attention(Q, K, V, mask=causal_mask(4))
    print("因果掩码下，第 1 个位置只关注自己：", np.round(w_c[0, 0], 3))
