import streamlit as st
from chatbot import inicializar_chatbot

st.set_page_config(
    page_title="Asistente Mercado Central 24h",
    page_icon="🛒",
    layout="centered"
)

# Cargar agente en caché para no recargar modelos en memoria
@st.cache_resource(show_spinner="Iniciando sistema de inteligencia artificial...")
def cargar_agente():
    return inicializar_chatbot()

agente = cargar_agente()

st.title("🛒 Asistente Virtual - Mercado Central 24h")
st.markdown("¡Hola! Soy el asistente inteligente de la tienda. Puedes preguntarme sobre políticas de devolución, Recursos Humanos, o consultar el inventario y precios.")

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Historial con ÍCONOS ORIGINALES (Persona y Robot)
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])

if pregunta := st.chat_input("Escribe tu pregunta aquí... (ej: ¿Tienen stock de arroz?)"):
    
    # Usuario original
    with st.chat_message("user"):
        st.markdown(pregunta)
    st.session_state.mensajes.append({"rol": "user", "contenido": pregunta})
    
    # Asistente robot original
    with st.chat_message("assistant"):
        with st.spinner("Procesando respuesta..."):
            try:
                respuesta = agente.invoke(pregunta)
                st.markdown(respuesta)
                st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta})
            except Exception as e:
                error_msg = f"⚠️ Error detectado: {str(e)}"
                st.error(error_msg)
                st.session_state.mensajes.append({"rol": "assistant", "contenido": error_msg})