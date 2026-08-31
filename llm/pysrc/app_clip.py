# -*- coding: utf-8 -*-
"""4.3 多模态 / CLIP —— 从零实现对比学习的相似度与损失。

CLIP 用海量图文对训练：让配对的图像/文本向量靠近、不配对的远离。
学到的共享嵌入空间可做零样本分类、图文检索。
"""
import numpy as np


def l2norm(x):
    return x / np.linalg.norm(x, axis=-1, keepdims=True)


def clip_similarity(img_emb, txt_emb):
    """归一化后的图文相似度矩阵 [n_img, n_txt]。"""
    return l2norm(img_emb) @ l2norm(txt_emb).T


def contrastive_loss(sim, temp=0.07):
    """对称的 InfoNCE：对角线（正确配对）应最大。"""
    logits = sim / temp
    n = logits.shape[0]

    def ce(z):
        p = np.exp(z - z.max(1, keepdims=True))
        p /= p.sum(1, keepdims=True)
        return -np.log(p[np.arange(n), np.arange(n)] + 1e-9).mean()

    return (ce(logits) + ce(logits.T)) / 2


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    # 构造「对齐」的图文嵌入：第 i 张图和第 i 段文本共享一个基向量
    base = rng.standard_normal((4, 16))
    img = base + 0.01 * rng.standard_normal((4, 16))
    txt = base + 0.01 * rng.standard_normal((4, 16))
    sim = clip_similarity(img, txt)
    print("相似度矩阵对角(正确配对)均值", round(float(np.diag(sim).mean()), 3))
    print("非对角(错误配对)均值", round(float((sim - np.diag(np.diag(sim))).sum() / 12), 3))
    print("对齐时对比损失", round(float(contrastive_loss(sim)), 4))
    # 打乱文本 → 损失变大
    print("打乱后对比损失", round(float(contrastive_loss(clip_similarity(img, txt[::-1]))), 4))
