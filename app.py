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

    st.info("Bienvenido al Sistema")

elif menu == "Nueva Formulación":

    st.header("Nueva Formulación")

    fecha = st.date_input("Fecha")

    operador = st.text_input("Operador")

    lote = st.text_input("Código de lote")

    ro = st.number_input(
        "Residuos Orgánicos (ton)",
        min_value=0.0
    )

    rod = st.number_input(
        "Residuos Orgánicos Deshidratados (ton)",
        min_value=0.0
    )

    ld = st.number_input(
        "Lodo Deshidratado (ton)",
        min_value=0.0
    )

    carton = st.number_input(
        "Cartón (ton)",
        min_value=0.0
    )

    comentarios = st.text_area("Comentarios")

    if st.button("Guardar Formulación"):

        total = ro + rod + ld + carton

        st.success("Formulación registrada")

        st.metric(
            "Masa Total",
            f"{round(total,2)} ton"
        )

elif menu == "Seguimiento":

    st.header("Seguimiento de Lotes")

elif menu == "Inventario":

    st.header("Inventario")

elif menu == "Indicadores":

    st.header("Indicadores")
