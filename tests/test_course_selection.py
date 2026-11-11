import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.generators.base_generator import generate_document
from services.knowledge.course_selection import (
    find_topic_for_module,
    get_course_module_options,
    resolve_module_identifier,
)
from services.workflows import GenerationWizard
from streamlit.testing.v1 import AppTest


def sample_course():
    return {
        "project": "Course",
        "modules": [
            "KM-01: Knowledge Module",
            "PM-02: Practical Module",
        ],
        "module_records": [
            {"code": "KM-01", "title": "Knowledge Module"},
            {"code": "PM-02", "title": "Practical Module"},
        ],
        "knowledge_topics": [
            {
                "code": "KM-01-KT01",
                "title": "Legislative Requirements",
                "knowledge_items": [
                    {"code": "KT0101", "description": "Comply with legislation."}
                ],
            },
            {
                "code": "PM-02-KT03",
                "title": "Retail Activities",
                "knowledge_items": [
                    {"code": "KT0301", "description": "Complete retail activities."}
                ],
            },
        ],
        "source_documents": [
            {
                "name": "Guide.docx",
                "content": "Course source material includes relevant knowledge.",
            }
        ],
        "documents": ["Guide.docx"],
        "learning_outcomes": [],
        "assessment_criteria": [],
        "knowledge_requirements": [],
        "practical_activities": [],
        "workplace_activities": [],
    }


