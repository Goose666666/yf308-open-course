# -*- coding: utf-8 -*-
"""1.1 张量与自动求导 —— 从零实现一个标量自动微分引擎（micrograd 风格）。

核心思想：每个 Value 记住它是由哪些 Value、经过什么运算得到的（构建计算图），
反向传播时按拓扑序从输出往输入,用链式法则把梯度一层层乘回去。
"""
import math


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


if __name__ == "__main__":
    # 例子：f = (a*b + c).tanh，手算与自动微分对比
    a, b, c = Value(2.0), Value(-3.0), Value(10.0)
    f = (a * b + c).tanh()
    f.backward()
    print("f =", round(f.data, 4))
    print("df/da =", round(a.grad, 4), " df/db =", round(b.grad, 4), " df/dc =", round(c.grad, 4))
    # 数值梯度校验
    h = 1e-6
    a2 = Value(2.0 + h)
    f2 = (a2 * Value(-3.0) + Value(10.0)).tanh()
    print("数值 df/da ≈", round((f2.data - f.data) / h, 4))
