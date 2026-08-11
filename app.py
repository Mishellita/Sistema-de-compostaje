import streamlit as st

st.set_page_config(
    page_title="SAFCO",
    page_icon="🌱",
    layout="wide"
)

st.title("🌱SAFCO")
st.subheader("Sistema de Apoyo para Formulación de Compostaje")

menu = st.sidebar.radio(
    "Menú",
    [
        "Inicio",
        "Nueva Formulación",
        "Capacidad de lodo",
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

    lote = st.text_input(
        "Código de lote",
        value="CMP-001-2026"
    )

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

        agua_total = 0
        masa_seca_total = 0
        carbono_total = 0
        nitrogeno_total = 0

        for material, masa in masas.items():

            humedad = insumos[material]["humedad"]

            masa_seca = masa * (1 - humedad / 100)

            agua = masa - masa_seca

            carbono = masa_seca * insumos[material]["c"] / 100

            nitrogeno = masa_seca * insumos[material]["n"] / 100

            agua_total += agua
            masa_seca_total += masa_seca
            carbono_total += carbono
            nitrogeno_total += nitrogeno

        if masa_total > 0:

            humedad_mezcla = (
                agua_total / masa_total
            ) * 100

            carbono_pct = (
                carbono_total / masa_seca_total
            ) * 100

            nitrogeno_pct = (
                nitrogeno_total / masa_seca_total
            ) * 100

            relacion_cn = (
                carbono_pct / nitrogeno_pct
            )

            if humedad_mezcla < 50:
                estado_humedad = "BAJA"
            elif humedad_mezcla > 60:
                estado_humedad = "ALTA"
            else:
                estado_humedad = "CORRECTA"

            if relacion_cn < 25:
                estado_cn = "BAJO"
            elif relacion_cn > 35:
                estado_cn = "ALTO"
            else:
                estado_cn = "CORRECTO"

            if (
                estado_humedad == "CORRECTA"
                and estado_cn == "CORRECTO"
            ):
                estado_formulacion = "APROBADA"
            else:
                estado_formulacion = "REFORMULAR"

            st.success("Cálculo realizado correctamente")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Masa Total",
                    f"{masa_total:.2f} ton"
                )

            with col2:
                st.metric(
                    "Humedad Inicial",
                    f"{humedad_mezcla:.2f}%"
                )

            with col3:
                st.metric(
                    "Relación C/N",
                    f"{relacion_cn:.2f}"
                )
            st.subheader("Evaluación")

            st.write(
                f"Estado Humedad: {estado_humedad}"
            )

            st.write(
                f"Estado Relación C/N: {estado_cn}"
            )

            st.write(
                f"Estado Formulación: {estado_formulacion}"
            )

            if estado_humedad == "BAJA":
                st.warning(
                    "Incrementar humedad antes de conformar la pila."
                )

            if estado_humedad == "ALTA":
                st.warning(
                    "Agregar material estructurante seco."
                )

            if estado_cn == "BAJO":
                st.warning(
                    "Agregar materiales ricos en carbono."
                )

            if estado_cn == "ALTO":
                st.warning(
                    "Agregar materiales ricos en nitrógeno."
                )
elif menu == "Capacidad de lodo":

    st.header("Capacidad de lodo")

    st.write(
        "Estima la cantidad máxima de lodo que puede incorporarse "
        "según los criterios de relación C/N y humedad de la formulación inicial."
    )

    ro_cap = st.number_input(
        "Residuos Orgánicos disponibles (ton)",
        min_value=0.0,
        value=0.0,
        key="ro_cap"
    )

    rod_cap = st.number_input(
        "Residuos Orgánicos Deshidratados disponibles (ton)",
        min_value=0.0,
        value=0.0,
        key="rod_cap"
    )

    ca_cap = st.number_input(
        "Cartón / Material estructurante disponible (ton)",
        min_value=0.0,
        value=0.0,
        key="ca_cap"
    )
