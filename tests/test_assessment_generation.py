import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.generators import assessment_generator as assessment


def build_mcq(count=10, option_prefix=""):
    questions = []
    for number in range(1, count + 1):
        options = "\n".join(
            f"{option_prefix}{label}) Option {label}"
            for label in "ABCD"
        )
        questions.append(f"{number}. Question {number}?\n{options}")
    return "Section A\n\n" + "\n\n".join(questions)


class AssessmentValidationTests(unittest.TestCase):
    def test_heading_does_not_count_as_question(self):
        content = build_mcq()
        self.assertEqual(len(assessment._split_question_blocks(content)), 10)
        self.assertTrue(assessment._validate_section_a(content, 10))

    def test_markdown_bullet_options_are_accepted(self):
        content = build_mcq(option_prefix="- ")
        self.assertTrue(assessment._validate_section_a(content, 10))

    def test_dot_options_are_accepted(self):
        content = build_mcq().replace(")", ".", 40)
        self.assertTrue(assessment._validate_section_a(content, 10))

    def test_markdown_bullet_dot_options_are_accepted(self):
        content = build_mcq(option_prefix="- ").replace(")", ".", 40)
        self.assertTrue(assessment._validate_section_a(content, 10))

    def test_missing_option_is_rejected(self):
        content = build_mcq().replace("D) Option D\n", "", 1)
        self.assertFalse(assessment._validate_section_a(content, 10))

    def test_duplicate_option_is_rejected(self):
        content = build_mcq().replace("D) Option D", "C) Option D", 1)
        self.assertFalse(assessment._validate_section_a(content, 10))

    def test_additional_e_option_is_rejected(self):
        content = build_mcq().replace(
            "D) Option D",
            "D) Option D\nE) Additional option",
            1,
        )
        self.assertFalse(assessment._validate_section_a(content, 10))

    def test_incorrect_question_count_is_rejected(self):
        self.assertFalse(assessment._validate_section_a(build_mcq(9), 10))
        self.assertFalse(assessment._validate_section_a(build_mcq(11), 10))

    def test_generated_questions_require_source_reference_metadata(self):
        content = build_mcq(1)
        errors = assessment._grounding_reference_errors(
            content,
            "Section A",
            1,
        )
        self.assertEqual(len(errors), 1)
        cited = content.replace(
            "Question 1?",
            "Question 1? [Source: Learner Guide — Business Planning]",
        )
        self.assertEqual(
            assessment._grounding_reference_errors(cited, "Section A", 1),
            [],
        )

    def test_memorandum_requires_corresponding_answer_and_marking_entries(self):
        section_a = "1. Question?\nA) one\nB) two\nC) three\nD) four"
        section_b = "1. Short answer question?"
        section_c = "\n".join(
            f"{number}. Case scenario {number}?"
            for number in range(1, 6)
        )
        memo = (
            "Section A Answer Key\n1. A\n\n"
            "Section B Marking Guide\n1. Award one mark.\n\n"
            "Section C Marking Guide\n"
            + "\n".join(
                f"{number}. Award two marks."
                for number in range(1, 6)
            )
        )
        self.assertEqual(
            assessment._memorandum_errors(memo, section_a, section_b, section_c),
            [],
        )
        invalid_memo = memo.replace("1. A", "2. A", 1)
        self.assertTrue(
            assessment._memorandum_errors(
                invalid_memo,
                section_a,
                section_b,
                section_c,
            )
        )

    def test_retry_prompt_contains_specific_validation_feedback(self):
        responses = iter(["invalid", "valid"])
        prompts = []

        def fake_generate_document(*args, **kwargs):
            prompts.append(args[4])
            return next(responses)

        with patch.object(
            assessment,
            "generate_document",
            side_effect=fake_generate_document,
        ):
            result = assessment._generate_validated_section(
                "project",
                "module",
                "Create content",
                object(),
                lambda text: text == "valid",
                validation_feedback=lambda text: ["Expected four options."],
            )

        self.assertEqual(result, "valid")
        self.assertIn("Expected four options.", prompts[1])

    def test_successful_generation_uses_real_course_text_and_matching_memo(self):
        class FakeProvider:
            def __init__(self):
                self.prompts = []

            def generate(self, prompt):
                self.prompts.append(prompt)
                if "Create Section A" in prompt:
                    return (
                        "Section A\n\n1. What is the role of a business plan? "
                        "[Source: Learner Guide.docx — Document]\n"
                        "A) To guide the business\nB) To record sales\n"
                        "C) To hire staff\nD) To register tax"
                    )
                if "Create Section B" in prompt:
                    return (
                        "Section B\n\n1. Explain the role of a business plan. "
                        "[Source: Learner Guide.docx — Document]"
                    )
                if "Create Section C" in prompt:
                    return "Section C\n\n" + "\n\n".join(
                        f"{number}. Case scenario: a retailer plans growth. "
                        "What should be considered? "
                        "[Source: Learner Guide.docx — Document]"
                        for number in range(1, 6)
                    )
                if "Create Memorandum" in prompt:
                    return (
                        "Section A Answer Key\n1. A\n\n"
                        "Section B Marking Guide\n1. Describes how it guides "
                        "business decisions.\n\n"
                        "Section C Marking Guide\n"
                        + "\n".join(
                            f"{number}. Discuss an appropriate consideration."
                            for number in range(1, 6)
                        )
                    )
                self.fail("Unexpected generation prompt")

        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        original_directory = Path.cwd()
        self.addCleanup(os.chdir, original_directory)
        project = Path(temporary_directory.name) / "projects" / "Course"
        (project / "knowledge").mkdir(parents=True)
        (project / "knowledge" / "legacy.json").write_text(
            (
                '{"document":"Learner Guide.docx",'
                '"module":{"code":"KM-01","title":"Knowledge Module"},'
                '"knowledge_topics":[{"code":"KM-01-KT02",'
                '"title":"The Business Plan","knowledge_items":['
                '{"code":"KT0201","description":"The role of a business '
                'plan in a business."}]}]}'
            ),
            encoding="utf-8",
        )
        (project / "formatted").mkdir()
        source_text = (
            "The Business Plan\n\nThe role of a business plan in a "
            "business is to guide its objectives, decisions and growth."
        )
        (project / "formatted" / "Learner Guide_structured.txt").write_text(
            source_text,
            encoding="utf-8",
        )
        provider = FakeProvider()
        os.chdir(temporary_directory.name)
        result = assessment.generate_assessment(
            "Course",
            "The Business Plan",
            1,
            "Moderate",
            provider,
        )

        self.assertIn(source_text, provider.prompts[0])
        self.assertIn("Do not copy existing questions", provider.prompts[0])
        self.assertIn("GENERATED ASSESSMENT QUESTIONS", provider.prompts[-1])
        self.assertIn("What is the role of a business plan?", provider.prompts[-1])
        self.assertIn("Section A Answer Key\n1. A", result)


if __name__ == "__main__":
    unittest.main()
