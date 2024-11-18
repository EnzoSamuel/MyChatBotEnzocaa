import streamlit as st
from groq import Groq
import json
import os
import uuid
import hashlib
from datetime import datetime

# Configuración inicial
HISTORIAL_FILE = "historial_chat.json"
MODELOS = ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"]

# Configurar la página (mover esta llamada al principio)
st.set_page_config(layout="wide", page_title="Eudaimon")
st.title("🤖 Eudaimon Chatbot by Enzo")

# Crear cliente Groq
def crear_usuario_groq():
    clave_usuario = st.secrets["CLAVE_API"]
    return Groq(api_key=clave_usuario)

# Configurar el modelo
def configurar_modelo(cliente, modelo, mensajeDeEntrada):
    try:
        return cliente.chat.completions.create(
            model=modelo,
            messages=[ 
                {"role": "system", "content": "Responde siempre en español."},
                {"role": "user", "content": mensajeDeEntrada}
            ],
            stream=True
        )
    except Exception as e:
        st.error(f"Error en la API: {e}")
        return None

# Generar respuesta
def generar_respuesta(chat_completo):
    respuesta_completa = ""
    for frase in chat_completo:
        if frase.choices[0].delta.content:
            respuesta_completa += frase.choices[0].delta.content
            yield frase.choices[0].delta.content
    return respuesta_completa

# Inicializar estado de la sesión
def inicializar_estado():
    if 'historial_chat' not in st.session_state:
        st.session_state.historial_chat = []  # Inicializa historial_chat
    if 'historial_chat_hash' not in st.session_state:
        st.session_state.historial_chat_hash = ''
    if 'historial_chat_str' not in st.session_state:
        st.session_state.historial_chat_str = ''
    if 'mensajes' not in st.session_state:
        st.session_state.mensajes = []
    if 'token' not in st.session_state:
        st.session_state.token = str(uuid.uuid4())

# Actualizar y mostrar historial
def actualizar_historial(rol, contenido, avatar):
    timestamp = str(datetime.now())  # Funciona correctamente ahora
    st.session_state.historial_chat.append({"role": rol, "content": contenido, "avatar": avatar, "timestamp": timestamp})
    guardar_historial_cookies()

def mostrar_historial():
    # Asegurarse de que el historial esté inicializado
    if 'historial_chat' in st.session_state:
        for mensaje in st.session_state.historial_chat:
            style = "color: white;" if mensaje["role"] == "user" else "color: green;"
            with st.chat_message(mensaje["role"], avatar=mensaje["avatar"]):
                st.markdown(f"<span style='{style}'>{mensaje['content']}</span>", unsafe_allow_html=True)

# Aplicar estilo visual a mensajes
def aplicar_estilo_mensaje(rol, contenido):
    style = "color: white;" if rol == "user" else "color: green;"
    return f"<span style='{style}'>{contenido}</span>"

# Configurar la página
def configurar_pagina():
    # Barra lateral
    st.sidebar.title("Configuración")
    modelo_seleccionado = st.sidebar.selectbox("Seleccionar modelo", MODELOS, index=0)
    st.sidebar.markdown("---")
    st.sidebar.markdown("💡 **Consejo**: Estás interactuando en español.")
    
    # Botón para borrar historial
    if st.sidebar.button("🗑️ Borrar historial"):
        inicializar_historial()  # Borra historial solo cuando lo pida el usuario
        st.sidebar.success("El historial ha sido eliminado.")
    
    return modelo_seleccionado

# Área de chat
def area_de_chat():
    with st.container():
        mostrar_historial()

# Función para guardar el historial de cookies
def guardar_historial_cookies():
    st.session_state.historial_chat.sort(key=lambda x: x['timestamp'], reverse=True)
    st.session_state.historial_chat = st.session_state.historial_chat[:100]  # Limitar a los últimos 100 mensajes
    st.session_state.historial_chat_str = json.dumps(st.session_state.historial_chat)
    st.session_state.historial_chat_hash = hashlib.sha256(st.session_state.historial_chat_str.encode()).hexdigest()

# Inicializar historial
def inicializar_historial():
    st.session_state.historial_chat = []  # Solo borra el historial cuando se presiona el botón

# Aplicación principal
def main():
    inicializar_estado()  # Inicializa el estado antes de usar session_state
    usuario = crear_usuario_groq()
    modelo_actual = configurar_pagina()
    area_de_chat()

    # Entrada del usuario
    mensaje = st.chat_input("Escribe tu mensaje...")
    if mensaje:
        actualizar_historial("user", mensaje, "😊")
        respuesta_chat_bot = configurar_modelo(usuario, modelo_actual, mensaje)

        if respuesta_chat_bot:
            with st.chat_message("assistant", avatar="🤖"):
                respuesta_completa = st.write_stream(generar_respuesta(respuesta_chat_bot))
                actualizar_historial("assistant", respuesta_completa, "🤖")

if __name__ == "__main__":
    main()
