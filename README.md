# 幼儿园教案工作台 · kindergarten-lesson-plan-workbench

**给一线老师用的教案工具，不是给会议室看的模板。**

按园所格式生成、评审、归档集体教学活动方案。默认直接产出可打印的 A4 HTML 教案，老师双击就能看、Ctrl+P 就能打。

> A workbench for Chinese kindergarten collective-activity lesson plans: generate, review and archive plans in the school's own format, and deliver print-ready A4 HTML by default.

---

## 先说清一件容易搞错的事

幼儿园的"教案"，是一次集体教学活动的执行方案，它和中小学学科教案、家长亲子活动卡是三种东西。分不清就会生成"看着像教案、老师拿着上不了"的东西。

| | 幼儿园教案（本仓库） | 中小学学科教案 | 家长亲子活动卡 |
|---|---|---|---|
| 单位 | 一次 20—35 分钟活动 | 一节 40—45 分钟课 | 家庭任意时长 |
| 依据 | 《3—6 岁儿童学习与发展指南》五大领域 | 课程标准、教材 | 无 |
| 核心 | 活动过程分环节，老师孩子各做什么 | 知识点讲授与练习 | 陪玩步骤 |
| 验收 | 另一位老师能不能照着上 | 目标是否达成 | 家长能不能带着玩 |

## 三种模式

- **模式 A 单份生成**：一份具体活动的教案，分导入 → 展开 → 结束，展开再拆 2—3 个环节
- **模式 B 批量计划**：周计划、月计划、主题系列活动方案
- **模式 C 评审与入库**：按五维评分表打分、按命名规范入库、支撑月度教研更新

三种模式可以组合：先 B 定框架，再 A 逐份细化，最后 C 评审入库。

## 六条硬性质量规则

违反任意一条即视为不合格，必须重写：

1. **目标必须可观察**——不写"培养……能力""激发……兴趣"这类无法判断的表述
2. **环节必须能照着走**——另一位老师拿到就能上，不依赖"老师自己把握"
3. **材料必须是园里现成的**——不写需要提前一周采购的特殊材料
4. **必须写孩子可能的反应**——至少两条，含应对办法
5. **必须写清材料发放时机**——材料早发一秒，孩子就开始玩，导入就废了
6. **时间必须对得上**——各环节时长相加等于总时长，且符合年龄段注意力上限

## 快速开始

```bash
# 生成教案骨架（默认直接出 HTML）
python scripts/scaffold_plan.py --class 中班 --domain 科学 --theme "影子从哪里来"

# 把 Markdown 教案渲染成 A4 打印友好的单文件 HTML
python scripts/render_html.py 中班_科学_影子从哪里来.md

# 结构校验与空话检测（.md 与 .html 都支持）
python scripts/check_lesson_plan.py 中班_科学_影子从哪里来.html

# 冒烟测试（六个用例）
python scripts/selftest.py
```

校验项：七段是否齐全、目标是否含可观察动词、是否写了孩子反应预判、是否含风险材料但缺安全提示、是否出现空话套话。有告警就改，改完再交付。

## 脚本

| 脚本 | 作用 |
|---|---|
| `scripts/scaffold_plan.py` | 按班级/领域/主题生成教案骨架（默认出 HTML） |
| `scripts/render_html.py` | Markdown → A4 打印友好、屏幕可读的单文件 HTML |
| `scripts/check_lesson_plan.py` | 结构校验与空话检测 |
| `scripts/selftest.py` | 六个用例的冒烟测试 |

## 参考文档

| 文件 | 内容 |
|---|---|
| `references/lesson-plan-template.md` | 七段模板、每段填写标准、正反例 |
| `references/domain-age-matrix.md` | 五大领域 × 四个年龄段的目标侧重、时长、材料与安全约束 |
| `references/activity-seeds.md` | 40 个园所向活动种子（可直接选用或改造） |
| `references/review-rubric.md` | 优秀教案评审表与打分口径（五维，每维 1—5 分） |
| `references/library-ops.md` | 命名规范、目录结构、元信息头、月更新流程、署名与版权 |

## 评审口径

| 维度 | 通过线 |
|---|---|
| 目标可测 | ≥4 |
| 环节可操作 | ≥4 |
| 材料可得 | ≥4 |
| 孩子反应预判 | ≥3 |
| 反思有抓手 | ≥3 |

输出是**分数表 + 三条改进建议**，按分数最低的三维各给一条，必须具体到"改哪一句"。禁止只给总分——教学主任要的是"哪里要改"，不是排名。

## 边界与红线

- **不编园所信息**：园名、班额、教师姓名、场地条件一律用占位符或向用户确认，不自造
- **不碰幼儿个人信息**：教案里不出现具体幼儿姓名、照片、家庭情况
- **不做教研管理机制设计**：可以给入库规范建议，但不承诺"帮你把教研制度建起来"
- **不替代听课评果**：评审针对教案文本，不对教师现场表现下判断
- **不生成中小学学科教案**：需要课标、45 分钟课时、分层作业、板书时，本 skill 不适用

## 安装

```bash
skillhub install kindergarten-lesson-plan-workbench --namespace user_9462735f

# 或用 Git
git clone https://github.com/madiWeb3Ca/kindergarten-lesson-plan-workbench.git
```

## License

MIT © 2026 马迪 (madiWeb3Ca)
