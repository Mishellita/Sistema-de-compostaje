import streamlit as st
import pandas as pd
df_insumos = pd.read_csv("insumos.csv")
df_parametros = pd.read_csv("parametros.csv")
df_reglas = pd.read_csv("reglas.csv")
insumos = {
    fila["codigo"]: {
        "humedad": fila["humedad"],
        "c": fila["carbono"],
        "n": fila["nitrogeno"]
    }
    for _, fila in df_insumos.iterrows()
}
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
    fila_mesofila = df_parametros[
        df_parametros["fase"] == "Mesofila I"
    ].iloc[0]
    
    hum_min = fila_mesofila["humedad_min"]
    hum_max = fila_mesofila["humedad_max"]
    cn_min = fila_mesofila["cn_min"]
    cn_max = fila_mesofila["cn_max"]
    
    carbono_sin_lodo = (
        ro_cap * (1 - insumos["RO"]["humedad"] / 100) * insumos["RO"]["c"] / 100
        + rod_cap * (1 - insumos["ROD"]["humedad"] / 100) * insumos["ROD"]["c"] / 100
        + ca_cap * (1 - insumos["CA"]["humedad"] / 100) * insumos["CA"]["c"] / 100
    )
    
    nitrogeno_sin_lodo = (
        ro_cap * (1 - insumos["RO"]["humedad"] / 100) * insumos["RO"]["n"] / 100
        + rod_cap * (1 - insumos["ROD"]["humedad"] / 100) * insumos["ROD"]["n"] / 100
        + ca_cap * (1 - insumos["CA"]["humedad"] / 100) * insumos["CA"]["n"] / 100
    )
    carbono_por_ton_lodo = (
        (1 - insumos["LD"]["humedad"] / 100)
        * insumos["LD"]["c"] / 100
    )
    
    nitrogeno_por_ton_lodo = (
        (1 - insumos["LD"]["humedad"] / 100)
        * insumos["LD"]["n"] / 100
    )
    denominador_cn = (
        cn_min * nitrogeno_por_ton_lodo
        - carbono_por_ton_lodo
    )
    
    if denominador_cn != 0:
        lodo_por_cn = (
            carbono_sin_lodo
            - cn_min * nitrogeno_sin_lodo
        ) / denominador_cn
    else:
        lodo_por_cn = 0
    
    lodo_por_cn = max(0, lodo_por_cn)
    st.write("Lodo máximo por C/N:", round(lodo_por_cn, 4), "ton")
    agua_sin_lodo = (
        ro_cap * insumos["RO"]["humedad"] / 100
        + rod_cap * insumos["ROD"]["humedad"] / 100
        + ca_cap * insumos["CA"]["humedad"] / 100
    )
    
    masa_sin_lodo = ro_cap + rod_cap + ca_cap
    
    humedad_lodo = insumos["LD"]["humedad"] / 100
    humedad_max = hum_max / 100
    
    if humedad_lodo <= humedad_max:
        lodo_por_humedad = None
    else:
        lodo_por_humedad = (
            humedad_max * masa_sin_lodo - agua_sin_lodo
        ) / (
            humedad_lodo - humedad_max
        )
    if lodo_por_humedad is None:
        st.write("Límite por humedad: NO LIMITA")
    else:
        st.write(
            "Lodo máximo por humedad:",
            round(lodo_por_humedad, 4),
            "ton"
        )
    if lodo_por_humedad is None:
        lodo_recomendado = lodo_por_cn
    else:
        lodo_recomendado = min(lodo_por_cn, lodo_por_humedad)
        st.write(
            "Lodo recomendado:",
            round(lodo_recomendado, 4),
            "ton"
        )
    st.subheader("Resultado del simulador")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Lodo máximo por C/N",
            f"{lodo_por_cn:.2f} ton"
        )
    
    with col2:
        if lodo_por_humedad is None:
            st.metric(
                "Límite por humedad",
                "NO LIMITA"
            )
        else:
            st.metric(
                "Lodo máximo por humedad",
                f"{lodo_por_humedad:.2f} ton"
            )
    
    with col3:
        st.metric(
            "Lodo recomendado final",
            f"{lodo_recomendado:.2f} ton"
        )
    masa_total_formulacion = masa_sin_lodo + lodo_recomendado
    
    agua_total_formulacion = (
        agua_sin_lodo
        + lodo_recomendado * humedad_lodo
    )
    
    if masa_total_formulacion > 0:
        humedad_resultante = (
            agua_total_formulacion / masa_total_formulacion
        ) * 100
    else:
        humedad_resultante = 0
    
    carbono_final = (
        carbono_sin_lodo
        + lodo_recomendado * carbono_por_ton_lodo
    )
    
    nitrogeno_final = (
        nitrogeno_sin_lodo
        + lodo_recomendado * nitrogeno_por_ton_lodo
    )
    
    if nitrogeno_final > 0:
        cn_resultante = carbono_final / nitrogeno_final
    else:
        cn_resultante = 0
    st.subheader("Resultados de la formulación")
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric(
            "Masa total de formulación",
            f"{masa_total_formulacion:.2f} ton"
        )
    
    with col5:
        st.metric(
            "Humedad resultante",
            f"{humedad_resultante:.2f}%"
        )
    
    with col6:
        st.metric(
            "Relación C/N resultante",
            f"{cn_resultante:.2f}"
        )
    cn_evaluado = round(cn_resultante, 2)
    humedad_evaluada = round(humedad_resultante, 2)
    
    if (
        cn_evaluado < cn_min
        or cn_evaluado > cn_max
        or humedad_evaluada > hum_max
    ):
        estado_simulador = "NO ADMISIBLE"
    
    elif humedad_evaluada < hum_min:
        estado_simulador = "ADMISIBLE CON AJUSTE DE HUMEDAD"
    
    else:
        estado_simulador = "ADMISIBLE"
    st.subheader("Evaluación")
    if estado_simulador == "ADMISIBLE":
        st.success("Resultado: ADMISIBLE")
    
    elif estado_simulador == "ADMISIBLE CON AJUSTE DE HUMEDAD":
        st.warning("Resultado: ADMISIBLE CON AJUSTE DE HUMEDAD")
    
    else:
        st.error("Resultado: NO ADMISIBLE")
    
    clave_regla = f"ESTADO DE CAPACIDAD|{estado_simulador}"
    
    fila_regla = df_reglas[
        df_reglas["clave"] == clave_regla
    ]
    
    if not fila_regla.empty:
        recomendacion = fila_regla.iloc[0]["recomendacion"]
    else:
        recomendacion = "Regla no encontrada"
    st.info(f"Recomendación: {recomendacion}")
