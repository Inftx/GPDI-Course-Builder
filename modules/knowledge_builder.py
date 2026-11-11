import json
import re
from pathlib import Path


# ---------------------------------------------------------
# NORMALISATION
# ---------------------------------------------------------

def normalize(line):
    """
    Clean whitespace while preserving the actual text.
    """
    return " ".join(line.strip().split())


# ---------------------------------------------------------
# MODULE DETECTION
# ---------------------------------------------------------

def parse_module_code(line):
    """
    Detect a standalone Knowledge Module code.

    Supported examples:
        KM-01
        KM – 01
        KM — 01
        KM 01

    Returns:
        KM-01
        or None
    """

    normalized = normalize(line)

    pattern = re.compile(
        r"^KM\s*(?:-|–|—)?\s*(\d{2})$",
        re.IGNORECASE
    )

    match = pattern.match(normalized)

    if not match:
        return None

    return f"KM-{match.group(1)}"


def is_knowledge_module_heading(line):
    """
    Detect the generic Knowledge Module heading.
    """

    return normalize(line).upper() == "KNOWLEDGE MODULE"


# ---------------------------------------------------------
# KNOWLEDGE TOPIC DETECTION
# ---------------------------------------------------------

def parse_knowledge_topic(line):
    """
    Detect Knowledge Topic headings.

    Examples:
        KM-01-KT01: Legislative Requirements (25%)
        KM-01-KT02: The Business Plan (25%)
    """

    pattern = re.compile(
        r"^(KM-\d{2}-KT\d{2})\s*:\s*(.+?)(?:\s*\(\d+%\))?$",
        re.IGNORECASE
    )

    match = pattern.match(line)

    if not match:
        return None

    code = match.group(1).upper()
    title = match.group(2).strip()

    return {
        "code": code,
        "title": title,
        "description": line,
        "knowledge_items": []
    }


# ---------------------------------------------------------
# KNOWLEDGE ITEM DETECTION
# ---------------------------------------------------------

def parse_knowledge_item(line):
    """
    Detect individual knowledge items.

    Normal format:
        KT0101
        KT0205
        KT0407

    The parser also accepts unusual five-digit codes such as:
        KT03110

    Unusual codes are preserved and reported as warnings.
    """

    pattern = re.compile(
        r"^(KT\d{4,5})\s+(.+)$",
        re.IGNORECASE
    )

    match = pattern.match(line)

    if not match:
        return None

    code = match.group(1).upper()
    description = match.group(2).strip()

    return {
        "code": code,
        "description": description
    }


# ---------------------------------------------------------
# BUILD KNOWLEDGE STRUCTURE
# ---------------------------------------------------------

def build_knowledge(
    structured_text,
    original_filename,
    project_name
):

    knowledge = {
        "document": original_filename,

        "module": {
            "code": None,
            "title": None
        },

        "modules": [],

        "knowledge_topics": [],

        "learning_outcomes": [],
        "assessment_criteria": [],
        "knowledge_requirements": [],
        "practical_activities": [],
        "workplace_activities": [],

        "warnings": []
    }

    current_topic = None

    # Track warnings so the same warning is only reported once.
    warning_set = set()

    # Track unusual knowledge codes so each is warned about once.
    unusual_codes = set()

    # -----------------------------------------------------
    # PROCESS DOCUMENT
    # -----------------------------------------------------

    for raw_line in structured_text.splitlines():

        line = normalize(raw_line)

        if not line:
            continue

        # Ignore visual separators
        if set(line) <= {"=", "-", "–", "—"}:
            continue

        # -------------------------------------------------
        # GENERIC KNOWLEDGE MODULE HEADING
        # -------------------------------------------------

        if is_knowledge_module_heading(line):

            continue

        # -------------------------------------------------
        # STANDALONE KM CODE
        # -------------------------------------------------

        module_code = parse_module_code(line)

        if module_code:

            knowledge["module"]["code"] = module_code

            continue

        # -------------------------------------------------
        # KNOWLEDGE TOPIC
        # -------------------------------------------------

        topic = parse_knowledge_topic(line)

        if topic:

            # Prevent duplicate KT headings.
            existing = next(
                (
                    item
                    for item in knowledge["knowledge_topics"]
                    if item["code"] == topic["code"]
                ),
                None
            )

            if existing:

                current_topic = existing

            else:

                knowledge["knowledge_topics"].append(topic)

                current_topic = topic

            continue

        # -------------------------------------------------
        # KNOWLEDGE ITEM
        # -------------------------------------------------

        item = parse_knowledge_item(line)

        if item:

            # Knowledge item before a topic.
            if current_topic is None:

                warning = (
                    "Knowledge item found before a Knowledge Topic: "
                    f"{item['code']}"
                )

                if warning not in warning_set:

                    knowledge["warnings"].append(warning)
                    warning_set.add(warning)

                continue

            # -------------------------------------------------
            # Detect suspicious KT codes
            # -------------------------------------------------

            if len(item["code"]) != 6:

                if item["code"] not in unusual_codes:

                    warning = (
                        "Unusual knowledge code detected: "
                        f"{item['code']}"
                    )

                    knowledge["warnings"].append(warning)

                    warning_set.add(warning)
                    unusual_codes.add(item["code"])

            # -------------------------------------------------
            # Prevent duplicate knowledge items
            # -------------------------------------------------

            existing_codes = {
                x["code"]
                for x in current_topic["knowledge_items"]
            }

            if item["code"] not in existing_codes:

                current_topic["knowledge_items"].append(item)

            continue

    # ---------------------------------------------------------
    # SET MODULE TITLE
    # ---------------------------------------------------------

    if knowledge["knowledge_topics"]:

        knowledge["module"]["title"] = "Knowledge Module"

    module_parts = [
        str(knowledge["module"][key]).strip()
        for key in ("code", "title")
        if knowledge["module"].get(key)
    ]
    if module_parts:
        knowledge["modules"] = [": ".join(module_parts)]

    # ---------------------------------------------------------
    # CHECK FOR EMPTY TOPICS
    # ---------------------------------------------------------

    for topic in knowledge["knowledge_topics"]:

        if not topic["knowledge_items"]:

            warning = (
                f"{topic['code']} contains no knowledge items."
            )

            if warning not in warning_set:

                knowledge["warnings"].append(warning)
                warning_set.add(warning)

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    project_folder = (
        Path("projects") /
        project_name
    )

    knowledge_folder = (
        project_folder /
        "knowledge"
    )

    knowledge_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        knowledge_folder /
        f"{Path(original_filename).stem}.json"
    )

    with output_file.open(
        "x",
        encoding="utf-8"
    ) as file:

        json.dump(
            knowledge,
            file,
            indent=4,
            ensure_ascii=False
        )

    return knowledge