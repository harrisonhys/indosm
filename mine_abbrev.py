"""Mine an abbreviation dictionary from the SIMRS Khanza DDL (no GT, no external dictionary).

Signals, highest precision first:
  context  identifiers that differ in exactly one token:  nm_pasien ~ nama_pasien      -> nm = nama
  acronym  one token vs. 2-3 tokens whose initials match: jk_pasien ~ jenis_kelamin_pasien -> jk = jenis kelamin
  subseq   fallback: most frequent vocabulary word (columns, tables, enum text) that starts with the
           same letter and contains the token as a subsequence: brng -> barang
Usage: python mine_abbrev.py data/subset_e/raw/sik.sql data/abbrev_khanza.json
"""
import collections
import json
import math
import re
import sys

MIN_SUPPORT = 2  # identifier pairs needed for a context/acronym rule
MAX_ABBR_LEN = 5


def is_subseq(short: str, long: str) -> bool:
    it = iter(long)
    return all(ch in it for ch in short)


def plausible(short: str, long: str) -> bool:
    return len(long) >= len(short) + 2 and short[0] == long[0] and is_subseq(short, long)


def overlap(a: collections.Counter, b: collections.Counter) -> int:
    return sum(min(a[k], b[k]) for k in a.keys() & b.keys())


def vowel_poor(s: str) -> bool:
    """Indonesian abbreviations drop vowels (nm, stts, brng, kab); real words (nama, suku, email) keep them."""
    return sum(ch in "aeiou" for ch in s) / len(s) < 0.34


def compound(w: str, freq: collections.Counter) -> bool:
    """Khanza glues words together (ttlranap, pjpengujian); such tokens are not expansions."""
    return any(freq[w[:i]] and freq[w[i:]] for i in range(2, len(w) - 1))


def vocab(sql: str):
    tables = re.findall(r"CREATE TABLE `(\w+)`", sql)
    cols = re.findall(r"^\s+`(\w+)`\s+[a-z]", sql, re.M)
    words = re.findall(r"[a-z]{3,}", " ".join(re.findall(r"enum\(([^)]*)\)", sql)).lower())
    idents = sorted({c.lower() for c in cols} | {t.lower() for t in tables})
    toks = lambda s: [t for t in re.split(r"[_\d]+", s) if t]
    freq = collections.Counter(t for i in idents for t in toks(i)) + collections.Counter(words)
    split = [toks(i) for i in idents]
    neigh = collections.defaultdict(collections.Counter)  # token -> tokens it shares identifiers with
    for t in split:
        for a in t:
            neigh[a].update(b for b in t if b != a)
    return split, freq, set(words), neigh


def mine(sql: str) -> dict:
    idents, freq, natural, neigh = vocab(sql)
    by_len = collections.defaultdict(set)
    for t in idents:
        by_len[len(t)].add(tuple(t))
    votes = collections.defaultdict(collections.Counter)  # abbr -> Counter(expansion)
    method = {}
    # context: same length, exactly one differing position
    for n, group in by_len.items():
        if n < 2:
            continue
        index = collections.defaultdict(list)
        for t in group:
            for i in range(n):
                index[(i, t[:i] + t[i + 1:])].append(t[i])
        for (i, _), variants in index.items():
            for s in variants:
                for l in variants:
                    if len(s) <= MAX_ABBR_LEN and plausible(s, l):
                        votes[s][l] += 1
                        method[(s, l)] = "context"
    # acronym: one token vs. k consecutive tokens (k=2,3), rest identical
    full = {tuple(t) for t in idents}
    for t in full:
        for i, s in enumerate(t):
            if not 2 <= len(s) <= 3:
                continue
            for k in (2, 3):
                if len(s) != k:
                    continue
                for u in full:
                    if len(u) == len(t) + k - 1 and u[:i] == t[:i] and u[i + k:] == t[i + 1:] \
                            and "".join(w[0] for w in u[i:i + k]) == s and all(len(w) > 2 for w in u[i:i + k]):
                        exp = " ".join(u[i:i + k])
                        votes[s][exp] += 1
                        method[(s, exp)] = "acronym"
    out = {}
    for s, c in votes.items():
        exp, n = c.most_common(1)[0]
        if n >= MIN_SUPPORT and s not in natural:
            out[s] = {"expansion": exp, "support": n, "method": method[(s, exp)]}
    # subseq fallback: rank candidate words by how many neighbouring tokens they share with the abbreviation
    # (rkm sits next to `medis`, so does `rekam`), frequency only breaks ties
    for s, f in freq.items():
        if s in out or s in natural or not 3 <= len(s) <= MAX_ABBR_LEN or not vowel_poor(s):  # 2-letter tokens are acronyms (pj, rs, wp)
            continue
        cands = [(overlap(neigh[s], neigh[w]), math.log(freq[w]), w) for w in freq
                 if plausible(s, w) and not compound(w, freq)]
        if cands:
            *_, w = max(cands)
            out[s] = {"expansion": w, "support": 0, "method": "subseq"}
    return out


if __name__ == "__main__":
    src, dst = sys.argv[1:3]
    d = mine(open(src, encoding="utf-8", errors="replace").read().replace("\r\n", "\n"))
    json.dump(dict(sorted(d.items())), open(dst, "w"), ensure_ascii=False, indent=1)
    print(len(d), "entries:", collections.Counter(v["method"] for v in d.values()))
