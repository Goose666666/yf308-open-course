# -*- coding: utf-8 -*-
"""1.5 CNN —— 从零实现卷积与池化的前向（im2col 加速），搭一个小 LeNet 骨架。

理解卷积 = 局部感受野 + 权重共享；im2col 把卷积转成矩阵乘，
让人看清参数量与计算量的来源。
"""
import numpy as np


def im2col(x, kh, kw, stride=1, pad=0):
    """把 [N,C,H,W] 展成 [N*out_h*out_w, C*kh*kw]，每行是一个感受野。"""
    n, c, h, w = x.shape
    out_h = (h + 2 * pad - kh) // stride + 1
    out_w = (w + 2 * pad - kw) // stride + 1
    xp = np.pad(x, ((0, 0), (0, 0), (pad, pad), (pad, pad)))
    cols = np.zeros((n, c, kh, kw, out_h, out_w))
    for i in range(kh):
        for j in range(kw):
            cols[:, :, i, j, :, :] = xp[:, :, i:i + stride * out_h:stride,
                                        j:j + stride * out_w:stride]
    # [N, out_h, out_w, C, kh, kw] -> 二维
    cols = cols.transpose(0, 4, 5, 1, 2, 3).reshape(n * out_h * out_w, -1)
    return cols, out_h, out_w


class Conv2d:
    """卷积层。W 形状 [out_c, in_c, kh, kw]。"""

    def __init__(self, in_c, out_c, k, stride=1, pad=0, seed=0):
        rng = np.random.default_rng(seed)
        self.W = rng.standard_normal((out_c, in_c, k, k)) * np.sqrt(2.0 / (in_c * k * k))
        self.b = np.zeros(out_c)
        self.k, self.stride, self.pad = k, stride, pad

    def forward(self, x):
        out_c = self.W.shape[0]
        cols, out_h, out_w = im2col(x, self.k, self.k, self.stride, self.pad)
        w_col = self.W.reshape(out_c, -1).T          # [in_c*k*k, out_c]
        out = cols @ w_col + self.b                  # [N*oh*ow, out_c]
        n = x.shape[0]
        return out.reshape(n, out_h, out_w, out_c).transpose(0, 3, 1, 2)


class MaxPool2d:
    def __init__(self, k=2, stride=2):
        self.k, self.stride = k, stride

    def forward(self, x):
        n, c, h, w = x.shape
        out_h = (h - self.k) // self.stride + 1
        out_w = (w - self.k) // self.stride + 1
        out = np.zeros((n, c, out_h, out_w))
        for i in range(out_h):
            for j in range(out_w):
                region = x[:, :, i * self.stride:i * self.stride + self.k,
                           j * self.stride:j * self.stride + self.k]
                out[:, :, i, j] = region.max(axis=(2, 3))
        return out


class TinyLeNet:
    """一个 LeNet 风格骨架（仅前向）：conv-pool-conv-pool，用于观察形状与参数量。"""

    def __init__(self):
        self.conv1 = Conv2d(1, 6, 5, pad=2)          # 28x28 -> 28x28
        self.pool1 = MaxPool2d(2, 2)                 # -> 14x14
        self.conv2 = Conv2d(6, 16, 5)                # -> 10x10
        self.pool2 = MaxPool2d(2, 2)                 # -> 5x5

    def forward(self, x):
        x = self.pool1.forward(np.maximum(self.conv1.forward(x), 0))
        x = self.pool2.forward(np.maximum(self.conv2.forward(x), 0))
        return x

    def num_params(self):
        return (self.conv1.W.size + self.conv1.b.size +
                self.conv2.W.size + self.conv2.b.size)


if __name__ == "__main__":
    x = np.random.default_rng(0).standard_normal((2, 1, 28, 28))
    net = TinyLeNet()
    out = net.forward(x)
    print("输入", x.shape, "-> 特征图", out.shape)
    print("卷积参数量：", net.num_params())
    # 验证权重共享：卷积核参数远少于同规模全连接
    fc_params = 28 * 28 * (6 * 28 * 28)
    print(f"对比：第一层若用全连接约需 {fc_params:,} 参数，卷积仅 {net.conv1.W.size} 个")
