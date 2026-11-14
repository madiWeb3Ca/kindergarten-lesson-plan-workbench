#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验幼儿园教案的结构与质量。

支持 .md 与 .html 两种教案文件（HTML 会先转成纯文本再走同一套规则）。

用法：
    python check_lesson_plan.py 中班_科学_影子从哪里来.html
    python check_lesson_plan.py 教案.md --strict   # 警告也按错误处理

退出码：0 = 通过（可含警告）；1 = 有错误（缺段等硬伤）；2 = 文件读取失败。
"""

import argparse
import html as html_mod
import os
import re
import sys

REQUIRED_SECTIONS = [
    ("活动目标", r"^\s*#+\s*.*活动目标"),
    ("活动准备", r"^\s*#+\s*.*活动准备"),
    ("活动过程", r"^\s*#+\s*.*活动过程"),
    ("孩子可能的反应与应对", r"^\s*#+\s*.*(孩子可能的反应|反应与应对)"),
    ("活动延伸", r"^\s*#+\s*.*活动延伸"),
    ("安全提示", r"^\s*#+\s*.*安全提示"),
    ("活动反思", r"^\s*#+\s*.*活动反思"),
]

VAGUE_WORDS = ["培养", "激发", "感受", "体会", "了解", "认识", "初步感知", "体验", "引导幼儿"]
OBSERVABLE = ["能", "会", "愿意", "说出", "做到", "完成", "分辨", "记录", "讲述", "排序",
              "拼", "贴", "画", "跳", "走", "拍", "数", "找出", "按", "讲给"]

RISK_WORDS = ["剪刀", "小珠", "珠子", "豆", "玻璃", "热水", "手电筒", "激光", "绳", "攀爬",
              "户外", "插座", "火", "刀"]
QUANTITY_VAGUE = ["若干", "适量", "一些", "等材料", "少量"]

MAX_MINUTES = {"小班": 20, "中班": 25, "大班": 30, "幼小衔接": 35}


def html_to_text(src):
    """把渲染出的教案 HTML 还原成等效 Markdown 文本，供同一套校验规则使用。

    关键映射：h1/h2/h3 → #/##/###；li → "- "；tr/td → 竖线表格行；
    <span class="role">老师</span> → "老师："（否则「老师/孩子/材料」成对性检测会失效）。
    """
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", src)
    s = re.sub(r'(?is)<span class="role">([^<]+)</span>', r"\1：", s)
    s = re.sub(r"(?is)<h1[^>]*>", "\n\n# ", s)
    s = re.sub(r"(?is)<h2[^>]*>", "\n\n## ", s)
    s = re.sub(r"(?is)<h3[^>]*>", "\n\n### ", s)
    s = re.sub(r"(?is)</h[123]>", "\n", s)
    s = re.sub(r"(?is)<tr[^>]*>", "\n| ", s)
    s = re.sub(r"(?is)</tr>", " |", s)
    s = re.sub(r"(?is)<t[dh][^>]*>", "", s)
    s = re.sub(r"(?is)</t[dh]>", " | ", s)
    s = re.sub(r"(?is)<li[^>]*>", "\n- ", s)
    s = re.sub(r"(?is)</li>", "", s)
    s = re.sub(r"(?is)<br[^>]*>", "\n", s)
    s = re.sub(r"(?is)<(p|div|section|header|footer|main|ul|table|thead|tbody)[^>]*>", "\n", s)
    s = re.sub(r"(?is)</(p|div|section|header|footer|main|ul|table|thead|tbody)>", "\n", s)
    s = re.sub(r"(?is)<[^>]+>", "", s)
    s = html_mod.unescape(s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s


def html_to_text(s):
    """把 HTML 教案压成 markdown 风格纯文本，让同一套校验规则也能检查 HTML。"""
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", s)
    # 角色标签还原成「老师：」，否则过程成对性检查会失效
    s = re.sub(r'(?is)<span class="role">([^<]+)</span>', r"\1：", s)
    s = re.sub(r"(?is)<tr[^>]*>", "\n| ", s)
    s = re.sub(r"(?is)<t[dh][^>]*>", "", s)
    s = re.sub(r"(?is)</t[dh]>", " | ", s)
    s = re.sub(r"(?is)</tr>", "\n", s)
    s = re.sub(r"(?is)<h1[^>]*>", "\n# ", s)
    s = re.sub(r"(?is)<h2[^>]*>", "\n## ", s)
    s = re.sub(r"(?is)<h3[^>]*>", "\n### ", s)
    s = re.sub(r"(?is)<li[^>]*>", "\n- ", s)
    s = re.sub(r"(?is)<br[^>]*>", "\n", s)
    s = re.sub(r"(?is)<(p|div|ul|table|section|tbody|thead|h1|h2|h3)[^>]*>", "\n", s)
    s = re.sub(r"(?is)</(p|div|ul|table|section|tbody|thead|h1|h2|h3|li)>", "\n", s)
    s = re.sub(r"(?is)<[^>]+>", "", s)
    s = html_mod.unescape(s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s


def find_section(text, pattern):
    """返回 (起始行号, 该段正文)；未找到返回 (-1, "")

    段边界只认一级/二级标题：教案过程里用 ### 分环节，若在 ### 处截断，
    过程段的「老师/孩子/材料」检查会整体失效。
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.search(pattern, line):
            body = []
            for j in range(i + 1, len(lines)):
                if re.match(r"^\s*#{1,2}\s", lines[j]):
                    break
                body.append(lines[j])
            return i, "\n".join(body)
    return -1, ""


