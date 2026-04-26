# Example Knowledge Base

This directory contains example knowledge bases for testing and demonstration.

## Structure

```
examples/
├── knowledge-base/           # Example SDD-compatible knowledge base
│   ├── patterns/
│   └── lessons/
├── sample-queries.json       # Sample queries for testing
└── platform-configs/         # Platform-specific configurations
    ├── openclaw/
    ├── claude/
    └── qoder/
```

## Usage

```bash
# Use example knowledge base
rlm-kb search --kb-path examples/knowledge-base < examples/sample-queries.json
```
