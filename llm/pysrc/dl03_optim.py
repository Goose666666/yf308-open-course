# -*- coding: utf-8 -*-
"""1.3 优化器 —— 从零实现 SGD / Momentum / Adam。

优化器接收一组参数（每个是 {"w": 数组, "grad": 数组}），
按各自的更新规则原地修改 w。用一个凸二次函数演示三者的收敛差异。
"""
import numpy as np


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


if __name__ == "__main__":
    print("在病态二次函数上跑 60 步后的剩余损失（越小越好）：")
    print(f"  SGD      {run(SGD,      lr=0.02):.6f}")
    print(f"  Momentum {run(Momentum, lr=0.02, mu=0.9):.6f}")
    print(f"  Adam     {run(Adam,     lr=0.5):.6f}")
