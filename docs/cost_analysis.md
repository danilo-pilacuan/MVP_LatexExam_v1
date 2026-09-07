# Análisis de Costos: Modelo Local vs. Nube

> **Elemento de acción 6** — Comparativa de costos entre el modelo local (vLLM + DeepSeek-V4-Flash-0731) y modelos en la nube (OpenAI/Claude), para decidir el despliegue final y justificar la elección en la tesis.

---

## 1. Modelo actual (local)

- **Modelo:** `deepseek-ai/DeepSeek-V4-Flash-0731` servido con **vLLM** en una GPU interna (H200).
- **Costo:** hardware + electricidad + mantenimiento (capex/opex), **sin costo por token**.
- **Ventajas:** privacidad (los datos no salen de la infraestructura), sin costo marginal por uso, control total.
- **Desventajas:** requiere GPU dedicada, mantenimiento, y el costo es fijo aunque el uso sea bajo.

---

## 2. Alternativas en la nube

### OpenAI (GPT-4o / GPT-4o-mini)
- **GPT-4o-mini:** ~$0.15 / 1M input tokens, ~$0.60 / 1M output tokens.
- **GPT-4o:** ~$2.50 / 1M input, ~$10.00 / 1M output.

### Anthropic Claude (Sonnet / Haiku)
- **Haiku:** ~$0.25 / 1M input, ~$1.25 / 1M output.
- **Sonnet:** ~$3.00 / 1M input, ~$15.00 / 1M output.

### DeepSeek API (si se usara la nube de DeepSeek)
- Muy barato: ~$0.14 / 1M input, ~$0.28 / 1M output (cache miss).

> Los precios son aproximados y cambian; verificar en las páginas oficiales al momento de escribir la tesis.

---

## 3. Estimación de consumo por examen

Basado en el pipeline actual (8 preguntas, RAG con top_k=3):

| Concepto | Tokens aprox. |
|---|---|
| Prompt por pregunta (spec + contexto RAG) | ~1.500 |
| Completion por pregunta (GeneratedItem) | ~300 |
| Evaluación por pregunta (prompt + completion) | ~800 |
| **Total por examen (8 preguntas)** | **~20.800 tokens** |
| **Total por pregunta** | **~2.600 tokens** |

> Supuestos: 8 preguntas, 1 generación + 1 evaluación por pregunta, sin reintentos. Con reintentos y rechazos, el consumo puede multiplicarse por 1.5-2x.

---

## 4. Comparativa de costos por examen

| Proveedor | Costo/1M input | Costo/1M output | Costo aprox. por examen (20.8k tokens, mix 80/20) |
|---|---|---|---|
| **Local (vLLM)** | $0 | $0 | **$0.00** (costo fijo de hardware) |
| GPT-4o-mini | $0.15 | $0.60 | ~$0.005 |
| Claude Haiku | $0.25 | $1.25 | ~$0.009 |
| DeepSeek API | $0.14 | $0.28 | ~$0.003 |
| GPT-4o | $2.50 | $10.00 | ~$0.08 |
| Claude Sonnet | $3.00 | $15.00 | ~$0.12 |

> Cálculo: `(0.8 * input_tokens * input_price + 0.2 * output_tokens * output_price) / 1e6` con 20.8k tokens totales.

---

## 5. Análisis y recomendación

### Punto de equilibrio (local vs. nube)
- El costo local es **fijo** (hardware). El costo en nube es **variable** (por token).
- Si el uso es **bajo** (tesis, uso personal), la nube puede ser más económica *si no se tiene ya la GPU*.
- Si ya se dispone de la GPU interna (como en este MVP) y el uso es **medio/alto**, el local es claramente más barato a largo plazo.

### Trade-offs
| Criterio | Local | Nube |
|---|---|---|
| Costo por token | $0 | Bajo-Medio |
| Costo fijo inicial | Alto (GPU) | $0 |
| Privacidad de datos | ✅ Alta | ⚠️ Depende del proveedor |
| Escalabilidad | Limitada a hardware | Alta |
| Mantenimiento | Alto | Bajo |
| Latencia | Baja (local) | Media (red) |

### Recomendación
- **Para la tesis/MVP:** mantener el **local** (ya funciona, sin costo marginal, datos privados). Es la opción más defendible académicamente y no genera facturas.
- **Para escalar/despliegue de producción:** evaluar **DeepSeek API** (muy barato) o **GPT-4o-mini** como respaldo si no se dispone de GPU propia. El diseño del pipeline es agnóstico al proveedor (solo cambia `llm_base_url` en `.env`), por lo que migrar es trivial.

---

## 6. Cómo instrumentar el costo real

1. Registrar **tokens por llamada** (prompt + completion) en cada nodo.
2. Sumar tokens por examen y por pregunta.
3. Aplicar la tarifa del proveedor para obtener el costo.
4. Comparar el costo real medido con la estimación teórica.
