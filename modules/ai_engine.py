class AILecturer:

    """
    Core AI Engine.

    Every future AI feature will call this class.
    """

    def __init__(self, course):

        self.course = course

    def generate_prompt(
        self,
        task
    ):

        prompt = f"""

You are an experienced South African QCTO Lecturer.

You are creating educational material.

PROJECT:
{self.course['project']}

DOCUMENTS:
{len(self.course['documents'])}

MODULES:
{len(self.course.get('modules') or [])}

TASK:

{task}

Generate professional educational content.

"""

        return prompt