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

if menu == "Inicio":

    st.header("Inicio")

    st.info(
        "Bienvenido al Sistema de Apoyo para Formulación de Compostaje"
    )

elif menu == "Nueva Formulación":

    st.header("Nueva Formulación")

    st.number_input(
        "Toneladas de Residuos Orgánicos"
    )

    st.number_input(
        "Toneladas de Residuos Orgánicos Deshidratados"
    )

    st.number_input(
        "Toneladas de Lodo Deshidratado"
    )

    st.number_input(
        "Toneladas de Cartón"
    )

    st.button("Calcular")

elif menu == "Seguimiento":

    st.header("Seguimiento de Lotes")

elif menu == "Inventario":

    st.header("Inventario")

elif menu == "Indicadores":

    st.header("Indicadores")
