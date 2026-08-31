# -*- coding: utf-8 -*-
"""4.1 RAG —— 从零实现最小检索增强：向量化 + 余弦相似度检索。

RAG 把外部文档编码成向量存起来，用问题向量去检索最相关的片段，
再把片段拼进提示交给 LLM。这里用词袋向量演示检索的核心。
"""
import numpy as np


def embed(text, vocab):
    """词袋向量并 L2 归一化（归一化后点积即余弦相似度）。"""
    v = np.zeros(len(vocab))
    for w in text.lower().split():
        if w in vocab:
            v[vocab[w]] += 1
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


class TinyRAG:
    def __init__(self, docs):
        words = sorted(set(w for d in docs for w in d.lower().split()))
        self.vocab = {w: i for i, w in enumerate(words)}
        self.docs = docs
        self.mat = np.array([embed(d, self.vocab) for d in docs])   # 文档向量库

    def retrieve(self, query, k=2):
        q = embed(query, self.vocab)
        sims = self.mat @ q                                          # 余弦相似度
        idx = np.argsort(-sims)[:k]
        return [(self.docs[i], round(float(sims[i]), 3)) for i in idx]


if __name__ == "__main__":
    docs = [
        "the cat sat on the mat",
        "dogs are loyal animals",
        "python is a programming language",
        "cats and dogs are common pets",
    ]
    rag = TinyRAG(docs)
    print("词表大小", len(rag.vocab))
    for d, s in rag.retrieve("tell me about cats", k=2):
        print(f"  相似度 {s}: {d}")
