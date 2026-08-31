# -*- coding: utf-8 -*-
"""1.6 RNN / LSTM —— 从零实现循环单元的前向，理解序列建模与门控。

RNNCell 只有一条隐状态，长序列易梯度消失；LSTM 增加细胞状态 c 与三个门，
让信息可以近乎无损地沿时间流动。
"""
import numpy as np


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


class RNNCell:
    """h_t = tanh(x_t Wx + h_{t-1} Wh + b)。"""

    def __init__(self, in_dim, hid_dim, seed=0):
        rng = np.random.default_rng(seed)
        s = np.sqrt(1.0 / hid_dim)
        self.Wx = rng.standard_normal((in_dim, hid_dim)) * s
        self.Wh = rng.standard_normal((hid_dim, hid_dim)) * s
        self.b = np.zeros(hid_dim)

    def step(self, x, h):
        return np.tanh(x @ self.Wx + h @ self.Wh + self.b)

    def forward(self, xs, h0=None):
        """xs: [T, B, in_dim]。返回每步隐状态 [T, B, hid_dim]。"""
        t, b, _ = xs.shape
        h = np.zeros((b, self.Wh.shape[0])) if h0 is None else h0
        out = []
        for x in xs:
            h = self.step(x, h)
            out.append(h)
        return np.stack(out)


class LSTMCell:
    """标准 LSTM：输入门 i、遗忘门 f、输出门 o、候选 g。"""

    def __init__(self, in_dim, hid_dim, seed=0):
        rng = np.random.default_rng(seed)
        s = np.sqrt(1.0 / hid_dim)
        # 4 个门的权重合并为一块，一次矩阵乘算完
        self.Wx = rng.standard_normal((in_dim, 4 * hid_dim)) * s
        self.Wh = rng.standard_normal((hid_dim, 4 * hid_dim)) * s
        self.b = np.zeros(4 * hid_dim)
        self.b[hid_dim:2 * hid_dim] = 1.0      # 遗忘门偏置初始化为 1，利于长程记忆
        self.hid = hid_dim

    def step(self, x, h, c):
        z = x @ self.Wx + h @ self.Wh + self.b
        H = self.hid
        i = sigmoid(z[:, :H])
        f = sigmoid(z[:, H:2 * H])
        o = sigmoid(z[:, 2 * H:3 * H])
        g = np.tanh(z[:, 3 * H:])
        c = f * c + i * g                       # 细胞状态：遗忘旧的 + 写入新的
        h = o * np.tanh(c)
        return h, c

    def forward(self, xs, h0=None, c0=None):
        t, b, _ = xs.shape
        h = np.zeros((b, self.hid)) if h0 is None else h0
        c = np.zeros((b, self.hid)) if c0 is None else c0
        out = []
        for x in xs:
            h, c = self.step(x, h, c)
            out.append(h)
        return np.stack(out)


if __name__ == "__main__":
    T, B, D, H = 12, 4, 8, 16
    xs = np.random.default_rng(0).standard_normal((T, B, D))

    rnn = RNNCell(D, H)
    print("RNN  输出序列形状：", rnn.forward(xs).shape)

    lstm = LSTMCell(D, H)
    hs = lstm.forward(xs)
    print("LSTM 输出序列形状：", hs.shape, " 末步隐状态范数：", round(np.linalg.norm(hs[-1]), 3))
    print("LSTM 遗忘门偏置初值为 1，帮助长序列保留信息、缓解梯度消失。")
