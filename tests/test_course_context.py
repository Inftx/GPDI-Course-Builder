import json
import os
import tempfile
import unittest
from pathlib import Path

from modules.course_builder import build_course
from services.generators.base_generator import (
    _load_course_knowledge,
    generate_document,
)
from services.rag.chunker import chunk_document
from services.rag.indexer import build_index, search_index


class CourseContextTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.original_directory = Path.cwd()
        self.addCleanup(self.temporary_directory.cleanup)
        self.addCleanup(os.chdir, self.original_directory)
        os.chdir(self.root)
        (self.root / "projects").mkdir()

    def project_path(self, name="Course"):
        path = self.root / "projects" / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_legacy_knowledge_schema_is_read_without_losing_topics(self):
        project = self.project_path()
        (project / "knowledge").mkdir()
        legacy = {
            "document": "Legacy Guide.docx",
            "module": {"code": "KM-01", "title": "Knowledge Module"},
            "knowledge_topics": [
                {
                    "code": "KM-01-KT01",
                    "title": "Business Registration",
                    "knowledge_items": [
                        {"code": "KT0101", "description": "Register with CIPC."}
                    ],
                }
            ],
            "learning_outcomes": ["Explain business registration."],
            "assessment_criteria": ["Identify required registrations."],
        }
        source = project / "knowledge" / "legacy.json"
        source.write_text(json.dumps(legacy), encoding="utf-8")
        original_source = source.read_text(encoding="utf-8")

        course = build_course("Course")

        self.assertIn("KM-01: Knowledge Module", course["modules"])
        self.assertEqual(course["knowledge_topics"], legacy["knowledge_topics"])
        self.assertEqual(course["learning_outcomes"], legacy["learning_outcomes"])
        self.assertEqual(course["assessment_criteria"], legacy["assessment_criteria"])
        self.assertEqual(source.read_text(encoding="utf-8"), original_source)

    def test_new_documents_after_prior_build_are_incorporated(self):
        project = self.project_path()
        (project / "knowledge").mkdir()
        old_knowledge = {
            "document": "Old Guide.docx",
            "modules": ["Retail Operations"],
            "learning_outcomes": ["Explain retail operations."],
        }
        (project / "knowledge" / "old.json").write_text(
            json.dumps(old_knowledge),
            encoding="utf-8",
        )
        stale = {"project": "Course", "documents": ["Old Guide.docx"]}
        (project / "course.json").write_text(json.dumps(stale), encoding="utf-8")
        original_document = b"uploaded source remains unchanged"
        (project / "documents").mkdir()
        (project / "documents" / "New Guide.docx").write_bytes(original_document)

        new_knowledge = {
            "document": "New Guide.docx",
            "module": {"code": "KM-02", "title": "Customer Service"},
            "knowledge_topics": [
                {
                    "code": "KM-02-KT01",
                    "title": "Customer Care",
                    "knowledge_items": [],
                }
            ],
        }
        (project / "knowledge" / "new.json").write_text(
            json.dumps(new_knowledge),
            encoding="utf-8",
        )
        (project / "formatted").mkdir()
        new_text = "Customer care requires listening and resolving complaints."
        (project / "formatted" / "New Guide_structured.txt").write_text(
            new_text,
            encoding="utf-8",
        )

        course = build_course("Course")

        self.assertIn("New Guide.docx", course["documents"])
        self.assertIn(
            new_text,
            [source["content"] for source in course["source_documents"]],
        )
        latest = _load_course_knowledge("Course")
        self.assertIn(
            new_text,
            [source["content"] for source in latest["source_documents"]],
        )
        self.assertEqual(
            (project / "documents" / "New Guide.docx").read_bytes(),
            original_document,
        )

    def test_empty_retrieval_fails_before_provider_call(self):
        project = self.project_path()
        course = {
            "project": "Course",
            "documents": [],
            "modules": ["Retail Operations and Business Administration"],
            "knowledge_topics": [],
            "learning_outcomes": [],
            "assessment_criteria": [],
            "knowledge_requirements": [],
            "practical_activities": [],
            "workplace_activities": [],
            "source_documents": [],
        }
        (project / "course.json").write_text(json.dumps(course), encoding="utf-8")

        class Provider:
            called = False

            def generate(self, prompt):
                self.called = True
                return "generated"

        provider = Provider()
        with self.assertRaisesRegex(ValueError, "No usable course context"):
            generate_document(
                "Course",
                "Retail Operations and Business Administration",
                1,
                "lesson_plans",
                "Use context: {context}",
                provider,
            )
        self.assertFalse(provider.called)

    def test_generic_module_terms_do_not_match_unrelated_source_text(self):
        index = build_index(
            [
                {
                    "title": "Unrelated Guide",
                    "content": "RAG context for unrelated material.",
                }
            ]
        )

        self.assertEqual(
            search_index(index, "RAG Context Course Module"),
            [],
        )

    def test_generation_uses_relevant_uploaded_source_not_generic_matches(self):
        project = self.project_path()
        knowledge_folder = project / "knowledge"
        knowledge_folder.mkdir()
        (knowledge_folder / "customer_guide.json").write_text(
            json.dumps(
                {
                    "document": "Customer Service Guide.docx",
                    "module": {
                        "code": "CM-01",
                        "title": "Customer Service",
                    },
                    "knowledge_topics": [
                        {
                            "code": "CM-01-KT01",
                            "title": "Complaint Resolution",
                            "knowledge_items": [
                                {
                                    "code": "KT0101",
                                    "description": (
                                        "Listen to the customer's complaint, "
                                        "confirm the issue, and agree on a "
                                        "fair resolution."
                                    ),
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        formatted = project / "formatted"
        formatted.mkdir()
        source_text = (
            "Complaint resolution requires staff to listen carefully, "
            "confirm the customer's issue, and agree on a fair resolution."
        )
        (formatted / "Customer Service Guide_structured.txt").write_text(
            source_text,
            encoding="utf-8",
        )
        unrelated_text = (
            "RAG context explains retrieval augmented generation, model "
            "embeddings, and vector databases."
        )
        (formatted / "Unrelated Guide_structured.txt").write_text(
            unrelated_text,
            encoding="utf-8",
        )

        class Provider:
            prompt = ""

            def generate(self, prompt):
                self.prompt = prompt
                return "Generated lesson content."

        provider = Provider()

        result = generate_document(
            "Course",
            "CM-01: Customer Service",
            1,
            "lesson_plans",
            "Use the supplied context: {context}",
            provider,
        )

        self.assertEqual(result, "Generated lesson content.")
        self.assertIn(source_text, provider.prompt)
        self.assertNotIn(unrelated_text, provider.prompt)
        self.assertIn("Create original content", provider.prompt)

    def test_generation_stops_when_uploaded_source_has_no_relevant_content(self):
        project = self.project_path()
        (project / "knowledge").mkdir()
        (project / "knowledge" / "guide.json").write_text(
            json.dumps(
                {
                    "document": "Guide.docx",
                    "module": {"code": "CM-01", "title": "Customer Service"},
                    "knowledge_topics": [
                        {
                            "code": "CM-01-KT01",
                            "title": "Complaint Resolution",
                            "knowledge_items": [
                                {
                                    "code": "KT0101",
                                    "description": (
                                        "Confirm the complaint and agree on "
                                        "a fair resolution."
                                    ),
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        formatted = project / "formatted"
        formatted.mkdir()
        (formatted / "Guide_structured.txt").write_text(
            "Vector databases store embeddings for semantic retrieval.",
            encoding="utf-8",
        )

        class Provider:
            called = False

            def generate(self, prompt):
                self.called = True
                return "Should not be generated."

        provider = Provider()

        with self.assertRaisesRegex(
            ValueError,
            "No relevant uploaded source material",
        ):
            generate_document(
                "Course",
                "Complaint Resolution",
                1,
                "lesson_plans",
                "Use the supplied context: {context}",
                provider,
            )

        self.assertFalse(provider.called)

    def test_unresolved_module_fails_with_available_module_names(self):
        project = self.project_path()
        (project / "knowledge").mkdir()
        (project / "knowledge" / "legacy.json").write_text(
            json.dumps(
                {
                    "document": "Guide.docx",
                    "modules": ["Retail Operations"],
                    "source_text": "Retail operations include stock and sales.",
                }
            ),
            encoding="utf-8",
        )

        class Provider:
            def generate(self, prompt):
                raise AssertionError("Provider must not be called")

        with self.assertRaisesRegex(ValueError, "Retail Operations"):
            generate_document(
                "Course",
                "Unknown module",
                1,
                "lesson_plans",
                "{context}",
                Provider(),
            )

    def test_large_source_sections_are_bounded_without_dropping_tail(self):
        source_text = "\n".join(
            [f"Section {number}: " + ("course material " * 400) for number in range(8)]
        )

        chunks = chunk_document(source_text, max_chars=5000)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk["content"]) <= 5000 for chunk in chunks))
        self.assertIn("Section 7", "\n".join(chunk["content"] for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