class CourseSelectionTests(unittest.TestCase):
    def test_duplicate_module_records_merge_and_keep_all_matching_topics(self):
        course = sample_course()
        course["module_records"] = [
            {"document": "Guide.docx", "code": "KM-01", "title": None},
            {
                "document": "Guide copy.docx",
                "name": "KM-01: Knowledge Module",
            },
            {"document": "Other.docx", "code": "PM-02", "title": "Practical Module"},
        ]
        course["modules"] = [
            "KM-01",
            "KM-01: Knowledge Module",
            "PM-02: Practical Module",
        ]
        course["knowledge_topics"] = [
            {
                "code": f"KM-01-KT0{index}",
                "title": f"Topic {index}",
                "knowledge_items": [],
            }
            for index in range(1, 5)
        ] + [
            {
                "code": "PM-02-KT01",
                "title": "Practical Topic",
                "knowledge_items": [],
            }
        ]

        modules = get_course_module_options(course)

        self.assertEqual(
            [(module.identifier, module.label) for module in modules],
            [
                ("KM-01", "KM-01: Knowledge Module"),
                ("PM-02", "PM-02: Practical Module"),
            ],
        )
        self.assertEqual(
            [topic.identifier for topic in modules[0].topics],
            [f"KM-01-KT0{index}" for index in range(1, 5)],
        )
        self.assertEqual(
            [topic.identifier for topic in modules[1].topics],
            ["PM-02-KT01"],
        )

    def test_legacy_full_module_label_resolves_to_canonical_identifier(self):
        course = {
            "module_records": [
                {"code": "KM-01", "title": "Knowledge Module"},
                {"name": "KM-01: Knowledge Module"},
            ],
            "knowledge_topics": [
                {"code": "KM-01-KT01", "title": "Legislative Requirements"},
                {"code": "KM-01-KT02", "title": "The Business Plan"},
                {"code": "KM-01-KT03", "title": "Business Factors"},
                {"code": "KM-01-KT04", "title": "Human Resources"},
            ],
        }
        modules = get_course_module_options(course)

        self.assertEqual(len(modules), 1)
        self.assertEqual(
            resolve_module_identifier(modules, "KM-01: Knowledge Module"),
            "KM-01",
        )
        self.assertEqual(
            find_topic_for_module(
                course,
                "KM-01: Knowledge Module",
                "KM-01-KT01",
            )["code"],
            "KM-01-KT01",
        )
        self.assertEqual(len(modules[0].topics), 4)

    def test_module_options_use_codes_and_topics_are_filtered(self):
        options = get_course_module_options(sample_course())

        self.assertEqual(
            [(module.identifier, module.label) for module in options],
            [
                ("KM-01", "KM-01: Knowledge Module"),
                ("PM-02", "PM-02: Practical Module"),
            ],
        )
        self.assertEqual(
            [topic.identifier for topic in options[0].topics],
            ["KM-01-KT01"],
        )
        self.assertEqual(
            [topic.identifier for topic in options[1].topics],
            ["PM-02-KT03"],
        )

    def test_legacy_module_names_and_unlinked_topics_remain_selectable(self):
        options = get_course_module_options(
            {
                "modules": ["Retail Operations"],
                "knowledge_topics": ["Stock Management"],
            }
        )

        self.assertEqual(options[0].identifier, "Retail Operations")
        self.assertEqual(options[0].topics[0].identifier, "Stock Management")

    def test_course_without_modules_has_no_selectable_modules(self):
        self.assertEqual(
            get_course_module_options(
                {"knowledge_topics": [{"code": "KM-01-KT01", "title": "Topic"}]}
            ),
            [],
        )

    def test_invalid_topic_does_not_resolve_for_another_module(self):
        course = sample_course()
        self.assertIsNone(
            find_topic_for_module(course, "KM-01", "PM-02-KT03")
        )
        self.assertIsNotNone(
            find_topic_for_module(course, "KM-01", "KM-01-KT01")
        )

    def test_explicit_topic_module_reference_takes_precedence_over_code_prefix(self):
        course = {
            "modules": ["KM-01: Knowledge Module"],
            "knowledge_topics": [
                {
                    "code": "KM-01-KT01",
                    "module_code": "UNKNOWN",
                    "title": "Unlinked Topic",
                }
            ],
        }

        self.assertEqual(get_course_module_options(course)[0].topics, [])

    def test_backend_accepts_identifiers_and_applies_selected_topic(self):
        course = sample_course()

        class Provider:
            prompt = ""

            def generate(self, prompt):
                self.prompt = prompt
                return "generated"

        provider = Provider()
        with (
            patch(
                "services.generators.base_generator._load_course_knowledge",
                return_value=course,
            ),
            patch(
                "services.generators.base_generator.chunk_document",
                return_value=[{"title": "Course", "content": "course knowledge"}],
            ),
            patch(
                "services.generators.base_generator.build_index",
                return_value=[{"id": 1, "title": "Guide.docx — Course", "content": (
                    "Course source material includes relevant knowledge."
                )}],
            ),
            patch(
                "services.generators.base_generator.search_index",
                return_value=[{
                    "id": 1,
                    "title": "Guide.docx — Course",
                    "content": "Course source material includes relevant knowledge.",
                }],
            ),
            patch(
                "services.generators.base_generator.retrieve_context",
                return_value="Course source material includes relevant knowledge.",
            ),
            patch(
                "services.generators.base_generator.save_output"
            ) as save_output_mock,
        ):
            result = generate_document(
                "Course",
                "KM-01",
                1,
                "lesson_plans",
                "{context}\nModule: {module_name}",
                provider,
                knowledge_topic_id="KM-01-KT01",
            )
            unsaved_result = generate_document(
                "Course",
                "KM-01",
                1,
                "lesson_plans",
                "{context}\nModule: {module_name}",
                provider,
                knowledge_topic_id="KM-01-KT01",
                save_result=False,
            )

        self.assertEqual(result, "generated")
        self.assertEqual(unsaved_result, "generated")
        save_output_mock.assert_called_once_with(
            "Course", "lesson_plans", "generated"
        )
        self.assertIn("Module: KM-01: Knowledge Module", provider.prompt)
        self.assertIn("KM-01-KT01: Legislative Requirements", provider.prompt)
        self.assertIn("Comply with legislation.", provider.prompt)

    def test_backend_rejects_topic_not_belonging_to_selected_module(self):
        with patch(
            "services.generators.base_generator._load_course_knowledge",
            return_value=sample_course(),
        ):
            with self.assertRaisesRegex(ValueError, "not available for module"):
                generate_document(
                    "Course",
                    "KM-01",
                    1,
                    "lesson_plans",
                    "{context}",
                    object(),
                    knowledge_topic_id="PM-02-KT03",
                )

    def test_ai_workspace_dropdowns_follow_module_selection(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        original_directory = Path.cwd()
        self.addCleanup(os.chdir, original_directory)
        root = Path(temporary_directory.name)
        project = root / "projects" / "Course"
        project.mkdir(parents=True)
        (project / "course.json").write_text(
            json.dumps(sample_course()),
            encoding="utf-8",
        )
        os.chdir(root)

        wizard = GenerationWizard()
        wizard.set_project("Course")
        wizard.go_to_step(2)
        app = AppTest.from_file(
            Path(__file__).parents[1] / "pages" / "4_🤖_AI_Workspace.py",
            default_timeout=20,
        )
        app.session_state["generation_wizard"] = wizard

        with patch(
            "services.ai.provider_manager.ProviderManager.get_provider",
            return_value=object(),
        ):
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox[0].label, "Select Module")
            self.assertEqual(
                app.selectbox[0].options,
                ["KM-01: Knowledge Module", "PM-02: Practical Module"],
            )
            self.assertEqual(app.selectbox[0].value, "KM-01")
            self.assertEqual(
                app.selectbox[1].options,
                ["KM-01-KT01: Legislative Requirements"],
            )
            self.assertEqual(app.selectbox[1].value, "KM-01-KT01")

            app.selectbox[0].set_value("PM-02").run()

        self.assertFalse(app.exception)
        self.assertEqual(
            app.selectbox[1].options,
            ["PM-02-KT03: Retail Activities"],
        )
        self.assertEqual(app.selectbox[0].value, "PM-02")
        self.assertEqual(app.selectbox[1].value, "PM-02-KT03")

    def test_ai_workspace_resolves_legacy_module_state_to_canonical_id(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        original_directory = Path.cwd()
        self.addCleanup(os.chdir, original_directory)
        root = Path(temporary_directory.name)
        project = root / "projects" / "Course"
        project.mkdir(parents=True)
        course = sample_course()
        course["module_records"] = [
            {"code": "KM-01", "title": "Knowledge Module"},
            {"name": "KM-01: Knowledge Module"},
        ]
        course["modules"] = ["KM-01", "KM-01: Knowledge Module"]
        (project / "course.json").write_text(json.dumps(course), encoding="utf-8")
        os.chdir(root)

        wizard = GenerationWizard()
        wizard.set_project("Course")
        wizard.set_module("KM-01: Knowledge Module")
        wizard.go_to_step(2)
        app = AppTest.from_file(
            Path(__file__).parents[1] / "pages" / "4_🤖_AI_Workspace.py",
            default_timeout=20,
        )
        app.session_state["generation_wizard"] = wizard

        with patch(
            "services.ai.provider_manager.ProviderManager.get_provider",
            return_value=object(),
        ):
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox[0].value, "KM-01")
            self.assertEqual(
                app.selectbox[1].options,
                [
                    "KM-01-KT01: Legislative Requirements",
                ],
            )
            app.button[-1].click().run()

        self.assertFalse(app.exception)
        self.assertEqual(wizard.get_state().module, "KM-01")

    def test_ai_workspace_directs_lecturer_to_build_empty_knowledge_base(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        original_directory = Path.cwd()
        self.addCleanup(os.chdir, original_directory)
        root = Path(temporary_directory.name)
        project = root / "projects" / "Course"
        project.mkdir(parents=True)
        (project / "course.json").write_text(
            json.dumps({"project": "Course", "modules": [], "knowledge_topics": []}),
            encoding="utf-8",
        )
        os.chdir(root)

        wizard = GenerationWizard()
        wizard.set_project("Course")
        wizard.go_to_step(2)
        app = AppTest.from_file(
            Path(__file__).parents[1] / "pages" / "4_🤖_AI_Workspace.py",
            default_timeout=20,
        )
        app.session_state["generation_wizard"] = wizard
        app.run()

        self.assertFalse(app.exception)
        self.assertTrue(
            any("Build the Course Knowledge Base" in item.value for item in app.warning)
        )
        self.assertEqual(len(app.selectbox), 0)

    def test_module_without_topics_cannot_advance(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        original_directory = Path.cwd()
        self.addCleanup(os.chdir, original_directory)
        root = Path(temporary_directory.name)
        project = root / "projects" / "Course"
        project.mkdir(parents=True)
        (project / "course.json").write_text(
            json.dumps(
                {
                    "project": "Course",
                    "modules": ["Retail Operations"],
                    "knowledge_topics": [],
                }
            ),
            encoding="utf-8",
        )
        os.chdir(root)

        wizard = GenerationWizard()
        wizard.set_project("Course")
        wizard.go_to_step(2)
        app = AppTest.from_file(
            Path(__file__).parents[1] / "pages" / "4_🤖_AI_Workspace.py",
            default_timeout=20,
        )
        app.session_state["generation_wizard"] = wizard

        with patch(
            "services.ai.provider_manager.ProviderManager.get_provider",
            return_value=object(),
        ):
            app.run()
            self.assertFalse(app.exception)
            self.assertTrue(
                any("No processed knowledge topics" in item.value for item in app.info)
            )
            app.button[-1].click().run()

        self.assertFalse(app.exception)
        self.assertEqual(wizard.get_state().step, 2)
        self.assertTrue(
            any("no selectable processed knowledge topics" in item.value for item in app.warning)
        )


if __name__ == "__main__":
    unittest.main()
