import subprocess
import uuid
import os
import shutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="LaTeX Sandbox Compiler")

class CompileRequest(BaseModel):
    latex_code: str

@app.post("/compile")
def compile_latex(req: CompileRequest):
    job_id = str(uuid.uuid4())
    work_dir = f"/tmp/{job_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    tex_path = os.path.join(work_dir, "document.tex")
    pdf_path = os.path.join(work_dir, "document.pdf")
    log_path = os.path.join(work_dir, "document.log")

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(req.latex_code)

    try:
        # Ejecutar pdflatex DOS veces: la primera genera el .aux con los
        # totales de puntos/referencias, la segunda los resuelve. Sin la
        # segunda pasada, pdflatex termina con "Rerun to get ... right"
        # (returncode != 0) aunque el PDF ya esté generado.
        for _ in range(2):
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", work_dir, tex_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )

        # Consideramos éxito si el PDF se generó, aunque returncode != 0
        # (puede haber warnings no fatales de "rerun" o overfull hbox).
        if os.path.exists(pdf_path):
            output_dest = f"/app/output/{job_id}.pdf"
            # Ensure output dir exists (bind mount may not be present at first run)
            os.makedirs("/app/output", exist_ok=True)
            # Use shutil.move instead of os.rename to support cross-device moves
            shutil.move(pdf_path, output_dest)
            return {"status": "success", "pdf_path": output_dest}
        else:
            log_content = ""
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                    log_content = lf.read()
            return {"status": "error", "error_log": log_content[-2000:]} # Retorna los últimos 2000 chars del log

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Timeout durante la compilación de LaTeX")