# -*- coding: utf-8 -*-
"""3.2 预训练 —— 用一个字符级 bigram 语言模型演示「预测下一个 token」。

预训练的本质就是最大化下一个 token 的概率。这里用最简单的统计 bigram
（数相邻字符出现次数 → 归一成概率）来体现：训练后困惑度（NLL）显著下降。
"""
import numpy as np


class BigramLM:
    def __init__(self):
        self.chars, self.stoi, self.P = [], {}, None

    def train(self, text):
        self.chars = sorted(set(text))
        self.stoi = {c: i for i, c in enumerate(self.chars)}
        n = len(self.chars)
        counts = np.ones((n, n))                       # +1 拉普拉斯平滑，避免 0 概率
        for a, b in zip(text, text[1:]):
            counts[self.stoi[a], self.stoi[b]] += 1
        self.P = counts / counts.sum(1, keepdims=True)  # 每行归一成条件概率

    def nll(self, text):
        """平均负对数似然（越小越好），等价于 log 困惑度。"""
        total = 0.0
        n = 0
        for a, b in zip(text, text[1:]):
            total += -np.log(self.P[self.stoi[a], self.stoi[b]])
            n += 1
        return total / n

    def generate(self, start, n_new, seed=0):
        rng = np.random.default_rng(seed)
        i = self.stoi[start]
        out = [start]
        for _ in range(n_new):
            i = rng.choice(len(self.chars), p=self.P[i])   # 按学到的分布采样
            out.append(self.chars[i])
        return "".join(out)


if __name__ == "__main__":
    text = "hello world. " * 100
    lm = BigramLM()
    lm.train(text)
    uniform_nll = np.log(len(lm.chars))               # 随机猜的 NLL
    print("字符表大小", len(lm.chars))
    print("随机基线 NLL", round(uniform_nll, 3), " 训练后 NLL", round(lm.nll(text), 3))
    print("生成:", repr(lm.generate("h", 20)))
