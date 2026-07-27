# 🛒 Agente Inteligente - Mercado Central 24h

Este proyecto es la entrega final para el **Challenge Alura Agente** del programa Oracle Next Education (ONE). Consiste en un Asistente Virtual Corporativo impulsado por Inteligencia Artificial, diseñado para responder consultas sobre políticas internas, recursos humanos e inventario en tiempo real.

## 🧠 Arquitectura de la Solución (RAG Híbrido)

Para garantizar latencia ultra-baja y alta precisión en consultas de inventario, se implementó una **Arquitectura RAG Híbrida**:

1. **Ruta Semántica (Políticas y Documentos):** 
   - Los documentos PDF son procesados, etiquetados con metadatos de dominio y vectorizados.
   - **Embeddings Locales:** `paraphrase-multilingual-MiniLM-L12-v2` (HuggingFace) para búsqueda cruzada multi-idioma sin depender de APIs externas.
   - **Vector Store:** ChromaDB (Local).
2. **Ruta Estructurada (Inventario y Catálogo):**
   - El archivo CSV se mantiene en memoria utilizando `Pandas`.
   - Se utiliza **Fuzzy Matching** (`rapidfuzz`) para tolerar errores de tipeo en marcas o productos (Ej: "Arroz Gayo" -> "Arroz Gallo").
3. **Orquestación y LLM:** 
   - LangChain Expression Language (LCEL) orquesta la unión de ambos contextos.
   - **LLM:** `gemini-3.5-flash-lite` de Google, elegido por su alta velocidad y generosa cuota de procesamiento de lenguaje natural.

## 🛠️ Tecnologías y Herramientas Utilizadas
- **Python 3.14**
- **LangChain & LCEL** (Framework de orquestación IA)
- **Google Gemini API** (Modelo de Lenguaje)
- **ChromaDB & HuggingFace** (Base de datos vectorial y Embeddings)
- **Pandas & Rapidfuzz** (Manipulación de datos y búsqueda difusa)
- **Streamlit** (Interfaz de usuario Web)

## 💬 Ejemplos de Preguntas Soportadas
El agente tiene soporte multilingüe nativo. Puede responder en el idioma en el que se le pregunte leyendo las fuentes en español:

- **Español:** *"¿Tienen en stock Arroz Integral Molinos Ala y cuál es su precio?"*
- **Inglés:** *"What are the levels of the Central VIP Customer program?"*
- **Portugués:** *"O estacionamento tem algum custo para os clientes?"*

### 📸 Capturas de la demostración:
<img width="1190" height="527" alt="asistente_mercado_central 24h_captura01" src="https://github.com/user-attachments/assets/7f32e09b-a969-4a7f-bed9-e4323c168b99" />
<img width="1190" height="363" alt="asistente_mercado_central 24h_captura02" src="https://github.com/user-attachments/assets/4bf5c928-73ec-415f-8ddf-9da6012f2d6e" />
<img width="1190" height="585" alt="asistente_mercado_central 24h_captura03" src="https://github.com/user-attachments/assets/eb30f6a0-1446-4e35-a704-b1571f8da283" />

## 🚀 Instrucciones para ejecutar localmente

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/Pablo-Damian/Agente_Mercado_Central.git
   cd Agente_Mercado_Central
   ```

2. Crear y activar un entorno virtual:
   ```bash
   python -m venv venv
   # En Windows:
   .\venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar la API Key de Google:
   ```bash
   Crear un archivo .env en la raíz del proyecto y agregar:
   GOOGLE_API_KEY="TU_API_KEY_AQUI"
   ```

5. Ejecutar la aplicación:
   ```bash
   streamlit run app.py
   ```

☁️ Evidencia del Deploy en la Nube

La aplicación ha sido desplegada exitosamente y es accesible públicamente en el siguiente enlace:
👉 **https://agentemercadocentral.streamlit.app/**
