#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把幼儿园教案 Markdown 渲染成单文件 HTML（A4 打印友好 + 屏幕阅读舒适）。

用法：
    python render_html.py 中班_科学_影子从哪里来.md
    python render_html.py 教案.md -o 输出.html

生成的 HTML 不依赖任何外部资源，双击即可打开，也可直接 Ctrl+P 打印或存 PDF。
"""

import argparse
import html
import os
import re
import sys

# ---------- 行内处理 ----------

def inline(text):
    """转义 + 行内加粗 + 【待填】高亮"""
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"【(待填[^】]*)】", r'<span class="todo">【\1】</span>', t)
    return t


def strip_inline(text):
    return text.replace("**", "").strip()


# ---------- 解析 ----------

def parse(md):
    title = None
    meta = []
    sections = []
    cur = None

    for raw in md.splitlines():
        line = raw.rstrip()
        if title is None and line.startswith("# "):
            title = line[2:].strip()
            continue
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            name = re.sub(r"^[一二三四五六七八九十]+\s*、\s*", "", m.group(1)).strip()
            cur = [name, []]
            sections.append(cur)
            continue
        if cur is None:
            if not line.strip():
                continue
            for k, v in re.findall(r"\*\*(.+?)\*\*[：:]\s*([^　]*)", line):
                meta.append((k.strip(), v.strip()))
            continue
        cur[1].append(line)

    return (title or "幼儿园教案"), meta, sections


# ---------- 章节渲染 ----------

def render_goals(lines):
    items = []
    for l in lines:
        m = re.match(r"^\s*(?:\d+[.、]|-|\*)\s*(.*)$", l)
        if m and m.group(1).strip():
            items.append(m.group(1).strip())
    if not items:
        return "<p class=\"muted\">（未填写）</p>"
    lis = "".join(f'<li data-n="{i}">{inline(x)}</li>' for i, x in enumerate(items, 1))
    return f'<ul class="goals">{lis}</ul>'


def render_prep(lines):
    items = []
    for l in lines:
        m = re.match(r"^\s*-\s*(.+?)[：:]\s*(.*)$", l)
        if m:
            items.append((m.group(1).strip(), m.group(2).strip()))
    if not items:
        body = "".join(f"<p>{inline(l)}</p>" for l in lines if l.strip())
        return body or "<p class=\"muted\">（未填写）</p>"
    rows = "".join(
        f'<div class="prep-item"><span class="prep-label">{inline(k)}</span>'
        f'<span class="prep-text">{inline(v)}</span></div>'
        for k, v in items
    )
    return f'<div class="prep">{rows}</div>'


def split_steps(lines):
    """把过程章节拆成环节列表：[(标题, 时间, [(角色, 内容)])]"""
    steps, cur = [], None
    for l in lines:
        if not l.strip():
            continue
        head = re.match(r"^\s*###\s+(.*)$", l) or re.match(r"^\s*\*\*([^*]+)\*\*\s*$", l)
        if head:
            t = head.group(1).strip()
            t = re.sub(r"^[（(][一二三四五六七八九十]+[）)]\s*", "", t)
            minutes = ""
            mm = re.search(r"约\s*(\d+)\s*分钟", t)
            if mm:
                minutes = mm.group(1) + " 分钟"
                t = re.sub(r"[　 ]*约\s*\d+\s*分钟\s*", "", t).strip()
            t = re.sub(r"[：:]", "　·　", t).strip("　 ")
            cur = [t, minutes, []]
            steps.append(cur)
            continue
        m = re.match(r"^\s*-\s*(老师|孩子|材料|收尾|导入|展开|结束)[：:]\s*(.*)$", l)
        if m and cur:
            cur[2].append((m.group(1), m.group(2).strip()))
        elif cur:
            cur[2].append(("补充", re.sub(r"^\s*-\s*", "", l).strip()))
    return steps


ROLE_CLASS = {
    "老师": "teacher", "孩子": "child", "材料": "material",
    "收尾": "wrap", "导入": "open", "展开": "body", "结束": "close", "补充": "extra",
}


def render_steps(lines):
    steps = split_steps(lines)
    if not steps:
        return "<p class=\"muted\">（未填写）</p>"
    out = ['<div class="steps">']
    idx = 0
    for t, minutes, rows in steps:
        if not rows:
            # 只有分组作用、自身没有具体动作的标题（如“展开”）
            out.append(f'<div class="group-title">{inline(t)}</div>')
            continue
        idx += 1
        badge = f'<span class="mins">约 {minutes}</span>' if minutes else ""
        body = "".join(
            f'<div class="row role-{ROLE_CLASS.get(role, "extra")}"><span class="role">{role}</span>'
            f'<span class="txt">{inline(txt)}</span></div>'
            for role, txt in rows
        )
        out.append(
            f'<div class="step"><div class="step-head"><span class="idx">{idx}</span>'
            f'<span class="step-title">{inline(t)}</span>{badge}</div>{body}</div>'
        )
    out.append("</div>")
    return "".join(out)


def render_table(lines):
    rows = [l.strip() for l in lines if l.strip().startswith("|")]
    if not rows:
        return "".join(f"<p>{inline(l)}</p>" for l in lines if l.strip()) or "<p class=\"muted\">（未填写）</p>"
    data = []
    for r in rows:
        cells = [c.strip() for c in r.strip("|").split("|")]
        if all(re.match(r"^[-: ]*$", c) for c in cells):
            continue
        data.append(cells)
    if not data:
        return "<p class=\"muted\">（未填写）</p>"
    head, body = data[0], data[1:]
    th = "".join(f"<th>{inline(c)}</th>" for c in head)
    trs = "".join(
        "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>"
        for row in body
    )
    return f'<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'


def render_list(lines):
    items = []
    for l in lines:
        m = re.match(r"^\s*(?:\d+[.、]|-|\*)\s*(.*)$", l)
        if m and m.group(1).strip():
            items.append(m.group(1).strip())
    if not items:
        return "".join(f"<p>{inline(l)}</p>" for l in lines if l.strip()) or "<p class=\"muted\">（未填写）</p>"
    return "<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>"


def render_paragraphs(lines, cls=""):
    body = "".join(
        f"<p>{inline(re.sub(r'^\s*-\s*', '', l))}</p>" for l in lines if l.strip()
    )
    return f'<div class="{cls}">{body}</div>' if cls else (body or "<p class=\"muted\">（未填写）</p>")


def render_section(name, lines):
    if "目标" in name:
        return render_goals(lines)
    if "准备" in name:
        return render_prep(lines)
    if "过程" in name:
        return render_steps(lines)
    if "反应" in name or "应对" in name:
        return render_table(lines)
    if "延伸" in name:
        return render_list(lines)
    if "安全" in name:
        return render_paragraphs(lines, "safety")
    if "反思" in name:
        inner = render_list(lines)
        lines_html = '<div class="write-lines">' + "<div></div>" * 3 + "</div>"
        return inner + lines_html
    return render_paragraphs(lines)


# ---------- 整页模板 ----------

CSS = """
:root{
  --ink:#1f2328; --muted:#6b7480; --line:#d9dfe5; --paper:#ffffff;
  --brand:#9B1C2C; --brand-soft:#f7ecec; --warm:#FAF6EE; --todo:#fff3c4;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:#eef1f5; color:var(--ink);
  font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC","Source Han Sans SC",sans-serif;
  font-size:16px; line-height:1.75; -webkit-font-smoothing:antialiased;
}
.toolbar{max-width:210mm;margin:18px auto 0;text-align:right}
.toolbar button{
  font:inherit;font-size:14px;padding:8px 18px;border-radius:6px;border:1px solid var(--line);
  background:#fff;color:var(--ink);cursor:pointer
}
.toolbar button:hover{border-color:var(--brand);color:var(--brand)}
.sheet{
  max-width:210mm;margin:14px auto 40px;background:var(--paper);
  padding:16mm 15mm 18mm;box-shadow:0 6px 24px rgba(20,30,45,.10);border-radius:2px;
}
.eyebrow{font-size:12.5px;letter-spacing:.18em;color:var(--muted);margin-bottom:6px}
h1{font-size:27px;line-height:1.35;margin:0 0 10px;padding-bottom:10px;border-bottom:2px solid var(--brand)}
.meta{display:flex;flex-wrap:wrap;gap:9px 24px;margin:0 0 4px;padding:0;font-size:14.5px;color:var(--ink)}
.meta span{display:inline-flex;align-items:baseline}
.meta span strong{color:var(--muted);font-weight:500;margin-right:7px;flex:0 0 auto}
section{margin-top:24px}
h2{font-size:17.5px;margin:0 0 12px;display:flex;align-items:center;gap:9px}
h2::before{content:"";width:4px;height:16px;background:var(--brand);border-radius:2px;display:inline-block}
ul{margin:0;padding-left:0;list-style:none}
ul:not(.goals) li{position:relative;padding-left:17px;margin:5px 0}
ul:not(.goals) li::before{
  content:"";position:absolute;left:2px;top:11px;width:5px;height:5px;border-radius:50%;background:#b6bec8
}
.goals li{position:relative;padding:9px 12px 9px 40px;margin-bottom:8px;background:var(--warm);border-left:3px solid #e2d6bd;border-radius:4px}
.goals li::before{
  content:attr(data-n);position:absolute;left:12px;top:9px;width:19px;height:19px;border-radius:50%;
  background:var(--brand);color:#fff;font-size:12.5px;line-height:19px;text-align:center
}
.prep-item{display:flex;gap:10px;padding:8px 0;border-bottom:1px dashed var(--line)}
.prep-item:last-child{border-bottom:0}
.prep-label{flex:0 0 4.6em;color:var(--muted);font-size:14.5px}
.prep-text{flex:1}
.steps{display:flex;flex-direction:column;gap:12px}
.step{border:1px solid var(--line);border-radius:6px;padding:12px 14px;break-inside:avoid;page-break-inside:avoid}
.step-head{display:flex;align-items:center;gap:9px;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid #edf0f4}
.idx{flex:0 0 auto;width:22px;height:22px;border-radius:50%;background:var(--brand);color:#fff;font-size:13px;line-height:22px;text-align:center}
.step-title{font-weight:700;font-size:16.5px}
.mins{margin-left:auto;font-size:13.5px;color:var(--brand);background:var(--brand-soft);padding:2px 9px;border-radius:11px;white-space:nowrap}
.row{display:flex;gap:10px;margin:5px 0}
.role{flex:0 0 3.6em;font-size:13.5px;color:var(--muted);padding-top:2px}
.role-teacher .role{color:#8a5a12}
.role-child .role{color:#1d6b52}
.role-material .role{color:#345573}
.txt{flex:1}
.group-title{display:flex;align-items:center;gap:12px;font-size:13.5px;color:var(--muted);letter-spacing:.06em;margin:8px 0 0}
.group-title::before,.group-title::after{content:"";flex:1;height:1px;background:var(--line)}
table{width:100%;border-collapse:collapse;font-size:15px;break-inside:avoid;page-break-inside:avoid}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th:first-child,td:first-child{width:36%}
th{background:#f3f5f8;font-weight:600}
tbody tr:nth-child(even){background:#fbfbfc}
.safety{background:#fff8e6;border-left:3px solid #e0a638;border-radius:4px;padding:10px 14px}
.safety p{margin:4px 0}
.write-lines{margin-top:10px}
.write-lines div{border-bottom:1px dashed #c9d0d8;height:30px}
.muted{color:var(--muted)}
.todo{background:var(--todo);border-radius:3px;padding:0 2px}
footer{margin-top:26px;padding-top:10px;border-top:1px solid var(--line);font-size:12.5px;color:var(--muted);display:flex;justify-content:space-between}
@media print{
  @page{size:A4;margin:12mm 12mm 12mm}
  body{background:#fff;font-size:14.5px;line-height:1.62}
  .toolbar{display:none}
  .sheet{box-shadow:none;margin:0;padding:0;max-width:none}
  .eyebrow{font-size:11px;margin-bottom:3px}
  h1{font-size:22px;margin-bottom:7px;padding-bottom:7px}
  .meta{font-size:13px;gap:5px 16px}
  section{margin-top:13px}
  h2{font-size:16px;margin-bottom:7px}
  .goals li{padding:6px 11px 6px 36px;margin-bottom:5px}
  .prep-item{padding:5px 0}
  .steps{gap:7px}
  .step{padding:8px 11px}
  .step-head{margin-bottom:5px;padding-bottom:5px}
  .row{margin:2px 0}
  table{font-size:13.5px}
  th,td{padding:5px 8px}
  .safety{padding:8px 12px}
  .write-lines div{height:22px}
  footer{margin-top:14px;padding-top:7px}
}
@media (max-width:720px){
  .sheet{padding:20px 16px;margin:0;border-radius:0}
  h1{font-size:22px}
  .meta{font-size:13.5px}
  .row{flex-direction:column;gap:2px}
  .role{flex:none;font-size:12.5px}
}
"""


def build_html(title, meta, sections):
    meta_html = "".join(
        f"<span><strong>{html.escape(k)}</strong>{inline(v)}</span>" for k, v in meta
    )
    body = []
    for name, lines in sections:
        body.append(f"<section><h2>{html.escape(name)}</h2>{render_section(name, lines)}</section>")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · 教案</title>
<style>{CSS}</style>
</head>
<body>
<div class="toolbar"><button onclick="window.print()">打印 / 存 PDF</button></div>
<main class="sheet">
  <header>
    <div class="eyebrow">幼儿园集体教学活动教案</div>
    <h1>{html.escape(title)}</h1>
    <div class="meta">{meta_html}</div>
  </header>
  {''.join(body)}
  <footer>
    <span>幼儿园教案工作台</span>
    <span>打印建议：A4 纵向，页边距选"默认"</span>
  </footer>
</main>
</body>
</html>
"""


# ---------- CLI ----------

def render_markdown(md_text):
    title, meta, sections = parse(md_text)
    return build_html(title, meta, sections)


def main():
    ap = argparse.ArgumentParser(description="把教案 Markdown 渲染为单文件 HTML")
    ap.add_argument("path", help="教案 Markdown 文件")
    ap.add_argument("-o", "--out", default=None, help="输出 HTML 路径（默认同名 .html）")
    args = ap.parse_args()

    try:
        with open(args.path, "r", encoding="utf-8") as f:
            md = f.read()
    except Exception as e:
        print(f"[错误] 无法读取：{e}", file=sys.stderr)
        return 2

    doc = render_markdown(md)
    out = args.out or os.path.splitext(args.path)[0] + ".html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"[完成] 已生成 HTML：{out}")
    print(f"[提示] 双击打开即可阅读，Ctrl+P 可直接打印或存 PDF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
