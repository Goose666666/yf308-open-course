# -*- coding: utf-8 -*-
"""1.4 正则化与训练技巧 —— Dropout / BatchNorm / LayerNorm / 权重初始化。

关注两点：训练与推理阶段行为不同（Dropout、BatchNorm）；
归一化如何稳定分布、初始化如何保持信号方差。
"""
import numpy as np


class Dropout:
    """训练时按概率 p 置零并放大 1/(1-p)（inverted dropout），推理时恒等。"""

    def __init__(self, p=0.5, seed=0):
        self.p = p
        self.rng = np.random.default_rng(seed)

    def forward(self, x, training=True):
        if not training or self.p == 0:
            return x
        mask = (self.rng.random(x.shape) > self.p) / (1 - self.p)
        self._mask = mask
        return x * mask

    def backward(self, dout):
        return dout * self._mask


class BatchNorm1d:
    """按 batch 维归一化。训练用当前 batch 统计量并更新运行均值/方差，推理用运行值。"""

    def __init__(self, dim, momentum=0.1, eps=1e-5):
        self.gamma = np.ones(dim)
        self.beta = np.zeros(dim)
        self.run_mean = np.zeros(dim)
        self.run_var = np.ones(dim)
        self.momentum, self.eps = momentum, eps

    def forward(self, x, training=True):
        if training:
            mu = x.mean(0)
            var = x.var(0)
            self.run_mean = (1 - self.momentum) * self.run_mean + self.momentum * mu
            self.run_var = (1 - self.momentum) * self.run_var + self.momentum * var
        else:
            mu, var = self.run_mean, self.run_var
        x_hat = (x - mu) / np.sqrt(var + self.eps)
        return self.gamma * x_hat + self.beta


class LayerNorm:
    """按特征维（每个样本自己）归一化。与 batch 大小无关，Transformer 首选。"""

    def __init__(self, dim, eps=1e-5):
        self.gamma = np.ones(dim)
        self.beta = np.zeros(dim)
        self.eps = eps

    def forward(self, x):
        mu = x.mean(-1, keepdims=True)
        var = x.var(-1, keepdims=True)
        x_hat = (x - mu) / np.sqrt(var + self.eps)
        return self.gamma * x_hat + self.beta


def xavier_init(fan_in, fan_out, seed=0):
    """Xavier/Glorot：适配 tanh/sigmoid，方差 1/fan_in 量级。"""
    rng = np.random.default_rng(seed)
    return rng.standard_normal((fan_in, fan_out)) * np.sqrt(1.0 / fan_in)


def he_init(fan_in, fan_out, seed=0):
    """He/Kaiming：适配 ReLU，方差 2/fan_in。"""
    rng = np.random.default_rng(seed)
    return rng.standard_normal((fan_in, fan_out)) * np.sqrt(2.0 / fan_in)


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    x = rng.standard_normal((4, 8)) * 5 + 3
    print("LayerNorm 后每行均值≈0 方差≈1：")
    y = LayerNorm(8).forward(x)
    print("  mean", np.round(y.mean(-1), 4), " var", np.round(y.var(-1), 3))

    bn = BatchNorm1d(8)
    yt = bn.forward(x, training=True)
    print("BatchNorm(train) 后每列均值≈0：", np.round(yt.mean(0), 4))

    d = Dropout(p=0.5)
    xt = d.forward(np.ones((2, 6)), training=True)
    print("Dropout(train) 期望不变，样例：", np.round(xt[0], 2))
    print("Dropout(eval) 恒等：", d.forward(np.ones((2, 6)), training=False)[0])

    # 初始化对比：8 层线性传播后信号方差是否稳定
    for name, init in [("Xavier", xavier_init), ("He(+ReLU)", he_init)]:
        h = rng.standard_normal((256, 128))
        for i in range(8):
            W = init(h.shape[1], 128, seed=i)
            h = h @ W
            if name.startswith("He"):
                h = np.maximum(h, 0)
        print(f"{name} 8 层后方差 {h.var():.4f}")
