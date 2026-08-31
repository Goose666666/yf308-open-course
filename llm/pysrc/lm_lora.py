# -*- coding: utf-8 -*-
"""3.5 LoRA —— 从零实现低秩适配（Low-Rank Adaptation）。

冻结原权重 W，只训练两个小矩阵 A、B（秩 r 远小于维度），
用 W + (B A)·(α/r) 近似微调。可训练参数从 d² 降到 2dr，省显存、易切换。
"""
import numpy as np


class LoRALinear:
    def __init__(self, W, rank=4, alpha=8, seed=0):
        self.W = W                              # 冻结的原权重 [d_in, d_out]
        d_in, d_out = W.shape
        rng = np.random.default_rng(seed)
        self.A = rng.standard_normal((d_in, rank)) * 0.01
        self.B = np.zeros((rank, d_out))        # B 初始化为 0 → 起点等于原模型
        self.scale = alpha / rank

    def __call__(self, x):
        return x @ self.W + (x @ self.A @ self.B) * self.scale

    def trainable_params(self):
        return self.A.size + self.B.size        # 只有 A、B 可训

    def frozen_params(self):
        return self.W.size


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    W = rng.standard_normal((512, 512))         # 原始全连接权重
    lora = LoRALinear(W, rank=8)
    x = rng.standard_normal((2, 512))
    print("输出形状", lora(x).shape)
    tp, fp = lora.trainable_params(), lora.frozen_params()
    print(f"冻结参数 {fp}, 可训练参数 {tp}, 仅占 {100*tp/fp:.2f}%")
    print("B 初始化为 0，微调起点 = 原模型（输出与仅用 W 一致）:",
          np.allclose(lora(x), x @ W))
