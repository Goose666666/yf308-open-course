# -*- coding: utf-8 -*-
"""第一部分 · 深度学习基础 —— 全部从零手写代码（合订单文件）。
只依赖 numpy（1.1 的 Value 用 math）。按小节顺序组织，可整体阅读、整体运行。
逐节拆分版见 dl01_*.py ~ dl06_*.py，两者内容一致。
"""
import math
import numpy as np


# ==============================================================
# 1.1 张量与自动求导
# ==============================================================
class Value:
    """一个标量及其梯度。支持 + - * / ** 以及 relu/tanh/exp。"""

    def __init__(self, data, _children=(), _op=""):
        self.data = float(data)
        self.grad = 0.0
        self._backward = lambda: None      # 局部反向函数，默认什么都不做
        self._prev = set(_children)        # 生成它的父节点
        self._op = _op

    # ---- 基本运算：每个运算都定义好 forward 结果与 _backward ----
    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), "+")

        def _backward():
            self.grad += out.grad          # d(a+b)/da = 1
            other.grad += out.grad
        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), "*")

        def _backward():
            self.grad += other.data * out.grad   # d(ab)/da = b
            other.grad += self.data * out.grad
        out._backward = _backward
        return out

    def __pow__(self, p):
        assert isinstance(p, (int, float))
        out = Value(self.data ** p, (self,), f"**{p}")

        def _backward():
            self.grad += p * self.data ** (p - 1) * out.grad
        out._backward = _backward
        return out

    def relu(self):
        out = Value(0.0 if self.data < 0 else self.data, (self,), "relu")

        def _backward():
            self.grad += (out.data > 0) * out.grad
        out._backward = _backward
        return out

    def tanh(self):
        t = math.tanh(self.data)
        out = Value(t, (self,), "tanh")

        def _backward():
            self.grad += (1 - t * t) * out.grad
        out._backward = _backward
        return out

    def exp(self):
        e = math.exp(self.data)
        out = Value(e, (self,), "exp")

        def _backward():
            self.grad += e * out.grad
        out._backward = _backward
        return out

    # ---- 反向传播：拓扑排序后逆序调用每个节点的 _backward ----
    def backward(self):
        topo, visited = [], set()

        def build(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build(child)
                topo.append(v)
        build(self)
        self.grad = 1.0                    # 输出对自身的梯度是 1
        for v in reversed(topo):
            v._backward()

    # ---- 语法糖 ----
    def __neg__(self):        return self * -1
    def __sub__(self, o):     return self + (-o if isinstance(o, Value) else Value(-o))
    def __radd__(self, o):    return self + o
    def __rmul__(self, o):    return self * o
    def __truediv__(self, o): return self * (o ** -1 if isinstance(o, Value) else Value(1 / o))
    def __repr__(self):       return f"Value(data={self.data:.4f}, grad={self.grad:.4f})"


# ==============================================================
# 1.2 手写 MLP
# ==============================================================
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


# ==============================================================
# 1.3 优化器
# ==============================================================
class SGD:
    def __init__(self, params, lr=0.01):
        self.params, self.lr = params, lr

    def step(self):
        for p in self.params:
            p["w"] -= self.lr * p["grad"]


class Momentum:
    """带动量的 SGD：v = μv - lr·g；w += v。"""

    def __init__(self, params, lr=0.01, mu=0.9):
        self.params, self.lr, self.mu = params, lr, mu
        self.v = [np.zeros_like(p["w"]) for p in params]

    def step(self):
        for i, p in enumerate(self.params):
            self.v[i] = self.mu * self.v[i] - self.lr * p["grad"]
            p["w"] += self.v[i]


class Adam:
    """Adam：一阶矩 m、二阶矩 v 各自指数滑动，并做偏差校正。"""

    def __init__(self, params, lr=0.01, betas=(0.9, 0.999), eps=1e-8):
        self.params, self.lr = params, lr
        self.b1, self.b2, self.eps = betas[0], betas[1], eps
        self.m = [np.zeros_like(p["w"]) for p in params]
        self.v = [np.zeros_like(p["w"]) for p in params]
        self.t = 0

    def step(self):
        self.t += 1
        for i, p in enumerate(self.params):
            g = p["grad"]
            self.m[i] = self.b1 * self.m[i] + (1 - self.b1) * g
            self.v[i] = self.b2 * self.v[i] + (1 - self.b2) * g * g
            m_hat = self.m[i] / (1 - self.b1 ** self.t)   # 偏差校正
            v_hat = self.v[i] / (1 - self.b2 ** self.t)
            p["w"] -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


def make_quadratic():
    """f(x) = 0.5 xᵀ A x，A 病态（不同方向曲率差异大），最小值在原点。"""
    A = np.array([[20.0, 0.0], [0.0, 1.0]])
    w = np.array([-8.0, -8.0])                # 起点
    param = {"w": w, "grad": np.zeros_like(w)}

    def compute_grad():
        param["grad"][:] = A @ param["w"]
        return 0.5 * param["w"] @ A @ param["w"]
    return param, compute_grad


def run(opt_cls, steps=60, **kw):
    param, compute_grad = make_quadratic()
    opt = opt_cls([param], **kw)
    for _ in range(steps):
        compute_grad()
        opt.step()
    return float(0.5 * param["w"] @ np.array([[20.0, 0.0], [0.0, 1.0]]) @ param["w"])


# ==============================================================
# 1.4 正则化与训练技巧
# ==============================================================
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


# ==============================================================
# 1.5 CNN
# ==============================================================
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


# ==============================================================
# 1.6 RNN / LSTM
# ==============================================================
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
    # 各节最小自检，跑通即说明合订本可用
    print("1.1 autograd:", end=" ")
    a, b = Value(2.0), Value(-3.0)
    f = (a * b).tanh(); f.backward()
    print("f=%.4f  da=%.4f" % (f.data, a.grad))

    print("1.2 MLP:", end=" ")
    rng = np.random.default_rng(0)
    X = np.vstack([rng.standard_normal((50, 2)) + 2, rng.standard_normal((50, 2)) - 2])
    y = np.array([0] * 50 + [1] * 50)
    net = MLP([2, 16, 2], seed=1)
    for _ in range(100):
        loss, d = softmax_cross_entropy(net.forward(X), y); net.backward(d)
        for p in net.params(): p["w"] -= 0.1 * p["grad"]
    print("acc=%.3f" % (net.forward(X).argmax(1) == y).mean())

    print("1.3 optim:", end=" ")
    print("SGD=%.3f Momentum=%.3f Adam=%.3f" %
          (run(SGD, lr=0.02), run(Momentum, lr=0.02, mu=0.9), run(Adam, lr=0.5)))

    print("1.4 norm/init:", end=" ")
    x = np.random.default_rng(0).standard_normal((4, 8)) * 5 + 3
    ln = LayerNorm(8).forward(x)
    print("LN mean=%.2f var=%.2f" % (ln.mean(-1).mean(), ln.var(-1).mean()))

    print("1.5 CNN:", end=" ")
    out = TinyLeNet().forward(np.random.default_rng(0).standard_normal((2, 1, 28, 28)))
    print("feat", out.shape)

    print("1.6 RNN/LSTM:", end=" ")
    xs = np.random.default_rng(0).standard_normal((12, 4, 8))
    print("RNN", RNNCell(8, 16).forward(xs).shape, "LSTM", LSTMCell(8, 16).forward(xs).shape)
