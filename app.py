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

    st.title("SAFCO")
    st.subheader("Sistema de Apoyo para Formulación y Control de Compostaje")

    st.info(
        "Seleccione un módulo desde el menú lateral para registrar información, "
        "evaluar el proceso de compostaje o consultar indicadores."
    )

    st.subheader("Resumen operativo")

    df_inv_inicio = pd.read_csv("Inventario.csv")
    df_seg_inicio = pd.read_csv("seguimiento.csv")
    df_form_inicio = pd.read_csv("formulaciones.csv")

    # Stock total
    for columna in [
        "compost_ingresado",
        "salida_remediacion",
        "salida_donacion"
    ]:
        df_inv_inicio[columna] = pd.to_numeric(
            df_inv_inicio[columna],
            errors="coerce"
        ).fillna(0)

    stock_inicio = (
        df_inv_inicio["compost_ingresado"].sum()
        - df_inv_inicio["salida_remediacion"].sum()
        - df_inv_inicio["salida_donacion"].sum()
    )

    # Alertas
    if not df_seg_inicio.empty:

        df_seg_inicio["estado_general"] = (
            df_seg_inicio["estado_general"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        alertas_inicio = (
            df_seg_inicio["estado_general"]
            == "REQUIERE AJUSTE OPERATIVO"
        ).sum()

    else:
        alertas_inicio = 0

    # Lotes registrados
    if not df_form_inicio.empty:

        lotes_registrados = (
            df_form_inicio["codigo_lote"]
            .dropna()
            .astype(str)
            .nunique()
        )

    else:
        lotes_registrados = 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Lotes registrados",
            lotes_registrados
        )

    with col2:
        st.metric(
            "Alertas activas",
            int(alertas_inicio)
        )

    with col3:
        st.metric(
            "Stock disponible",
            f"{stock_inicio:.2f} ton"
        )

    st.subheader("Módulos disponibles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(
            "🧪 NUEVA FORMULACIÓN\n\n"
            "Registra materiales y evalúa humedad y relación C/N."
        )
    
        st.info(
            "🌡️ SEGUIMIENTO\n\n"
            "Registra temperatura, humedad, pH y genera recomendaciones."
        )
    
        st.info(
            "📊 INDICADORES\n\n"
            "Consulta producción, valorización, alertas y gráficos del proceso."
        )
    
    with col2:
        st.info(
            "🧮 CAPACIDAD DE LODO\n\n"
            "Estima cuánto lodo puede incorporarse según los criterios de formulación."
        )
    
        st.info(
            "📦 INVENTARIO\n\n"
            "Controla ingresos, salidas y stock disponible por lote."
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
        "Residuos Orgánicos añadidos (ton)",
        min_value=0.0,
        value=0.0
    )

    rod = st.number_input(
        "Residuos Orgánicos Deshidratados añadidos (ton)",
        min_value=0.0,
        value=0.0
    )

    ld = st.number_input(
        "Lodo Deshidratado añadido (ton)",
        min_value=0.0,
        value=0.0
    )

    ca = st.number_input(
        "Cartón / Material estructurante añadido (ton)",
        min_value=0.0,
        value=0.0
    )

    comentarios = st.text_area("Comentarios")

    if st.button("Calcular Formulación"):

        # =========================
        # LEER HISTORIAL DEL LOTE
        # =========================

        df_form_hist = pd.read_csv("formulaciones.csv")

        registros_lote = df_form_hist[
            df_form_hist["codigo_lote"].astype(str)
            == str(lote)
        ]

        if not registros_lote.empty:

            ro_prev = pd.to_numeric(
                registros_lote["ro_ingreso"],
                errors="coerce"
            ).fillna(0).sum()

            rod_prev = pd.to_numeric(
                registros_lote["rod_ingreso"],
                errors="coerce"
            ).fillna(0).sum()

            ld_prev = pd.to_numeric(
                registros_lote["ld_ingreso"],
                errors="coerce"
            ).fillna(0).sum()

            ca_prev = pd.to_numeric(
                registros_lote["ca_ingreso"],
                errors="coerce"
            ).fillna(0).sum()

        else:

            ro_prev = 0
            rod_prev = 0
            ld_prev = 0
            ca_prev = 0

        # =========================
        # ACUMULADO DEL LOTE
        # =========================

        ro_acumulado = ro_prev + ro
        rod_acumulado = rod_prev + rod
        ld_acumulado = ld_prev + ld
        ca_acumulado = ca_prev + ca

        masas = {
            "RO": ro_acumulado,
            "ROD": rod_acumulado,
            "LD": ld_acumulado,
            "CA": ca_acumulado
        }

        masa_total = sum(masas.values())

        agua_total = 0
        masa_seca_total = 0
        carbono_total = 0
        nitrogeno_total = 0

        for material, masa in masas.items():

            humedad = insumos[material]["humedad"]

            masa_seca = masa * (
                1 - humedad / 100
            )

            agua = masa - masa_seca

            carbono = (
                masa_seca
                * insumos[material]["c"]
                / 100
            )

            nitrogeno = (
                masa_seca
                * insumos[material]["n"]
                / 100
            )

            agua_total += agua
            masa_seca_total += masa_seca
            carbono_total += carbono
            nitrogeno_total += nitrogeno

        if masa_total > 0:

            humedad_mezcla = (
                agua_total / masa_total
            ) * 100

            if nitrogeno_total > 0:
                relacion_cn = (
                    carbono_total
                    / nitrogeno_total
                )
            else:
                relacion_cn = 0

            fila_mesofila = df_parametros[
                df_parametros["fase"]
                == "Mesofila I"
            ].iloc[0]

            hum_min = fila_mesofila[
                "humedad_min"
            ]

            hum_max = fila_mesofila[
                "humedad_max"
            ]

            cn_min = fila_mesofila[
                "cn_min"
            ]

            cn_max = fila_mesofila[
                "cn_max"
            ]

            # =========================
            # ESTADOS
            # =========================

            if humedad_mezcla < hum_min:
                estado_humedad = "BAJA"

            elif humedad_mezcla > hum_max:
                estado_humedad = "ALTA"

            else:
                estado_humedad = "CORRECTA"

            if relacion_cn < cn_min:
                estado_cn = "BAJO"

            elif relacion_cn > cn_max:
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

            # =========================
            # REGISTRO HISTÓRICO
            # =========================

            nueva_formulacion = pd.DataFrame([{
                "fecha": fecha,
                "operador": operador,
                "codigo_lote": lote,

                "ro_ingreso": ro,
                "rod_ingreso": rod,
                "ld_ingreso": ld,
                "ca_ingreso": ca,

                "ro_acumulado": ro_acumulado,
                "rod_acumulado": rod_acumulado,
                "ld_acumulado": ld_acumulado,
                "ca_acumulado": ca_acumulado,

                "masa_acumulada": masa_total,
                "humedad_inicial": humedad_mezcla,
                "relacion_cn": relacion_cn,
                "estado_formulacion": estado_formulacion
            }])

            nueva_formulacion.to_csv(
                "formulaciones.csv",
                mode="a",
                header=False,
                index=False
            )

            st.success(
                "Ingreso registrado y formulación acumulada calculada correctamente"
            )

            # =========================
            # RESULTADOS
            # =========================

            st.caption(
                f"El cálculo corresponde al acumulado del lote {lote}."
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Masa acumulada del lote",
                    f"{masa_total:.2f} ton"
                )

            with col2:
                st.metric(
                    "Humedad acumulada",
                    f"{humedad_mezcla:.2f}%"
                )

            with col3:
                st.metric(
                    "Relación C/N acumulada",
                    f"{relacion_cn:.2f}"
                )

            st.subheader(
                "Composición acumulada del lote"
            )

            col4, col5, col6, col7 = (
                st.columns(4)
            )

            with col4:
                st.metric(
                    "RO acumulado",
                    f"{ro_acumulado:.2f} ton"
                )

            with col5:
                st.metric(
                    "ROD acumulado",
                    f"{rod_acumulado:.2f} ton"
                )

            with col6:
                st.metric(
                    "Lodo acumulado",
                    f"{ld_acumulado:.2f} ton"
                )

            with col7:
                st.metric(
                    "Estructurante acumulado",
                    f"{ca_acumulado:.2f} ton"
                )

            # =========================
            # EVALUACIÓN
            # =========================

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

            # =========================
            # RECOMENDACIONES
            # =========================

            clave_humedad = (
                f"HUMEDAD INICIAL|"
                f"{estado_humedad}"
            )

            fila_humedad = df_reglas[
                df_reglas["clave"]
                == clave_humedad
            ]

            clave_cn = (
                f"RELACION C/N|"
                f"{estado_cn}"
            )

            fila_cn = df_reglas[
                df_reglas["clave"]
                == clave_cn
            ]

            if not fila_humedad.empty:
                st.info(
                    "Recomendación humedad: "
                    f"{fila_humedad.iloc[0]['recomendacion']}"
                )

            if not fila_cn.empty:
                st.info(
                    "Recomendación C/N: "
                    f"{fila_cn.iloc[0]['recomendacion']}"
                )

        else:

            st.warning(
                "Ingrese al menos una cantidad de material "
                "para realizar la formulación."
            )

    # =========================
    # HISTORIAL
    # =========================

    st.subheader(
        "Historial de formulaciones"
    )

    df_form_hist = pd.read_csv(
        "formulaciones.csv"
    )

    if not df_form_hist.empty:

        lotes_disponibles = sorted(
            df_form_hist[
                "codigo_lote"
            ]
            .dropna()
            .astype(str)
            .unique()
        )

        lote_filtro = st.selectbox(
            "Seleccionar código de lote",
            ["Todos"] + lotes_disponibles,
            key="filtro_lote_formulacion"
        )

        if lote_filtro == "Todos":

            df_form_filtrado = (
                df_form_hist
            )

        else:

            df_form_filtrado = (
                df_form_hist[
                    df_form_hist[
                        "codigo_lote"
                    ].astype(str)
                    == lote_filtro
                ]
            )

        st.dataframe(
            df_form_filtrado,
            use_container_width=True
        )

    else:

        st.info(
            "Aún no existen formulaciones registradas."
        )

elif menu == "Capacidad de lodo":

    st.header("Capacidad de lodo")

    st.write(
        "Este módulo permite estimar cuánto lodo puede incorporarse "
        "según los materiales disponibles o qué ajuste necesita una "
        "mezcla cuando se desea procesar una cantidad específica de lodo."
    )

    # ============================================================
    # PARÁMETROS MESÓFILA I
    # ============================================================

    fila_mesofila = df_parametros[
        df_parametros["fase"] == "Mesofila I"
    ].iloc[0]

    hum_min = float(fila_mesofila["humedad_min"])
    hum_max = float(fila_mesofila["humedad_max"])
    cn_min = float(fila_mesofila["cn_min"])
    cn_max = float(fila_mesofila["cn_max"])

    # Objetivo operativo dentro del rango técnico de humedad
    hum_objetivo = (hum_min + hum_max) / 2

    # ============================================================
    # SELECCIÓN DEL MODO
    # ============================================================

    modo_capacidad = st.radio(
        "Seleccione el tipo de cálculo",
        [
            "Calcular lodo máximo según materiales disponibles",
            "Calcular ajuste para una cantidad de lodo a procesar"
        ]
    )

    # ============================================================
    # MODO 1
    # CALCULAR LODO MÁXIMO SEGÚN MATERIALES DISPONIBLES
    # ============================================================

    if modo_capacidad == "Calcular lodo máximo según materiales disponibles":

        st.subheader("Materiales disponibles")

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
            "Cartón disponible (ton)",
            min_value=0.0,
            value=0.0,
            key="ca_cap"
        )

        as_cap = st.number_input(
            "Aserrín disponible (ton)",
            min_value=0.0,
            value=0.0,
            key="as_cap"
        )

            if as_cap > 0:
        st.warning(
            "Las propiedades del aserrín utilizadas en el cálculo "
            "son valores referenciales. Se recomienda actualizar "
            "humedad, carbono y nitrógeno con resultados de "
            "caracterización del material utilizado en planta."
        )

        masa_sin_lodo = (
            ro_cap
            + rod_cap
            + ca_cap
            + as_cap
        )

        # --------------------------------------------------------
        # CARBONO DE LA MEZCLA BASE
        # --------------------------------------------------------

        carbono_sin_lodo = (
            ro_cap
            * (1 - insumos["RO"]["humedad"] / 100)
            * insumos["RO"]["c"] / 100

            + rod_cap
            * (1 - insumos["ROD"]["humedad"] / 100)
            * insumos["ROD"]["c"] / 100

            + ca_cap
            * (1 - insumos["CA"]["humedad"] / 100)
            * insumos["CA"]["c"] / 100

            + as_cap
            * (1 - insumos["AS"]["humedad"] / 100)
            * insumos["AS"]["c"] / 100
        )

        # --------------------------------------------------------
        # NITRÓGENO DE LA MEZCLA BASE
        # --------------------------------------------------------

        nitrogeno_sin_lodo = (
            ro_cap
            * (1 - insumos["RO"]["humedad"] / 100)
            * insumos["RO"]["n"] / 100

            + rod_cap
            * (1 - insumos["ROD"]["humedad"] / 100)
            * insumos["ROD"]["n"] / 100

            + ca_cap
            * (1 - insumos["CA"]["humedad"] / 100)
            * insumos["CA"]["n"] / 100

            + as_cap
            * (1 - insumos["AS"]["humedad"] / 100)
            * insumos["AS"]["n"] / 100
        )

        # --------------------------------------------------------
        # AGUA DE LA MEZCLA BASE
        # --------------------------------------------------------

        agua_sin_lodo = (
            ro_cap
            * insumos["RO"]["humedad"] / 100

            + rod_cap
            * insumos["ROD"]["humedad"] / 100

            + ca_cap
            * insumos["CA"]["humedad"] / 100

            + as_cap
            * insumos["AS"]["humedad"] / 100
        )

        # --------------------------------------------------------
        # PROPIEDADES DEL LODO
        # --------------------------------------------------------

        humedad_lodo = (
            insumos["LD"]["humedad"] / 100
        )

        carbono_por_ton_lodo = (
            (1 - humedad_lodo)
            * insumos["LD"]["c"] / 100
        )

        nitrogeno_por_ton_lodo = (
            (1 - humedad_lodo)
            * insumos["LD"]["n"] / 100
        )

        # Solo calcular cuando existen materiales base
        if masa_sin_lodo > 0:

            # ====================================================
            # LÍMITE TÉCNICO POR C/N
            # ====================================================

            denominador_cn = (
                cn_min * nitrogeno_por_ton_lodo
                - carbono_por_ton_lodo
            )

            if denominador_cn > 0:

                lodo_por_cn = (
                    carbono_sin_lodo
                    - cn_min * nitrogeno_sin_lodo
                ) / denominador_cn

                lodo_por_cn = max(
                    0,
                    lodo_por_cn
                )

            else:

                # Si agregar lodo no reduce la relación C/N
                # hacia el límite mínimo, este criterio no limita.
                lodo_por_cn = None

            # ====================================================
            # LÍMITE TÉCNICO POR HUMEDAD MÁXIMA
            # ====================================================

            humedad_max_decimal = hum_max / 100

            if humedad_lodo > humedad_max_decimal:

                lodo_por_humedad = (
                    humedad_max_decimal * masa_sin_lodo
                    - agua_sin_lodo
                ) / (
                    humedad_lodo
                    - humedad_max_decimal
                )

                lodo_por_humedad = max(
                    0,
                    lodo_por_humedad
                )

            else:

                lodo_por_humedad = None

            # ====================================================
            # LODO PARA HUMEDAD OBJETIVO
            # ====================================================

            hum_objetivo_decimal = (
                hum_objetivo / 100
            )

            if humedad_lodo > hum_objetivo_decimal:

                lodo_por_humedad_objetivo = (
                    hum_objetivo_decimal * masa_sin_lodo
                    - agua_sin_lodo
                ) / (
                    humedad_lodo
                    - hum_objetivo_decimal
                )

                lodo_por_humedad_objetivo = max(
                    0,
                    lodo_por_humedad_objetivo
                )

            else:

                lodo_por_humedad_objetivo = None

            # ====================================================
            # MÁXIMO TÉCNICAMENTE ADMISIBLE
            # ====================================================

            limites_tecnicos = []

            if lodo_por_cn is not None:
                limites_tecnicos.append(lodo_por_cn)

            if lodo_por_humedad is not None:
                limites_tecnicos.append(lodo_por_humedad)

            if limites_tecnicos:

                lodo_maximo_admisible = min(
                    limites_tecnicos
                )

            else:

                lodo_maximo_admisible = 0

            # ====================================================
            # RESTRICCIÓN DOMINANTE
            # ====================================================

            if (
                lodo_por_cn is not None
                and lodo_por_humedad is not None
            ):

                if lodo_por_cn < lodo_por_humedad:
                    restriccion_dominante = "C/N"

                elif lodo_por_humedad < lodo_por_cn:
                    restriccion_dominante = "HUMEDAD"

                else:
                    restriccion_dominante = "C/N Y HUMEDAD"

            elif lodo_por_cn is not None:

                restriccion_dominante = "C/N"

            elif lodo_por_humedad is not None:

                restriccion_dominante = "HUMEDAD"

            else:

                restriccion_dominante = "SIN LÍMITE CALCULABLE"

            # ====================================================
            # RECOMENDACIÓN OPERATIVA
            # ====================================================

            if (
                lodo_por_humedad_objetivo is not None
                and lodo_maximo_admisible > 0
            ):

                lodo_recomendado = min(
                    lodo_maximo_admisible,
                    lodo_por_humedad_objetivo
                )

            else:

                lodo_recomendado = (
                    lodo_maximo_admisible
                )

            # ====================================================
            # RESULTADOS DEL SIMULADOR
            # ====================================================

            st.subheader(
                "Límites técnicos"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                if lodo_por_cn is None:

                    st.metric(
                        "Límite técnico por C/N",
                        "NO LIMITA"
                    )

                else:

                    st.metric(
                        "Límite técnico por C/N",
                        f"{lodo_por_cn:.2f} ton"
                    )

            with col2:

                if lodo_por_humedad is None:

                    st.metric(
                        "Límite técnico por humedad",
                        "NO LIMITA"
                    )

                else:

                    st.metric(
                        "Límite técnico por humedad",
                        f"{lodo_por_humedad:.2f} ton"
                    )

            with col3:

                st.metric(
                    "Máximo técnicamente admisible",
                    f"{lodo_maximo_admisible:.2f} ton"
                )

            # ====================================================
            # RECOMENDACIÓN OPERATIVA
            # ====================================================

            st.subheader(
                "Recomendación operativa"
            )

            col_op1, col_op2, col_op3 = (
                st.columns(3)
            )

            with col_op1:

                st.metric(
                    "Lodo recomendado",
                    f"{lodo_recomendado:.2f} ton"
                )

            with col_op2:

                st.metric(
                    "Humedad objetivo",
                    f"{hum_objetivo:.1f}%"
                )

            with col_op3:

                st.metric(
                    "Restricción dominante",
                    restriccion_dominante
                )

            if (
                lodo_recomendado
                < lodo_maximo_admisible
            ):

                st.info(
                    f"El máximo técnicamente admisible es "
                    f"{lodo_maximo_admisible:.2f} ton de lodo. "
                    f"Sin embargo, se recomienda incorporar "
                    f"{lodo_recomendado:.2f} ton para trabajar "
                    f"con una humedad cercana al objetivo "
                    f"operativo de {hum_objetivo:.1f}%."
                )

            else:

                st.info(
                    f"La cantidad recomendada está determinada "
                    f"por el criterio de "
                    f"{restriccion_dominante}."
                )

            # ====================================================
            # FORMULACIÓN CON EL LODO RECOMENDADO
            # ====================================================

            masa_total_formulacion = (
                masa_sin_lodo
                + lodo_recomendado
            )

            agua_total_formulacion = (
                agua_sin_lodo
                + lodo_recomendado
                * humedad_lodo
            )

            if masa_total_formulacion > 0:

                humedad_resultante = (
                    agua_total_formulacion
                    / masa_total_formulacion
                ) * 100

            else:

                humedad_resultante = 0

            carbono_final = (
                carbono_sin_lodo
                + lodo_recomendado
                * carbono_por_ton_lodo
            )

            nitrogeno_final = (
                nitrogeno_sin_lodo
                + lodo_recomendado
                * nitrogeno_por_ton_lodo
            )

            if nitrogeno_final > 0:

                cn_resultante = (
                    carbono_final
                    / nitrogeno_final
                )

            else:

                cn_resultante = 0

            # ====================================================
            # RESULTADOS DE LA FORMULACIÓN
            # ====================================================

            st.subheader(
                "Resultado con la cantidad recomendada"
            )

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

            # ====================================================
            # EVALUACIÓN
            # ====================================================

            cn_evaluado = round(
                cn_resultante,
                2
            )

            humedad_evaluada = round(
                humedad_resultante,
                2
            )

            if (
                cn_evaluado < cn_min
                or cn_evaluado > cn_max
                or humedad_evaluada > hum_max
            ):

                estado_simulador = (
                    "NO ADMISIBLE"
                )

            elif humedad_evaluada < hum_min:

                estado_simulador = (
                    "ADMISIBLE CON AJUSTE DE HUMEDAD"
                )

            else:

                estado_simulador = (
                    "ADMISIBLE"
                )

            st.subheader("Evaluación")

            if estado_simulador == "ADMISIBLE":

                st.success(
                    "Resultado: ADMISIBLE"
                )

            elif (
                estado_simulador
                == "ADMISIBLE CON AJUSTE DE HUMEDAD"
            ):

                st.warning(
                    "Resultado: ADMISIBLE "
                    "CON AJUSTE DE HUMEDAD"
                )

            else:

                st.error(
                    "Resultado: NO ADMISIBLE"
                )

            clave_regla = (
                f"ESTADO DE CAPACIDAD|"
                f"{estado_simulador}"
            )

            fila_regla = df_reglas[
                df_reglas["clave"]
                == clave_regla
            ]

            if not fila_regla.empty:

                recomendacion = (
                    fila_regla.iloc[0][
                        "recomendacion"
                    ]
                )

            else:

                recomendacion = (
                    "Regla no encontrada"
                )

            st.info(
                f"Recomendación: {recomendacion}"
            )

        else:

            st.info(
                "Ingrese al menos una cantidad de material "
                "disponible para realizar la simulación."
            )

    # ============================================================
    # MODO 2
    # AJUSTAR MEZCLA PARA UNA CANTIDAD ESPECÍFICA DE LODO
    # ============================================================

    else:

        st.subheader(
            "Ajuste para una cantidad de lodo a procesar"
        )

        st.write(
            "Ingrese la cantidad de lodo que desea procesar "
            "y los materiales disponibles. SAFCO calculará "
            "si la mezcla necesita aserrín adicional para "
            "alcanzar el C/N mínimo establecido."
        )

        ro_obj = st.number_input(
            "Residuos Orgánicos disponibles (ton)",
            min_value=0.0,
            value=0.0,
            key="ro_obj"
        )

        rod_obj = st.number_input(
            "Residuos Orgánicos Deshidratados disponibles (ton)",
            min_value=0.0,
            value=0.0,
            key="rod_obj"
        )

        ca_obj = st.number_input(
            "Cartón disponible (ton)",
            min_value=0.0,
            value=0.0,
            key="ca_obj"
        )

        as_obj = st.number_input(
            "Aserrín disponible actualmente (ton)",
            min_value=0.0,
            value=0.0,
            key="as_obj"
        )

        lodo_obj = st.number_input(
            "Lodo que se desea procesar (ton)",
            min_value=0.0,
            value=0.0,
            key="lodo_obj"
        )

        masa_base = (
            ro_obj
            + rod_obj
            + ca_obj
            + as_obj
            + lodo_obj
        )

        if masa_base > 0:

            # ====================================================
            # CARBONO BASE
            # ====================================================

            carbono_base = (
                ro_obj
                * (1 - insumos["RO"]["humedad"] / 100)
                * insumos["RO"]["c"] / 100

                + rod_obj
                * (1 - insumos["ROD"]["humedad"] / 100)
                * insumos["ROD"]["c"] / 100

                + ca_obj
                * (1 - insumos["CA"]["humedad"] / 100)
                * insumos["CA"]["c"] / 100

                + as_obj
                * (1 - insumos["AS"]["humedad"] / 100)
                * insumos["AS"]["c"] / 100

                + lodo_obj
                * (1 - insumos["LD"]["humedad"] / 100)
                * insumos["LD"]["c"] / 100
            )

            # ====================================================
            # NITRÓGENO BASE
            # ====================================================

            nitrogeno_base = (
                ro_obj
                * (1 - insumos["RO"]["humedad"] / 100)
                * insumos["RO"]["n"] / 100

                + rod_obj
                * (1 - insumos["ROD"]["humedad"] / 100)
                * insumos["ROD"]["n"] / 100

                + ca_obj
                * (1 - insumos["CA"]["humedad"] / 100)
                * insumos["CA"]["n"] / 100

                + as_obj
                * (1 - insumos["AS"]["humedad"] / 100)
                * insumos["AS"]["c"] * 0
                + as_obj
                * (1 - insumos["AS"]["humedad"] / 100)
                * insumos["AS"]["n"] / 100

                + lodo_obj
                * (1 - insumos["LD"]["humedad"] / 100)
                * insumos["LD"]["n"] / 100
            )

            # ====================================================
            # PROPIEDADES DEL ASERRÍN
            # ====================================================

            carbono_por_ton_aserrin = (
                (1 - insumos["AS"]["humedad"] / 100)
                * insumos["AS"]["c"] / 100
            )

            nitrogeno_por_ton_aserrin = (
                (1 - insumos["AS"]["humedad"] / 100)
                * insumos["AS"]["n"] / 100
            )
            # ====================================================
            # ASERRÍN ADICIONAL PARA ALCANZAR C/N MÍNIMO
            # ====================================================

            denominador_aserrin = (
                carbono_por_ton_aserrin
                - cn_min
                * nitrogeno_por_ton_aserrin
            )

            if denominador_aserrin > 0:

                aserrin_adicional = (
                    cn_min * nitrogeno_base
                    - carbono_base
                ) / denominador_aserrin

            else:

                aserrin_adicional = 0

            aserrin_adicional = max(
                0,
                aserrin_adicional
            )

            aserrin_total = (
                as_obj
                + aserrin_adicional
            )

            # ====================================================
            # C/N FINAL
            # ====================================================

            carbono_final_ajuste = (
                carbono_base
                + aserrin_adicional
                * carbono_por_ton_aserrin
            )

            nitrogeno_final_ajuste = (
                nitrogeno_base
                + aserrin_adicional
                * nitrogeno_por_ton_aserrin
            )

            if nitrogeno_final_ajuste > 0:

                cn_final_ajuste = (
                    carbono_final_ajuste
                    / nitrogeno_final_ajuste
                )

            else:

                cn_final_ajuste = 0

            # ====================================================
            # HUMEDAD FINAL
            # ====================================================

            agua_total_ajuste = (
                ro_obj
                * insumos["RO"]["humedad"] / 100

                + rod_obj
                * insumos["ROD"]["humedad"] / 100

                + ca_obj
                * insumos["CA"]["humedad"] / 100

                + as_obj
                * insumos["AS"]["humedad"] / 100

                + lodo_obj
                * insumos["LD"]["humedad"] / 100

                + aserrin_adicional
                * insumos["AS"]["humedad"] / 100
            )

            masa_total_ajuste = (
                ro_obj
                + rod_obj
                + ca_obj
                + aserrin_total
                + lodo_obj
            )

            humedad_final_ajuste = (
                agua_total_ajuste
                / masa_total_ajuste
            ) * 100

            # ====================================================
            # AJUSTE RECOMENDADO
            # ====================================================

            st.subheader(
                "Ajuste recomendado"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Aserrín adicional recomendado",
                    f"{aserrin_adicional:.2f} ton"
                )

            with col2:

                st.metric(
                    "Aserrín total requerido",
                    f"{aserrin_total:.2f} ton"
                )

            with col3:

                st.metric(
                    "Masa total ajustada",
                    f"{masa_total_ajuste:.2f} ton"
                )

            # ====================================================
            # RESULTADO FINAL
            # ====================================================

            st.subheader(
                "Resultado después del ajuste"
            )

            col4, col5 = st.columns(2)

            with col4:

                st.metric(
                    "Relación C/N resultante",
                    f"{cn_final_ajuste:.2f}"
                )

            with col5:

                st.metric(
                    "Humedad resultante",
                    f"{humedad_final_ajuste:.2f}%"
                )

            # ====================================================
            # EVALUACIÓN
            # ====================================================

            if (
                cn_final_ajuste >= cn_min
                and cn_final_ajuste <= cn_max
            ):

                if (
                    humedad_final_ajuste >= hum_min
                    and humedad_final_ajuste <= hum_max
                ):

                    st.success(
                        "La mezcla ajustada cumple los criterios "
                        "de C/N y humedad."
                    )

                elif humedad_final_ajuste < hum_min:

                    st.warning(
                        "La mezcla alcanza el C/N requerido, "
                        "pero presenta humedad baja. Se requiere "
                        "ajustar la humedad antes de conformar "
                        "la pila."
                    )

                else:

                    st.warning(
                        "La mezcla alcanza el C/N requerido, "
                        "pero presenta humedad superior al rango "
                        "establecido."
                    )

            else:

                st.error(
                    "La mezcla aún no cumple el criterio de C/N. "
                    "Revise la composición de los materiales."
                )

        else:

            st.info(
                "Ingrese materiales y la cantidad de lodo que "
                "desea procesar para realizar el cálculo."
            )
elif menu == "Seguimiento":
    st.header("Seguimiento del compostaje")

    fecha_seg = st.date_input(
        "Fecha de seguimiento",
        key="fecha_seg"
    )
    
    lote_seg = st.text_input(
        "Código de lote",
        key="lote_seg"
    )
    
    fase_seg = st.selectbox(
        "Fase del compostaje",
        ["Mesofila I", "Termofila", "Mesofila II", "Maduracion"]
    )
    fila_fase = df_parametros[
        df_parametros["fase"] == fase_seg
    ].iloc[0]
    
    temp_min = fila_fase["temperatura_min"]
    temp_max = fila_fase["temperatura_max"]
    
    hum_min_seg = fila_fase["humedad_min"]
    hum_max_seg = fila_fase["humedad_max"]
    
    ph_min = fila_fase["ph_min"]
    ph_max = fila_fase["ph_max"]

    temp1 = st.number_input(
        "Temperatura 1 (°C)",
        min_value=0.0,
        value=0.0,
        key="temp1"
    )
    
    temp2 = st.number_input(
        "Temperatura 2 (°C)",
        min_value=0.0,
        value=0.0,
        key="temp2"
    )
    
    temp3 = st.number_input(
        "Temperatura 3 (°C)",
        min_value=0.0,
        value=0.0,
        key="temp3"
    )
    
    humedad_seg = st.number_input(
        "Humedad medida (%)",
        min_value=0.0,
        value=0.0,
        key="humedad_seg"
    )
    
    ph1 = st.number_input(
        "pH 1",
        min_value=0.0,
        value=0.0,
        key="ph1"
    )
    
    ph2 = st.number_input(
        "pH 2",
        min_value=0.0,
        value=0.0,
        key="ph2"
    )
    
    ph3 = st.number_input(
        "pH 3",
        min_value=0.0,
        value=0.0,
        key="ph3"
    )
    
    volteos = st.number_input(
        "Número de volteos",
        min_value=0,
        value=0,
        step=1,
        key="volteos"
    )
    temp_prom = (temp1 + temp2 + temp3) / 3
    ph_prom = (ph1 + ph2 + ph3) / 3

    if temp_prom < temp_min:
        estado_temp = "BAJA"
    elif temp_prom > temp_max:
        estado_temp = "ALTA"
    else:
        estado_temp = "CORRECTA"
    
    if humedad_seg < hum_min_seg:
        estado_hum = "BAJA"
    elif humedad_seg > hum_max_seg:
        estado_hum = "ALTA"
    else:
        estado_hum = "CORRECTA"
    
    if ph_prom < ph_min:
        estado_ph = "BAJO"
    elif ph_prom > ph_max:
        estado_ph = "ALTO"
    else:
        estado_ph = "CORRECTO"
        
    st.subheader("Resultados del seguimiento")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Temperatura promedio",
            f"{temp_prom:.2f} °C"
        )
        st.caption(f"Estado: {estado_temp}")
    
    with col2:
        st.metric(
            "Humedad",
            f"{humedad_seg:.2f}%"
        )
        st.caption(f"Estado: {estado_hum}")
    
    with col3:
        st.metric(
            "pH promedio",
            f"{ph_prom:.2f}"
        )
        st.caption(f"Estado: {estado_ph}")

    if (
        estado_temp == "CORRECTA"
        and estado_hum == "CORRECTA"
        and estado_ph == "CORRECTO"
    ):
        estado_general = "OPERACION NORMAL"
    else:
        estado_general = "REQUIERE AJUSTE OPERATIVO"

    st.subheader("Evaluación del seguimiento")
    
    if estado_general == "OPERACION NORMAL":
        st.success("Resultado: OPERACIÓN NORMAL")
    else:
        st.warning("Resultado: REQUIERE AJUSTE OPERATIVO")
    
    clave_temp = f"TEMPERATURA|{estado_temp}"
    clave_hum = f"HUMEDAD|{estado_hum}"
    clave_ph = f"PH|{estado_ph}"
    
    fila_temp = df_reglas[df_reglas["clave"] == clave_temp]
    fila_hum = df_reglas[df_reglas["clave"] == clave_hum]
    fila_ph = df_reglas[df_reglas["clave"] == clave_ph]
    
    st.subheader("Recomendaciones")
    
    if estado_temp != "CORRECTA" and not fila_temp.empty:
        st.warning(
            f"Temperatura: {fila_temp.iloc[0]['recomendacion']}"
        )
    
    if estado_hum != "CORRECTA" and not fila_hum.empty:
        st.warning(
            f"Humedad: {fila_hum.iloc[0]['recomendacion']}"
        )
    
    if estado_ph != "CORRECTO" and not fila_ph.empty:
        st.warning(
            f"pH: {fila_ph.iloc[0]['recomendacion']}"
        )
    
    if estado_general == "OPERACION NORMAL":
        st.success(
            "Los parámetros evaluados se encuentran dentro de los rangos "
            "esperados para la fase seleccionada."
        )
    if st.button("Registrar seguimiento"):
    
        nuevo_seguimiento = pd.DataFrame([{
            "fecha": fecha_seg,
            "codigo_lote": lote_seg,
            "fase": fase_seg,
            "temperatura_promedio": temp_prom,
            "humedad": humedad_seg,
            "ph_promedio": ph_prom,
            "estado_temperatura": estado_temp,
            "estado_humedad": estado_hum,
            "estado_ph": estado_ph,
            "estado_general": estado_general
        }])
    
        nuevo_seguimiento.to_csv(
            "seguimiento.csv",
            mode="a",
            header=False,
            index=False
        )
    
        st.success("Seguimiento registrado correctamente")
