# OpenClaw Skill Integration

## Installation

Add to your agent's `SKILL.md`:

```yaml
skills:
  - rlm-knowledge-retriever
```

Or install via ClawHub:

```bash
openclaw skills install rlm-knowledge-retriever
```

## Tool Usage

### `rlm_kb_search`

```
→ rlm_kb_search(
    query: "设计10万QPS的JWT认证系统",
    strategy: "recursive",
    max_depth: 2,
    context: {
      phase: "designing",
      domain: "backend"
    }
  )
```

### `rlm_kb_inspect`

```
→ rlm_kb_inspect(
    entry_id: "auth-jwt-best-practice",
    max_depth: 2
  )
```

## Configuration

Set environment variables in your agent config:

```bash
KB_PATH=./.sdd/knowledge
OPENAI_API_KEY=your-key
RLM_MAX_DEPTH=2
```
