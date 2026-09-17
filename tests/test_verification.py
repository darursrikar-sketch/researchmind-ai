"""
Automated verification tests for ResearchMind AI core modules.
"""
import unittest
import json
from pathlib import Path

from researchmind.paper_loader import extract_arxiv_id, PaperMetadata
from researchmind.storage import storage
from researchmind.core.agent import PaperAnalysisResult, AnalysisSection
from researchmind.exporter import PaperExporter
from researchmind.web.app import app


class TestResearchMind(unittest.TestCase):
    def test_arxiv_id_extraction(self):
        self.assertEqual(extract_arxiv_id("1706.03762"), "1706.03762")
        self.assertEqual(extract_arxiv_id("1706.03762v5"), "1706.03762v5")
        self.assertEqual(extract_arxiv_id("https://arxiv.org/abs/2106.09685"), "2106.09685")
        self.assertEqual(extract_arxiv_id("https://arxiv.org/pdf/2501.12948.pdf"), "2501.12948")
        self.assertEqual(extract_arxiv_id("arxiv:2303.08774"), "2303.08774")

    def test_paper_metadata_and_storage(self):
        test_paper = PaperMetadata(
            id="test_paper_123",
            title="Attention Is All You Need",
            authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
            abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
            published="2017-06-12",
            arxiv_id="1706.03762",
            pdf_path="dummy.pdf",
            num_pages=15,
            word_count=5200,
            full_text="--- [Page 1] ---\nAbstract\nWe propose the Transformer.",
        )
        storage.save_paper(test_paper)

        retrieved = storage.get_paper("test_paper_123")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Attention Is All You Need")
        self.assertEqual(len(retrieved.authors), 3)

        papers = storage.list_papers()
        self.assertTrue(any(p["id"] == "test_paper_123" for p in papers))

        analysis = PaperAnalysisResult(
            paper_id="test_paper_123",
            paper_title="Attention Is All You Need",
            model_used="gemini-3.7-flash",
            sections={
                "summary": AnalysisSection(
                    key="summary",
                    title="Executive Summary & TL;DR",
                    content="### TL;DR\n- Replaces recurrence entirely with Multi-Head Attention.",
                    generation_time_s=1.2,
                )
            },
            metadata=test_paper.to_dict(),
        )
        storage.save_analysis(analysis)
        retrieved_analysis = storage.get_analysis("test_paper_123")
        self.assertIsNotNone(retrieved_analysis)
        self.assertIn("summary", retrieved_analysis.sections)

        md = PaperExporter.to_markdown(analysis)
        self.assertIn("# Research Analysis: Attention Is All You Need", md)
        self.assertIn("Multi-Head Attention", md)

        html = PaperExporter.to_html(analysis)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("ResearchMind AI", html)

        json_str = PaperExporter.to_json(analysis)
        data = json.loads(json_str)
        self.assertEqual(data["paper_id"], "test_paper_123")

        storage.delete_paper("test_paper_123")
        self.assertIsNone(storage.get_paper("test_paper_123"))

    def test_flask_endpoints(self):
        client = app.test_client()
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"ResearchMind AI", res.data)

        res = client.get("/api/config")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("available_models", data)
        self.assertIn("default_model", data)

        res = client.get("/api/papers")
        self.assertEqual(res.status_code, 200)
        self.assertIn("papers", res.get_json())


if __name__ == "__main__":
    unittest.main()

