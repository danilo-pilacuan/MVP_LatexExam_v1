# Métricas de Evaluación del Agente y del RAG

> **Elemento de acción 5** — Definición de métricas para evaluar formalmente al agente y al componente RAG (requisito de Felipe: "no vender agentes sin métricas duras").

Este documento propone el conjunto de métricas para la tesis. Se dividen en tres bloques: **métricas del agente**, **métricas del RAG** y **métricas operativas**.

---

## 1. Métricas del Agente

### 1.1 Tasa de alucinación (hallucination rate)
Mide cuántas preguntas generadas contienen información falsa o inventada (no respaldada por el material).

- **Definición:** `n_preguntas_con_alucinacion / n_preguntas_generadas`
- **Cómo medirla:** un evaluador LLM (o revisión humana en una muestra) compara cada respuesta contra el material de origen (RAG). Se marca `alucinación` si la respuesta contradice o inventa contenido.
- **Fuente de datos:** el `rejection_log` del pipeline ya registra rechazos; se añade un campo de auditoría por ítem.

### 1.2 Tasa de aprobación / rechazo (acceptance rate)
- **Definición:** `n_items_aprobados / n_items_generados`
- Ya disponible en el pipeline (`approved_items` vs `rejection_log`). Una tasa baja indica que el generador produce ítems de baja calidad o mal alineados.

### 1.3 Distribución de motivos de rechazo
- Desglose del `rejection_log` por `reason`: `duplicate`, `low_quality`, `difficulty_mismatch`, `validation_error`.
- Ayuda a diagnosticar si el problema es el generador, el evaluador o el RAG.

### 1.4 Precisión de la verificación por IA (agreement con humano)
- Comparar `verified_by_ai` contra la decisión humana final (`verified_by_human`) en una muestra.
- **Definición:** `acuerdos / total_revisados` (coincidencia de aprobación/rechazo entre IA y humano).

### 1.5 Tasa de modificación/borrado bloqueado (safety)
- **Definición:** `intentos_bloqueados / intentos_totales_de_escritura`
- Mide cuántas veces el agente intentó modificar/borrar una pregunta verificada por humano y fue bloqueado por el service layer. Idealmente 0 intentos exitosos.

---

## 2. Métricas del RAG

### 2.1 Recall@k (recuperación)
- ¿El fragmento correcto está entre los `top_k` recuperados?
- **Definición:** `relevantes_recuperados / relevantes_totales`

### 2.2 Precision@k (precisión)
- De los `top_k` recuperados, ¿cuántos son realmente relevantes?
- **Definición:** `relevantes_recuperados / k`

### 2.3 MRR (Mean Reciprocal Rank)
- Posición del primer fragmento relevante. Útil si solo se necesita 1 fragmento bueno.

### 2.4 Fidelidad de la respuesta (faithfulness)
- ¿La respuesta generada está respaldada por los fragmentos recuperados? Se mide con un evaluador LLM (groundedness).

### 2.5 Relevancia de la respuesta (answer relevance)
- ¿La respuesta responde realmente a la pregunta/tema solicitado?

### 2.6 Contexto de recuperación (context precision/recall)
- Calidad del contexto inyectado al generador. Se puede medir con frameworks como **RAGAS** o **LangSmith**.

> **Herramienta sugerida:** [RAGAS](https://github.com/explodinggradients/ragas) para métricas RAG (faithfulness, answer_relevancy, context_precision, context_recall) y un evaluador LLM propio para la tasa de alucinación.

---

## 3. Métricas Operativas

### 3.1 Costo por examen / por pregunta
- Tokens consumidos (prompt + completion) por examen y por pregunta.
- **Fuente:** `total_llm_calls` + conteo de tokens por llamada.

### 3.2 Latencia
- Tiempo total del pipeline y tiempo por pregunta generada.

### 3.3 Tasa de éxito de compilación LaTeX
- `compilaciones_exitosas / intentos` (ya en `compilation_log`).

---

## 4. Recomendación de implementación

1. **Instrumentar el pipeline** para registrar por cada ítem: `topic`, `spec`, `approved`, `reason`, `quality_score`, `similarity_score`, tokens usados.
2. **Crear un dataset de evaluación** (ground truth) con una muestra de preguntas revisadas por humano.
3. **Correr RAGAS** sobre el RAG para obtener las métricas de recuperación.
4. **Calcular la tasa de alucinación** con un evaluador LLM sobre una muestra etiquetada por humano.
5. **Reportar** en la tesis: tabla de métricas + comparativa de modelos.
