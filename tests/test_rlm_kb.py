import pytest
import json
import tempfile
from pathlib import Path

from rlm_kb import RLMKnowledgeEngine, KnowledgeEntry


class TestRLMKnowledgeEngine:
    """Test RLM Knowledge Engine core functionality"""
    
    @pytest.fixture
    def sample_kb(self):
        """Create a temporary knowledge base for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_path = Path(tmpdir)
            
            # Create test patterns
            patterns_dir = kb_path / "patterns"
            patterns_dir.mkdir()
            
            pattern1 = {
                "id": "test-auth",
                "type": "pattern",
                "tags": ["auth", "jwt"],
                "summary": "Test auth pattern",
                "content": "Test content for auth",
                "metadata": {"priority": 10}
            }
            
            (patterns_dir / "test-auth.json").write_text(json.dumps(pattern1))
            
            # Create test lessons
            lessons_dir = kb_path / "lessons"
            lessons_dir.mkdir()
            
            lesson1 = {
                "id": "test-lesson",
                "type": "lesson",
                "tags": ["database", "performance"],
                "summary": "Test lesson",
                "content": "Test lesson content",
                "metadata": {"trigger": "implementing-database"}
            }
            
            (lessons_dir / "test-lesson.json").write_text(json.dumps(lesson1))
            
            yield str(kb_path)
    
    def test_load_kb(self, sample_kb):
        """Test knowledge base loading"""
        engine = RLMKnowledgeEngine(kb_path=sample_kb)
        
        assert len(engine.entries) == 2
        assert "test-auth" in engine.entries
        assert "test-lesson" in engine.entries
    
    def test_get_by_tags(self, sample_kb):
        """Test tag-based retrieval"""
        engine = RLMKnowledgeEngine(kb_path=sample_kb)
        
        results = engine.get_by_tags(["auth"])
        assert "test-auth" in results
        
        results = engine.get_by_tags(["database"])
        assert "test-lesson" in results
    
    def test_search_content(self, sample_kb):
        """Test content search"""
        engine = RLMKnowledgeEngine(kb_path=sample_kb)
        
        results = engine.search_content("auth")
        assert len(results) >= 1
        assert any(r.id == "test-auth" for r in results)
    
    def test_search_without_rlm(self, sample_kb):
        """Test search without RLM (fallback mode)"""
        engine = RLMKnowledgeEngine(kb_path=sample_kb)
        
        result = engine.search(
            query="auth pattern",
            context={"tags": ["auth"]}
        )
        
        assert result.original_query == "auth pattern"
        assert len(result.results) > 0
        assert result.method == "rlm-recursive"
    
    def test_inspect_short_entry(self, sample_kb):
        """Test inspect on short entry"""
        engine = RLMKnowledgeEngine(kb_path=sample_kb)
        
        result = engine.inspect("test-auth")
        
        assert result["id"] == "test-auth"
        assert "summary" in result
        assert "full_content" in result
    
    def test_tag_index_building(self, sample_kb):
        """Test tag index is built correctly"""
        engine = RLMKnowledgeEngine(kb_path=sample_kb)
        
        assert "auth" in engine.tag_index
        assert "jwt" in engine.tag_index
        assert "database" in engine.tag_index
        
        assert "test-auth" in engine.tag_index["auth"]
        assert "test-lesson" in engine.tag_index["database"]


class TestKnowledgeEntry:
    """Test KnowledgeEntry data model"""
    
    def test_embedding_text(self):
        """Test embedding text generation"""
        entry = KnowledgeEntry(
            id="test",
            type="pattern",
            tags=["test"],
            summary="Test summary",
            content="Test content" * 100,  # Long content
            source_file="test.json"
        )
        
        text = entry.embedding_text
        assert "Test summary" in text
        assert len(text) <= len("Test summary") + 2000


class TestIntegration:
    """Integration tests"""
    
    def test_full_retrieval_flow(self):
        """Test complete retrieval flow with sample KB"""
        # This test uses the example knowledge base
        example_kb = Path(__file__).parent.parent / "examples" / "knowledge-base"
        
        if not example_kb.exists():
            pytest.skip("Example knowledge base not found")
        
        engine = RLMKnowledgeEngine(kb_path=str(example_kb))
        
        # Search for auth-related patterns
        result = engine.search(
            query="JWT authentication",
            context={"tags": ["auth", "jwt"]}
        )
        
        assert len(result.results) > 0
        assert any("auth" in r.entry.tags for r in result.results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
