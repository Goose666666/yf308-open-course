# -*- coding: utf-8 -*-
"""2.3 位置编码 —— 正弦编码与 RoPE 从零实现（numpy）。

自注意力对顺序不敏感，必须显式注入位置信息。
正弦编码用不同频率的 sin/cos；RoPE 用旋转把相对位置编进 Q/K。
"""
import numpy as np


def sinusoidal_encoding(seq, d):
    """经典正弦位置编码，形状 [seq, d]。偶数维用 sin、奇数维用 cos。"""
    pos = np.arange(seq)[:, None]
    i = np.arange(d)[None, :]
    angle = pos / np.power(10000, (2 * (i // 2)) / d)
    pe = np.zeros((seq, d))
    pe[:, 0::2] = np.sin(angle[:, 0::2])
    pe[:, 1::2] = np.cos(angle[:, 1::2])
    return pe


def apply_rope(x, base=10000):
    """旋转位置编码：对 x[..., seq, d] 的每对维度按位置旋转。d 需为偶数。"""
    seq, d = x.shape[-2], x.shape[-1]
    theta = 1.0 / np.power(base, np.arange(0, d, 2) / d)   # [d/2]
    ang = np.arange(seq)[:, None] * theta[None, :]         # [seq, d/2]
    cos, sin = np.cos(ang), np.sin(ang)
    x1, x2 = x[..., 0::2], x[..., 1::2]
    out = np.empty_like(x)
    out[..., 0::2] = x1 * cos - x2 * sin
    out[..., 1::2] = x1 * sin + x2 * cos
    return out


if __name__ == "__main__":
    pe = sinusoidal_encoding(16, 32)
    print("正弦编码形状", pe.shape, " 每行范数相近：", np.round(np.linalg.norm(pe, axis=1)[:3], 3))
    x = np.random.default_rng(0).standard_normal((1, 8, 16))
    xr = apply_rope(x)
    print("RoPE 后形状不变", xr.shape, " 且保范数：", np.round(np.linalg.norm(x), 3),
          "≈", np.round(np.linalg.norm(xr), 3))
