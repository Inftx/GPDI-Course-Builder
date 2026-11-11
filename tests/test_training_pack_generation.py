from unittest.mock import patch

from services.generators.training_pack_generator import generate_training_pack


def test_training_pack_forwards_generation_options_to_every_document():
    provider = object()
    options = {
        "audience": "New retail business owners",
        "teaching_style": "Practical",
        "detail_level": "Detailed",
        "knowledge_topic_id": "KM-01-KT02",
    }

    with (
        patch(
            "services.generators.training_pack_generator.generate_lesson_plan",
            return_value="lesson",
        ) as lesson_plan,
        patch(
            "services.generators.training_pack_generator.generate_facilitator_guide",
            return_value="guide",
        ) as facilitator_guide,
        patch(
            "services.generators.training_pack_generator.generate_teaching_script",
            return_value="script",
        ) as teaching_script,
        patch(
            "services.generators.training_pack_generator.generate_assessment",
            return_value="assessment",
        ) as assessment,
    ):
        result = generate_training_pack(
            "Course",
            "Retail",
            2,
            provider,
            **options,
            number_of_questions=6,
            difficulty="Advanced",
        )

    expected_shared_options = {
        "audience": options["audience"],
        "teaching_style": options["teaching_style"],
        "detail_level": options["detail_level"],
        "knowledge_topic_id": options["knowledge_topic_id"],
    }
    lesson_plan.assert_called_once_with(
        "Course",
        "Retail",
        2,
        provider,
        **expected_shared_options,
    )
    facilitator_guide.assert_called_once_with(
        "Course",
        "Retail",
        2,
        provider,
        **expected_shared_options,
    )
    teaching_script.assert_called_once_with(
        "Course",
        "Retail",
        2,
        provider,
        **expected_shared_options,
    )
    assessment.assert_called_once_with(
        "Course",
        "Retail",
        6,
        "Advanced",
        provider,
        **expected_shared_options,
    )
    assert result["assessment"] == "assessment"
