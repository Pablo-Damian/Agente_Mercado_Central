import os
import re
import warnings
import pandas as pd
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.documents import Document
from rapidfuzz import fuzz

load_dotenv()

CARPETA_DATOS = "./datos"
CARPETA_BD = "./chroma_db_v2"

CAMPOS_PRODUCTO = ["Descripción", "Marca", "Categoría", "Subcategoría", "SKU"]

STOPWORDS_ES = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y", "o", "del",
    "con", "para", "por", "en", "que", "cual", "cuál", "cuales", "cuáles",
    "cualquier", "cualquiera", "todos", "todas", "todo", "toda", "hay", "tiene",
    "tienen", "tienes", "quiero", "busco", "necesito", "me", "mi", "su", "sus",
    "es", "son", "precio", "precios", "cuesta", "cuestan", "vale", "valen",
    "cuanto", "cuánto", "producto", "productos", "marca", "marcas", "algo",
    "sobre", "tienda", "hola"
}

def cargar_documentos_pdf():
    documentos = []
    for archivo in sorted(os.listdir(CARPETA_DATOS)):
        if not archivo.endswith(".pdf"):
            continue
        ruta_completa = os.path.join(CARPETA_DATOS, archivo)
        loader = PyPDFLoader(ruta_completa)
        docs = loader.load()

        # Nombres explícitos para no confundir a la IA
        if "Atención al Cliente" in archivo:
            tipo_doc = "POLÍTICA DE DEVOLUCIONES Y CLIENTES"
        elif "Proveedores" in archivo:
            tipo_doc = "MANUAL DE PROVEEDORES"
        elif "Reglamento" in archivo:
            tipo_doc = "REGLAMENTO INTERNO DE EMPLEADOS"
        else:
            tipo_doc = "PREGUNTAS FRECUENTES (FAQ)"

        for doc in docs:
            doc.page_content = f"[{tipo_doc}]\n{doc.page_content}"
        documentos.extend(docs)
    return documentos

def cargar_catalogo_productos() -> pd.DataFrame:
    dfs = []
    for archivo in sorted(os.listdir(CARPETA_DATOS)):
        if archivo.endswith(".csv"):
            ruta_completa = os.path.join(CARPETA_DATOS, archivo)
            try:
                df = pd.read_csv(ruta_completa, sep=",")
                dfs.append(df)
            except Exception:
                pass
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def crear_base_de_datos():
    embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
    if os.path.exists(CARPETA_BD):
        return Chroma(persist_directory=CARPETA_BD, embedding_function=embeddings)
    documentos_crudos = cargar_documentos_pdf()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    splits = text_splitter.split_documents(documentos_crudos)
    return Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory=CARPETA_BD)

def formatear_documentos(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs) if docs else ""

def extraer_palabras_clave(texto: str) -> list[str]:
    palabras = re.findall(r"\b\w+\b", texto.lower())
    return [p for p in palabras if p not in STOPWORDS_ES and len(p) > 2]

def buscar_productos_fuzzy(terminos: list[str], df: pd.DataFrame, limite: int = 15, umbral: int = 55) -> pd.DataFrame:
    if df.empty or not terminos:
        return df.iloc[0:0]

    def score_fila(row) -> float:
        texto_fila = " ".join(str(row.get(c, "")) for c in CAMPOS_PRODUCTO).lower()
        scores = [
            max(fuzz.partial_ratio(t.lower(), texto_fila), fuzz.token_set_ratio(t.lower(), texto_fila))
            for t in terminos
        ]
        return sum(scores) / len(scores) if scores else 0

    df = df.copy()
    df["_score"] = df.apply(score_fila, axis=1)
    resultados = df[df["_score"] >= umbral].sort_values("_score", ascending=False)
    return resultados.drop(columns="_score").head(limite)

def formatear_resultados_productos(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    lineas = ["[INVENTARIO Y PRECIOS DE PRODUCTOS]"]
    for _, row in df.iterrows():
        lineas.append(
            f"Producto: {row.get('Descripción', 'N/A')} (Marca: {row.get('Marca', 'N/A')}). "
            f"SKU: {row.get('SKU', 'N/A')}. "
            f"Categoría: {row.get('Categoría', 'N/A')} > {row.get('Subcategoría', 'N/A')}. "
            f"Ubicación: {row.get('Ubicación', 'N/A')}. "
            f"Stock: {row.get('Stock Actual', '0')} unidades. "
            f"Precio: ${row.get('Precio de Venta Unitario', '0')} ARS."
        )
    return "\n".join(lineas)

TEMPLATE = """
Eres un asistente virtual experto de 'Mercado Central 24h' (Argentina).
Responde a los usuarios utilizando ÚNICAMENTE la información del "Contexto recuperado".

Reglas:
1. El contexto incluye políticas (ej. devoluciones de perecederos/carnes) e inventario. Lee todo detalladamente.
2. Si la respuesta no está en el contexto, discúlpate amablemente sin inventar datos.
3. IMPORTANTE: Responde SIEMPRE en el MISMO IDIOMA de la pregunta (incluso si debes disculparte).
4. Formato de precios: "$[precio] ARS".

Contexto recuperado:
{context}

Pregunta del usuario: {question}

Respuesta:
"""

def inicializar_chatbot():
    vectorstore = crear_base_de_datos()
    # Aumentamos K a 10 para garantizar que encuentre la tabla de devoluciones
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})
    df_productos = cargar_catalogo_productos()

    # SOLUCIÓN DE VELOCIDAD: Usamos solo 1 modelo ultrarrápido sin reintentos (gemini-3.5-flash-lite)
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.1)

    prompt = ChatPromptTemplate.from_template(TEMPLATE)

    def obtener_contexto(pregunta: str) -> dict:
        palabras_clave = extraer_palabras_clave(pregunta)
        productos_df = buscar_productos_fuzzy(palabras_clave, df_productos)
        contexto_productos = formatear_resultados_productos(productos_df)

        docs_politica = retriever.invoke(pregunta)
        contexto_politica = formatear_documentos(docs_politica)

        contexto_completo = "\n\n".join(filter(None, [contexto_productos, contexto_politica]))
        if not contexto_completo:
            contexto_completo = "(No hay contexto)"

        return {"context": contexto_completo, "question": pregunta}

    rag_chain = RunnableLambda(obtener_contexto) | prompt | llm | StrOutputParser()
    return rag_chain

if __name__ == "__main__":
    print("\n🏪 INICIANDO AGENTE VELOZ...")
    agente = inicializar_chatbot()
    print("(Escribe 'salir' para terminar)")
    while True:
        pregunta = input("\n👤 Tú: ")
        if pregunta.lower() in ['salir', 'exit', 'quit', 'sair']:
            break
        respuesta = agente.invoke(pregunta)
        print(f"\n🟢 Asistente: {respuesta}")