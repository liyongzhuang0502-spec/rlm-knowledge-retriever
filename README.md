# RLM Knowledge Retriever

> **Recursive Language Model based knowledge base retrieval for AI agents.**
>
> 让 LLM 递归分解查询、代码化检索、自动追踪关联 —— 突破传统 RAG 的上下文限制。

[![PyPI version](https://img.shields.io/pypi/v/rlm-knowledge-retriever.svg)](https://pypi.org/project/rlm-knowledge-retriever/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Why RLM Retriever?

传统 RAG 的问题是：**一把梭查整个知识库**，上下文窗口受限，关联靠人工维护。

RLM Knowledge Retriever 用**递归式检索**解决这个问题：

```
传统 RAG:                    RLM Retriever:
┌──────────┐                ┌──────────┐
│ 用户查询  │                │ 用户查询  │
└────┬─────┘                └────┬─────┘
     ▼                          ▼
┌──────────┐                ┌──────────┐
│ 查向量库  │                │ RLM分解  │
│ top-k    │                │ 子查询1  │
└────┬─────┘                │ 子查询2  │
     ▼                      │ 子查询3  │
┌──────────┐                └────┬─────┘
│ 返回结果  │                     ▼
└──────────┘                ┌──────────┐
                            │ 递归检索  │
                            │ 代码化执行│
                            │ 语义关联  │
                            └────┬─────┘
                                 ▼
                            ┌──────────┐
                            │ 合并去重  │
                            │ 完整路径  │
                            └────┬─────┘
                                 ▼
                            ┌──────────┐
                            │ 返回结果  │
                            └──────────┘
```

## Core Capabilities

### 1. Recursive Query Decomposition

复杂查询自动分解为独立子查询，递归检索：

```python
"设计10万QPS的JWT认证系统"
    ↓ RLM分解
["JWT认证", "高并发设计", "安全漏洞", "Token刷新"]
    ↓ 递归检索
合并结果 → 去重 → 语义重排
```

### 2. REPL-based Code Retrieval

检索逻辑不是固定算法，而是**动态生成 Python 代码执行**：

```python
# RLM 自动生成的检索代码
candidates = kb.get_by_tags(["auth", "jwt"])
high_perf = [c for c in candidates if "concurrent" in c.content]
security = kb.search_content("vulnerability")
return sorted(high_perf + security, key=lambda x: x.priority)
```

### 3. Semantic Association Discovery

不依赖人工维护 `related_ids`，**LLM 自动判断语义关联**。

### 4. Near-Infinite Context

递归加载 + 按需分解，突破上下文窗口限制。

## Quick Start

### Installation

```bash
pip install rlm-knowledge-retriever
```

### CLI Usage

```bash
# Search with recursive decomposition
echo '{"query":"high concurrency JWT auth","context":{"phase":"designing"}}' | rlm-kb search

# Deep inspect an entry
rlm-kb inspect auth-jwt-pattern

# Status
rlm-kb status --kb-path ./.sdd/knowledge
```

### Python API

```python
from rlm_kb import RLMKnowledgeEngine

# Initialize
kb = RLMKnowledgeEngine(
    kb_path="./.sdd/knowledge",
    rlm_backend="openai",
    rlm_model="gpt-5-nano",
    max_depth=2
)

# Recursive search
result = kb.search(
    query="design 100k QPS JWT auth system with security",
    context={"phase": "designing", "domain": "backend"}
)

for r in result.results:
    print(f"[{r.relevance:.2f}] {r.entry.summary}")
    print(f"    Path: {r.retrieval_path}")
```

### OpenClaw Skill

```yaml
# In your agent's SKILL.md
skills:
  - rlm-knowledge-retriever
```

Then use:
```
→ rlm_kb_search(query="...", strategy="recursive", max_depth=2)
```

## Knowledge Base Format

Compatible with any knowledge base structure:

```
.sdd/knowledge/          # SDD compatible
├── index.json
├── patterns/
│   ├── auth-jwt.json
│   └── database-pool.json
└── lessons/
    └── race-condition.json

.kb/                     # Generic format
├── docs/
├── snippets/
└── notes/
```

Entry format (JSON):
```json
{
  "id": "auth-jwt-pattern",
  "type": "pattern",
  "tags": ["auth", "jwt", "security"],
  "summary": "JWT authentication best practices",
  "content": "...",
  "metadata": {
    "priority": 10,
    "related_ids": ["oauth2-pattern"]
  }
}
```

## Architecture

```
┌────────────────────────────────────────────────────┐
│ Agent Layer (OpenClaw/Claude/Qoder/AgentScope/...) │
├────────────────────────────────────────────────────┤
│  CLI / Python API / MCP / Function Call            │
├────────────────────────────────────────────────────┤
│  RLM Knowledge Engine                              │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐   │
│  │ Decompose  │ │ Code Gen   │ │ Semantic     │   │
│  │ Sub-queries│ │ REPL Exec  │ │ Rerank       │   │
│  └────────────┘ └────────────┘ └──────────────┘   │
├────────────────────────────────────────────────────┤
│  Knowledge Store (File System / JSON / Markdown)   │
└────────────────────────────────────────────────────┘
```

## Configuration

`.rlm_kb_config.json`:

```json
{
  "kb_path": "./.sdd/knowledge",
  "rlm_backend": "openai",
  "rlm_model": "gpt-5-nano",
  "max_depth": 2,
  "enable_repl": true,
  "sandbox": "local",
  "cache_embeddings": true
}
```

Environment variables:
- `KB_PATH` - Knowledge base path
- `OPENAI_API_KEY` - OpenAI API key for RLM
- `RLM_MAX_DEPTH` - Default recursion depth

## Platform Integration

| Platform | Integration | Example |
|----------|------------|---------|
| **OpenClaw** | Skill tool call | `rlm_kb_search(query="...")` |
| **Claude Code** | MCP Server | See `examples/mcp-config.json` |
| **Qoder** | Slash command | See `examples/qoder-command.yaml` |
| **AgentScope** | Function call | `from rlm_kb import RLMKnowledgeEngine` |
| **Generic** | Subprocess / HTTP | `rlm-kb search < query.json` |

## Comparison

| Dimension | Traditional RAG | RLM Knowledge Retriever |
|-----------|----------------|------------------------|
| Query handling | Monolithic | **Recursive decomposition** |
| Retrieval logic | Fixed algorithm | **REPL code generation** |
| Association | Manual `related_ids` | **LLM semantic discovery** |
| Context | Window limited | **Near-infinite** |
| Explainability | Black box | **Full retrieval path** |

## Development

```bash
# Clone
git clone https://github.com/yourusername/rlm-knowledge-retriever.git
cd rlm-knowledge-retriever

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black rlm_kb/
```

## License

MIT License - see [LICENSE](LICENSE) file.

## Contributing

Pull requests welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## Acknowledgments

- [Recursive Language Models](https://github.com/alexzhang13/rlm) - The RLM framework
- [SDD Knowledge Base](https://skillsmp.com/skills/leoheart0125-sdd-skills-skills-sdd-knowledge-base-skill-md) - SDD framework inspiration
