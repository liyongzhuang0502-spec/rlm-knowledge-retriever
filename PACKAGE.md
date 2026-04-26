# RLM Knowledge Retriever - Skill Package

This is a complete OpenClaw-compatible skill package.

## Structure

```
rlm-knowledge-retriever/
├── SKILL.md              # OpenClaw skill definition
├── README.md             # Full documentation
├── setup.py              # Python package setup
├── requirements.txt      # Dependencies
├── LICENSE               # MIT License
├── CONTRIBUTING.md       # Contribution guide
├── .gitignore           # Git ignore rules
├── rlm_kb/              # Core package
│   ├── __init__.py
│   └── rlm_kb.py        # Main engine
├── examples/            # Examples and configs
│   ├── knowledge-base/  # Sample KB
│   ├── sample-queries.json
│   └── platform-configs/# Platform integrations
└── tests/               # Test suite
    └── test_rlm_kb.py
```

## Quick Start for OpenClaw

```bash
# Install
pip install rlm-knowledge-retriever

# Configure environment
export KB_PATH=./.sdd/knowledge
export OPENAI_API_KEY=your-key

# Use in OpenClaw
# → rlm_kb_search(query="...", strategy="recursive")
```

## For Other Platforms

See `examples/platform-configs/` for:
- Claude Code (MCP)
- Qoder (Slash commands)
- AgentScope (Function calls)
