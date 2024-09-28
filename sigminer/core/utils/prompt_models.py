THOUGHT_PROCESS_DESCRIPTION = """
1. Carefully read and analyze the source material.
2. Identify key information relevant to the question.
3. Formulate a clear and concise answer based on the source material.
4. Support your answer with relevant quotes or paraphrases from the source material.
5. Conclude with the answer if it is concise enough.
Be concise.
"""


def get_answer_field_description(meta: str, description: str) -> str:
    return f"This value will be stored in database in the {meta} column. {description}"
