# AI 客服通话智能质检系统（LangGraph 版本）

将金融客服通话质检流程改造为 LangGraph 模块化图结构，保留原始对话文本、支持知识检索、可循环重打分与人工复核兜底。

## 流程概览

```
输入 → 问题提取 → 知识检索 → 打分循环（≤3 次） ⇄ 审核 → 输出
                                       ↑__________|
                            审核不通过 → 重打分；3 次仍不通过 → 标记人工复核
```

## 目录结构

```
ai-call-quality/
├── src/call_quality/
│   ├── state.py            # LangGraph state 定义
│   ├── graph.py            # 图编排（节点、条件边）
│   ├── schemas.py          # Pydantic 输入输出模型
│   ├── llm.py              # LLM 客户端（DeepSeek / Claude / OpenAI 可切换）
│   ├── kb.py               # 知识库接口（默认本地 JSON）
│   ├── nodes/              # 6 个节点实现
│   └── prompts/            # 提示词模板
├── examples/               # 示例输入与运行脚本
└── tests/                  # 冒烟测试
```

## 核心设计

| 节点 | 输入 | 输出 |
|---|---|---|
| `input_node` | `call_id`, `call_type`, `conversation`, `rules_json` | 透传 |
| `question_extractor` | `conversation` | `questions: [{timestamp, question_text}]` |
| `knowledge_retriever` | `questions` | `qa_pairs: [{..., kb_answer, kb_title}]` |
| `scoring_loop` | 全部上下文 | `deductions`, `fatal_triggers` |
| `auditor` | 打分结果 | `audit_passed: bool` |
| `aggregator` | 最终状态 | 完整质检 JSON |

## 关键业务规则

- **致命项命中** → `final_score = 0`
- **答非所问**（客服回答与 KB 答案语义不符）→ 计入 `rule_id=17` 业务差错
- **`hot_words`**：通话中高频且有信息价值的词
- **`business_words`**：业务差错相关词
- **审核循环**：最多 3 次，超出后 `requires_human_review = true`，**不**默认满分

## 快速开始

```bash
pip install -e .
cp .env.example .env  # 填入 DEEPSEEK_API_KEY 等
python examples/run_example.py
```

## 部署到 LangGraph Platform

```bash
pip install -U langgraph-cli
langgraph dev          # 本地起 LangGraph Studio（浏览器调试）
langgraph build        # 构建 Docker 镜像
langgraph up           # 本地起服务
```

`langgraph.json` 暴露的 graph 名是 `call_quality`，入口是
`./src/call_quality/graph.py:graph`。

## 可视化（LangSmith）

`.env` 里填 `LANGCHAIN_API_KEY` 后，每次运行图都会上传 trace 到
https://smith.langchain.com → project `ai-call-quality`，可看节点流转 + LLM 调用细节。