elif menu == "Inventario":

    st.header("Inventario de compost")

    fecha_inv = st.date_input(
        "Fecha",
        key="fecha_inv"
    )

    operador_inv = st.text_input(
        "Operador",
        key="operador_inv"
    )

    lote_inv = st.text_input(
        "Código de lote",
        key="lote_inv"
    )

    numero_ficha = st.text_input(
        "Número de ficha de pesaje",
        key="numero_ficha"
    )

    compost_ingreso = st.number_input(
        "Compost ingresado a stock (ton)",
        min_value=0.0,
        value=0.0,
        key="compost_ingreso"
    )

    salida_rem = st.number_input(
        "Salida para remediación (ton)",
        min_value=0.0,
        value=0.0,
        key="salida_rem"
    )

    salida_don = st.number_input(
        "Salida para donación (ton)",
        min_value=0.0,
        value=0.0,
        key="salida_don"
    )
    # Stock disponible del lote antes del nuevo movimiento
    df_actual = pd.read_csv("Inventario.csv")
    
    if not df_actual.empty:
    
        for columna in [
            "compost_ingresado",
            "salida_remediacion",
            "salida_donacion"
        ]:
            df_actual[columna] = pd.to_numeric(
                df_actual[columna],
                errors="coerce"
            ).fillna(0)
    
        df_lote_actual = df_actual[
            df_actual["codigo_lote"] == lote_inv
        ]
    
        if not df_lote_actual.empty:
            stock_disponible_lote = (
                df_lote_actual["compost_ingresado"].sum()
                - df_lote_actual["salida_remediacion"].sum()
                - df_lote_actual["salida_donacion"].sum()
            )
        else:
            stock_disponible_lote = 0
    else:
        stock_disponible_lote = 0

    if st.button("Registrar movimiento"):
    
        salida_solicitada = salida_rem + salida_don
    
        stock_disponible_con_ingreso = (
            stock_disponible_lote + compost_ingreso
        )

        if salida_solicitada > stock_disponible_con_ingreso:
    
            st.error(
                "Movimiento no permitido: la salida solicitada "
                "supera el stock disponible del lote."
            )
    
        else:
    
            nuevo_movimiento = pd.DataFrame([{
                "fecha": fecha_inv,
                "operador": operador_inv,
                "codigo_lote": lote_inv,
                "numero_ficha": numero_ficha,
                "compost_ingresado": compost_ingreso,
                "salida_remediacion": salida_rem,
                "salida_donacion": salida_don
            }])
    
            nuevo_movimiento.to_csv(
                "Inventario.csv",
                mode="a",
                header=False,
                index=False
            )
    
            st.success("Movimiento registrado correctamente")

    df_Inventario = pd.read_csv("Inventario.csv")

    columnas_numericas = [
        "compost_ingresado",
        "salida_remediacion",
        "salida_donacion"
    ]

    for columna in columnas_numericas:
        df_Inventario[columna] = pd.to_numeric(
            df_Inventario[columna],
            errors="coerce"
        ).fillna(0)

    df_Inventario["movimiento_neto"] = (
        df_Inventario["compost_ingresado"]
        - df_Inventario["salida_remediacion"]
        - df_Inventario["salida_donacion"]
    )

    df_Inventario["stock_acumulado_lote"] = (
        df_Inventario
        .groupby("codigo_lote")["movimiento_neto"]
        .cumsum()
    )

    movimientos_lote = df_Inventario[
        df_Inventario["codigo_lote"] == lote_inv
    ]

    stock_total = df_Inventario["movimiento_neto"].sum()

    if not movimientos_lote.empty:
        stock_lote = movimientos_lote[
            "stock_acumulado_lote"
        ].iloc[-1]
    else:
        stock_lote = 0

    st.subheader("Estado del Inventario")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Stock del lote",
            f"{stock_lote:.2f} ton"
        )

    with col2:
        st.metric(
            "Stock total disponible",
            f"{stock_total:.2f} ton"
        )

    st.subheader("Historial de movimientos")

    st.dataframe(
        df_Inventario,
        use_container_width=True
    )

