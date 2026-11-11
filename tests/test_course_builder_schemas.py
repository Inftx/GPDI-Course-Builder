
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules.ai_engine import AILecturer
from modules.course_builder import build_course
from streamlit.testing.v1 import AppTest


class CourseBuilderSchemaTests(unittest.TestCase):

    def setUp(self):
        self.repository = Path.cwd()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)

        self.root = Path(self.temporary_directory.name)
        self.original_directory = Path.cwd()
        self.addCleanup(os.chdir, self.original_directory)

        os.chdir(self.root)
        (self.root / "projects").mkdir()

        self.index_patcher = patch(
            "modules.course_builder.build_index",
            return_value=[],
        )

        self.save_index_patcher = patch(
            "modules.course_builder.save_index"
        )

        self.index_patcher.start()
        self.addCleanup(self.index_patcher.stop)

        self.save_index_patcher.start()
        self.addCleanup(self.save_index_patcher.stop)

    def project_path(self):
        project = self.root / "projects" / "Course"

        (project / "knowledge").mkdir(
            parents=True,
            exist_ok=True,
        )

        return project

    def write_knowledge(self, filename, knowledge):
        path = self.project_path() / "knowledge" / filename

        path.write_text(
            json.dumps(knowledge),
            encoding="utf-8",
        )

        return path

    def test_legacy_modules_schema_is_normalized_and_retained(self):

        self.write_knowledge(
            "legacy.json",
            {
                "document": "Legacy Guide.docx",
                "modules": [
                    "Retail Operations",
                    "Business Planning",
                ],
                "learning_outcomes": [
                    "Explain retail operations.",
                ],
                "assessment_criteria": [
                    "Identify retail processes.",
                ],
                "source_reference": {
                    "page": 12,
                    "citation": "Legacy Guide, p. 12",
                },
            },
        )

        course = build_course("Course")

        self.assertEqual(
            course["modules"],
            [
                "Retail Operations",
                "Business Planning",
            ],
        )

        self.assertEqual(
            course["learning_outcomes"],
            ["Explain retail operations."],
        )

        self.assertEqual(
            course["assessment_criteria"],
            ["Identify retail processes."],
        )

        self.assertEqual(
            course["source_references"],
            [
                {
                    "page": 12,
                    "citation": "Legacy Guide, p. 12",
                }
            ],
        )

    def test_current_module_and_knowledge_topics_are_normalized(self):

        self.write_knowledge(
            "current.json",
            {
                "document": "Current Guide.docx",
                "module": {
                    "code": "KM-01",
                    "title": "Knowledge Module",
                },
                "knowledge_topics": [
                    {
                        "code": "KM-01-KT01",
                        "title": "Business Registration",
                        "knowledge_items": [
                            {
                                "code": "KT0101",
                                "description": "Register the business.",
                            }
                        ],
                    }
                ],
            },
        )

        course = build_course("Course")

        self.assertIn(
            "KM-01: Knowledge Module",
            course["modules"],
        )

        self.assertEqual(
            course["module_records"],
            [
                {
                    "document": "Current Guide.docx",
                    "code": "KM-01",
                    "title": "Knowledge Module",
                }
            ],
        )

        self.assertEqual(
            course["knowledge_topics"][0]["knowledge_items"][0]["description"],
            "Register the business.",
        )

    def test_course_builder_page_handles_current_record_without_modules_key(self):

        project = self.project_path()

        (project / "course.json").write_text(
            json.dumps(
                {
                    "project": "Course",
                    "documents": ["Current Guide.docx"],
                }
            ),
            encoding="utf-8",
        )

        self.write_knowledge(
            "current.json",
            {
                "document": "Current Guide.docx",
                "module": {
                    "code": "KM-01",
                    "title": "Knowledge Module",
                },
                "knowledge_topics": [
                    {
                        "code": "KM-01-KT01",
                        "title": "Business",
                    }
                ],
            },
        )

        page = next(
            (self.repository / "pages").glob(
                "3_*_Course_Builder.py"
            )
        )

        app = AppTest.from_file(
            page,
            default_timeout=20,
        )

        app.session_state["current_project"] = "Course"
        app.run()

        app.button[0].click().run()

        self.assertFalse(app.exception)

        self.assertTrue(
            any(
                item.value == "Course knowledge successfully built."
                for item in app.success
            )
        )

        self.assertIn(
            "KM-01: Knowledge Module",
            build_course("Course")["modules"],
        )

    def test_ai_engine_handles_course_without_modules_key(self):

        prompt = AILecturer(
            {
                "project": "Course",
                "documents": [],
            }
        ).generate_prompt("Create course material.")

        self.assertIn(
            "MODULES:\n0",
            prompt,
        )

    def test_missing_optional_fields_and_empty_records_are_safe(self):

        self.write_knowledge(
            "empty.json",
            {},
        )

        self.write_knowledge(
            "minimal.json",
            {
                "document": "Minimal Guide.docx",
                "module": {
                    "code": None,
                    "title": None,
                },
                "modules": [],
                "knowledge_topics": [],
            },
        )

        course = build_course("Course")

        self.assertEqual(
            course["documents"],
            [
                "empty",
                "Minimal Guide.docx",
            ],
        )

        for field in (
            "modules",
            "knowledge_topics",
            "learning_outcomes",
            "assessment_criteria",
            "knowledge_requirements",
            "practical_activities",
            "workplace_activities",
            "source_references",
        ):
            self.assertEqual(
                course[field],
                [],
            )

    def test_multiple_documents_with_different_schemas_are_combined(self):

        self.write_knowledge(
            "legacy.json",
            {
                "document": "Legacy Guide.docx",
                "modules": ["Legacy Module"],
                "knowledge_topics": [
                    {"title": "Legacy Topic"},
                ],
            },
        )

        self.write_knowledge(
            "current.json",
            {
                "document": "Current Guide.docx",
                "module": {
                    "code": "KM-02",
                    "title": "Current Module",
                },
                "knowledge_topics": [
                    {"title": "Current Topic"},
                ],
                "learning_outcomes": [
                    "Describe the current module.",
                ],
            },
        )

        course = build_course("Course")

        self.assertEqual(
            course["documents"],
            [
                "Current Guide.docx",
                "Legacy Guide.docx",
            ],
        )

        self.assertIn(
            "Legacy Module",
            course["modules"],
        )

        self.assertIn(
            "KM-02: Current Module",
            course["modules"],
        )

        self.assertEqual(
            [
                topic["title"]
                for topic in course["knowledge_topics"]
            ],
            [
                "Current Topic",
                "Legacy Topic",
            ],
        )

    def test_rebuild_keeps_existing_topics_and_adds_new_processed_document(self):

        project = self.project_path()

        original = b"original educational source material"

        (project / "documents").mkdir()

        (project / "documents" / "New Guide.docx").write_bytes(
            original
        )

        existing_topic = {
            "code": "KT-OLD",
            "title": "Previously built topic",
        }

        (project / "course.json").write_text(
            json.dumps(
                {
                    "project": "Course",
                    "knowledge_topics": [existing_topic],
                    "source_references": [
                        {"citation": "Existing citation"},
                    ],
                }
            ),
            encoding="utf-8",
        )

        self.write_knowledge(
            "new.json",
            {
                "document": "New Guide.docx",
                "module": {
                    "code": "KM-03",
                    "title": "New Module",
                },
                "knowledge_topics": [
                    {
                        "code": "KT-NEW",
                        "title": "New topic",
                    }
                ],
            },
        )

        formatted = project / "formatted"
        formatted.mkdir()

        (formatted / "New Guide_structured.txt").write_text(
            "Newly uploaded training material.",
            encoding="utf-8",
        )

        course = build_course("Course")

        self.assertEqual(
            course["knowledge_topics"],
            [
                existing_topic,
                {
                    "code": "KT-NEW",
                    "title": "New topic",
                },
            ],
        )

        self.assertIn(
            "New Guide.docx",
            course["documents"],
        )

        self.assertNotIn(
            "New Guide",
            course["documents"],
        )

        self.assertEqual(
            len(course["source_documents"]),
            1,
        )

        self.assertIn(
            "Newly uploaded training material.",
            [
                source["content"]
                for source in course["source_documents"]
            ],
        )

        self.assertEqual(
            (project / "documents" / "New Guide.docx").read_bytes(),
            original,
        )

    def test_invalid_knowledge_json_reports_its_filename(self):

        project = self.project_path()

        (project / "knowledge" / "broken.json").write_text(
            "{",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ValueError,
            "broken.json",
        ):
            build_course("Course")

    def test_repeated_builds_are_idempotent(self):

        self.write_knowledge(
            "course_material.json",
            {
                "document": "Course Material.docx",
                "modules": [
                    "Module One",
                    "Module Two",
                ],
                "knowledge_topics": [
                    {"code": "KT01", "title": "Topic One"},
                    {"code": "KT02", "title": "Topic Two"},
                ],
                "learning_outcomes": [
                    "Explain concept one.",
                    "Explain concept two.",
                ],
                "assessment_criteria": [
                    "Identify concept one.",
                    "Identify concept two.",
                ],
                "knowledge_requirements": [
                    "Knowledge requirement one.",
                ],
                "practical_activities": [
                    "Practical activity one.",
                ],
                "workplace_activities": [
                    "Workplace activity one.",
                ],
                "source_references": [
                    {"citation": "Reference One"},
                    {"citation": "Reference Two"},
                ],
                "warnings": [
                    "Warning one.",
                ],
            },
        )

        first_result = build_course("Course")

        first_snapshot = json.loads(
            (
                self.project_path() / "course.json"
            ).read_text(encoding="utf-8")
        )

        second_result = build_course("Course")

        second_snapshot = json.loads(
            (
                self.project_path() / "course.json"
            ).read_text(encoding="utf-8")
        )

        third_result = build_course("Course")

        third_snapshot = json.loads(
            (
                self.project_path() / "course.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(first_result, second_result)
        self.assertEqual(second_result, third_result)

        self.assertEqual(first_snapshot, second_snapshot)
        self.assertEqual(second_snapshot, third_snapshot)

        self.assertEqual(
            len(third_result["learning_outcomes"]),
            2,
        )

        self.assertEqual(
            len(third_result["assessment_criteria"]),
            2,
        )

        self.assertEqual(
            len(third_result["source_references"]),
            2,
        )

    def test_existing_exact_duplicates_are_cleaned_without_losing_distinct_entries(self):

        project = self.project_path()

        existing_course = {
            "project": "Course",
            "learning_outcomes": [
                "Explain concept one.",
                "Explain concept one.",
                "Explain concept two.",
            ],
            "assessment_criteria": [
                "Identify concept one.",
                "Identify concept one.",
            ],
            "knowledge_requirements": [
                "Requirement one.",
                "Requirement one.",
            ],
            "practical_activities": [
                "Activity one.",
                "Activity two.",
            ],
            "workplace_activities": [
                "Workplace activity one.",
                "Workplace activity one.",
            ],
            "source_references": [
                {"citation": "Reference one"},
                {"citation": "Reference one"},
                {"citation": "Reference two"},
            ],
            "warnings": [
                "Warning one.",
                "Warning one.",
            ],
        }

        (project / "course.json").write_text(
            json.dumps(existing_course),
            encoding="utf-8",
        )

        course = build_course("Course")

        self.assertEqual(
            course["learning_outcomes"],
            [
                "Explain concept one.",
                "Explain concept two.",
            ],
        )

        self.assertEqual(
            course["assessment_criteria"],
            ["Identify concept one."],
        )

        self.assertEqual(
            course["knowledge_requirements"],
            ["Requirement one."],
        )

        self.assertEqual(
            course["practical_activities"],
            [
                "Activity one.",
                "Activity two.",
            ],
        )

        self.assertEqual(
            course["workplace_activities"],
            ["Workplace activity one."],
        )

        self.assertEqual(
            course["source_references"],
            [
                {"citation": "Reference one"},
                {"citation": "Reference two"},
            ],
        )

        self.assertEqual(
            course["warnings"],
            ["Warning one."],
        )


if __name__ == "__main__":
    unittest.main()
