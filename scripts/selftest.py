#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""六个用例的冒烟测试：验证 scaffold、render_html 与 check 三个脚本的行为符合规范。

用法：python selftest.py
退出码：0 = 全部通过；1 = 有用例失败。
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCAFFOLD = os.path.join(HERE, "scaffold_plan.py")
CHECK = os.path.join(HERE, "check_lesson_plan.py")
RENDER = os.path.join(HERE, "render_html.py")

GOOD = """# 影子从哪里来

**班级**：中班　**人数**：24　**领域**：科学　**时长**：22 分钟

## 一、活动目标

1. 能在手电筒照射时说出影子在物体的哪一侧
2. 能用 2 种方法让同一个玩具的影子变大或变小
3. 愿意把自己的发现讲给同伴听

## 二、活动准备

- 材料：手电筒 6 支（每组 1 支）、白色卡纸 6 张、小动物玩具 6 个
- 环境：活动室拉一半窗帘，每组一块背光墙面
- 经验准备：此前玩过踩影子游戏

## 三、活动过程

### （一）导入　约 4 分钟

- 老师：用手电筒照墙，问"墙上这个东西是什么？从哪里来的？"
- 孩子：观察、猜测、说出影子
- 材料：此时不发玩具和卡纸

### （二）展开

**环节 1　约 8 分钟**

- 老师：每组发 1 个玩具、1 支手电筒，提问影子在哪边
- 孩子：两人一组，一人照一人看
- 材料：先放玩具，再发手电筒

**环节 2　约 6 分钟**

- 老师：提挑战"不换玩具，能让影子变大吗"
- 孩子：尝试靠近或远离光源，描下影子轮廓
- 材料：卡纸和马克笔此时发

### （三）结束　约 4 分钟

- 老师：请 3 组展示影子图，问"怎么把它变大的"
- 孩子：说出"手电筒离得远或者近"
- 材料：不再发放新材料

## 四、孩子可能的反应与应对

| 可能发生的情况 | 应对 |
|---|---|
| 孩子拿手电筒互相照眼睛 | 发前约定只照墙和桌子，照到人立即收回 |
| 有孩子说不会 | 给一个描了一半的轮廓让他接着描 |

## 五、活动延伸

- 区域内：科学区投放手电筒和积木，玩影子剧场
- 家园：请家长晚上和孩子在灯下玩手影
- 下次衔接：大班影子为什么会变长

## 六、安全提示

- 手电筒不得直射眼睛，中班需老师全程提醒；不使用激光笔

## 七、活动反思（上完之后填）

- 环节 2 超时 3 分钟，下次把卡纸换成更大尺寸
"""

BAD = """# 小班手工活动

**班级**：小班　**时长**：30 分钟

## 一、活动目标

1. 培养幼儿的动手能力和审美情趣

## 二、活动准备

- 材料：剪刀若干、彩纸若干

## 三、活动过程

- 老师：带领幼儿做手工
- 孩子：跟着做

## 四、孩子可能的反应与应对

| 可能发生的情况 | 应对 |
|---|---|
| 孩子不会做 | 及时引导 |

## 五、活动延伸

- 回家和家长一起复习
"""


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def case(name, cond, detail=""):
    if cond:
        print(f"[通过] {name}")
        return True
    print(f"[失败] {name}　{detail}")
    return False


def main():
    results = []
    tmp = tempfile.mkdtemp(prefix="klp_selftest_")

    # 用例 1：合格教案应通过校验
    good_path = os.path.join(tmp, "good.md")
    with open(good_path, "w", encoding="utf-8") as f:
        f.write(GOOD)
    r = run([sys.executable, CHECK, good_path])
    results.append(case("1 合格教案通过校验", r.returncode == 0 and "[通过]" in r.stdout,
                        r.stdout[-200:]))

    # 用例 2：缺安全提示、目标空话的教案应判为不通过
    bad_path = os.path.join(tmp, "bad.md")
    with open(bad_path, "w", encoding="utf-8") as f:
        f.write(BAD)
    r = run([sys.executable, CHECK, bad_path])
    results.append(case("2 缺陷教案被拦截", r.returncode == 1 and "[错误]" in r.stdout,
                        r.stdout[-200:]))

    # 用例 3：正常生成骨架（默认 HTML），七段齐全且能被校验脚本读取
    out = os.path.join(tmp, "中班_科学_影子从哪里来.html")
    r = run([sys.executable, SCAFFOLD, "--class", "中班", "--domain", "科学",
             "--title", "影子从哪里来", "--out", out])
    ok = r.returncode == 0 and os.path.exists(out)
    if ok:
        with open(out, "r", encoding="utf-8") as f:
            content = f.read()
        sections = ["活动目标", "活动准备", "活动过程", "孩子可能的反应", "活动延伸",
                    "安全提示", "活动反思"]
        ok = all(s in content for s in sections)
        r = run([sys.executable, CHECK, out])
        ok = ok and r.returncode != 2
    results.append(case("3 骨架生成且七段齐全", ok, r.stderr[:200]))

    # 用例 4：超年龄段时长应被拒绝
    r = run([sys.executable, SCAFFOLD, "--class", "小班", "--domain", "艺术",
             "--title", "手指点画", "--minutes", "40", "--out",
             os.path.join(tmp, "overflow.html")])
    results.append(case("4 超时长被拒绝", r.returncode == 2, r.stderr[:200]))

    # 用例 5：缺必填参数应报错退出
    r = run([sys.executable, SCAFFOLD, "--domain", "科学", "--title", "缺班级"])
    results.append(case("5 缺班级参数报错", r.returncode != 0, r.stderr[:200]))

    # 用例 6：缺陷教案转成 HTML 后仍必须被拦截（HTML 路径不能空转）
    html_path = os.path.join(tmp, "bad.html")
    r = run([sys.executable, RENDER, bad_path, "-o", html_path])
    ok = r.returncode == 0 and os.path.exists(html_path)
    if ok:
        r = run([sys.executable, CHECK, html_path])
        ok = r.returncode == 1 and "[错误]" in r.stdout
    results.append(case("6 HTML 缺陷件同样被拦截", ok, r.stdout[-200:] if r.stdout else r.stderr[:200]))

    print(f"\n=== {sum(results)}/6 用例通过 ===")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
