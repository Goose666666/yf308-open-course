# -*- coding: utf-8 -*-
"""1.2 手写一个 MLP —— 用 numpy 从零实现全连接网络的前向与反向。

只依赖 numpy。实现 Linear / ReLU 两种层，以及 Softmax + 交叉熵损失，
把它们串成一个能在小数据上真正训练收敛的多层感知机。
"""
import numpy as np


class Linear:
    """全连接层 y = x @ W + b。缓存输入用于反向。"""

    def __init__(self, in_dim, out_dim, seed=None):
        rng = np.random.default_rng(seed)
        # He 初始化：适配 ReLU，方差 2/in_dim
        self.W = rng.standard_normal((in_dim, out_dim)) * np.sqrt(2.0 / in_dim)
        self.b = np.zeros(out_dim)
        self.dW = np.zeros_like(self.W)
        self.db = np.zeros_like(self.b)
        self._x = None

    def forward(self, x):
        self._x = x
        return x @ self.W + self.b

    def backward(self, dout):
        # 原地写入梯度（保持数组引用稳定），这样优化器可一次持有 params 跨步更新
        self.dW[...] = self._x.T @ dout       # dL/dW = xᵀ · dout
        self.db[...] = dout.sum(axis=0)       # dL/db = Σ dout
        return dout @ self.W.T                # dL/dx 往前传

    def params(self):
        return [{"w": self.W, "grad": self.dW}, {"w": self.b, "grad": self.db}]


class ReLU:
    def forward(self, x):
        self._mask = x > 0
        return x * self._mask

    def backward(self, dout):
        return dout * self._mask

    def params(self):
        return []


def softmax_cross_entropy(logits, y):
    """数值稳定的 softmax + 交叉熵。返回 (loss, dlogits)。y 是整数标签。"""
    z = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(z)
    probs = exp / exp.sum(axis=1, keepdims=True)
    n = logits.shape[0]
    loss = -np.log(probs[np.arange(n), y] + 1e-12).mean()
    dlogits = probs.copy()
    dlogits[np.arange(n), y] -= 1           # softmax+CE 的梯度就是 probs - onehot
    dlogits /= n
    return loss, dlogits


class MLP:
    """把若干 Linear/ReLU 串起来的多层感知机。"""

    def __init__(self, sizes, seed=0):
        self.layers = []
        for i in range(len(sizes) - 1):
            self.layers.append(Linear(sizes[i], sizes[i + 1], seed=seed + i))
            if i < len(sizes) - 2:
                self.layers.append(ReLU())

    def forward(self, x):
        for layer in self.layers:
            x = layer.forward(x)
        return x

    def backward(self, dout):
        for layer in reversed(self.layers):
            dout = layer.backward(dout)

    def params(self):
        return [p for layer in self.layers for p in layer.params()]


if __name__ == "__main__":
    # 造一个两类螺旋/高斯数据，训练 MLP 分类
    rng = np.random.default_rng(0)
    n = 200
    X0 = rng.standard_normal((n, 2)) + np.array([2, 2])
    X1 = rng.standard_normal((n, 2)) + np.array([-2, -2])
    X = np.vstack([X0, X1])
    y = np.array([0] * n + [1] * n)

    net = MLP([2, 32, 32, 2], seed=1)
    lr = 0.1
    for epoch in range(200):
        logits = net.forward(X)
        loss, dlogits = softmax_cross_entropy(logits, y)
        net.backward(dlogits)
        for p in net.params():                # 朴素 SGD
            p["w"] -= lr * p["grad"]
        if epoch % 50 == 0 or epoch == 199:
            acc = (net.forward(X).argmax(1) == y).mean()
            print(f"epoch {epoch:3d}  loss {loss:.4f}  acc {acc:.3f}")
