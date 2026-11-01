#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诗笺 · 每日一诗 静态站生成器

单一数据源：data/poems.json
产出：index.html / poems/<date>.md / README.md

用法：python scripts/build.py
"""
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "poems.json")

CN_NUM = "〇一二三四五六七八九"


def cn_date(iso: str) -> str:
    y, m, d = iso.split("-")
    y_txt = "".join(CN_NUM[int(c)] for c in y)
    m_txt = ("十" + CN_NUM[int(m[1])]) if int(m) >= 10 else CN_NUM[int(m)]
    if int(m) == 10:
        m_txt = "十"
    d_i = int(d)
    if d_i <= 10:
        d_txt = CN_NUM[d_i]
    elif d_i < 20:
        d_txt = "十" + CN_NUM[d_i - 10]
    elif d_i == 20:
        d_txt = "二十"
    elif d_i < 30:
        d_txt = "二十" + CN_NUM[d_i - 20]
    elif d_i == 30:
        d_txt = "三十"
    else:
        d_txt = "三十" + CN_NUM[d_i - 30]
    return f"{y_txt}年{m_txt}月{d_txt}日"


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_poem(p: dict, today: str) -> str:
    is_today = p["date"] == today
    lines = "".join(f'<p class="line">{esc(x)}</p>' for x in p["lines"])
    notes = "".join(f"<li>{esc(x)}</li>" for x in p["note"])
    paras = "".join(f"<p>{esc(x)}</p>" for x in p["appreciation"])
    badge = '<span class="badge">今日</span>' if is_today else ""
    return f"""
    <article class="poem{' is-today' if is_today else ''}" id="d-{p['date']}">
      <header class="poem-head">
        <div class="poem-meta">
          <time datetime="{p['date']}">{cn_date(p['date'])}</time>
          <span class="dot">·</span>
          <span>{esc(p['form'])}</span>
          {badge}
        </div>
        <h2 class="poem-title">{esc(p['title'])}</h2>
        <p class="poem-author">{esc(p['dynasty'])} · {esc(p['author'])}</p>
      </header>

      <div class="verse">{lines}</div>

      <p class="why"><span class="why-tag">为何是这一首</span>{esc(p['why'])}</p>

      <div class="gloss">
        <section>
          <h3>注</h3>
          <ul class="notes">{notes}</ul>
        </section>
        <section>
          <h3>白话</h3>
          <p>{esc(p['translation'])}</p>
        </section>
        <section>
          <h3>赏</h3>
          <div class="prose">{paras}</div>
        </section>
      </div>
    </article>"""


def render_index(site: dict, poems: list) -> str:
    today = site.get("updated") or poems[0]["date"]
    ordered = sorted(poems, key=lambda x: x["date"], reverse=True)
    body = "".join(render_poem(p, today) for p in ordered)
    nav = "".join(
        f'<a href="#d-{p["date"]}"><b>{p["title"]}</b><span>{p["author"]}</span></a>'
        for p in ordered
    )
    return TPL.replace("__TITLE__", esc(site["title"])) \
              .replace("__SUB__", esc(site["subtitle"])) \
              .replace("__COUNT__", str(len(ordered))) \
              .replace("__NAV__", nav) \
              .replace("__BODY__", body) \
              .replace("__YEAR__", today[:4])


def render_md(p: dict) -> str:
    lines = "\n".join("> " + x for x in p["lines"])
    note = "\n".join("- " + x for x in p["note"])
    appr = "\n\n".join(p["appreciation"])
    return f"""# {p['title']}

**{p['dynasty']} · {p['author']}**　｜　{cn_date(p['date'])}　｜　{p['form']}

{lines}

---

### 为何是这一首

{p['why']}

### 注

{note}

### 白话

{p['translation']}

### 赏

{appr}

---

[← 返回诗笺首页](../index.html)
"""


def render_readme(site: dict, poems: list) -> str:
    rows = "\n".join(
        f"| {p['date']} | {p['title']} | {p['dynasty']} · {p['author']} | {p['form']} |"
        for p in sorted(poems, key=lambda x: x["date"], reverse=True)
    )
    return f"""# {site['title']}

