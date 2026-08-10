import streamlit as st

st.set_page_config(
    page_title="SAFCO",
    page_icon="🌱",
    layout="wide"
)

st.title("🌱 SAFCO")
st.subheader("Sistema de Apoyo para Formulación de Compostaje")

menu = st.sidebar.radio(
    "Menú",
    [
        "Inicio",
        "Nueva Formulación",
        "Seguimiento",
        "Inventario",
        "Indicadores"
    ]
)

# Datos de insumos
insumos = {
    "RO": {"humedad": 80, "c": 48, "n": 3.2},
    "ROD": {"humedad": 15, "c": 48.3, "n": 3.26},
    "LD": {"humedad": 40, "c": 32, "n": 3.5},
    "CA": {"humedad": 0, "c": 45, "n": 0.11},
}

if menu == "Inicio":

    st.info(
        "Bienvenido al Sistema de Apoyo para Formulación de Compostaje"
    )

elif menu == "Nueva Formulación":

    st.header("Nueva Formulación")

    fecha = st.date_input("Fecha")

    operador = st.text_input(
        "Operador",
        value="Mishel Ruiz"
    )

   