def detect_class(text):
    m = re.search(r"班级\D{0,4}(小班|中班|大班|幼小衔接)", text)
    if m:
        return m.group(1)
    return None


def main():
    parser = argparse.ArgumentParser(description="校验幼儿园教案")
    parser.add_argument("path", help="教案文件（.md 或 .html）")
    parser.add_argument("--strict", action="store_true", help="警告也按错误处理")
    args = parser.parse_args()

    try:
        with open(args.path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"[错误] 无法读取文件：{e}", file=sys.stderr)
        return 2

    if os.path.splitext(args.path)[1].lower() in (".html", ".htm"):
        text = html_to_text(text)

    errors, warnings = [], []

    # 1. 章节齐全
    bodies = {}
    for name, pattern in REQUIRED_SECTIONS:
        idx, body = find_section(text, pattern)
        if idx < 0:
            errors.append(f"缺少必需段落「{name}」")
        else:
            bodies[name] = body

    # 2. 目标可测
    goals = bodies.get("活动目标", "")
    goal_lines = [l for l in goals.splitlines() if re.match(r"^\s*(\d+[.、]|-|\*)", l)]
    if goal_lines:
        if len(goal_lines) > 4:
            warnings.append(f"目标有 {len(goal_lines)} 条，建议 3 条（一次活动撑不住太多目标）")
        for l in goal_lines:
            has_vague = any(w in l for w in VAGUE_WORDS)
            has_obs = any(w in l for w in OBSERVABLE)
            if has_vague and not has_obs:
                warnings.append(f"目标不可测：「{l.strip()[:40]}」缺少可观察的动作")
        if all(not any(w in l for w in OBSERVABLE) for l in goal_lines):
            errors.append("三条目标均无可观察行为，无法验收")
    elif "活动目标" in bodies:
        warnings.append("目标段没有条目，无法判断可测性")

    # 3. 孩子反应预判
    reacts = bodies.get("孩子可能的反应与应对", "")
    rows = [l for l in reacts.splitlines() if l.strip().startswith("|")]
    rows = [l for l in rows if not re.match(r"^\s*\|[\s\-:|]+\|?\s*$", l)]
    data_rows = max(len(rows) - 1, 0)  # 去掉表头
    if "孩子可能的反应与应对" in bodies and data_rows < 2:
        warnings.append(f"孩子反应预判只有 {data_rows} 条，建议至少 2 条（决定新老师能否上下来）")

    # 4. 材料数量
    prep = bodies.get("活动准备", "")
    if any(w in prep for w in QUANTITY_VAGUE):
        warnings.append("材料写了「若干/适量」等模糊数量，明天备料会不够或不齐")

    # 5. 风险材料必须有安全提示
    has_risk = any(w in text for w in RISK_WORDS)
    if has_risk:
        safe = bodies.get("安全提示", "")
        stripped = re.sub(r"\s", "", safe)
        if "无特殊风险" in stripped or len(stripped) < 8:
            errors.append("出现剪刀/小颗粒/热水/手电筒等风险材料，但安全提示缺失或写「无特殊风险」")

    # 6. 时长核算
    total_m = re.search(r"时长\D{0,4}(\d+)\s*分钟", text)
    seg_m = [int(x) for x in re.findall(r"约\s*(\d+)\s*分钟", text)]
    if total_m and seg_m:
        total = int(total_m.group(1))
        s = sum(seg_m)
        if abs(s - total) > 3:
            warnings.append(f"各环节时长合计 {s} 分钟，与总时长 {total} 分钟相差超过 3 分钟")
        klass = detect_class(text)
        if klass and total > MAX_MINUTES[klass]:
            errors.append(f"{klass}活动 {total} 分钟，超出注意力上限 {MAX_MINUTES[klass]} 分钟")

    # 7. 过程环节完整性
    proc = bodies.get("活动过程", "")
    if proc:
        n_teacher = proc.count("老师：") + proc.count("老师:")
        n_child = proc.count("孩子：") + proc.count("孩子:")
        n_material = proc.count("材料：") + proc.count("材料:")
        if n_teacher == 0 or n_child == 0:
            errors.append("活动过程缺少「老师：」或「孩子：」，另一位老师无法照着上")
        elif n_teacher != n_child:
            warnings.append(f"过程里老师动作 {n_teacher} 处、孩子动作 {n_child} 处，不成对")
        if n_material == 0:
            warnings.append("活动过程未写材料发放时机（材料早发会毁掉导入）")

    # 8. 空话反思
    refl = bodies.get("活动反思", "")
    if refl and ("效果良好" in refl or "达到预期" in refl) and len(re.sub(r"\s", "", refl)) < 40:
        warnings.append("反思写成总结（只写效果好），要写「下次改哪一句」")

    # 汇总输出
    print(f"=== 校验结果：{args.path} ===")
    if errors:
        print(f"\n[错误] {len(errors)} 项（必须修）")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print(f"\n[警告] {len(warnings)} 项（建议修）")
        for w in warnings:
            print(f"  ! {w}")
    if not errors and not warnings:
        print("\n[通过] 结构完整，质量项无告警")
    elif not errors:
        print("\n[通过] 结构完整（有警告，建议修改后再交付）")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
