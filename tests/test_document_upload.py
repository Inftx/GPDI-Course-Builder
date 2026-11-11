import io
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from modules.course_builder import build_course
from modules.metadata_manager import save_document_metadata
from services.document_upload import process_uploaded_documents


class UploadedText(io.BytesIO):
    def __init__(self, filename, content):
        super().__init__(content)
        self.name = filename


class DocumentUploadTests(unittest.TestCase):
    def setUp(self):
        self.repository = Path.cwd()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.original_directory = Path.cwd()
        self.addCleanup(self.temporary_directory.cleanup)
        self.addCleanup(os.chdir, self.original_directory)
        os.chdir(self.root)
        self.project = "Course"
        (self.root / "projects" / self.project).mkdir(parents=True)

    def test_multiple_documents_are_processed_as_a_batch(self):
        first = UploadedText(
            "First Guide.txt",
            b"Retail planning includes budgeting and inventory control.",
        )
        second = UploadedText(
            "Second Guide.txt",
            b"Customer service includes listening and resolving complaints.",
        )

        results = process_uploaded_documents([first, second], self.project)

        self.assertEqual([result.status for result in results], ["success", "success"])
        self.assertTrue(
            (
                self.root
                / "projects"
                / self.project
                / "knowledge"
                / "First Guide.json"
            ).exists()
        )
        self.assertTrue(
            (
                self.root
                / "projects"
                / self.project
                / "knowledge"
                / "Second Guide.json"
            ).exists()
        )

    def test_uploaded_knowledge_schema_builds_course_end_to_end(self):
        uploaded_text = (
            "KM-01\n"
            "KM-01-KT01: Business Registration\n"
            "KT0101 Register the business with the appropriate authority."
        )
        original_document = UploadedText(
            "Business Guide.txt",
            uploaded_text.encode("utf-8"),
        )

        results = process_uploaded_documents([original_document], self.project)

        self.assertEqual(results[0].status, "success", results[0].message)
        knowledge_path = (
            self.root
            / "projects"
            / self.project
            / "knowledge"
            / "Business Guide.json"
        )
        knowledge = json.loads(knowledge_path.read_text(encoding="utf-8"))
        self.assertEqual(knowledge["document"], "Business Guide.txt")
        self.assertEqual(knowledge["modules"], ["KM-01: Knowledge Module"])
        self.assertEqual(
            knowledge["knowledge_topics"][0]["knowledge_items"][0]["description"],
            "Register the business with the appropriate authority.",
        )

        with patch("modules.course_builder.save_index"):
            course = build_course(self.project)

        self.assertEqual(course["project"], self.project)
        self.assertIn("Business Guide.txt", course["documents"])
        self.assertIn("KM-01: Knowledge Module", course["modules"])
        self.assertEqual(
            course["knowledge_topics"],
            knowledge["knowledge_topics"],
        )
        self.assertTrue(
            any(
                source["content"].strip() == uploaded_text
                for source in course["source_documents"]
            )
        )
        self.assertEqual(
            (
                self.root
                / "projects"
                / self.project
                / "documents"
                / "Business Guide.txt"
            ).read_bytes(),
            uploaded_text.encode("utf-8"),
        )
        metadata = json.loads(
            (
                self.root
                / "projects"
                / self.project
                / "metadata"
                / "Business Guide.txt.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(metadata["filename"], "Business Guide.txt")
        self.assertEqual(
            metadata["content_hash"],
            hashlib.sha256(uploaded_text.encode("utf-8")).hexdigest(),
        )

    def test_failure_is_reported_per_document_without_stopping_the_batch(self):
        valid = UploadedText("Valid.txt", b"Valid training content.")
        invalid = UploadedText("Unsupported.bin", b"Unsupported file content.")

        results = process_uploaded_documents([valid, invalid], self.project)

        self.assertEqual([result.status for result in results], ["success", "failure"])
        self.assertIn("Unsupported file type", results[1].message)
        self.assertEqual(
            (self.root / "projects" / self.project / "documents" / "Unsupported.bin")
            .read_bytes(),
            b"Unsupported file content.",
        )

    def test_duplicate_names_use_new_paths_and_preserve_existing_documents(self):
        documents = self.root / "projects" / self.project / "documents"
        documents.mkdir()
        original = b"existing educational source material"
        (documents / "Guide.txt").write_bytes(original)
        first = UploadedText("Guide.txt", b"First new guide content.")
        second = UploadedText("Guide.txt", b"Second new guide content.")

        results = process_uploaded_documents([first, second], self.project)

        self.assertEqual([result.status for result in results], ["success", "success"])
        self.assertEqual(results[0].filename, "Guide (1).txt")
        self.assertEqual(results[1].filename, "Guide (2).txt")
        self.assertEqual((documents / "Guide.txt").read_bytes(), original)
        self.assertEqual(
            (documents / "Guide (1).txt").read_bytes(),
            b"First new guide content.",
        )
        self.assertEqual(
            (documents / "Guide (2).txt").read_bytes(),
            b"Second new guide content.",
        )

    def test_repeated_submission_of_identical_file_is_skipped(self):
        attempted = set()
        first = UploadedText("Guide.txt", b"Same content.")
        results = process_uploaded_documents([first], self.project, attempted)
        repeated = UploadedText("Guide.txt", b"Same content.")

        second_results = process_uploaded_documents(
            [repeated],
            self.project,
            attempted,
        )

        self.assertEqual(results[0].status, "success")
        self.assertEqual(second_results[0].status, "duplicate")
        documents = self.root / "projects" / self.project / "documents"
        self.assertEqual(sorted(path.name for path in documents.iterdir()), ["Guide.txt"])

    def test_identical_file_with_different_name_is_skipped_across_submissions(self):
        first = UploadedText("Guide.txt", b"Same course document content.")
        first_results = process_uploaded_documents([first], self.project)

        renamed = UploadedText("Renamed Guide.txt", b"Same course document content.")
        second_results = process_uploaded_documents([renamed], self.project)

        documents = self.root / "projects" / self.project / "documents"
        self.assertEqual(first_results[0].status, "success")
        self.assertEqual(second_results[0].status, "duplicate")
        self.assertIn(
            "already been processed successfully",
            second_results[0].message,
        )
        self.assertEqual([path.name for path in documents.iterdir()], ["Guide.txt"])

    def test_saved_document_with_processing_failure_can_be_retried(self):
        attempted = set()
        original_content = b"Retry after OCR failure."
        first = UploadedText("Guide.txt", original_content)
        with patch(
            "services.document_upload.process_document",
            side_effect=RuntimeError("OCR failed"),
        ):
            failed = process_uploaded_documents([first], self.project, attempted)

        self.assertEqual(failed[0].status, "failure")
        self.assertFalse(attempted)

        retry = UploadedText("Guide.txt", original_content)
        succeeded = process_uploaded_documents([retry], self.project, attempted)

        self.assertEqual(succeeded[0].status, "success", succeeded[0].message)
        self.assertIn(
            (self.project, hashlib.sha256(original_content).hexdigest()),
            attempted,
        )
        documents = self.root / "projects" / self.project / "documents"
        self.assertEqual((documents / "Guide.txt").read_bytes(), original_content)
        self.assertEqual((documents / "Guide (1).txt").read_bytes(), original_content)

    def test_metadata_creation_failure_does_not_block_retry(self):
        content = b"Retry after metadata failure."
        calls = 0

        def fail_once_then_save(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("metadata storage unavailable")
            return save_document_metadata(*args, **kwargs)

        with patch(
            "services.document_upload.save_document_metadata",
            side_effect=fail_once_then_save,
        ):
            first = process_uploaded_documents(
                [UploadedText("Guide.txt", content)],
                self.project,
            )
            retry = process_uploaded_documents(
                [UploadedText("Guide.txt", content)],
                self.project,
            )

        self.assertEqual(first[0].status, "failure")
        self.assertEqual(retry[0].status, "success", retry[0].message)
        metadata_folder = self.root / "projects" / self.project / "metadata"
        metadata_records = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in metadata_folder.glob("*.json")
        ]
        self.assertTrue(
            any(record.get("content_hash") for record in metadata_records)
        )

    def test_legacy_metadata_without_hash_does_not_block_processing(self):
        metadata_folder = self.root / "projects" / self.project / "metadata"
        metadata_folder.mkdir()
        (metadata_folder / "Guide.json").write_text(
            json.dumps({"filename": "Guide.txt", "word_count": 3}),
            encoding="utf-8",
        )
        content = b"Previously processed metadata has no hash."

        results = process_uploaded_documents(
            [UploadedText("Guide.txt", content)],
            self.project,
        )

        self.assertEqual(results[0].status, "success", results[0].message)
        self.assertTrue(
            (metadata_folder / "Guide (1).txt.json").exists()
        )

    def test_same_stem_different_extensions_get_distinct_metadata_records(self):
        uploaded = [
            UploadedText("Course Guide.docx", b"word source bytes"),
            UploadedText("Course Guide.pdf", b"pdf source bytes"),
        ]
        processed = {
            "raw": "Course content.",
            "clean": "Course content.",
            "structured": "",
        }
        analysis = {
            "word_count": 2,
            "character_count": 15,
            "estimated_pages": 1,
            "reading_time": 1,
            "headings": [],
            "keywords": [],
        }

        with (
            patch(
                "services.document_upload.process_document",
                return_value=processed,
            ),
            patch(
                "services.document_upload.analyze_document",
                return_value=analysis,
            ),
        ):
            results = process_uploaded_documents(uploaded, self.project)

        self.assertEqual([result.status for result in results], ["success", "success"])
        metadata_folder = self.root / "projects" / self.project / "metadata"
        records = {
            record["filename"]: record
            for path in metadata_folder.glob("*.json")
            for record in [json.loads(path.read_text(encoding="utf-8"))]
        }
        self.assertEqual(
            set(records),
            {"Course Guide.docx", "Course Guide (1).pdf"},
        )
        self.assertEqual(
            {path.name for path in metadata_folder.glob("*.json")},
            {
                "Course Guide.docx.json",
                "Course Guide (1).pdf.json",
            },
        )

    def test_interrupted_metadata_write_leaves_no_partial_record_and_can_retry(self):
        content = b"Retry after interrupted metadata write."

        def partial_write_then_fail(metadata, file, indent):
            file.write("{")
            raise OSError("simulated interruption during metadata write")

        with patch(
            "modules.metadata_manager.json.dump",
            side_effect=partial_write_then_fail,
        ):
            first = process_uploaded_documents(
                [UploadedText("Guide.txt", content)],
                self.project,
            )

        metadata_folder = self.root / "projects" / self.project / "metadata"
        self.assertEqual(first[0].status, "failure")
        self.assertFalse(list(metadata_folder.glob("*.json")))
        self.assertFalse(list(metadata_folder.glob(".document-metadata-*.tmp")))
        original_source = (
            self.root / "projects" / self.project / "documents" / "Guide.txt"
        )
        self.assertEqual(original_source.read_bytes(), content)
        project_path = self.root / "projects" / self.project
        existing_outputs = {
            path: path.read_bytes()
            for folder in ("documents", "extracted_text", "formatted", "knowledge")
            for path in (project_path / folder).glob("*")
            if path.is_file()
        }

        retry = process_uploaded_documents(
            [UploadedText("Guide.txt", content)],
            self.project,
        )

        self.assertEqual(retry[0].status, "success", retry[0].message)
        retry_source = (
            self.root / "projects" / self.project / "documents" / "Guide (1).txt"
        )
        self.assertEqual(retry_source.read_bytes(), content)
        self.assertEqual(original_source.read_bytes(), content)
        self.assertTrue((metadata_folder / "Guide (1).txt.json").exists())
        for path, original_bytes in existing_outputs.items():
            self.assertEqual(path.read_bytes(), original_bytes)

    def test_metadata_collision_refuses_overwrite_and_cleans_temporary_file(self):
        metadata_folder = (
            self.root / "projects" / self.project / "metadata"
        )
        metadata_folder.mkdir()
        destination = metadata_folder / "Guide.txt.json"
        original = b'{"filename": "existing"}'
        destination.write_bytes(original)
        analysis = {
            "word_count": 1,
            "character_count": 4,
            "estimated_pages": 1,
            "reading_time": 1,
            "headings": [],
            "keywords": [],
        }

        with self.assertRaisesRegex(FileExistsError, "refusing to overwrite"):
            save_document_metadata(
                self.project,
                "Guide.txt",
                analysis,
                content_hash="new-hash",
            )

        self.assertEqual(destination.read_bytes(), original)
        self.assertFalse(list(metadata_folder.glob(".document-metadata-*.tmp")))

    def test_legacy_and_full_filename_metadata_paths_block_source_overwrite(self):
        project_path = self.root / "projects" / self.project
        metadata_folder = project_path / "metadata"
        metadata_folder.mkdir()
        (metadata_folder / "Legacy Guide.json").write_text(
            '{"filename":"Legacy Guide.docx"}',
            encoding="utf-8",
        )
        (metadata_folder / "Current Guide.pdf.json").write_text(
            '{"filename":"Current Guide.pdf"}',
            encoding="utf-8",
        )

        from modules.file_manager import _upload_outputs_exist

        self.assertTrue(_upload_outputs_exist(project_path, "Legacy Guide.docx"))
        self.assertTrue(_upload_outputs_exist(project_path, "Current Guide.pdf"))

    def test_upload_page_waits_for_submit_and_processes_multiple_files(self):
        page = next((self.repository / "pages").glob("2_*_Upload_Documents.py"))
        app = AppTest.from_file(page, default_timeout=20)
        app.session_state["current_project"] = self.project
        app.run()

        app.file_uploader[0].set_value(
            [
                ("First.txt", b"First selected course document.", "text/plain"),
                ("Second.txt", b"Second selected course document.", "text/plain"),
                ("Broken.pdf", b"not a valid PDF", "application/pdf"),
            ]
        ).run()
        documents = self.root / "projects" / self.project / "documents"
        self.assertFalse(documents.exists())

        next(
            button
            for button in app.button
            if button.label == "Submit Documents"
        ).click().run()

        self.assertEqual(
            sorted(path.name for path in documents.iterdir()),
            ["Broken.pdf", "First.txt", "Second.txt"],
        )
        self.assertTrue(
            any(
                element.value == "First.txt: Document processed successfully."
                for element in app.success
            )
        )
        self.assertTrue(
            any(
                element.value == "Second.txt: Document processed successfully."
                for element in app.success
            )
        )
        self.assertTrue(
            any(
                "Broken.pdf: Document could not be processed:" in element.value
                for element in app.error
            )
        )
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
