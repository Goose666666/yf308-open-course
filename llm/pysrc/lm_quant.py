# -*- coding: utf-8 -*-
"""3.6 量化与推理 —— 从零实现 int8 对称量化。

把 float32 权重用一个缩放因子映射到 [-127,127] 的 int8，存储从 4 字节降到 1 字节，
显存降到 1/4。量化误差通常很小，是大模型部署的常用手段。
"""
import numpy as np


def quantize_int8(W):
    """对称量化：scale = max|W| / 127；q = round(W/scale)。"""
    scale = np.abs(W).max() / 127.0
    q = np.round(W / scale).astype(np.int8)
    return q, scale


def dequantize(q, scale):
    return q.astype(np.float32) * scale


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    W = rng.standard_normal((256, 256)).astype(np.float32)
    q, scale = quantize_int8(W)
    W_hat = dequantize(q, scale)
    err = np.abs(W - W_hat).mean()
    print("原始 dtype", W.dtype, "字节/元素 4 -> int8 字节/元素 1")
    print("显存占用降到", round(q.nbytes / W.nbytes, 3), "倍")
    print("平均量化误差", round(float(err), 5), " (相对幅度很小)")