{site['subtitle']}

每天一首，专挑课本里没有、却又确实写得好的诗与词。每首配简注、白话与一段赏析。

**在线阅读 →** <https://kinghihido.github.io/daily-poem/>

## 目录

| 日期 | 篇名 | 作者 | 体裁 |
| --- | --- | --- | --- |
{rows}

共 {len(poems)} 首。

## 仓库结构

```
data/poems.json      唯一数据源，新增诗词只改这里
scripts/build.py     由 JSON 生成 index.html、poems/*.md、README.md
index.html           生成的阅读页面（GitHub Pages 入口）
poems/2026-10-31.md  单篇 Markdown 存档
```

## 本地重建

```bash
python scripts/build.py
```

## 选诗标准

1. 不是必背篇目，尽量避开人人熟诵的名篇；
2. 一首诗里至少有一处真正的好：一个好字、一层转折，或一种别人没写过的看法；
3. 篇幅短，适合通勤或睡前读完。
"""


TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ · 每日一诗</title>
<meta name="description" content="__SUB__">
<style>
  :root{
    --paper:#f3eee2;
    --paper-2:#fbf8f0;
    --ink:#221f19;
    --ink-2:#544c3f;
    --ink-3:#8b8172;
    --seal:#a3342a;
    --line:rgba(34,31,25,.13);
    --max:760px;
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{
    margin:0;
    background:
      radial-gradient(1100px 620px at 12% -8%, #fffdf6 0%, rgba(255,253,246,0) 62%),
      radial-gradient(900px 520px at 92% 4%, #f6efe0 0%, rgba(246,239,224,0) 58%),
      var(--paper);
    color:var(--ink);
    font-family:"Songti SC","STSong","SimSun","Noto Serif CJK SC","Source Han Serif SC",serif;
    -webkit-font-smoothing:antialiased;
    line-height:1.9;
  }
  a{color:inherit}
  .wrap{max-width:var(--max);margin:0 auto;padding:0 26px 90px}

  /* 报头 */
  .masthead{padding:66px 0 30px;text-align:center;position:relative}
  .seal{
    display:inline-block;width:52px;height:52px;line-height:52px;
    border:1.5px solid var(--seal);color:var(--seal);
    font-size:26px;letter-spacing:0;border-radius:5px;
    background:rgba(163,52,42,.045);
    margin-bottom:20px;
  }
  h1{
    margin:0;font-size:34px;font-weight:500;letter-spacing:.42em;
    text-indent:.42em;line-height:1.4;
  }
  .sub{
    margin:14px 0 0;color:var(--ink-2);font-size:13.5px;
    letter-spacing:.16em;
  }
  .rule{
    margin:34px auto 0;height:1px;max-width:calc(var(--max) - 52px);
    background:linear-gradient(90deg,transparent,var(--line) 18%,var(--line) 82%,transparent);
    position:relative;
  }
  .rule::after{
    content:"";position:absolute;left:50%;top:-2.5px;width:5px;height:5px;
    margin-left:-2.5px;background:var(--seal);border-radius:50%;opacity:.55;
  }

  /* 篇目导航 */
  .nav{
    display:flex;flex-wrap:wrap;gap:8px;justify-content:center;
    padding:26px 0 8px;
  }
  .nav a{
    display:inline-flex;align-items:baseline;gap:7px;
    padding:5px 13px;border:1px solid var(--line);border-radius:999px;
    text-decoration:none;font-size:12.5px;color:var(--ink-2);
    background:rgba(255,255,255,.34);
    transition:.22s;
  }
  .nav a b{font-weight:500;color:var(--ink)}
  .nav a span{color:var(--ink-3);font-size:11.5px}
  .nav a:hover{border-color:rgba(163,52,42,.42);background:rgba(255,255,255,.7);transform:translateY(-1px)}

  /* 单篇 */
  .poem{
    margin:44px 0 0;padding:44px 0 8px;
    border-top:1px solid var(--line);
  }
  .poem:first-of-type{border-top:none}
  .poem-head{text-align:center}
  .poem-meta{
    font-size:12px;color:var(--ink-3);letter-spacing:.1em;
    display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;
  }
  .poem-meta .dot{opacity:.5}
  .badge{
    color:var(--seal);border:1px solid rgba(163,52,42,.4);
    border-radius:3px;padding:0 6px;font-size:11px;letter-spacing:.14em;
    background:rgba(163,52,42,.05);
  }
  .poem-title{
    margin:16px 0 6px;font-size:27px;font-weight:500;letter-spacing:.18em;
    text-indent:.18em;
  }
  .poem-author{margin:0;color:var(--ink-2);font-size:13px;letter-spacing:.14em}

  .verse{
    margin:34px 0 30px;padding:32px 0;
    border-top:1px solid var(--line);border-bottom:1px solid var(--line);
    text-align:center;
  }
  .verse .line{
    margin:0;font-size:22px;line-height:2.15;letter-spacing:.13em;
    text-indent:.13em;color:#191712;
  }

  .why{
    margin:0 0 30px;padding:14px 18px;
    background:linear-gradient(180deg,rgba(255,255,255,.62),rgba(255,255,255,.3));
    border-left:2px solid rgba(163,52,42,.45);
    border-radius:0 4px 4px 0;
    font-size:13.5px;color:var(--ink-2);line-height:1.85;
  }
  .why-tag{
    display:inline-block;color:var(--seal);font-size:11.5px;letter-spacing:.14em;
    margin-right:10px;border-bottom:1px solid rgba(163,52,42,.3);padding-bottom:1px;
  }

  .gloss{display:grid;gap:26px}
  .gloss h3{
    margin:0 0 10px;font-size:12px;font-weight:500;letter-spacing:.3em;
    color:var(--seal);position:relative;padding-left:16px;
  }
  .gloss h3::before{
    content:"";position:absolute;left:0;top:.62em;width:8px;height:1px;background:var(--seal);opacity:.65;
  }
  .gloss p,.gloss li{font-size:14.5px;color:var(--ink-2);line-height:2.05;margin:0}
  .gloss .prose p+p{margin-top:14px;text-indent:2em}
  .notes{margin:0;padding-left:0;list-style:none}
  .notes li{position:relative;padding-left:14px}
  .notes li::before{
    content:"";position:absolute;left:2px;top:.95em;width:3px;height:3px;
    border-radius:50%;background:var(--ink-3);opacity:.6;
  }

  /* 页脚 */
  footer{
    margin-top:80px;padding-top:26px;border-top:1px solid var(--line);
    text-align:center;color:var(--ink-3);font-size:12px;letter-spacing:.12em;line-height:2.2;
  }
  footer .big{color:var(--ink-2);font-size:13px;letter-spacing:.3em}

  @media (max-width:560px){
    .wrap{padding:0 18px 70px}
    .masthead{padding:46px 0 22px}
    h1{font-size:26px;letter-spacing:.32em;text-indent:.32em}
    .poem-title{font-size:23px}
    .verse .line{font-size:19px;line-height:2.1}
    .poem{padding-top:36px}
  }
</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <div class="seal">诗</div>
    <h1>__TITLE__</h1>
    <p class="sub">__SUB__</p>
    <div class="rule"></div>
  </header>

  <nav class="nav">__NAV__</nav>

  <main>__BODY__</main>

  <footer>
    <div class="big">每 日 一 首 · 共 __COUNT__ 首</div>
    诗不必有名，只要有一句让人停一停。<br>
    __YEAR__ · 由 <a href="https://github.com/kinghihido/daily-poem">daily-poem</a> 自动生成
  </footer>
</div>
</body>
</html>
"""


def main():
    with open(DATA, encoding="utf-8") as f:
        doc = json.load(f)
    site, poems = doc["site"], doc["poems"]

    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(site, poems))

    pdir = os.path.join(ROOT, "poems")
    os.makedirs(pdir, exist_ok=True)
    for p in poems:
        with open(os.path.join(pdir, p["date"] + ".md"), "w", encoding="utf-8") as f:
            f.write(render_md(p))

    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as f:
        f.write(render_readme(site, poems))

    print(f"built: index.html, poems/*.md ({len(poems)}), README.md")


if __name__ == "__main__":
    main()
