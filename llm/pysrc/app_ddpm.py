# -*- coding: utf-8 -*-
"""4.4 扩散模型 DDPM —— 从零实现前向扩散（加噪）过程。

扩散模型分两步：前向逐步给数据加高斯噪声直到变成纯噪声；
反向训练一个网络逐步去噪、从噪声还原数据。这里实现可解析的前向过程。
"""
import numpy as np


def make_schedule(T, beta_start=1e-4, beta_end=0.02):
    """线性噪声表。返回 betas 与累积 alpha_bar。"""
    betas = np.linspace(beta_start, beta_end, T)
    alphas = 1 - betas
    alpha_bar = np.cumprod(alphas)
    return betas, alpha_bar


def q_sample(x0, t, alpha_bar, noise):
    """前向扩散闭式解：x_t = √ᾱ_t · x0 + √(1−ᾱ_t) · ε。"""
    ab = alpha_bar[t]
    return np.sqrt(ab) * x0 + np.sqrt(1 - ab) * noise


if __name__ == "__main__":
    T = 200
    betas, alpha_bar = make_schedule(T)
    rng = np.random.default_rng(0)
    x0 = np.ones((1000,)) * 2.0                  # 原始「数据」
    noise = rng.standard_normal(x0.shape)
    print("噪声表长度", T)
    for t in [0, 50, 150, 199]:
        xt = q_sample(x0, t, alpha_bar, noise)
        print(f"  t={t:3d}: 信号占比 √ᾱ={np.sqrt(alpha_bar[t]):.3f}, "
              f"x_t 均值={xt.mean():.3f} 标准差={xt.std():.3f}")
    print("t 越大信号越弱、越接近标准正态噪声")
