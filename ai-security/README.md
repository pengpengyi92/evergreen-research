# ai-security — P-Research AI 安全专题

> 栏目定位：用研究基础设施的方式做 AI 安全研究——攻击面、防御体系、
> 评测基准、事件编年史，全部档案化、可检索、可持续生长。

## 为什么在 P-Research 里做

AI 安全是我们语料的天然支柱之一（RL / Alignment / Safety，84 篇；
Safety/Jailbreak 方法族 43 篇且 2026 年半年已超往年全年）。这个栏目
让"安全"从语料里的一个标签，变成一个可持续研究的知识库——
与 dsh-quant 的 quant-history 同构：**档案化 + 可读化 + 可追踪**。

## 栏目框架（四个面）

```
攻击面 ATTACKS      —— 对手怎么打进来
防御体系 DEFENSES   —— 我们怎么守
评测基准 BENCHMARKS —— 怎么量安全
事件编年史 INCIDENTS —— 历史上发生了什么
```

加上开栏第一篇 **LANDSCAPE**：从我们 574 篇语料看 AI 安全研究的现状。

## 收录标准（对齐 quant-history 的 DD_STANDARD）

1. 每个档案统一结构：定位 → 分类/时间线 → 代表工作 → 对我们的意义
2. **事实与数字标注"待考证"**——安全领域谣言多，宁缺毋编
3. 与语料联动：能用 `papers.jsonl` 支撑的观察，必须给数字
4. 安全相关的"人文事实"优先沉淀成 fun facts（dsh-quant）

## 档案清单

| 文件 | 内容 | 状态 |
|------|------|------|
| [LANDSCAPE.md](./LANDSCAPE.md) | 语料视角的 AI 安全现状（43 篇方法族数据） | ✅ |
| [ATTACKS.md](./ATTACKS.md) | 攻击面地图（含 agent 时代新攻击面） | ✅ |
| [DEFENSES.md](./DEFENSES.md) | 防御体系（对齐/红队/护栏/纵深防御） | ✅ |
| [BENCHMARKS.md](./BENCHMARKS.md) | 安全评测基准清单 | ✅ |
| [INCIDENTS.md](./INCIDENTS.md) | 重大安全事件编年史 | ✅ |
| （队列） | 关键研究组档案 · 开源安全工具清单 · 法规地图 | 📋 |

## 读取方式

```bash
python3 -m presearch.cli security            # 栏目索引
python3 -m presearch.cli security attacks    # 单个档案
```

## 栏目哲学

> 安全不是模型的附加属性，是系统的工程属性。
> 我们研究 agent 工程（agentic engineering），而 agent 工程的另一半
> 就是安全工程——这个栏目是我们的三条研究线里最严肃的那一条。
