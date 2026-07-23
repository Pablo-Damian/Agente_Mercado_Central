import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Cargar la clave secreta desde el archivo .env
load_dotenv()

# Inicializar el modelo Gemini 3.5 Flash
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash", # <--- el modelo más moderno y potente
    temperature=0.3
)

# Hacerle una pregunta de prueba
print("🤖 Enviando pregunta a Gemini...")
respuesta = llm.invoke("Hola Gemini, responde en español: ¿Cuál es la capital de Argentina y cuál es su comida típica?")

print("\n✅ Respuesta de Gemini:")
print(respuesta.content)