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

# DATOS DE INSUMOS
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

    operador = st.text_input("Operador")

    lote = st.text_input("Código de lote")

    ro = st.number_input(
        "Residuos Orgánicos (ton)",
        min_value=0.0,
        value=0.0
    )

    rod = st.number_input(
        "Residuos Orgánicos Deshidratados (ton)",
        min_value=0.0,
        value=0.0
    )

    ld = st.number_input(
        "Lodo Deshidratado (ton)",
        min_value=0.0,
        value=0.0
    )

    ca = st.number_input(
        "Cartón (ton)",
        min_value=0.0,
        value=0.0
    )

    comentarios = st.text_area("Comentarios")

    if st.button("Calcular Formulación"):

        masas = {
            "RO": ro,
            "ROD": rod,
            "LD": ld,
            "CA": ca
        }

      masa_total = sum(masas.values())
