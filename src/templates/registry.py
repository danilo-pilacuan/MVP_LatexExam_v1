from enum import Enum
from pydantic import BaseModel
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent


class TemplateId(str, Enum):
    BASE_EXAM = "base_exam"
    QUIZ_SHORT = "quiz_short"


class ExamTemplate(BaseModel):
    id: TemplateId
    file: str
    description: str
    supports_answer_key: bool = True


TEMPLATE_REGISTRY: dict[TemplateId, ExamTemplate] = {
    TemplateId.BASE_EXAM: ExamTemplate(
        id=TemplateId.BASE_EXAM,
        file="base_exam.tex.jinja",
        description="Examen estándar a una columna, con tabla de calificación y clave de respuestas",
    ),
    TemplateId.QUIZ_SHORT: ExamTemplate(
        id=TemplateId.QUIZ_SHORT,
        file="quiz_short.tex.jinja",
        description="Quiz corto de 1-2 páginas, sin clave de respuestas",
        supports_answer_key=False,
    ),
}


def get_template_path(template_id: TemplateId) -> Path:
    return TEMPLATES_DIR / TEMPLATE_REGISTRY[template_id].file