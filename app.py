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

    # Objetivos operativos
    hum_objetivo = (hum_min + hum_max) / 2
    cn_objetivo = (cn_min + cn_max) / 2

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
                "humedad, carbono y nitrógeno cuando se disponga de "
                "caracterización real del material utilizado en planta."
            )

        masa_sin_lodo = (
            ro_cap
            + rod_cap
            + ca_cap
            + as_cap
        )

        # ========================================================
        # CARBONO, NITRÓGENO Y AGUA DE LA MEZCLA BASE
        # ========================================================

        carbono_sin_lodo = (
            ro_cap
            * (1 - insumos["RO"]["humedad"] / 100)
            * insumos["RO"]["c"] / 100
            +
            rod_cap
            * (1 - insumos["ROD"]["humedad"] / 100)
            * insumos["ROD"]["c"] / 100
            +
            ca_cap
            * (1 - insumos["CA"]["humedad"] / 100)
            * insumos["CA"]["c"] / 100
            +
            as_cap
            * (1 - insumos["AS"]["humedad"] / 100)
            * insumos["AS"]["c"] / 100
        )

        nitrogeno_sin_lodo = (
            ro_cap
            * (1 - insumos["RO"]["humedad"] / 100)
            * insumos["RO"]["n"] / 100
            +
            rod_cap
            * (1 - insumos["ROD"]["humedad"] / 100)
            * insumos["ROD"]["n"] / 100
            +
            ca_cap
            * (1 - insumos["CA"]["humedad"] / 100)
            * insumos["CA"]["n"] / 100
            +
            as_cap
            * (1 - insumos["AS"]["humedad"] / 100)
            * insumos["AS"]["n"] / 100
        )

        agua_sin_lodo = (
            ro_cap
            * insumos["RO"]["humedad"] / 100
            +
            rod_cap
            * insumos["ROD"]["humedad"] / 100
            +
            ca_cap
            * insumos["CA"]["humedad"] / 100
            +
            as_cap
            * insumos["AS"]["humedad"] / 100
        )

        # ========================================================
        # PROPIEDADES DEL LODO
        # ========================================================

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

        # ========================================================
        # SOLO CALCULAR SI EXISTE MEZCLA BASE
        # ========================================================

        if masa_sin_lodo > 0:

            # ----------------------------------------------------
            # ESTADO DE LA MEZCLA SIN LODO
            # ----------------------------------------------------

            humedad_base = (
                agua_sin_lodo
                / masa_sin_lodo
            ) * 100

            if nitrogeno_sin_lodo > 0:
                cn_base = (
                    carbono_sin_lodo
                    / nitrogeno_sin_lodo
                )
            else:
                cn_base = 0

            # ====================================================
            # LÍMITE TEÓRICO POR C/N
            # ====================================================

            denominador_cn = (
                cn_min
                * nitrogeno_por_ton_lodo
                - carbono_por_ton_lodo
            )

            if denominador_cn > 0:

                lodo_por_cn = (
                    carbono_sin_lodo
                    - cn_min
                    * nitrogeno_sin_lodo
                ) / denominador_cn

                lodo_por_cn = max(
                    0,
                    lodo_por_cn
                )

            else:

                lodo_por_cn = None

            # ====================================================
            # LÍMITE TÉCNICO POR HUMEDAD MÁXIMA
            # ====================================================

            humedad_max_decimal = (
                hum_max / 100
            )

            if humedad_lodo > humedad_max_decimal:

                lodo_por_humedad = (
                    humedad_max_decimal
                    * masa_sin_lodo
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
                    hum_objetivo_decimal
                    * masa_sin_lodo
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
                limites_tecnicos.append(
                    lodo_por_cn
                )

            if lodo_por_humedad is not None:
                limites_tecnicos.append(
                    lodo_por_humedad
                )

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
                    restriccion_dominante = (
                        "C/N Y HUMEDAD"
                    )

            elif lodo_por_cn is not None:

                restriccion_dominante = "C/N"

            elif lodo_por_humedad is not None:

                restriccion_dominante = "HUMEDAD"

            else:

                restriccion_dominante = (
                    "SIN LÍMITE CALCULABLE"
                )

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
            # FUNCIÓN PARA EVALUAR ESCENARIOS
            # ====================================================

            def evaluar_lodo(cantidad_lodo):

                masa_escenario = (
                    masa_sin_lodo
                    + cantidad_lodo
                )

                agua_escenario = (
                    agua_sin_lodo
                    + cantidad_lodo
                    * humedad_lodo
                )

                if masa_escenario > 0:

                    humedad_escenario = (
                        agua_escenario
                        / masa_escenario
                    ) * 100

                else:

                    humedad_escenario = 0

                carbono_escenario = (
                    carbono_sin_lodo
                    + cantidad_lodo
                    * carbono_por_ton_lodo
                )

                nitrogeno_escenario = (
                    nitrogeno_sin_lodo
                    + cantidad_lodo
                    * nitrogeno_por_ton_lodo
                )

                if nitrogeno_escenario > 0:

                    cn_escenario = (
                        carbono_escenario
                        / nitrogeno_escenario
                    )

                else:

                    cn_escenario = 0

                return (
                    masa_escenario,
                    humedad_escenario,
                    cn_escenario
                )

            # ====================================================
            # ESCENARIO RECOMENDADO
            # ====================================================

            (
                masa_recomendada,
                humedad_recomendada,
                cn_recomendado
            ) = evaluar_lodo(
                lodo_recomendado
            )

            # ====================================================
            # ESCENARIO MÁXIMO TÉCNICO
            # ====================================================

            (
                masa_maxima,
                humedad_maxima_escenario,
                cn_maximo_escenario
            ) = evaluar_lodo(
                lodo_maximo_admisible
            )

            # ====================================================
            # RECOMENDACIÓN PARA OPERACIÓN
            # ====================================================

            st.subheader(
                "Recomendación para operación"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Lodo recomendado",
                    f"{lodo_recomendado:.2f} ton"
                )

            with col2:
                st.metric(
                    "Humedad esperada",
                    f"{humedad_recomendada:.2f}%"
                )

            with col3:
                st.metric(
                    "Relación C/N estimada",
                    f"{cn_recomendado:.2f}"
                )

            st.caption(
                f"Rango técnico de humedad: "
                f"{hum_min:.0f}% - {hum_max:.0f}% | "
                f"Objetivo operativo: "
                f"{hum_objetivo:.1f}%"
            )

            st.caption(
                f"Rango técnico C/N: "
                f"{cn_min:.1f} - {cn_max:.1f} | "
                f"Referencia central: "
                f"{cn_objetivo:.1f}"
            )

            # ====================================================
            # SEMÁFORO OPERATIVO
            # ====================================================

            cumple_humedad = (
                humedad_recomendada >= hum_min
                and humedad_recomendada <= hum_max
            )

            cumple_cn = (
                cn_recomendado >= cn_min
                and cn_recomendado <= cn_max
            )

            if cumple_humedad and cumple_cn:

                cerca_objetivo_hum = (
                    abs(
                        humedad_recomendada
                        - hum_objetivo
                    ) <= 2
                )

                cerca_objetivo_cn = (
                    abs(
                        cn_recomendado
                        - cn_objetivo
                    ) <= 2.5
                )

                if (
                    cerca_objetivo_hum
                    and cerca_objetivo_cn
                ):

                    st.success(
                        "🟢 CONDICIÓN RECOMENDADA: "
                        "la formulación se encuentra dentro "
                        "de los rangos y con margen operativo "
                        "adecuado."
                    )

                else:

                    st.warning(
                        "🟡 CONDICIÓN ADMISIBLE: "
                        "la formulación cumple los límites "
                        "técnicos, pero alguno de los parámetros "
                        "se encuentra alejado del objetivo "
                        "operativo o cercano a un límite."
                    )

            else:

                st.error(
                    "🔴 CONDICIÓN NO RECOMENDADA: "
                    "uno o más parámetros se encuentran "
                    "fuera de los límites técnicos."
                )

            # ====================================================
            # MENSAJE PARA EL OPERADOR
            # ====================================================

            if (
                lodo_recomendado
                < lodo_maximo_admisible
            ):

                st.info(
                    f"El máximo técnicamente admisible es "
                    f"{lodo_maximo_admisible:.2f} ton de lodo. "
                    f"Sin embargo, se recomienda incorporar "
                    f"{lodo_recomendado:.2f} ton para mantener "
                    f"la humedad cercana al objetivo operativo "
                    f"de {hum_objetivo:.1f}%."
                )

            else:

                st.info(
                    f"La cantidad recomendada está determinada "
                    f"por el criterio de "
                    f"{restriccion_dominante}."
                )

            # ====================================================
            # DETALLE TÉCNICO PARA SUPERVISIÓN
            # ====================================================

            st.subheader(
                "Detalle técnico de capacidad"
            )

            col4, col5, col6 = st.columns(3)

            with col4:

                if lodo_por_cn is None:

                    st.metric(
                        "Límite por C/N",
                        "NO LIMITA"
                    )

                else:

                    st.metric(
                        "Límite por C/N",
                        f"{lodo_por_cn:.2f} ton"
                    )

            with col5:

                if lodo_por_humedad is None:

                    st.metric(
                        "Límite por humedad",
                        "NO LIMITA"
                    )

                else:

                    st.metric(
                        "Límite por humedad",
                        f"{lodo_por_humedad:.2f} ton"
                    )

            with col6:

                st.metric(
                    "Máximo técnicamente admisible",
                    f"{lodo_maximo_admisible:.2f} ton"
                )

            st.metric(
                "Restricción dominante",
                restriccion_dominante
            )

            # ====================================================
            # COMPARACIÓN DE ESCENARIOS
            # ====================================================

            st.subheader(
                "Comparación de escenarios"
            )

            df_escenarios = pd.DataFrame({
                "Escenario": [
                    "Mezcla sin lodo",
                    "Recomendación SAFCO",
                    "Máximo técnico"
                ],
                "Lodo (ton)": [
                    0,
                    lodo_recomendado,
                    lodo_maximo_admisible
                ],
                "Masa total (ton)": [
                    masa_sin_lodo,
                    masa_recomendada,
                    masa_maxima
                ],
                "Humedad (%)": [
                    humedad_base,
                    humedad_recomendada,
                    humedad_maxima_escenario
                ],
                "Relación C/N estimada": [
                    cn_base,
                    cn_recomendado,
                    cn_maximo_escenario
                ]
            })

            st.dataframe(
                df_escenarios,
                use_container_width=True
            )

            # ====================================================
            # EVALUACIÓN DE LA RECOMENDACIÓN
            # ====================================================

            st.subheader(
                "Evaluación"
            )

            if (
                humedad_recomendada >= hum_min
                and humedad_recomendada <= hum_max
                and cn_recomendado >= cn_min
                and cn_recomendado <= cn_max
            ):

                estado_simulador = "ADMISIBLE"

                st.success(
                    "Resultado: ADMISIBLE"
                )

            elif (
                cn_recomendado >= cn_min
                and cn_recomendado <= cn_max
                and humedad_recomendada < hum_min
            ):

                estado_simulador = (
                    "ADMISIBLE CON AJUSTE DE HUMEDAD"
                )

                st.warning(
                    "Resultado: ADMISIBLE "
                    "CON AJUSTE DE HUMEDAD"
                )

            else:

                estado_simulador = (
                    "NO ADMISIBLE"
                )

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
    # PLANIFICAR MATERIALES PARA UNA CANTIDAD DE LODO A PROCESAR
    # ============================================================

    else:

        st.subheader(
            "Planificación para una cantidad de lodo a procesar"
        )

        st.write(
            "Ingrese los materiales disponibles y la cantidad de lodo "
            "que necesita procesar. SAFCO comparará la mezcla real con "
            "la referencia histórica 60/20/20 y estimará el aserrín "
            "requerido para alcanzar una condición adecuada."
        )

        # ========================================================
        # ENTRADAS
        # ========================================================

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

        lodo_obj = st.number_input(
            "Lodo que se desea procesar (ton)",
            min_value=0.0,
            value=0.0,
            key="lodo_obj"
        )

        # ========================================================
        # OBJETIVOS OPERATIVOS
        # ========================================================

        hum_objetivo = (
            hum_min + hum_max
        ) / 2

        cn_objetivo = (
            cn_min + cn_max
        ) / 2

        # ========================================================
        # FUNCIÓN PARA CALCULAR PROPIEDADES DE UNA MEZCLA
        # ========================================================

        def calcular_mezcla(
            ro,
            rod,
            ca,
            ld,
            aserrin=0
        ):

            masa_total = (
                ro
                + rod
                + ca
                + ld
                + aserrin
            )

            carbono_total = (
                ro
                * (1 - insumos["RO"]["humedad"] / 100)
                * insumos["RO"]["c"] / 100

                + rod
                * (1 - insumos["ROD"]["humedad"] / 100)
                * insumos["ROD"]["c"] / 100

                + ca
                * (1 - insumos["CA"]["humedad"] / 100)
                * insumos["CA"]["c"] / 100

                + ld
                * (1 - insumos["LD"]["humedad"] / 100)
                * insumos["LD"]["c"] / 100

                + aserrin
                * (1 - insumos["AS"]["humedad"] / 100)
                * insumos["AS"]["c"] / 100
            )

            nitrogeno_total = (
                ro
                * (1 - insumos["RO"]["humedad"] / 100)
                * insumos["RO"]["n"] / 100

                + rod
                * (1 - insumos["ROD"]["humedad"] / 100)
                * insumos["ROD"]["n"] / 100

                + ca
                * (1 - insumos["CA"]["humedad"] / 100)
                * insumos["CA"]["n"] / 100

                + ld
                * (1 - insumos["LD"]["humedad"] / 100)
                * insumos["LD"]["n"] / 100

                + aserrin
                * (1 - insumos["AS"]["humedad"] / 100)
                * insumos["AS"]["n"] / 100
            )

            agua_total = (
                ro
                * insumos["RO"]["humedad"] / 100

                + rod
                * insumos["ROD"]["humedad"] / 100

                + ca
                * insumos["CA"]["humedad"] / 100

                + ld
                * insumos["LD"]["humedad"] / 100

                + aserrin
                * insumos["AS"]["humedad"] / 100
            )

            if masa_total > 0:

                humedad = (
                    agua_total
                    / masa_total
                ) * 100

            else:

                humedad = 0

            if nitrogeno_total > 0:

                cn = (
                    carbono_total
                    / nitrogeno_total
                )

            else:

                cn = 0

            return {
                "masa": masa_total,
                "carbono": carbono_total,
                "nitrogeno": nitrogeno_total,
                "agua": agua_total,
                "humedad": humedad,
                "cn": cn
            }

        # ========================================================
        # FUNCIÓN PARA CALCULAR ASERRÍN REQUERIDO
        # ========================================================

        def calcular_aserrin_requerido(
            carbono_base,
            nitrogeno_base,
            cn_actual
        ):

            humedad_aserrin = (
                insumos["AS"]["humedad"] / 100
            )

            carbono_por_ton_aserrin = (
                (1 - humedad_aserrin)
                * insumos["AS"]["c"] / 100
            )

            nitrogeno_por_ton_aserrin = (
                (1 - humedad_aserrin)
                * insumos["AS"]["n"] / 100
            )

            denominador = (
                carbono_por_ton_aserrin
                - cn_objetivo
                * nitrogeno_por_ton_aserrin
            )

            if cn_actual >= cn_objetivo:

                return 0

            elif denominador > 0:

                aserrin = (
                    cn_objetivo
                    * nitrogeno_base
                    - carbono_base
                ) / denominador

                return max(
                    0,
                    aserrin
                )

            else:

                return 0

        # ========================================================
        # SOLO CALCULAR SI HAY LODO
        # ========================================================

        if lodo_obj > 0:

            # ====================================================
            # ESCENARIO 1
            # MEZCLA REAL INGRESADA
            # ====================================================

            mezcla_real_base = calcular_mezcla(
                ro_obj,
                rod_obj,
                ca_obj,
                lodo_obj,
                0
            )

            aserrin_real = calcular_aserrin_requerido(
                mezcla_real_base["carbono"],
                mezcla_real_base["nitrogeno"],
                mezcla_real_base["cn"]
            )

            mezcla_real_final = calcular_mezcla(
                ro_obj,
                rod_obj,
                ca_obj,
                lodo_obj,
                aserrin_real
            )

            # ====================================================
            # ESCENARIO 2
            # REFERENCIA HISTÓRICA 60 / 20 / 20
            # ====================================================

            # Si LD representa 20%, entonces:
            # masa total histórica = LD / 0.20

            masa_hist_base = (
                lodo_obj / 0.20
            )

            ro_hist = (
                masa_hist_base * 0.60
            )

            ca_hist = (
                masa_hist_base * 0.20
            )

            ld_hist = (
                lodo_obj
            )

            # ROD no forma parte de la referencia histórica
            rod_hist = 0

            mezcla_hist_base = calcular_mezcla(
                ro_hist,
                rod_hist,
                ca_hist,
                ld_hist,
                0
            )

            aserrin_hist = calcular_aserrin_requerido(
                mezcla_hist_base["carbono"],
                mezcla_hist_base["nitrogeno"],
                mezcla_hist_base["cn"]
            )

            mezcla_hist_final = calcular_mezcla(
                ro_hist,
                rod_hist,
                ca_hist,
                ld_hist,
                aserrin_hist
            )

            # ====================================================
            # PROPORCIÓN REAL INGRESADA
            # SOLO RO + CA + LD PARA COMPARAR 60/20/20
            # ====================================================

            masa_proporcion_real = (
                ro_obj
                + ca_obj
                + lodo_obj
            )

            if masa_proporcion_real > 0:

                pct_ro_real = (
                    ro_obj
                    / masa_proporcion_real
                ) * 100

                pct_ca_real = (
                    ca_obj
                    / masa_proporcion_real
                ) * 100

                pct_ld_real = (
                    lodo_obj
                    / masa_proporcion_real
                ) * 100

            else:

                pct_ro_real = 0
                pct_ca_real = 0
                pct_ld_real = 0

            # ====================================================
            # DIFERENCIAS CONTRA REFERENCIA HISTÓRICA
            # ====================================================

            diferencia_ro = (
                ro_obj - ro_hist
            )

            diferencia_ca = (
                ca_obj - ca_hist
            )

            diferencia_ld = (
                lodo_obj - ld_hist
            )

            # ====================================================
            # REFERENCIA HISTÓRICA
            # ====================================================

            st.subheader(
                "Referencia histórica 60 / 20 / 20"
            )

            st.write(
                f"Para procesar {lodo_obj:.2f} ton de lodo siguiendo "
                f"la proporción histórica de planta, la mezcla base "
                f"correspondería aproximadamente a:"
            )

            col_hist1, col_hist2, col_hist3 = st.columns(3)

            with col_hist1:

                st.metric(
                    "RO de referencia",
                    f"{ro_hist:.2f} ton"
                )

            with col_hist2:

                st.metric(
                    "Cartón de referencia",
                    f"{ca_hist:.2f} ton"
                )

            with col_hist3:

                st.metric(
                    "Lodo",
                    f"{ld_hist:.2f} ton"
                )

            st.caption(
                "Esta proporción representa la práctica histórica "
                "de la planta y se utiliza como referencia de comparación, "
                "no como una formulación óptima obligatoria."
            )

            # ====================================================
            # PROPORCIÓN REAL
            # ====================================================

            st.subheader(
                "Proporción de la mezcla ingresada"
            )

            col_prop1, col_prop2, col_prop3 = st.columns(3)

            with col_prop1:

                st.metric(
                    "RO",
                    f"{pct_ro_real:.1f}%"
                )

            with col_prop2:

                st.metric(
                    "Cartón",
                    f"{pct_ca_real:.1f}%"
                )

            with col_prop3:

                st.metric(
                    "Lodo",
                    f"{pct_ld_real:.1f}%"
                )

            if rod_obj > 0:

                st.info(
                    f"Además se consideran {rod_obj:.2f} ton de ROD. "
                    f"Este insumo es complementario y no forma parte "
                    f"de la proporción histórica 60/20/20."
                )

            # ====================================================
            # DIFERENCIAS DE MATERIAL
            # ====================================================

            st.subheader(
                "Diferencia respecto a la referencia histórica"
            )

            col_dif1, col_dif2 = st.columns(2)

            with col_dif1:

                if diferencia_ro < 0:

                    st.metric(
                        "RO adicional para referencia",
                        f"{abs(diferencia_ro):.2f} ton"
                    )

                else:

                    st.metric(
                        "RO sobre referencia",
                        f"{diferencia_ro:.2f} ton"
                    )

            with col_dif2:

                if diferencia_ca < 0:

                    st.metric(
                        "Cartón adicional para referencia",
                        f"{abs(diferencia_ca):.2f} ton"
                    )

                else:

                    st.metric(
                        "Cartón sobre referencia",
                        f"{diferencia_ca:.2f} ton"
                    )

            # ====================================================
            # RESULTADO DE LA MEZCLA REAL
            # ====================================================

            st.subheader(
                "Planificación con los materiales ingresados"
            )

            col_real1, col_real2, col_real3 = st.columns(3)

            with col_real1:

                st.metric(
                    "Aserrín a gestionar",
                    f"{aserrin_real:.2f} ton"
                )

            with col_real2:

                st.metric(
                    "Humedad estimada",
                    f"{mezcla_real_final['humedad']:.2f}%"
                )

            with col_real3:

                st.metric(
                    "Relación C/N estimada",
                    f"{mezcla_real_final['cn']:.2f}"
                )

            # ====================================================
            # RESULTADO DE REFERENCIA HISTÓRICA
            # ====================================================

            st.subheader(
                "Resultado de la referencia histórica"
            )

            col_ref1, col_ref2, col_ref3 = st.columns(3)

            with col_ref1:

                st.metric(
                    "Aserrín requerido",
                    f"{aserrin_hist:.2f} ton"
                )

            with col_ref2:

                st.metric(
                    "Humedad estimada",
                    f"{mezcla_hist_final['humedad']:.2f}%"
                )

            with col_ref3:

                st.metric(
                    "Relación C/N estimada",
                    f"{mezcla_hist_final['cn']:.2f}"
                )

            # ====================================================
            # COMPARACIÓN DE ESCENARIOS
            # ====================================================

            st.subheader(
                "Comparación de escenarios"
            )

            df_comparacion = pd.DataFrame({
                "Indicador": [
                    "RO (ton)",
                    "ROD (ton)",
                    "Cartón (ton)",
                    "Lodo (ton)",
                    "Aserrín requerido (ton)",
                    "Masa total final (ton)",
                    "Humedad (%)",
                    "Relación C/N estimada"
                ],

                "Mezcla ingresada": [
                    ro_obj,
                    rod_obj,
                    ca_obj,
                    lodo_obj,
                    aserrin_real,
                    mezcla_real_final["masa"],
                    mezcla_real_final["humedad"],
                    mezcla_real_final["cn"]
                ],

                "Referencia histórica 60/20/20": [
                    ro_hist,
                    rod_hist,
                    ca_hist,
                    ld_hist,
                    aserrin_hist,
                    mezcla_hist_final["masa"],
                    mezcla_hist_final["humedad"],
                    mezcla_hist_final["cn"]
                ]
            })

            st.dataframe(
                df_comparacion,
                use_container_width=True
            )

            # ====================================================
            # AGUA TEÓRICA
            # PARA LA MEZCLA REAL
            # ====================================================

            agua_teorica_ton = 0

            if mezcla_real_final["humedad"] < hum_min:

                hum_objetivo_decimal = (
                    hum_objetivo / 100
                )

                agua_teorica_ton = (
                    hum_objetivo_decimal
                    * mezcla_real_final["masa"]
                    - mezcla_real_final["agua"]
                ) / (
                    1
                    - hum_objetivo_decimal
                )

                agua_teorica_ton = max(
                    0,
                    agua_teorica_ton
                )

            agua_teorica_m3 = (
                agua_teorica_ton
            )

            agua_teorica_litros = (
                agua_teorica_ton
                * 1000
            )

            # ====================================================
            # SEMÁFORO MEZCLA REAL
            # ====================================================

            st.subheader(
                "Evaluación de la mezcla ingresada"
            )

            cumple_cn_real = (
                mezcla_real_final["cn"] >= cn_min
                and mezcla_real_final["cn"] <= cn_max
            )

            cumple_hum_real = (
                mezcla_real_final["humedad"] >= hum_min
                and mezcla_real_final["humedad"] <= hum_max
            )

            if (
                cumple_cn_real
                and cumple_hum_real
            ):

                if (
                    mezcla_real_final["humedad"]
                    >= hum_max - 2
                ):

                    st.warning(
                        "🟠 ADMISIBLE CERCA DEL LÍMITE: "
                        "la mezcla cumple los criterios técnicos, "
                        "pero la humedad se encuentra próxima "
                        "al límite superior."
                    )

                else:

                    st.success(
                        "🟢 VIABLE PARA CONFORMACIÓN: "
                        "la mezcla cumple los criterios iniciales "
                        "de humedad y relación C/N."
                    )

            elif (
                cumple_cn_real
                and mezcla_real_final["humedad"] < hum_min
            ):

                st.warning(
                    "🟡 VIABLE CON AJUSTE DE HUMEDAD: "
                    "la relación C/N es adecuada, pero la mezcla "
                    "presenta humedad insuficiente."
                )

                col_agua1, col_agua2 = st.columns(2)

                with col_agua1:

                    st.metric(
                        "Agua teórica de riego",
                        f"{agua_teorica_m3:.2f} m³"
                    )

                with col_agua2:

                    st.metric(
                        "Equivalente",
                        f"{agua_teorica_litros:.0f} L"
                    )

                st.info(
                    f"El balance estima aproximadamente "
                    f"{agua_teorica_m3:.2f} m³ de agua para "
                    f"aproximar la mezcla a una humedad de "
                    f"{hum_objetivo:.1f}%."
                )

                st.warning(
                    "Aplicar progresivamente y verificar la "
                    "humedad real. El valor constituye una "
                    "estimación teórica de apoyo operacional."
                )

            elif (
                cumple_cn_real
                and mezcla_real_final["humedad"] > hum_max
            ):

                st.error(
                    "🔴 REFORMULAR POR HUMEDAD ALTA: "
                    "la relación C/N es adecuada, pero la humedad "
                    "supera el rango establecido."
                )

            else:
                st.error(
                    "🔴 REFORMULAR: la relación C/N estimada "
                    "se encuentra fuera del rango técnico."
                )
           # ====================================================
            # NOTAS DE INTERPRETACIÓN
            # ====================================================

            with st.expander(
                "¿Cómo interpretar esta comparación?"
            ):

                st.write(
                    "*Mezcla ingresada:* representa las cantidades "
                    "que el operador realmente tiene disponibles."
                )

                st.write(
                    "*Referencia histórica 60/20/20:* indica cuánto "
                    "RO y cartón se habría utilizado históricamente "
                    "para la cantidad de lodo seleccionada."
                )

                st.write(
                    "*ROD:* se evalúa como material complementario "
                    "porque es un insumo incorporado recientemente "
                    "y no forma parte de la referencia histórica."
                )

                st.write(
                    "*Aserrín requerido:* representa una cantidad "
                    "estimada que puede utilizarse para planificar "
                    "su solicitud o abastecimiento."
                )

                st.write(
                    "**La referencia histórica no reemplaza la "
                    "evaluación técnica:** la decisión final debe "
                    "considerar humedad y relación C/N."
                )

                st.write(
                    "*Aserrín:* actualmente se calcula con valores "
                    "referenciales de 20% de humedad, 50% de carbono "
                    "y 0.10% de nitrógeno. Estos parámetros deben "
                    "actualizarse cuando exista ficha técnica o "
                    "caracterización del material suministrado."
                )

            st.caption(
                "El posible uso de lixiviado como agente humectante "
                "permanece como alternativa futura pendiente de "
                "validación experimental."
            )

        else:

            st.info(
                "Ingrese una cantidad de lodo mayor a cero "
                "para realizar la planificación."
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
