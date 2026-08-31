# -*- coding: utf-8 -*-
"""3.1 Tokenizer / BPE —— 从零实现字节级 BPE（Byte Pair Encoding）。

BPE 从字节开始，反复把「出现最频繁的相邻对」合并成新符号，
逐步把常见片段压成单个 token。GPT 系列用的正是字节级 BPE。
"""
from collections import Counter


def get_stats(ids):
    """统计相邻对的出现次数。"""
    c = Counter()
    for pair in zip(ids, ids[1:]):
        c[pair] += 1
    return c


def merge(ids, pair, idx):
    """把序列中所有 pair 替换成新符号 idx。"""
    out, i = [], 0
    while i < len(ids):
        if i < len(ids) - 1 and ids[i] == pair[0] and ids[i + 1] == pair[1]:
            out.append(idx); i += 2
        else:
            out.append(ids[i]); i += 1
    return out


class BPETokenizer:
    def __init__(self):
        self.merges = {}          # (a,b) -> new_id

    def train(self, text, vocab_size):
        ids = list(text.encode("utf-8"))
        for k in range(vocab_size - 256):
            stats = get_stats(ids)
            if not stats:
                break
            pair = max(stats, key=stats.get)      # 最频繁的相邻对
            idx = 256 + k
            ids = merge(ids, pair, idx)
            self.merges[pair] = idx
        return ids

    def encode(self, text):
        ids = list(text.encode("utf-8"))
        while len(ids) >= 2:
            stats = get_stats(ids)
            # 按合并的先后顺序（idx 越小越先学到）优先合并
            pair = min(stats, key=lambda p: self.merges.get(p, float("inf")))
            if pair not in self.merges:
                break
            ids = merge(ids, pair, self.merges[pair])
        return ids

    def decode(self, ids):
        vocab = {i: bytes([i]) for i in range(256)}
        for (a, b), idx in self.merges.items():
            vocab[idx] = vocab[a] + vocab[b]
        return b"".join(vocab[i] for i in ids).decode("utf-8", errors="replace")


if __name__ == "__main__":
    text = "the cat sat on the mat, the cat ran. " * 20
    tok = BPETokenizer()
    tok.train(text, vocab_size=300)
    ids = tok.encode("the cat")
    print("原始字节数", len(text.encode("utf-8")), " 学到的合并数", len(tok.merges))
    print("'the cat' 编码为", len(ids), "个 token:", ids)
    print("往返解码:", repr(tok.decode(ids)))
