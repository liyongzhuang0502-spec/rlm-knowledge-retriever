# RLM Knowledge Retriever Skill

> 基于 Recursive Language Model (RLM) 核心能力的知识库检索系统
> 让 LLM 递归分解查询、代码化检索、自动追踪关联

## 核心能力（RLM 原生）

### 1. 递归查询分解

不像传统检索一把梭查整个知识库，RLM 会：
- **分析查询意图** → 分解成子查询
- **逐个检索子查询** → 递归调用自己
- **合并结果** → 去重、排序、关联

```
用户: "怎么设计一个高并发的JWT认证系统？"
    ↓
RLM 分解:
  ├─ 子查询1: "JWT 认证最佳实践"
  ├─ 子查询2: "高并发系统设计模式"  
  ├─ 子查询3: "认证系统安全漏洞"
  └─ 子查询4: "Token 刷新机制"
    ↓
递归检索每个子查询 → 合并 → 返回结构化结果
```

### 2. REPL 代码化检索

检索逻辑不是写死的，而是在 REPL 环境中**代码化执行**：

```python
# RLM 自动生成的检索代码
 candidates = kb.query(tags=["auth", "jwt"])
 high_concurrency = [c for c in candidates if "concurrent" in c.content]
 security_issues = kb.query(tags=["security", "vulnerability"])
 
 # 自定义排序逻辑
 ranked = sorted(
     candidates,
     key=lambda x: x.metadata.get("priority", 0),
     reverse=True
 )
```

### 3. 语义关联追踪（子 LLM 调用）

不依赖人工维护的 `related_ids`，而是**让 LLM 判断关联性**：

```python
# RLM 子调用：判断两个知识条目是否语义相关
related = rlm.completion(
    f"Entry A: {entry_a.summary}\n"
    f"Entry B: {entry_b.summary}\n"
    f"Are they semantically related? (0-1 score)"
)
```

### 4. 近无限上下文

通过递归加载，单次查询可覆盖**海量知识库**：
- 先读索引 → 过滤 → 只加载相关条目
- 条目太长？递归分解条目本身
- 跨文档关联？递归追踪引用链

---

## 使用场景

| 场景 | 传统 RAG | RLM Retriever |
|------|---------|---------------|
| 复杂查询 | 一把梭，容易漏 | 递归分解，全覆盖 |
| 跨领域关联 | 需要人工维护关联 | LLM 自动发现关联 |
| 长文档精读 | 切片丢失上下文 | 递归分解，保留完整逻辑 |
| 动态排序 | 固定相似度排序 | 代码化自定义排序逻辑 |

---

## 工具定义

### `rlm_kb_search`

基于 RLM 的递归知识库检索

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | ✅ | 自然语言查询 |
| `kb_path` | string | ❌ | 知识库路径，默认 `./.sdd/knowledge` |
| `max_depth` | integer | ❌ | 递归深度，默认 2 |
| `strategy` | string | ❌ | 检索策略：`recursive`(默认) / `semantic` / `code` |
| `context` | object | ❌ | 上下文信息：`{phase, domain, tags}` |

**返回:**

```json
{
  "query": "原始查询",
  "sub_queries": ["子查询1", "子查询2"],
  "results": [
    {
      "id": "entry-id",
      "type": "pattern",
      "summary": "...",
      "relevance": 0.95,
      "source": "文件路径",
      "related_entries": ["关联条目id"],
      "retrieval_path": "查询分解路径"
    }
  ],
  "method": "rlm-recursive",
  "time_ms": 1234
}
```

### `rlm_kb_inspect`

深度检视单个知识条目（递归分解长内容）

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `entry_id` | string | ✅ | 条目 ID |
| `kb_path` | string | ❌ | 知识库路径 |
| `max_depth` | integer | ❌ | 分解深度，默认 2 |

---

## 使用示例

### 示例1：复杂查询分解

<example>
用户: "设计一个支持 10万 QPS 的 JWT 认证系统，要考虑安全漏洞"

→ 调用 rlm_kb_search(
  query="设计一个支持 10万 QPS 的 JWT 认证系统，要考虑安全漏洞",
  strategy="recursive",
  max_depth=2,
  context={
    phase: "designing",
    domain: "backend",
    tags: ["auth", "jwt", "security"]
  }
)

→ RLM 内部执行:
  1. 分解为子查询: ["JWT认证", "高并发设计", "安全漏洞"]
  2. 递归检索每个子查询
  3. 发现跨领域关联: JWT + Redis缓存 + 限流算法
  4. 返回结构化结果，标注每个结果的检索路径
</example>

### 示例2：长文档深度检视

<example>
用户: "详细解释一下这个架构模式"
（指向一个长篇架构文档）

→ 调用 rlm_kb_inspect(
  entry_id="microservices-event-sourcing",
  max_depth=2
)

→ RLM 内部执行:
  1. 读取文档全文
  2. 递归分解: 概述 → 核心概念 → 实现细节 → 优缺点
  3. 每个部分单独生成摘要
  4. 返回层次化结构
</example>

---

## 配置文件

`.rlm_kb_config.json`:

```json
{
  "kb_path": "./.sdd/knowledge",
  "rlm_backend": "openai",
  "rlm_model": "gpt-5-nano",
  "max_depth": 2,
  "enable_repl": true,
  "repl_timeout": 30,
  "sandbox": "local",
  "cache_embeddings": true
}
```

---

## 集成方式

### OpenClaw

```yaml
# 在 SKILL.md 中引用
skills:
  - rlm-knowledge-retriever
```

### Claude Code

```bash
# MCP Server 配置
{
  "mcpServers": {
    "rlm-kb": {
      "command": "python",
      "args": ["-m", "rlm_kb.mcp_server"]
    }
  }
}
```

### AgentScope

```python
from rlm_kb import RLMKnowledgeRetriever

kb = RLMKnowledgeRetriever("./.sdd/knowledge")
result = kb.search("复杂查询", strategy="recursive")
```

---

## 与传统 RAG 对比

| 维度 | 传统 RAG | RLM Knowledge Retriever |
|------|---------|------------------------|
| 查询处理 | 一把梭 | 递归分解 |
| 关联发现 | 人工维护 related_ids | LLM 语义判断 |
| 检索逻辑 | 固定算法 | REPL 代码化执行 |
| 上下文长度 | 受限于窗口 | 递归分解，近无限 |
| 结果排序 | 固定相似度 | 代码化自定义 |
| 可解释性 | 黑盒 | 透明检索路径 |

---

## 依赖

- `rlms` (RLM 核心库)
- `sentence-transformers` (可选，语义层)
- `openai` 或 `anthropic` (LLM 后端)

---

## License

MIT
