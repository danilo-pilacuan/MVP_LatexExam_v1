from jinja2 import Environment, FileSystemLoader
from src.schemas.exam import GeneratedItem, QuestionType, CompiledExam
from src.templates.registry import get_template_path, TemplateId

LATEX_SPECIAL_CHARS = {
    "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}

def escape_latex(text: str) -> str:
    for char, repl in LATEX_SPECIAL_CHARS.items():
        text = text.replace(char, repl)
    return text


def render_item(item: GeneratedItem) -> str:
    statement = escape_latex(item.statement)

    if item.question_type in (QuestionType.OPCION_MULTIPLE, QuestionType.VERDADERO_FALSO):
        choices = "\n".join(
            f"    \\CorrectChoice {escape_latex(o.text)}" if o.is_correct
            else f"    \\choice {escape_latex(o.text)}"
            for o in item.options
        )
        block = (
            f"\\question[{item.points:g}] {statement}\n"
            f"\\begin{{choices}}\n{choices}\n\\end{{choices}}\n"
        )
    else:
        # respuesta_corta / desarrollo
        answer = escape_latex(item.expected_answer)
        solution = escape_latex(item.solution_explanation)
        block = (
            f"\\question[{item.points:g}] {statement}\n"
            f"\\droppoints\n"
            f"\\begin{{answers}}\n{answer}\n\\end{{answers}}\n"
            f"\\begin{{solution}}\n{solution}\n\\end{{solution}}\n"
            f"\\vspace{{2cm}}\n"
        )

    return block

def render_exam(
    exam: CompiledExam,
    template_id: TemplateId,
    subject_name: str,
    instructions: str,
    department: str = "",
    exam_date: str = "",
    exam_time: str = "",
    examiner_name: str = "",
    duration_minutes: int = 90,
    print_answers: bool = True,
) -> str:
    template_path = get_template_path(template_id)
    # Las macros LaTeX \newcommand{...}{#1} contienen '{#', que Jinja
    # interpretaría como inicio de comentario. Cambiamos SOLO el delimitador
    # de comentario a uno sin colisión; los de variable {{ }} y bloque {% %}
    # se mantienen (el template ya los usa).
    env = Environment(
        loader=FileSystemLoader(template_path.parent),
        comment_start_string="<#",
        comment_end_string="#>",
    )
    template = env.get_template(template_path.name)

    questions_block = "\n".join(render_item(item) for item in exam.items)

    return template.render(
        subject_name=escape_latex(subject_name),
        exam_title=escape_latex(f"Examen — {subject_name}"),
        department=escape_latex(department),
        exam_date=escape_latex(exam_date),
        exam_time=escape_latex(exam_time),
        duration=escape_latex(f"{duration_minutes} minutos"),
        examiner_name=escape_latex(examiner_name),
        instructions=escape_latex(instructions),
        questions_block=questions_block,
        print_answers=print_answers,
        include_answer_key=True,
    )