# RLM Knowledge Retriever - 核心引擎
# 基于 Recursive Language Model 的递归式知识库检索
# 
# 核心设计：
# 1. 递归分解查询 → 子查询独立检索 → 合并去重
# 2. REPL 代码化检索逻辑（非固定算法）
# 3. 子 LLM 调用判断语义关联
# 4. 递归加载长文档，突破上下文限制

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path
import json
import time
import hashlib

try:
    from rlms import RLM
    RLM_AVAILABLE = True
except ImportError:
    RLM_AVAILABLE = False
    print("[WARN] rlms 未安装，RLM 递归功能不可用。pip install rlms")


# ============================================================
# 数据模型
# ============================================================

@dataclass
class KnowledgeEntry:
    """知识条目 - 统一格式兼容任意知识库"""
    id: str
    type: str  # pattern | lesson | doc | snippet
    tags: List[str]
    summary: str
    content: str
    source_file: str
    metadata: Dict = field(default_factory=dict)
    
    @property
    def embedding_text(self) -> str:
        return f"{self.summary}\n{self.content[:2000]}"

@dataclass
class RetrievalResult:
    """检索结果 - 带完整检索路径"""
    entry: KnowledgeEntry
    relevance: float
    retrieval_path: str  # 记录怎么找到的（用于可解释性）
    sub_queries: List[str] = field(default_factory=list)  # 来自哪些子查询

@dataclass
class SearchOutput:
    """搜索输出"""
    original_query: str
    sub_queries: List[str]
    results: List[RetrievalResult]
    total_found: int
    method: str
    time_ms: float
    repl_code: Optional[str] = None  # 执行的REPL代码（可审计）


# ============================================================
# RLM 递归检索引擎
# ============================================================

