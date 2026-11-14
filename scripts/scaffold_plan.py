#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按园所格式生成幼儿园教案骨架（七段结构），保证格式统一。

用法：
    python scaffold_plan.py --class 中班 --domain 科学 --title "影子从哪里来" --out ./中班_科学_影子从哪里来.html
    python scaffold_plan.py --class 小班 --domain 艺术 --title "手指点画" --minutes 18
    python scaffold_plan.py --class 大班 --domain 社会 --title "逛超市" --format md

默认输出 HTML（老师直接阅读与打印）；需要纯文本底稿时用 --format md。
只生成骨架与填写提示，具体内容由使用者或 AI 按 references/lesson-plan-template.md 填充。
"""

import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_html import render_markdown  # noqa: E402

CLASSES = ["小班", "中班", "大班", "幼小衔接"]
DOMAINS = ["健康", "语言", "社会", "科学", "艺术"]

# 默认时长与环节数（依据 3-6 岁儿童注意力上限）
DEFAULT_MINUTES = {"小班": 18, "中班": 22, "大班": 28, "幼小衔接": 32}
MAX_MINUTES = {"小班": 20, "中班": 25, "大班": 30, "幼小衔接": 35}
SEGMENTS = {"小班": 1, "中班": 2, "大班": 3, "幼小衔接": 3}

TEMPLATE = """# {title}

**班级**：{klass}　　**人数**：{people}　　**领域**：{domain}　　**时长**：{minutes} 分钟
**设计者**：{author}　　**日期**：{date}　　**是否实际上过**：否

## 一、活动目标

1. （认知/技能）【待填：能在什么情况下，做到什么可观察的动作】
2. （操作/表达）【待填：能完成什么具体操作或表达】
3. （情感/意愿）【待填：愿意做什么，可观察】

## 二、活动准备

- 材料：【待填：名称 + 数量，园内现成可得】
- 环境：【待填：座位、场地、光线/背景】
- 经验准备：【待填：此前孩子已具备的相关经验】

## 三、活动过程

### （一）导入　约 {t_intro} 分钟

- 老师：【待填：动作 + 一句可直接照读的提问】
- 孩子：【待填：观察、猜测、回应】
- 材料：此时【待填：不发 / 发什么】

### （二）展开

{segments}

### （三）结束　约 {t_end} 分钟

- 老师：【待填：请谁分享、问什么】
- 孩子：【待填：说出发现 / 展示作品】
- 收尾：【待填：作品放哪、约定什么】

## 四、孩子可能的反应与应对

| 可能发生的情况 | 应对 |
|---|---|
| 【待填：情况一】 | 【待填：具体动作，不写"及时引导"】 |
| 【待填：情况二】 | 【待填：具体动作】 |

## 五、活动延伸

- 区域内：【待填：投放什么材料，玩什么】
- 家园：【待填：家长和孩子在家做什么具体的事】
- 下次衔接：【待填：下一次活动接什么】

## 六、安全提示

【待填：材料或场地风险 + 适用年龄限制；确认无风险时写"无特殊风险"】

## 七、活动反思（上完之后填）

- 哪个环节超时／提前结束？为什么？
- 哪条目标没达成？卡在哪？
- 下次改哪一句、换哪个材料？
"""

SEGMENT_TEMPLATE = """**环节 {i}　约 {t} 分钟**

- 老师：【待填：提什么要求、巡场时提示什么】
- 孩子：【待填：操作、尝试、记录】
- 材料：【待填：什么时候发、发多少】
"""


def build_segments(klass, minutes):
    count = SEGMENTS[klass]
    intro, end = 4, 4
    body = max(minutes - intro - end, 5)
    per = body // count
    blocks = []
    for i in range(1, count + 1):
        blocks.append(SEGMENT_TEMPLATE.format(i=i, t=per))
    return "\n".join(blocks), intro, end


def main():
    parser = argparse.ArgumentParser(description="生成幼儿园教案骨架")
    parser.add_argument("--class", dest="klass", required=True, choices=CLASSES, help="班级")
    parser.add_argument("--domain", required=True, choices=DOMAINS, help="领域")
    parser.add_argument("--title", required=True, help="活动名称")
    parser.add_argument("--minutes", type=int, default=None, help="总时长（分钟），默认按班级")
    parser.add_argument("--people", default="【待填】", help="人数")
    parser.add_argument("--author", default="【待填】", help="设计者")
    parser.add_argument("--out", default=None, help="输出路径（默认 班级_领域_活动名称.html）")
    parser.add_argument("--format", choices=["html", "md"], default="html",
                        help="输出格式：html（默认，老师直接看）或 md（纯文本底稿）")
    args = parser.parse_args()

    minutes = args.minutes or DEFAULT_MINUTES[args.klass]
    if minutes > MAX_MINUTES[args.klass]:
        print(f"[错误] {args.klass} 活动时长不宜超过 {MAX_MINUTES[args.klass]} 分钟（注意力上限）",
              file=sys.stderr)
        return 2
    if minutes < 10:
        print("[错误] 活动时长不足 10 分钟，无法容纳导入与结束环节", file=sys.stderr)
        return 2

    segments, intro, end = build_segments(args.klass, minutes)
    content = TEMPLATE.format(
        title=args.title.strip(),
        klass=args.klass,
        people=args.people,
        domain=args.domain,
        minutes=minutes,
        author=args.author,
        date=datetime.date.today().isoformat(),
        t_intro=intro,
        t_end=end,
        segments=segments,
    )

    ext = ".html" if args.format == "html" else ".md"
    base = args.out or f"{args.klass}_{args.domain}_{args.title.strip()}"
    root, given = os.path.splitext(base)
    if given.lower() in (".md", ".html"):
        base = root
    out = base + ext

    out_dir = os.path.dirname(os.path.abspath(out))
    os.makedirs(out_dir, exist_ok=True)
    payload = render_markdown(content) if args.format == "html" else content
    with open(out, "w", encoding="utf-8") as f:
        f.write(payload)

    print(f"[完成] 已生成教案骨架：{out}")
    print(f"[提示] {args.klass} 建议 {DEFAULT_MINUTES[args.klass]} 分钟，本次 {minutes} 分钟；"
          f"展开环节 {SEGMENTS[args.klass]} 个，每节约 {(minutes - intro - end) // SEGMENTS[args.klass]} 分钟")
    if args.format == "html":
        print("[提示] HTML 可直接双击阅读、Ctrl+P 打印或存 PDF；黄色高亮为【待填】处")
    print("[下一步] 按 references/lesson-plan-template.md 填充内容，再跑 check_lesson_plan.py 自检")
    return 0


if __name__ == "__main__":
    sys.exit(main())
