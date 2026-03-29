import streamlit as st

st.set_page_config(page_title="Txomin - Modo Puerto", page_icon="⚓")

st.title("🔱 Txomin v.0 - Modo Emergencia")
st.write("Si ves esto, el casco de la app está sano. El problema era la conexión con los satélites.")

tab1, tab2, tab3 = st.tabs(["⚓ ESTADO", "🗺️ MAPA", "🐟 ESPECIES"])

with tab1:
    st.header("Análisis de Puerto")
    st.info("Estamos en modo offline para verificar que la interfaz carga correctamente.")
    st.metric("Viento (Media)", "12 km/h")
    st.metric("Olatua", "1.2 m")

with tab2:
    st.write("Aquí irá el mapa de Mutriku una vez restablezcamos la corriente.")

with tab3:
    st.write("1. **Sargoa**: En las espumas.")
    st.write("2. **Lupina**: Spinning al amanecer.")