elif menu == "Indicadores":

    st.header("Indicadores")

    # =========================
    # INDICADORES DE INVENTARIO
    # =========================

    df_inv = pd.read_csv("Inventario.csv")

    for columna in [
        "compost_ingresado",
        "salida_remediacion",
        "salida_donacion"
    ]:
        df_inv[columna] = pd.to_numeric(
            df_inv[columna],
            errors="coerce"
        ).fillna(0)

    compost_producido = df_inv["compost_ingresado"].sum()

    stock_total = (
        df_inv["compost_ingresado"].sum()
        - df_inv["salida_remediacion"].sum()
        - df_inv["salida_donacion"].sum()
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Compost producido",
            f"{compost_producido:.2f} ton"
        )

    with col2:
        st.metric(
            "Stock total disponible",
            f"{stock_total:.2f} ton"
        )

    # =========================
    # INDICADORES DE SEGUIMIENTO
    # =========================

    df_seg = pd.read_csv("seguimiento.csv")

    if not df_seg.empty:

        df_seg["estado_general"] = (
            df_seg["estado_general"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        total_seguimientos = len(df_seg)

        numero_alertas = (
            df_seg["estado_general"]
            == "REQUIERE AJUSTE OPERATIVO"
        ).sum()

        operaciones_normales = (
            df_seg["estado_general"]
            == "OPERACION NORMAL"
        ).sum()

    else:
        total_seguimientos = 0
        numero_alertas = 0
        operaciones_normales = 0

    col3, col4, col5 = st.columns(3)

    with col3:
        st.metric(
            "Seguimientos registrados",
            total_seguimientos
        )

    with col4:
        st.metric(
            "Alertas de seguimiento",
            int(numero_alertas)
        )

    with col5:
        st.metric(
            "Operaciones normales",
            int(operaciones_normales)
        )

    # =========================
    # INDICADORES DE FORMULACIÓN
    # =========================

    df_form = pd.read_csv("formulaciones.csv")

    for columna in [
        "ro",
        "rod",
        "ld",
        "ca",
        "masa_total"
    ]:
        df_form[columna] = pd.to_numeric(
            df_form[columna],
            errors="coerce"
        ).fillna(0)

    total_residuos = df_form["masa_total"].sum()

    residuos_organicos_valorizados = (
        df_form["ro"].sum()
        + df_form["rod"].sum()
    )

    lodo_valorizado = df_form["ld"].sum()

    material_estructurante = df_form["ca"].sum()

    st.subheader("Valorización de residuos")

    col6, col7, col8, col9 = st.columns(4)

    with col6:
        st.metric(
            "Total de materiales ingresados",
            f"{total_residuos:.2f} ton"
        )

    with col7:
        st.metric(
            "Residuos orgánicos valorizados",
            f"{residuos_organicos_valorizados:.2f} ton"
        )

    with col8:
        st.metric(
            "Lodo valorizado",
            f"{lodo_valorizado:.2f} ton"
        )

    with col9:
        st.metric(
            "Material estructurante utilizado",
            f"{material_estructurante:.2f} ton"
        )
    st.subheader("Stock disponible por lote")
    
    df_stock_lote = (
        df_inv.groupby("codigo_lote")[
            [
                "compost_ingresado",
                "salida_remediacion",
                "salida_donacion"
            ]
        ]
        .sum()
        .reset_index()
    )
    
    df_stock_lote["stock_disponible"] = (
        df_stock_lote["compost_ingresado"]
        - df_stock_lote["salida_remediacion"]
        - df_stock_lote["salida_donacion"]
    )
    
    df_stock_lote = df_stock_lote[
        df_stock_lote["stock_disponible"] >= 0
    ]
    
    st.bar_chart(
        data=df_stock_lote,
        x="codigo_lote",
        y="stock_disponible"
    )
    st.subheader("Estado de los seguimientos")
    
    df_estado_seg = pd.DataFrame({
        "Estado": [
            "Operación normal",
            "Requiere ajuste"
        ],
        "Cantidad": [
            int(operaciones_normales),
            int(numero_alertas)
        ]
    })
    
    st.bar_chart(
        data=df_estado_seg,
        x="Estado",
        y="Cantidad"
    )
    st.subheader("Distribución de materiales valorizados")
    
    df_materiales = pd.DataFrame({
        "Material": [
            "Residuos orgánicos",
            "Residuos orgánicos deshidratados",
            "Lodo valorizado",
            "Material estructurante"
        ],
        "Toneladas": [
            df_form["ro"].sum(),
            df_form["rod"].sum(),
            df_form["ld"].sum(),
            df_form["ca"].sum()
        ]
    })
    
    st.bar_chart(
        data=df_materiales,
        x="Material",
        y="Toneladas"
    )
