#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EnglishPod 每日单词推送脚本
- 从 index.html 解析所有课时（倒序）
- 用 progress.json 记录推送进度，每天递进一期
- 通过 Server酱（方糖）推送到微信
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML = os.path.join(SCRIPT_DIR, "index.html")
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "progress.json")
PAGES_URL = "https://jasmine525525.github.io/englishpod-words/"


def parse_episodes():
    """用正则从 index.html 解析所有 episode 及其词条"""
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    episodes = []
    # 匹配每个 <section id="epXXX" class="episode"> ... </section>
    # 用非贪婪匹配，到下一个 section 或文件末尾
    section_re = re.compile(
        r'<section\s+id="([^"]+)"\s+class="episode">(.*?)</section>',
        re.DOTALL,
    )

    for m in section_re.finditer(html):
        ep_id = m.group(1)
        body = m.group(2)

        # 标题：<h2 ...>EP222 Carbon Footprint <span class="count">11</span></h2>
        title_m = re.search(r"<h2[^>]*>(.*?)</h2>", body, re.DOTALL)
        raw_title = title_m.group(1) if title_m else ""
        # 去掉 <span> 标签和多余空白
        title = re.sub(r"<[^>]+>", "", raw_title)
        title = re.sub(r"\s+", " ", title).strip()
        # 分离出期号、主题、词数
        title_parts = title.rsplit(" ", 1)
        ep_title = title_parts[0] if len(title_parts) == 2 else title
        word_count = int(title_parts[1]) if len(title_parts) == 2 and title_parts[1].isdigit() else 0

        # 词条：<div class="entry">...</div> 之间用 <div class="entry"> 分隔
        entries = []
        # 找出所有 entry 的起始位置
        entry_starts = [m.start() for m in re.finditer(r'<div class="entry">', body)]
        for i, start in enumerate(entry_starts):
            end = entry_starts[i + 1] if i + 1 < len(entry_starts) else len(body)
            # 去掉末尾 </div></div>（entries 容器的闭合）
            entry_html = body[start:end]
            # 截到最后一个 </div> 即 entry 自身的闭合
            last_close = entry_html.rfind("</div>")
            if last_close > 0:
                entry_html = entry_html[:last_close]

            word_m = re.search(r"<strong>(.*?)</strong>", entry_html, re.DOTALL)
            word = word_m.group(1).strip() if word_m else ""

            ipa_m = re.search(r'<div class="ipa">(.*?)</div>', entry_html, re.DOTALL)
            ipa_raw = ipa_m.group(1) if ipa_m else ""
            ipa_text = re.sub(r"<[^>]+>", "", ipa_raw)
            ipa_text = re.sub(r"\s+", " ", ipa_text).strip()
            # 分离音标和词性
            ipa_parts = ipa_text.rsplit(" ", 1)
            ipa = ipa_parts[0].strip() if ipa_parts else ""
            pos = ipa_parts[1].strip() if len(ipa_parts) == 2 else ""

            def_m = re.search(r'<div class="def">(.*?)</div>', entry_html, re.DOTALL)
            defn = def_m.group(1).strip() if def_m else ""

            ex_m = re.search(r'<div class="ex">(.*?)</div>', entry_html, re.DOTALL)
            ex_raw = ex_m.group(1) if ex_m else ""
            ex = re.sub(r"<[^>]+>", "", ex_raw)
            ex = ex.replace("原句：", "").replace("原句:", "").strip()
            # 去掉首尾中文全角引号，保留引号内的句子
            ex = ex.strip("\u201c\u201d").strip()
            ex = ex.strip('""').strip()

            entries.append({
                "word": word,
                "ipa": ipa,
                "pos": pos,
                "def": defn,
                "ex": ex,
            })

        episodes.append({
            "id": ep_id,
            "title": ep_title,
            "count": word_count,
            "entries": entries,
        })

    return episodes


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"index": 0, "history": []}


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def format_episode(ep, idx, total):
    """把一期内容格式化为 Markdown（Server酱支持 Markdown）"""
    anchor = ep["id"]
    entries = ep["entries"]

    lines = []
    lines.append(f"## {ep['title']}")
    lines.append("")
    lines.append(f"> 第 {idx + 1} / {total} 期  ·  本期 {len(entries)} 词")
    lines.append("")
    for e in entries:
        word = e.get("word", "")
        ipa = e.get("ipa", "")
        pos = e.get("pos", "")
        defn = e.get("def", "")
        ex = e.get("ex", "")

        header = f"**{word}**"
        if pos:
            header += f"（{pos}）"
        lines.append(header)
        if ipa:
            lines.append(f"- 音标：{ipa}")
        if defn:
            lines.append(f"- 释义：{defn}")
        if ex:
            lines.append(f"- 例句：{ex}")
        lines.append("")

    lines.append("---")
    lines.append(f"[📖 查看完整单词手册]({PAGES_URL}#{anchor})")
    lines.append("")
    lines.append(f"明天继续推送第 {idx + 2}/{total} 期")
    return "\n".join(lines)


def send_serverchan(sendkey, title, desp):
    """调用 Server酱 Turbo 版 API"""
    api_url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = urllib.parse.urlencode({
        "title": title,
        "desp": desp,
    }).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, body
    except Exception as e:
        return -1, str(e)


def main():
    sendkey = os.environ.get("SENDKEY", "").strip()
    if not sendkey:
        print("错误：环境变量 SENDKEY 未设置", file=sys.stderr)
        sys.exit(1)

    episodes = parse_episodes()
    total = len(episodes)
    if total == 0:
        print("错误：未解析到任何课时", file=sys.stderr)
        sys.exit(1)
    print(f"共解析到 {total} 期课时")

    progress = load_progress()
    idx = progress.get("index", 0)
    # 越界则循环回 0
    if idx >= total:
        idx = 0

    ep = episodes[idx]

    # 推送标题：取期号+主题前两个词
    short_title = ep["title"]
    push_title = f"EnglishPod {short_title}"

    desp = format_episode(ep, idx, total)

    print(f"准备推送：{push_title}（第 {idx + 1}/{total} 期）")
    print(f"内容预览（前300字）：\n{desp[:300]}")
    print(f"\n内容总长度：{len(desp)} 字符")

    status, body = send_serverchan(sendkey, push_title, desp)
    print(f"\nServer酱返回：HTTP {status}")
    print(f"响应内容：{body[:500]}")

    # Server酱成功返回 code:0
    try:
        resp_json = json.loads(body)
        success = resp_json.get("code", -1) == 0
    except Exception:
        success = status == 200 and '"code":0' in body

    if success:
        progress["index"] = idx + 1
        progress["history"].append({
            "index": idx,
            "title": ep["title"],
            "pushed": True,
        })
        save_progress(progress)
        print(f"\n✓ 推送成功！进度已更新：下次推送第 {idx + 2}/{total} 期")
    else:
        print("\n✗ 推送失败，进度未更新，下次会重试本期", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
