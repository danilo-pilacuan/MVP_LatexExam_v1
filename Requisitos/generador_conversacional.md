# Generador Conversacional con Agente IA para Exámenes y Banco de Preguntas

Proponente del tema: Felipe Grijalva
ID: PR-228
Cohorte: 3era MMIA
Estudiantes: Danilo Isaías Pilacuán Montalvo (https://app.notion.com/p/Danilo-Isa-as-Pilacu-n-Montalvo-1c805737435780eda05ce1d2b6b6c83b?pvs=21)
Proyecto Disponible en: Cohorte 3, Cohorte 5, Cohorte 6
Tutor: Felipe Grijalva

Este proyecto propone un **generador conversacional con agente IA para exámenes y banco de preguntas**. El sistema permite que un profesor interactúe con un agente como si fuera un asistente de cátedra: puede pedirle preguntas sobre temas específicos, solicitar la creación de nuevas preguntas o construir exámenes usando preguntas previamente almacenadas.

El agente analiza materiales de clase, genera preguntas alineadas con los contenidos, las clasifica automáticamente por tema y las organiza en un banco reutilizable. Además, incorpora validación humana y verificación por IA para asegurar que las preguntas sean correctas, relevantes y seguras de usar en evaluaciones reales.

El objetivo es reducir el trabajo manual de creación, etiquetado y reutilización de preguntas, manteniendo control académico sobre la calidad del contenido. El resultado esperado es una herramienta que ayude a los docentes a construir evaluaciones de forma más rápida, ordenada y confiable.

# Danilo Pilacuán MVP

Summary

### Elementos de Acción

- [ ]  Danilo: documentar el flujo del agente con diagrama (puntos de decisión, entradas, salidas, intervención humana)
- [ ]  Danilo: evolucionar el MVP hacia una interfaz conversacional (estilo chat, sin frontend tradicional)
- [ ]  Danilo: agregar campos de verificación humana y verificación por IA en la base de datos de preguntas
- [ ]  Danilo: diseñar restricciones de seguridad para el agente sobre escritura/modificación en la base de datos
- [ ]  Danilo: investigar métricas de evaluación para agentes y para el componente RAG
- [ ]  Danilo: analizar costos comparativos entre modelos locales y modelos en la nube
- [ ]  Danilo: compartir el repositorio (privado) con Felipe
- [ ]  Danilo: hacer seguimiento con Felipe al menos cada dos semanas
- [ ]  Felipe: compartir la página de Notion del proyecto con Danilo

---

### Concepto del Proyecto

- El objetivo es un agente de IA que asista a profesores en la **generación y catalogación automática de preguntas de examen** a partir de material de clase (diapositivas en una carpeta)
- Las preguntas deben ser **categorizadas automáticamente por tema** (ej. Regresión Lineal, Regresión Logística), reemplazando el etiquetado manual que se hace hoy en plataformas como D2L
- El objetivo final es un **banco de preguntas reutilizable** del que se puedan extraer preguntas aleatoriamente para armar exámenes

---

### Estado del MVP (Danilo)

- La infraestructura está **contenedorizada con Docker Compose** y compuesta por tres servicios:
    - Servicio de embeddings (PostgreSQL con pgvector)
    - Compilador de LaTeX para generar los PDFs de exámenes
    - Aplicación orquestadora que llama a los agentes
- El sistema está basado en **RAG (Retrieval-Augmented Generation)** con LangChain
- El LLM utilizado es el endpoint interno **Dipsy 24** (accesible vía VPN), aunque se mencionó OpenAI/Claude como alternativa
- Las entidades del modelo de datos incluyen: `Subject`, `Readings`, `Material Chunks` y preguntas generadas
- La interacción actual es mediante una **API** con endpoints para: registrar materia, alimentar embeddings y generar examen (indicando número y tipo de preguntas: selección múltiple, pregunta abierta, razonamiento)
- Las materias de prueba cargadas fueron **Economía Aplicada** e **Inglés Técnico**

---

### Visión de la Interfaz y Flujo de Usuario

- Felipe no quiere un frontend tradicional: quiere **conversar directamente con el agente**, como si fuera un asistente de cátedra
- Casos de uso conversacionales esperados:
    - Pedir preguntas ya existentes del banco ("dame 20 preguntas de estos temas, no generes nuevas")
    - Generar preguntas nuevas de un tema específico de forma interactiva, una por una
    - El agente debe **preguntar al usuario si la pregunta es correcta** antes de guardarla como verificada
- Las preguntas deben tener campos de: **verificado por humano** y **verificado por IA**
- Las preguntas ya verificadas por un humano **no deberían poder ser modificadas por el agente**

---

### Consideraciones de Diseño del Agente

- Riesgo crítico: el agente tiene **permiso de escritura en la base de datos**, lo que puede causar borrados o modificaciones no deseadas
- Se debe diseñar el flujo con **human-in-the-loop** explícito
- Felipe recomienda usar **Pydantic** para forzar un formato estructurado en los outputs del agente y evitar alucinaciones
- No generar demasiadas preguntas en una sola llamada para reducir alucinaciones
- El compilado LaTeX debe manejarse en código, no delegarse al modelo
- Para las plantillas LaTeX, Felipe recomienda usar **templates ya existentes** que soporten: múltiples versiones del examen, aleatorización de preguntas y generación automática de hoja de respuestas

---

### Evaluación del Agente

- Una vez completada la implementación, se deberá trabajar en la **evaluación formal del agente** con métricas del mundo agéntico:
    - Tasa de alucinación
    - Calidad del componente RAG (métricas específicas de RAG)
    - Análisis de costos (tokens consumidos, comparativa local vs. nube)
- La trazabilidad (monitoreo en producción) se descarta por ahora para este alcance

---

### Fechas y Seguimiento

- Danilo está en la **segunda corte** (corte 3 en Notion), con defensa entre el **14 y 21 de diciembre**
- Toda la implementación debe estar **lista en noviembre** para poder escribir y cerrar en diciembre
- Felipe ya actualizó la asignación de Danilo en Notion
- Se espera contacto frecuente: idealmente **cada dos semanas**, mínimo una vez al mes

Notes

Transcript

directo al grano. Yo te mandé una idea, no, en general. Sí, correcto. Es que se me viene a la mente, verás, o sea, realmente esto piensa, como te decía, es más un asunto de pensar cómo se va a implementar esto a nivel de agentes. Y también cómo se va a utilizar, o sea, piensa el caso de uso que te mencionaba, o sea, yo tengo, piensa en un profe que tiene diapositivas en una carpeta, ya, que no es una carpeta con un nombre específico ni nada, solo tiene ahí información general.

Yo quiero una gente que obviamente esté viviendo en el computador, que más o menos como hace, haría Cloud Code, digamos, directamente leyendo una carpeta. Y genere cuestionarios de acuerdo a los temas que le pidas y estas preguntas se guarden y luego pueden ser utilizadas para generar, tener un banco de preguntas enorme, ¿me cachas?

Esa es la idea un poco que quiero automatizar con este agente. O sea, si tú quieres, piensa si esto fuese como sin un agente. Sería que, verás, tú cuando generas una pregunta para una prueba en D2DLE o en alguna de estas plataformas, o sea, tú generas la pregunta a mano y todo, ¿no? Y tú mismo tienes que ir categorizando, decir, esta pregunta es de tal tema, no sé, por ejemplo, es de Regresión Iñal, es de Regresión Logística, como un poco para tener una idea, un orden de dónde están las preguntas y de qué tratan, ¿cachás?

Es decir, toca poner manualmente como unos labels, unos tags que diga esto está de tal tema, esto es de tal cosa, ¿me cachas? Entonces la idea es que con el agente las preguntas, además de ser generadas, sean catalogadas. Con eso luego yo puedo generar exámenes de ciertos temas y simplemente jalo de la base de datos aleatoriamente algo, ¿me cachas?

algo así es la idea más bien ¿qué has pensado tú hasta aquí? ¿le has podido dar algo de cabeza a esto? sí, más bien, hice bueno, a grandes rasgos también un pequeño MVP en función de lo que ya habíamos hablado. Muéstrame para chequearle y a ver si en este MVP...

Y como te decía, tal vez luego me puedes mandar algo escrito, más o menos, cuál es el workflow de la gente. Más o menos tener una idea de qué es lo que está haciendo, pero muestro tal vez para entender qué es lo que está haciendo. ¿Aló, aló? Sí, ahí está.

A ver, déjame ver...

Ya, ya te escucho, tú no me escuchas. Felipe, no sé si me escuchas tú, porque yo ya no.

No me escuchas, yo estoy en el micrófono.

No sé. Voy a intentar volver a conectar mis audífonos. Sí, conectale de nuevo los audífonos porque puede ser que algo sea en tu lado.

Porque yo si te escucho.

Ya, ahí. Ahí sí. Ahí sí. Ahí está reconectado. Sí, ya, chévere. Listo, entonces. Bueno, ahorita estoy en la computadora del trabajo, entonces no tengo como tal... el MVP corriendo, pero aquí tengo, por ejemplo, mi rep, con los otros cambios. Así que consiste así.

¿Sabes qué, Danilo? Es como que los audífonos ya te escuchan súper distorsionado, no intercortado. Algo pasó ahí, tal vez no... ¿Algo en los audífonos? Sí, exacto. Oye, dime algo.

más distorsionado, ahí, ahí mejor, ahí, sí exactamente, ahorita sí funciona

¿Ahí? ¿Ahí dime algo?

Aló, dime algo, dime algo, dime algo ahí, tal vez, porque no, no te escucho yo, ya no te escucho nada, no te escucho.

creative labs hay algo parece que es en tu mic en tu nuevo en tu jabra

Ahí ya regresó. Sí, solo que como te decía, lo que pasaba es que se distorsiona algún rato en el... no sé, es como que se empezó a sonar un sonido ahí, un zumbido ahí. Pero ya te escucho. Ya, chévere. Bueno, debe ser por lo que aquí tengo... estoy dentro de una máquina virtual, entonces para poderme conectar. Pero bueno, como decía, no puedo correr la infraestructura, pero como tal, vamos viéndole ya.

ya entonces ahorita la infraestructura está basada en tres aplicativos

que están, los tengo ya contenedorizados, entonces que son servicio de embeddings, lo típico que me permite generar y guardar los embeddings, tenemos ahí, estoy trabajando con Postgre, Vigivector, un compilador de latex que es el que ya me permite generar los outputs y como tal la aplicación que orquesta y...

Y llama a los agentes, estos pequeños que están creados aquí.

sabes que se fue de nuevo, ahorita se me fue de nuevo tu audio, se me fue de nuevo el audio

es como que algo se te está desconectando el audio

Ahí está. Ahí volvió. Ahí volvió. Ahí volvió.

Oye, ¿sabes qué, Danilo? Se me fue el audio. Se te está yendo el audio de nuevo. Está como yendo y viniendo y ahí... es tal vez en la...

en la...

en la máquina, no sé

No, no, ya no te escucho más.

no te escuchará

Ya mismo va a regresar, a ver, ahí habla de nuevo, ahí va a regresar. Ajá, sí. Sí, sí, es como que está yendo y viniendo, hablas un poco y luego se va, pero veamos si es que funciona esta vez. Ya, ok, este... bueno, volviendo a como te explicaba, tengo... ahorita más o menos es un...

funciona en base a un RAC, ¿no es cierto? Entonces tenemos algunas herramientas, tenemos la capa de embeddings, la capa de compilado. el compilado de latex y por acá tenemos los agentes que se encargan de obtener la información, hacer el retrieval. generar los embeddings y generar las preguntas. Eso lo hago con este par de agentes.

Ahorita como tal.

Una vez yo levanto la infraestructura, tengo este volumen de Docker.

En donde, justamente como me indicabas, tengo una carpeta con... Con...

Con material de un profesor de donde saque, me conseguí un repo donde aquí tienen ayudas, materias.

¿Analizador?

Ya, te me cortaste de nuevo. Tal vez no quieres llamarme por Whatsapp más fácil. Y hacemos el audio por Whatsapp y me muestras por ahí. Sí, sí. Sí, entonces. Ya, hagamos así más fácil. Yo te llamo, yo te llamo, Ismael Barzano. Listo.

Pasemos el audio por aquí, ya. Más fácil. Ya, listo. Listo, Felipe. Chévere.

Ya. Bueno, entonces, como te explicaba...

Le fui estructurando así, ¿no es cierto? Entonces, genero toda la parte de...

de retrieval y ya las preguntas las genero a partir de lo que procesé de la…

de lo que conseguí de la data, entonces...

Mi pregunta es...

yo te cacho todo ahora cuál es cómo es cómo hace luz ya yo levanto este este compose y ya está corriendo como un servicio no es cierto ya yo como usuario Piénsame como usuario, ¿cómo yo hago para generar, digamos, quiero generar un examen de estos tres temas? Cinco preguntas y...

¿Cómo es? ¿Cómo sería mi interacción como usuario con esto? Ya, correcto. Y... bueno...

¿Recuerdas la parte que habíamos visto de LATEX, no? Las plantillas. Entonces, lo que yo hice es definir una plantilla que a través de Jinga, que es el motor de plantillas, aquí nosotros vamos insertando la información, las preguntas generadas, ¿ya? Bueno, como usuario, ¿qué se tiene ahorita?

Como era el MVP, la primera parte, tengo ahorita solo un API en el que yo digo, bueno, primero registro una materia, como tal vamos con materias. Tengo las entidades, si leemos por aquí las entidades...

En modelos tenemos Subject, Silence y aquí ya va la parte de Readings, Material Chunks en donde ya vamos guardando... por pedazos la información y por último las preguntas generadas, esto que me ayuda a tener la base de conocimiento, ¿no es cierto? Entonces...

Bueno, primero, ahorita únicamente se expone una API en la que te digo, registra la materia y luego te digo, en esta carpeta está cargada la data. Ya, y después yo cuando quiero generar, ahorita está a nivel de API, ¿no es cierto? ¿Tú internamente estás usando OpenAI por debajo o quién estás usando como LLM?

Justamente aquí más bien estoy utilizando, sí quise probar si podía utilizar el utilizar la, el AirPlay que tenemos del Dipsy 24. Y funcionó bastante bien. Si le puedes ver que así internamente. Sí, exactamente. Internamente va a funcionar súper bien con la VPN. Y es estas allá. Estás ahí directamente conectado a ese endpoint. Eso es lo que te iba a pedir, que si es que también eres una opción para poner una piquí de de.

de algún, de OpenAI o Cloud, así, pero por... Bueno, OpenAI es independient. Ya, ahora, una vez que yo genero las preguntas, digamos que yo le digo, genere ese examen, ¿no es cierto? Sí. Va a generar las preguntas y va a guardar en dónde estás guardando las preguntas.

Las preguntas ya se guardan, bueno se pasan al generador de látex y éste les inserta en la plantilla, y si le damos aquí la plantilla final... generada, nosotros le decimos, bueno, habíamos visto que hay un endpoint de registrar materia, el otro es el endpoint de...

En el puente se me fue la palabra. ¿Generar el pdf? No, de alimento.

el alimentar los embeddings y después de eso está uno en el que dice generar examen y en el generar examen hasta ahorita le paso una estructura de un examen en el cual dice cuántas preguntas generar cuentas de qué tipo selección múltiple pregunta abierta

qué más será la otra y razonamiento entonces en base a eso ya genera los genera los pdf el resultado y ahora y los pdf es bueno pero todavía no quizás no tengas pero recuerda que el pdf que es lo interesante de esto de látex y estos generadores de exámenes

que una vez que tienes el código en Latex, puedes generar varias versiones del mismo examen y cada una con su respuesta. No sé qué template estás usando de Latex concretamente. O sea, alguno tuyo o alguno de algún ya hecho. Aquí hay unos con los que comencé a probar donde está el látex, hay este de Z y hay otro, uno de...

una universidad, donde le dan ya un template, pero este le veo como un paquete más potente, en el que las clases, ya el primero clases, y en estas ya se va a ya se puede hacer eso de barajarlos, el generar varios. Verás, eso ya déjale justamente para después, verás, eso si enteramente no hagas tú, déjale que esos templates tengas y lo hacen súper bien, que tú le dices, génerame cuatro versiones y te genera simplemente cuatro versiones del mismo examen y genera las respuestas, etcétera, y automáticamente te genera, digamos, una página de respuestas también, no sé si es exactamente.

Y usar alguno que ya te genera aleatorio y además ya te genera una hoja de respuestas, que es el mismo examen pero con respuestas, y varias versiones, lo importante es que sean varias, también te generan 4 o 5 versiones del mismo examen y generan el mismo PDF.

Eso se me viene a la cabeza, pero eso hazlo enteramente en el mundo de latex, deja que esas cosas funcionan súper bien en sus generadores. Ya, ya les voy a seguir bien. Y bueno, esta era una de las salidas, esta es una de las primeras en la que tienes una pregunta.

sale, responda, y esto es lo que ya obtuve a través del aprendizaje. Esta es matemática, no sé si le viste por aquí, ¿cuáles son las materias que yo cargué? Las materias que yo cargué fueron...

Economía aplicada e inglés técnico, entonces sí le vemos.

Creo que sería... veamos detenido... el Jason. Esto es lo que se pasa si el generador de látex. Entonces dice, estaría desmarcado en concepto objetivo, según el material de estudio. Y eso, todito eso, las preguntas generas con IA, pero ese formato, supongo que lo haces en programación, no lo haces con IA que te genere todo eso, ¿no? No, no todo, no. Bueno, para ahorrar...

todo lo que es para ahorrar, al máximo, más que nada, es únicamente la generación de las preguntas, ya la plantilla, todo eso, ya es únicamente... normalizar, siempre he pensado en normalizar las preguntas, no siempre voy a tener un output bueno Ajá. Verás, más bien ahí, bueno, ¿tú cómo sería? O sea, ¿tú estás usando LandChain o LandGraph o estás usando...? LandChain. Ah, LandChain, ya. Bueno, sin usar frameworks, puedes usar directamente Pydantic también para que... la idea es que te retorne un formato que tú esperas, ¿me entiendes?

Y eventualmente verás, yo por ejemplo cuando he generado esto, he generado directamente en el formato que entiende D2L. Solo que yo no quiero que esto esté en D2L, porque D2L es hecho pedazos, es de formato y es un relajo. Pero es bastante bueno en generar el formato que tú quieras y después obviamente la idea es que tú una vez que generas, tú le pongas, o sea, no le hagas generar 20 preguntas, va a alucinar de ley, o sea.

Pero... De ahí tú cómo le arregles eso ahí para ya presentarle el Atex, eso quizás de empezar en programación dura sería mejor. No, no que déjale al modelo que haga eso, porque ahí sí va a ser más propenso a alucinar. Pero bueno, algo parecido a lo que estás diciendo, a lo que veo. Ahora, verás, yo te entiendo, el MVP está súper bien. O sea, esta es la idea, ¿no es cierto? Tú te hiciste como un ejemplo. ¿Cómo sería hacer esto? Y tienes como nivel de API esto, ¿no es cierto?

Ya, verás, front end, yo realmente como front end, no, o sea, yo quiero, yo quiero conversar con tu agente. ¿Me entiendes? Ya no quiero un froneta así. Yo quiero conectarme, o sea, dime qué tan viable es esto, o sea, que yo me siente... Yo tengo mis documentos y yo simplemente le digo, génerame 5 preguntas o toma 5 preguntas que existen porque quisiera que se guarden, ¿me entiendes?, para no estar generando, generando de nuevo.

Y yo decir, oye, dame de estos temas 20 preguntas, bájate de la base de datos. Hechas, no generes más, simplemente bájate y automáticamente me baja. o también yo conversar y decirle quiero generar nuevas preguntas, añade nuevas preguntas de tales temas y va generando una pregunta y la idea verás idealmente si me gustaría que en la base de datos que vaya a haber haya un casillero o un campo más bien que diga si está verificado o no por un humano, que esté bien, ¿cachas?

Exacto. Y también verás, me gustaría que hay un campo también si es verificado por otra guía. ¿Cacha? Ya. Otra idea que le verifique, o sea, que tú le mandes y digas, oye, que está ambigua la pregunta, está correcta la respuesta, etcétera, y que taggee y que te diga simplemente, oye, no, no, está ambigua, o está mala la respuesta, y con eso un humano quizás va a revisar eso con prioridad, ¿cachas?

Ya. Entonces, eso quiero que me ayudes a pensar, verás, yo en principio como, yo le veía aplicación como un agente, ¿me entiendes? Imagínate que estoy usando Cloud Code. Yo tengo lo tuyo y simplemente le pido preguntas y genera y me retorna mi PDF con las preguntas. Pero si quiero que saque de la base de datos, pues también le digo, génerame, literalmente, sácame unas cuantas preguntas de aquí, no sé.

y me genera el examen. Entonces eso es un poco el front end que se me viene a la mente como cómo le ves. Sí, me va bien, porque esto ya sería como un chat urbano, igual de leer, evaluar, imprimir. Sí, y de ahí verás algo que también veo es en parte de tu agente, ya piensa en esto, o sea, yo le pido, génerame una pregunta de regresión niñera.

Y él, y él me genera. Yo quisiera que a esta gente le condiciones bien en el prompt y todo, en el comportamiento de tu agente, en el flujo. a que me pregunte si me digo oye eh guardamos la pregunta ¿está correcta la pregunta? ¿le das por verificada la pregunta?

¿Me cachas? O sea, es como piensa, más o menos piensa que el agente es un asistente de cátedra, que le mandé a hacer una pregunta. Y él me dice, yo le tengo que decir, oye, check, estoy de acuerdo con tu pregunta. y generamos, y le guarda ya automáticamente verificada, etcétera. ¿Sí me cachas?

Eso se me viene, o sea, ¿cachas que está súper interactivo esto con el chat? Y eso, y de ahí también que sea capaz de, no lo que te digo, de que si usa preguntas, ya que ya están, ya no necesito generar más, que yo pueda interactuar directamente como... O sea, siempre piensa esto, verás, que esto va a ser como un asistente de cátedra que te está generando las preguntas.

Piensa que tú eres mi asistente de cátedra y yo te diría, oye, hazme un examen de 20 preguntas. de tales temas y tú sabes que usa el banco de preguntas que tenemos, no, no, ya no te inventes nada más, solo usa lo que ya tenemos y va y busca todo y dice ya no, no voy a generar más simplemente, luego te digo sabes que generamos unas más, unas preguntas súper difíciles de redes neuronales, proponme una y después vamos a la siguiente, vamos y yo le voy diciendo en el loop que va guardando o no va guardando y si está verificada o no está verificada, ¿me entiendes?

O sea, esa parte es como la que yo le veo como pienso como usuario, ¿ya? Eso se me viene ahorita a la cabeza y verás, como MVP está súper bien, de hecho, justamente, súper bien como MVP. Ahora toca ponerle el resto, ahora solo yo quiero que tú pienses una cosa, verás.

tu agente, el flujo de tu agente yo tengo que entender, y eso es lo más importante cuando me, una vez que acabes la aplicación, ¿cuál es el flujo que sigue? o sea, el diagrama del flujo, literalmente, o sea, dónde están los puntos de decisión, dónde están los puntos de salida, dónde están entradas, etcétera, porque eso me da seguridad de qué está pasando, o sea, y eso ya va a depender cómo tú le diseñes el agente y dónde está el humano también, al ver un punto que va a estar aquí el humano.

Por ejemplo, ya sabes que ahorita parte de tu agente soy yo, o sea, yo voy a tener que verificar las preguntas. Ah, o el, bueno, el human in the middle, sí. Y eso más o menos, ¿verdad? O sea, no sé si me sigues del espíritu de esto para que me ayudes a pensar en programación. Que...

O sea, no sé, es un poco como, cachas, no te pido un front end, porque quiero que sea así, ¿me cachas? O sea, quiero que sea como conversar con un man y que le pidas cosas. Y que siga guardando, y siga guardando, y siga guardando la base de datos, etcétera, etcétera, etcétera, ¿me entiendes? Pero es como que no... Eres tú, tu aplicación está buena en tu Docker, pero eres tú conversando con la aplicación, o sea, conversando con la gente, en esencia.

Y eso se me viene así como idea ahorita, verás. Entonces... Bueno, esto localmente yo podría levantar, ¿no es cierto?, con Cell Compose ahí o podría localmente levantar como aplicación. Ya. Y, obviamente, si esto le levantaría en el servidor también, ¿no? Todo tendría que tener acceso al servidor y cualquiera podría utilizar. Pero, verás, ese esquema de usuarios no quiero que hagas. O sea, eso sí es una aplicación a aplicación.

No, eso olvídate. O sea, yo quiero ahorita que esto funcione de momento, digamos, para mí, ¿ok? Piensa un usuario así, nada más, ¿ok? Más me preocupe la gente, que esté funcionando bien la gente. Ahora, hazle eso, verás, empecemos con la parte de programación. A ver, más bien, dime, ¿tienes alguna duda hasta aquí de cómo sería? ¿Qué es el espíritu de esto? No, ninguna. Más bien, justamente lo que tú decías y yo tenía pensado yo. Justamente es cuando dije la mieta, porque ahorita los probes de sistemas son básicos.

Entonces no hay tampoco una sustentación muy clara en la cual, bajo la cual yo digo esta pregunta, como tú decías, la voy a verificar, no la voy a verificar y justamente estaba leyendo el tema de Harnessing, que es creo que el espíritu de lo que vamos a hacer.

Es limitable hasta cierto punto y... Creo que igual me serviría para el momento en el que yo escriba, ¿no? El darle pautas y limitar los agentes hasta...

reteniendo lo que puede ser y lo que no. Verás, ya viene algo bien importante lo que tú hablas, justamente, verás. Y esto es algo que vas a reflexionar bastante, o sea... Piensa, ¿qué pasa si es que tu agente me termina borrando algo que no debe en la base? Esas cosas tienes que cuidar tú en el diseño de esto.

Sí. Correcto. Porque yo no quiero que mañana, o sea, ah sí, le pregunté y me entendió, alucinó, lo que sea, y termina borrándome la basura. Una pregunta o alguna pregunta me cambia. Y por eso estos campos que te digo verificado por humano, verificado por una IA, quizás debemos pensar en que está verificado por un humano.

la gente no puede ya modificar esa pregunta, ¿me cachas?, porque se supone que ya yo le di el check, ¿no es cierto? Entonces, o sea, verás, piensa en esos escenarios, o sea, esto de los agentes es una joda por ese tipo de cosas, piensa en esos escenarios. Porque ahorita verás, lo que pasa es que tu agente va a modificar la base de datos.

necesita modificar. Entonces también el rato que le damos ese permiso, piénsame también cómo me aseguro de que no me hago una fregada, ¿me entiendes? que puede pasar, puede pasar, eso ya se sabe, porque le estamos dando acceso a la escritura, él no solo está leyendo, le está escribiendo la base de datos.

Es un poco que le pienses, ¿sí? Y también ahí viene lo otro. Acaba la aplicación, empieza con ya. Ahorita está en Bipi. Vamos a la versión inicial de esto. Y después digamos, recuerda, verás, los agentes, está bien el diseño, ¿no es cierto?, todo lo que te estás mencionando. Eso es desde el punto de vista del software. En esencia esto es software engineering, hacer esto.

Y ahora el asunto es que también piénsame cómo evaluar esto. Quiero que me pienses cómo evaluar a esta gente. Y con métricas de agentes. Me refiero a métricas del mundo agéntico. ¿Cuánto se está alucinando? ¿Cuánto se está equivocando? De alguna forma, búscame cómo yo evaluar que está siendo bien. ¿De acuerdo? Porque vamos a tener que reportar métricas, ¿verdad? El día de hoy hay muchos agentes desde afuera, pero lo más estorboso y las críticas más grandes al mundo de los agentes

es que muchos no les evalúan, ¿me cachas? Venden productos que no, yo no tengo idea, desde chatbots que no tengo idea qué tan buenos son y con métricas duras. Y eso obviamente depende del negocio, es un montón de cosas para poder evaluar a estos agentes.

Yo quiero que un poco pienses esto justamente de evaluación, tú tienes una etapa de RAG, también hay métricas para evaluar RAG, qué también se comporta tu RAG. entonces eso es un poco lo que ya va después cuando ya acabemos de implementación vamos a pensar en cómo evaluar esto lo más que hasta donde lleguemos y se nos acaba el tiempo para esto sí

Y eso va a ser, digamos, que la parte formal de la evaluación. Ahorita tú estás en la parte ya del agente, el diseño del agente, la implementación del agente, todo lo que viste, asegurar al agente, etcétera. Y después la parte de evaluación. viene como lo que necesito que hagas ya como formal a que me deje súper claro saber qué tan bueno es de la gente. Y obviamente ahí viene la otra parte que esa no te voy a pedir, que es la de trazabilidad.

porque eso no, eso sería ya mucha cosa más y esto no, ya está bastante, digamos, hay bastante cosa que hacer, sí, pero tras la habilidad recuerda que también es importante, o sea, pero esto ya es cuando está en un ambiente en producción. de saber qué se pregunta, qué se responde en todo momento, cómo está la gente, es monitorear a la gente en esencia. Digamos que eso ya sería si esto escala más allá de ser un MVP.

Entonces, hagamos eso ya. Verás, vamos con los tiempos. Bueno, ¿tienes alguna duda ya hasta aquí ya de hacia dónde va esto? No, ninguna. Se me queda claro justamente la parte de métricas y las tiendas pesadas. Igual creo que ahí aplica el probar la solución de la infraestructura local o de sus modelos más potentes, pegados. Sí. Creo que también para...

¿Aplica contra costos? Claro, exacto, eso también es un análisis súper chévere que suelen pedir bastante en la industria, verás, ¿cuánto me va a costar? Y sí, es bueno eso, porque si no las facturas de esta tontera, nosotros mismos a las facturas de estas cosas, puta, a veces se van al...

se van a las nubes, sí, y justamente lo que tú estás haciendo súper bien, verás, tratas de ahorrar tokens, ese tipo de cosas, o sea, sí es buena idea, o sea, no, y también tú creo que ya sabes bastante de esto que genera. Mientras más genera tokens, tokens y tokens, ventana y contexto gigante, más probabilidad de alucinar.

Y en software eso se ve clarito, o sea, que les quieren soltar todo el código ahí, no, en la ventana de contexto le matas, ¿me entiendes? Entonces eso. Ahora, vamos con las fechas, verás. Ahorita las fechas, de hecho ya están en las fechas preliminares de las... Tú vas a graduarte con, digamos, al final de este año.

Esa es tu primera prórroga, ¿sí? Y solo, verás, ahorita tú tienes acceso a la página de Notion de Capstone Projects, ¿no es cierto? creo que si veras estoy en notions yo te voy a mandar esto ahorita al whatsapp pero si tienes del acceso pero no no no no no no no

pero esta página quiero que estés presente porque las fechas son importantes

Quinta, verás. Ah, no, tú estás con la quinta corte, verás. Yo ahorita, eh...

Voy a mover esto de la quinta. En esa página de Notion, tú tienes acceso, supongo. Si no tienes acceso, me haces un request de acceso como lectura, ¿ya? No, sí, sí tengo. Ya, verás. Pero que ahorita no voy a poder ver porque no aquí en la que estoy. Ah, ya, fresco. Verás, solo una cosa, te recuerdo las fechas. Van a cambiar un poquito, ¿ya? Un poquito. Les voy a extender sobre todo la presentación del escrito.

Pero realmente las defensas suyas van a ser... desde el 14 de diciembre hasta el 21 de diciembre, eso quiere decir que más o menos nosotros deberíamos terminar de implementar todo, todo, todo hasta noviembre, máximo. máxima. Todo limpia, fácil de implementación, test, etcétera. Y para que tú tranquilamente puedes escribir noviembre y parte de diciembre ya cerramos esto de aquí, ¿sí?

Eso respecto de las fechas. Tú originalmente estabas en acorte 4, ¿verdad? Y... 3. Acorte 3. Vamos a ver, te voy a buscar, tú estabas con lo del audio y luego ahorita te voy a retirar de esto de ahí. Déjame removerte para que no me aparezcas duplicado.

Entonces, ahorita tú estás ya conmigo, déjame revisar.

y una vez de tutor, antes de que me olvide verás, antes de que me olvide de tutor, tu eres la tercera corte ¿verdad?

Perfecto, ya te cambié.

¿Ya? ¿Tú estás en la primera o en la segunda? Eh... hazme acuerdo. En la segunda, porra. ¡Ah, ya estás en la segunda, verás! ¡Ay, sí! ¡Ay, Danilo, ahora sí necesito que te partes pilas! Ah, yo estaba así tan relajada, digo, es la primera. Sí, ya, verás. Y queda claro. Recuerda que, verás, sí, sí existe una tercera prórroga, ya.

Pero mejor no te vayas. ¿Qué? Yo no. Ya, ya, mata esto rápido, ¿me entiendes? Ah, yo ahorita tomé este asunto... Como viste que ha cambiado mucho las temas de titulación. Muchos de ustedes están yendo por agentes y tú... Tú sabes que esto es software engineering en esencia, ¿sí?

Entonces, anímate y matemos esto este año, ¿ya? Para que ya es matar y en diciembre nos vamos libres de todo, ¿ok? Eso nada más verás, yo te tengo anotado aquí, ya te cambié y con eso ya te tengo, ok? eso entonces creo que eso sería más bien me escribes verdad aquí necesito que tú me escribas me digas oye ya tengo algo

Ok, no te pierdas, me refiero. No, no, no, no, no, no te asomes así, chuta, un día antes de ir, ahorita tengo nada, asómate seguido, ¿sí? Ya tienes algo, asómate al menos una vez por mes, quiero verte en los próximos dos, tres meses, si es posible más, pero ténme algo y dime ya, vamos y vamos probando, etc.

¿De acuerdo? Ya tengo definido que esto quiero acabarlo rápido también, así que espero que sea cada dos semanas. Perfecto. O sea, si tú ya me escribes, me dices, oye, ¿cuándo? Yo te busco un espacio, ¿sí? eso sería entonces, eso es Danilo, veamos ahí, está súper chévere todo y vamos viendo si lo logras, ok chao

Entonces quedamos en eso ya y estamos ahí conversando. Otra cosa, ¿tienes el repo? ¿me puedes compartir también quizás yo para ir jugando con lo tuyo también? Ya, sí, sí. ¿Le tienes privado, supongo, o no? No me acuerdo. Sí. Lo considero privado. Tenle privado y compárteme a mí, ahí te mandé mi story, ¿ya? Ya.

Listo. Chévere. Quedamos en eso, ¿ya? Cuídate, entonces, Danilo. ¿Ya? OK. Listo, listo, Felipe. Muchas gracias. Ya, bye. Entonces, mientras yo avance, te voy comentando. Me vas comentando y me tomas cita, ¿ya? Dale. Ya, listo, listo, muchas gracias. Ya, bye.

proyecto disponible. Ya verás, yo ahorita igual en Notion, solo para mi registro, te voy a mandar una página de Notion. No le puse un título específico así, solo le llamé a gente y a pruebas. No sé, le pusiste algún nombre a esta cosa. Todavía no. Ya, cuando la pongas de ahí la cambiamos. Ya. Pero... Sólo esto es para...

Yo tener un tracking nada más donde estás tú, ¿sí? Y esto verás, las fechas es lo más importante. para que estés... estés atento, ¿sí? y... déjame buscar... Si, ahorita, bueno, lo voy a poner disponible en la corte 3.

Ya, listo, ya te asigné. Te voy a asignar conmigo.