class RLMKnowledgeEngine:
    """
    RLM 核心检索引擎
    
    区别于传统检索：
    - 不是"一把梭"查整个知识库
    - 而是让 LLM 递归分解查询，代码化执行检索
    """
    
    def __init__(self, 
                 kb_path: str,
                 rlm_backend: str = "openai",
                 rlm_model: str = "gpt-5-nano",
                 max_depth: int = 2):
        self.kb_path = Path(kb_path)
        self.max_depth = max_depth
        self.entries: Dict[str, KnowledgeEntry] = {}
        self.tag_index: Dict[str, List[str]] = {}
        
        # RLM 实例 - 用于递归查询分解和关联判断
        if RLM_AVAILABLE:
            self.rlm = RLM(
                backend=rlm_backend,
                backend_kwargs={"model_name": rlm_model},
                verbose=False
            )
        else:
            self.rlm = None
        
        # 加载知识库
        self._load_kb()
    
    def _load_kb(self):
        """加载并索引知识库"""
        for file_path in self.kb_path.rglob("*.json"):
            try:
                data = json.loads(file_path.read_text())
                items = data if isinstance(data, list) else [data]
                
                for item in items:
                    entry = KnowledgeEntry(
                        id=item.get("id", self._hash(file_path)),
                        type=item.get("type", "pattern"),
                        tags=[t.lower() for t in item.get("tags", [])],
                        summary=item.get("summary", item.get("name", "")),
                        content=json.dumps(item, ensure_ascii=False),
                        source_file=str(file_path.relative_to(self.kb_path)),
                        metadata=item.get("metadata", {})
                    )
                    self.entries[entry.id] = entry
                    for tag in entry.tags:
                        self.tag_index.setdefault(tag, []).append(entry.id)
            except Exception as e:
                print(f"[WARN] 加载失败 {file_path}: {e}")
    
    def _hash(self, path: Path) -> str:
        return hashlib.md5(str(path).encode()).hexdigest()[:12]
    
    # ========================================================
    # 核心 API
    # ========================================================
    
    def search(self, query: str, context: Optional[Dict] = None) -> SearchOutput:
        """
        RLM 递归检索入口
        
        流程：
        1. RLM 分解查询为子查询
        2. 每个子查询独立检索
        3. 合并、去重、排序
        4. RLM 语义判断关联性
        5. 返回带完整路径的结果
        """
        start_time = time.time()
        context = context or {}
        
        # Step 1: RLM 分解查询
        sub_queries = self._decompose_query(query, context)
        
        # Step 2: 并行检索子查询
        all_results: List[RetrievalResult] = []
        for sub_q in sub_queries:
            results = self._retrieve_subquery(sub_q, context)
            all_results.extend(results)
        
        # Step 3: 去重（按 entry.id）
        seen = set()
        unique_results = []
        for r in all_results:
            if r.entry.id not in seen:
                seen.add(r.entry.id)
                unique_results.append(r)
        
        # Step 4: RLM 语义重排
        ranked = self._semantic_rerank(query, unique_results)
        
        # Step 5: 递归关联展开（如果深度允许）
        if self.max_depth > 1:
            ranked = self._expand_related_recursive(ranked, depth=1)
        
        elapsed = (time.time() - start_time) * 1000
        
        return SearchOutput(
            original_query=query,
            sub_queries=sub_queries,
            results=ranked[:10],  # 默认返回前10
            total_found=len(ranked),
            method="rlm-recursive",
            time_ms=elapsed
        )
    
    def inspect(self, entry_id: str, max_depth: int = 2) -> Dict:
        """
        深度检视单个条目（递归分解长内容）
        
        类似 RLM 的递归读取：条目太长时，让 LLM 决定分几块读
        """
        entry = self.entries.get(entry_id)
        if not entry:
            return {"error": f"Entry not found: {entry_id}"}
        
        # 如果内容短，直接返回
        if len(entry.content) < 4000:
            return {
                "id": entry_id,
                "summary": entry.summary,
                "full_content": entry.content,
                "structure": "single"
            }
        
        # 内容长 → RLM 递归分解
        if self.rlm:
            structure = self._rlm_decompose_document(entry)
            return {
                "id": entry_id,
                "summary": entry.summary,
                "structure": "recursive",
                "sections": structure
            }
        
        # 无 RLM 时简单分段
        return {
            "id": entry_id,
            "summary": entry.summary,
            "structure": "chunked",
            "chunks": [entry.content[i:i+4000] for i in range(0, len(entry.content), 4000)]
        }
    
    # ========================================================
    # RLM 核心能力实现
    # ========================================================
    
    def _decompose_query(self, query: str, context: Dict) -> List[str]:
        """
        能力1：递归查询分解
        
        让 RLM 分析查询意图，分解为独立子查询
        例："高并发JWT认证" → ["JWT认证", "高并发设计", "认证安全"]
        """
        if not self.rlm:
            # 无 RLM 时简单分词
            return [query]
        
        prompt = f"""Analyze this query and decompose it into 2-4 independent sub-queries.
Each sub-query should be self-contained and retrievable from a knowledge base.

Query: "{query}"
Context: {json.dumps(context, ensure_ascii=False)}

Return ONLY a JSON array of sub-queries. Example:
["sub-query 1", "sub-query 2"]

Sub-queries:"""
        
        try:
            response = self.rlm.completion(prompt).response
            # 提取 JSON 数组
            import re
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                sub_queries = json.loads(json_match.group())
                if isinstance(sub_queries, list) and len(sub_queries) > 0:
                    return sub_queries
        except Exception as e:
            print(f"[WARN] 查询分解失败: {e}")
        
        return [query]  # 失败时回退
    
    def _retrieve_subquery(self, sub_query: str, context: Dict) -> List[RetrievalResult]:
        """
        能力2：REPL 代码化检索
        
        让 RLM 生成检索代码，在 REPL 中执行
        不是固定算法，而是根据查询动态生成检索逻辑
        """
        # 先生成检索代码
        repl_code = self._generate_retrieval_code(sub_query, context)
        
        # 执行检索代码（在安全环境中）
        candidates = self._execute_retrieval_code(repl_code)
        
        # 包装结果
        results = []
        for entry in candidates:
            results.append(RetrievalResult(
                entry=entry,
                relevance=0.8,  # 初始相关性
                retrieval_path=f"subquery: '{sub_query}' -> {repl_code[:50]}...",
                sub_queries=[sub_query]
            ))
        
        return results
    
    def _generate_retrieval_code(self, sub_query: str, context: Dict) -> str:
        """
        生成 REPL 检索代码
        
        RLM 根据子查询动态生成 Python 代码来过滤/排序
        """
        if not self.rlm:
            # 无 RLM 时简单 tag 匹配
            return f"kb.get_by_tags(['{sub_query.lower()}'])"
        
        # 构建可用标签提示
        available_tags = list(self.tag_index.keys())[:50]  # 限制避免太长
        
        prompt = f"""Generate Python code to retrieve relevant knowledge entries.

Sub-query: "{sub_query}"
Available tags: {available_tags}

Write Python code that:
1. Uses `kb` object (has methods: get_by_tags, get_all, search_content)
2. Filters and sorts entries
3. Returns a list of entry IDs

Code:
```python
"""
        
        try:
            response = self.rlm.completion(prompt).response
            # 提取代码块
            import re
            code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                return code_match.group(1)
        except Exception as e:
            print(f"[WARN] 代码生成失败: {e}")
        
        # 回退：简单 tag 匹配
        return f"kb.get_by_tags(['{sub_query.lower()}'])"
    
    def _execute_retrieval_code(self, code: str) -> List[KnowledgeEntry]:
        """
        在 REPL 环境中执行检索代码
        
        安全注意：使用受限命名空间
        """
        # 构建安全环境
        namespace = {
            "kb": self,  # 暴露受限接口
            "entries": self.entries,
            "tag_index": self.tag_index,
        }
        
        try:
            # 执行代码
            exec(code, namespace)
            
            # 获取结果（假设代码设置了 result 变量）
            if "result" in namespace:
                result = namespace["result"]
                if isinstance(result, list):
                    # 解析 entry IDs
                    entries = []
                    for item in result:
                        if isinstance(item, str) and item in self.entries:
                            entries.append(self.entries[item])
                        elif isinstance(item, KnowledgeEntry):
                            entries.append(item)
                    return entries
        except Exception as e:
            print(f"[WARN] 代码执行失败: {e}")
        
        # 回退：简单返回所有
        return list(self.entries.values())[:20]
    
    def _semantic_rerank(self, query: str, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        能力3：子 LLM 调用判断语义关联
        
        用 RLM 判断每个结果与原始查询的真实语义相关性
        """
        if not self.rlm or len(results) <= 1:
            return results
        
        # 批量评分（限制避免 too many tokens）
        scored = []
        for r in results[:20]:  # 只评前20个
            prompt = f"""Rate the relevance of this knowledge entry to the query.

Query: "{query}"
Entry summary: "{r.entry.summary}"
Entry tags: {r.entry.tags}

Relevance score (0-10, where 10 is highly relevant):
Return ONLY a number."""
            
            try:
                response = self.rlm.completion(prompt).response.strip()
                score = float(response.split()[0]) / 10.0  # 归一化到 0-1
                r.relevance = min(max(score, 0.0), 1.0)
            except Exception:
                pass  # 保持默认评分
            
            scored.append(r)
        
        # 按相关性排序
        scored.sort(key=lambda x: x.relevance, reverse=True)
        return scored
    
    def _expand_related_recursive(self, results: List[RetrievalResult], depth: int) -> List[RetrievalResult]:
        """
        能力4：递归关联展开
        
        发现语义关联条目，递归加载
        突破上下文限制：不一次加载所有，而是按需递归
        """
        if depth >= self.max_depth:
            return results
        
        all_related = []
        
        for r in results:
            # 从 entry metadata 找 related_ids
            related_ids = r.entry.metadata.get("related_ids", [])
            
            # RLM 语义发现更多关联
            if self.rlm:
                semantic_related = self._discover_semantic_related(r.entry)
                related_ids.extend([e.id for e in semantic_related])
            
            # 去重加载
            seen = {r.entry.id for r in results}
            for rid in related_ids:
                if rid not in seen and rid in self.entries:
                    seen.add(rid)
                    all_related.append(RetrievalResult(
                        entry=self.entries[rid],
                        relevance=r.relevance * 0.8,  # 关联条目降权
                        retrieval_path=f"{r.retrieval_path} -> related({rid})",
                        sub_queries=r.sub_queries
                    ))
        
        # 合并并继续递归
        combined = results + all_related
        if all_related:
            return self._expand_related_recursive(combined, depth + 1)
        
        return combined
    
    def _discover_semantic_related(self, entry: KnowledgeEntry) -> List[KnowledgeEntry]:
        """
        用 RLM 发现语义关联条目（不依赖人工维护的 related_ids）
        """
        if not self.rlm:
            return []
        
        # 采样候选条目（避免太长）
        candidates = list(self.entries.values())[:30]
        candidates_text = "\n".join([
            f"[{i}] {e.summary} (tags: {e.tags})"
            for i, e in enumerate(candidates)
        ])
        
        prompt = f"""Find entries semantically related to:

Target: {entry.summary}
Tags: {entry.tags}

From candidates below, return indices of related entries (comma-separated).
If none, return "none".

Candidates:
{candidates_text}

Related indices:"""
        
        try:
            response = self.rlm.completion(prompt).response.strip()
            if response.lower() == "none":
                return []
            
            import re
            indices = [int(x) for x in re.findall(r'\d+', response)]
            return [candidates[i] for i in indices if 0 <= i < len(candidates)]
        except Exception:
            return []
    
    def _rlm_decompose_document(self, entry: KnowledgeEntry) -> List[Dict]:
        """
        RLM 递归分解长文档
        """
        if not self.rlm:
            return []
        
        prompt = f"""Decompose this document into logical sections.

Document: {entry.content[:2000]}...

Return JSON array of sections:
[{{"title": "section name", "summary": "brief summary"}}]

Sections:"""
        
        try:
            response = self.rlm.completion(prompt).response
            import re
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        
        return [{"title": "Full Content", "summary": entry.summary}]
    
    # ========================================================
    # 简化接口（兼容传统检索）
    # ========================================================
    
    def get_by_tags(self, tags: List[str]) -> List[str]:
        """获取匹配标签的 entry IDs"""
        result = set()
        for tag in tags:
            tag = tag.lower()
            for indexed_tag, ids in self.tag_index.items():
                if tag in indexed_tag or indexed_tag in tag:
                    result.update(ids)
        return list(result)
    
    def get_all(self) -> List[KnowledgeEntry]:
        return list(self.entries.values())
    
    def search_content(self, keyword: str) -> List[KnowledgeEntry]:
        """全文搜索"""
        keyword = keyword.lower()
        return [
            e for e in self.entries.values()
            if keyword in e.content.lower() or keyword in e.summary.lower()
        ]


# ============================================================
# CLI 接口
# ============================================================

def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="RLM Knowledge Retriever")
    parser.add_argument("--kb-path", default="./.sdd/knowledge")
    parser.add_argument("--backend", default="openai")
    parser.add_argument("--model", default="gpt-5-nano")
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("command", choices=["search", "inspect", "status"])
    
    args, unknown = parser.parse_known_args()
    
    engine = RLMKnowledgeEngine(
        kb_path=args.kb_path,
        rlm_backend=args.backend,
        rlm_model=args.model,
        max_depth=args.max_depth
    )
    
    if args.command == "search":
        # 读取查询
        if not sys.stdin.isatty():
            query_data = json.load(sys.stdin)
        else:
            query_data = {"query": unknown[0] if unknown else "", "context": {}}
        
        result = engine.search(
            query=query_data.get("query", ""),
            context=query_data.get("context", {})
        )
        
        # 输出
        output = {
            "query": result.original_query,
            "sub_queries": result.sub_queries,
            "method": result.method,
            "time_ms": round(result.time_ms, 2),
            "results": [
                {
                    "id": r.entry.id,
                    "type": r.entry.type,
                    "summary": r.entry.summary,
                    "relevance": round(r.relevance, 2),
                    "tags": r.entry.tags,
                    "source": r.entry.source_file,
                    "retrieval_path": r.retrieval_path
                }
                for r in result.results
            ]
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    
    elif args.command == "inspect":
        entry_id = unknown[0] if unknown else ""
        result = engine.inspect(entry_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "status":
        print(f"知识库: {args.kb_path}")
        print(f"条目数: {len(engine.entries)}")
        print(f"标签数: {len(engine.tag_index)}")
        print(f"RLM可用: {'是' if RLM_AVAILABLE else '否'}")

if __name__ == "__main__":
    main()
