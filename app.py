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
    # PLANIFICAR MEZCLA PARA PROCESAR UNA CANTIDAD DE LODO
    # ============================================================

    else:

        st.subheader(
            "Planificación para una cantidad de lodo a procesar"
        )

        st.write(
            "Ingrese los materiales disponibles en planta y la cantidad "
            "de lodo que necesita procesar. SAFCO estimará cuánto aserrín "
            "se requiere para obtener una relación C/N adecuada y verificará "
            "la humedad resultante de la mezcla."
        )

        # ========================================================
        # MATERIALES DISPONIBLES
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

        masa_base = (
            ro_obj
            + rod_obj
            + ca_obj
            + lodo_obj
        )

        if masa_base > 0 and lodo_obj > 0:

            # ====================================================
            # CARBONO DE LA MEZCLA BASE
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

                + lodo_obj
                * (1 - insumos["LD"]["humedad"] / 100)
                * insumos["LD"]["c"] / 100
            )

            # ====================================================
            # NITRÓGENO DE LA MEZCLA BASE
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

                + lodo_obj
                * (1 - insumos["LD"]["humedad"] / 100)
                * insumos["LD"]["n"] / 100
            )

            # ====================================================
            # AGUA DE LA MEZCLA BASE
            # ====================================================

            agua_base = (
                ro_obj
                * insumos["RO"]["humedad"] / 100

                + rod_obj
                * insumos["ROD"]["humedad"] / 100

                + ca_obj
                * insumos["CA"]["humedad"] / 100

                + lodo_obj
                * insumos["LD"]["humedad"] / 100
            )

            # ====================================================
            # C/N Y HUMEDAD ANTES DEL ASERRÍN
            # ====================================================

            if nitrogeno_base > 0:

                cn_base = (
                    carbono_base
                    / nitrogeno_base
                )

            else:

                cn_base = 0

            humedad_base = (
                agua_base
                / masa_base
            ) * 100

            # ====================================================
            # PROPIEDADES REFERENCIALES DEL ASERRÍN
            # ====================================================

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

            # ====================================================
            # ASERRÍN REQUERIDO PARA C/N OBJETIVO
            # ====================================================

            denominador_aserrin = (
                carbono_por_ton_aserrin
                - cn_objetivo
                * nitrogeno_por_ton_aserrin
            )

            # Si la mezcla ya supera el objetivo,
            # no necesita más aserrín por C/N.
            if cn_base >= cn_objetivo:

                aserrin_requerido = 0

            elif denominador_aserrin > 0:

                aserrin_requerido = (
                    cn_objetivo
                    * nitrogeno_base
                    - carbono_base
                ) / denominador_aserrin

                aserrin_requerido = max(
                    0,
                    aserrin_requerido
                )

            else:

                aserrin_requerido = 0

            # ====================================================
            # RESULTADO CON ASERRÍN
            # ====================================================

            carbono_final = (
                carbono_base
                + aserrin_requerido
                * carbono_por_ton_aserrin
            )

            nitrogeno_final = (
                nitrogeno_base
                + aserrin_requerido
                * nitrogeno_por_ton_aserrin
            )

            masa_con_aserrin = (
                masa_base
                + aserrin_requerido
            )

            agua_con_aserrin = (
                agua_base
                + aserrin_requerido
                * humedad_aserrin
            )

            if nitrogeno_final > 0:

                cn_final = (
                    carbono_final
                    / nitrogeno_final
                )

            else:

                cn_final = 0

            if masa_con_aserrin > 0:

                humedad_final = (
                    agua_con_aserrin
                    / masa_con_aserrin
                ) * 100

            else:

                humedad_final = 0

            # ====================================================
            # CÁLCULO DE AGUA TEÓRICA PARA RIEGO
            # SOLO SI LA HUMEDAD QUEDA POR DEBAJO DEL MÍNIMO
            # ====================================================

            agua_teorica_ton = 0

            if humedad_final < hum_min:

                hum_objetivo_decimal = (
                    hum_objetivo / 100
                )

                agua_teorica_ton = (
                    hum_objetivo_decimal
                    * masa_con_aserrin
                    - agua_con_aserrin
                ) / (
                    1 - hum_objetivo_decimal
                )

                agua_teorica_ton = max(
                    0,
                    agua_teorica_ton
                )

            # Aproximación:
            # 1 tonelada de agua ≈ 1 m3 ≈ 1000 litros

            agua_teorica_m3 = (
                agua_teorica_ton
            )

            agua_teorica_litros = (
                agua_teorica_ton
                * 1000
            )

            # ====================================================
            # HUMEDAD DESPUÉS DEL RIEGO TEÓRICO
            # ====================================================

            masa_final_ajustada = (
                masa_con_aserrin
                + agua_teorica_ton
            )

            agua_final_ajustada = (
                agua_con_aserrin
                + agua_teorica_ton
            )

            if masa_final_ajustada > 0:

                humedad_despues_riego = (
                    agua_final_ajustada
                    / masa_final_ajustada
                ) * 100

            else:

                humedad_despues_riego = 0

            # ====================================================
            # PLANIFICACIÓN DE MATERIALES
            # ====================================================

            st.subheader(
                "Planificación de materiales"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Lodo a procesar",
                    f"{lodo_obj:.2f} ton"
                )

            with col2:

                st.metric(
                    "Aserrín a gestionar",
                    f"{aserrin_requerido:.2f} ton"
                )

            with col3:

                st.metric(
                    "Masa estimada de mezcla",
                    f"{masa_con_aserrin:.2f} ton"
                )

            st.info(
                f"Para procesar {lodo_obj:.2f} ton de lodo con los "
                f"materiales ingresados, SAFCO estima que se requieren "
                f"{aserrin_requerido:.2f} ton de aserrín."
            )

            # ====================================================
            # RESULTADOS TÉCNICOS
            # ====================================================

            st.subheader(
                "Resultado técnico de la mezcla"
            )

            col4, col5, col6 = st.columns(3)

            with col4:

                st.metric(
                    "Relación C/N estimada",
                    f"{cn_final:.2f}"
                )

            with col5:

                st.metric(
                    "Humedad estimada",
                    f"{humedad_final:.2f}%"
                )

            with col6:

                st.metric(
                    "C/N objetivo operativo",
                    f"{cn_objetivo:.1f}"
                )

            st.caption(
                f"Rango técnico de C/N: "
                f"{cn_min:.1f} - {cn_max:.1f}"
            )

            st.caption(
                f"Rango técnico de humedad: "
                f"{hum_min:.0f}% - {hum_max:.0f}% | "
                f"Objetivo operativo: {hum_objetivo:.1f}%"
            )

            # ====================================================
            # EVALUACIÓN Y SEMÁFORO
            # ====================================================

            cumple_cn = (
                cn_final >= cn_min
                and cn_final <= cn_max
            )

            cumple_humedad = (
                humedad_final >= hum_min
                and humedad_final <= hum_max
            )

            # ----------------------------------------------------
            # VERDE
            # ----------------------------------------------------

            if cumple_cn and cumple_humedad:

                if humedad_final >= (
                    hum_max - 2
                ):

                    estado_planificacion = (
                        "ADMISIBLE CERCA DEL LÍMITE DE HUMEDAD"
                    )

                    st.warning(
                        "🟠 MEZCLA ADMISIBLE, PERO CON HUMEDAD "
                        "CERCANA AL LÍMITE SUPERIOR. "
                        "No se recomienda realizar riego adicional "
                        "antes de verificar la humedad real de la mezcla."
                    )

                else:

                    estado_planificacion = (
                        "VIABLE"
                    )

                    st.success(
                        "🟢 VIABLE PARA CONFORMACIÓN: "
                        "la mezcla cumple los criterios iniciales "
                        "de relación C/N y humedad."
                    )

            # ----------------------------------------------------
            # AMARILLO - FALTA HUMEDAD
            # ----------------------------------------------------

            elif (
                cumple_cn
                and humedad_final < hum_min
            ):

                estado_planificacion = (
                    "VIABLE CON AJUSTE DE HUMEDAD"
                )

                st.warning(
                    "🟡 VIABLE CON AJUSTE DE HUMEDAD: "
                    "la relación C/N se encuentra dentro del rango, "
                    "pero la mezcla presenta humedad insuficiente."
                )

                st.subheader(
                    "Ajuste teórico de humedad"
                )

                col7, col8 = st.columns(2)

                with col7:

                    st.metric(
                        "Agua teórica de riego",
                        f"{agua_teorica_m3:.2f} m³"
                    )

                with col8:

                    st.metric(
                        "Equivalente aproximado",
                        f"{agua_teorica_litros:.0f} L"
                    )

                st.info(
                    f"El cálculo estima que aproximadamente "
                    f"{agua_teorica_m3:.2f} m³ de agua permitirían "
                    f"llevar la mezcla hacia una humedad cercana a "
                    f"{hum_objetivo:.1f}%."
                )

                st.warning(
                    "Aplicar el riego progresivamente y verificar "
                    "la humedad durante la mezcla. El volumen calculado "
                    "es una estimación teórica de apoyo operacional y "
                    "no debe aplicarse automáticamente en una sola etapa."
                )

            # ----------------------------------------------------
            # HUMEDAD DEMASIADO ALTA
            # ----------------------------------------------------

            elif (
                cumple_cn
                and humedad_final > hum_max
            ):

                estado_planificacion = (
                    "REFORMULAR POR HUMEDAD ALTA"
                )

                st.error(
                    "🔴 REFORMULAR: la relación C/N es adecuada, "
                    "pero la humedad supera el límite establecido. "
                    "No se recomienda agregar agua. Revise la "
                    "proporción de materiales secos o estructurantes."
                )

            # ----------------------------------------------------
            # C/N FUERA DE RANGO
            # ----------------------------------------------------

            else:

                estado_planificacion = (
                    "REFORMULAR"
                )

                st.error(
                    "🔴 REFORMULAR MEZCLA: la relación C/N estimada "
                    "se encuentra fuera del rango técnico establecido. "
                    "Revise las cantidades de materiales antes de "
                    "conformar la pila."
                )

            # ====================================================
            # COMPARACIÓN ANTES / DESPUÉS
            # ====================================================

            st.subheader(
                "Comparación de la mezcla"
            )

            df_planificacion = pd.DataFrame({
                "Escenario": [
                    "Antes del aserrín",
                    "Después del aserrín"
                ],
                "Masa total (ton)": [
                    masa_base,
                    masa_con_aserrin
                ],
                "Humedad (%)": [
                    humedad_base,
                    humedad_final
                ],
                "Relación C/N estimada": [
                    cn_base,
                    cn_final
                ]
            })

            st.dataframe(
                df_planificacion,
                use_container_width=True
            )

            # ====================================================
            # EXPLICACIÓN PARA OPERADOR / SUPERVISOR
            # ====================================================

            with st.expander(
                "¿Cómo interpretar este resultado?"
            ):

                st.write(
                    "🟢 *VIABLE PARA CONFORMACIÓN:* "
                    "la mezcla se encuentra dentro de los rangos "
                    "establecidos de humedad y relación C/N."
                )

                st.write(
                    "🟡 *VIABLE CON AJUSTE DE HUMEDAD:* "
                    "la relación C/N es adecuada, pero la mezcla "
                    "está demasiado seca. SAFCO estima un volumen "
                    "teórico de agua para aproximarse al objetivo "
                    "de humedad."
                )

                st.write(
                    "🟠 *ADMISIBLE CERCA DEL LÍMITE:* "
                    "la mezcla todavía cumple técnicamente, pero "
                    "se encuentra próxima al límite superior de "
                    "humedad. Se recomienda verificar antes de "
                    "añadir más agua o material húmedo."
                )

                st.write(
                    "🔴 *REFORMULAR:* uno o más parámetros se "
                    "encuentran fuera de los límites establecidos. "
                    "La composición debe revisarse antes de conformar "
                    "la pila."
                )

                st.write(
                    "*Aserrín a gestionar:* representa la cantidad "
                    "estimada que debería solicitarse, prepararse o "
                    "adquirirse para procesar la cantidad de lodo "
                    "indicada."
                )

                st.write(
                    "*Agua teórica de riego:* es una estimación "
                    "matemática. El riego debe realizarse de manera "
                    "progresiva y verificando la humedad real de la mezcla."
                )

                st.write(
                    "*Relación C/N estimada:* el carbono utilizado "
                    "por SAFCO para los insumos caracterizados se estimó "
                    "a partir de los resultados de materia orgánica; "
                    "por ello no corresponde a una determinación directa "
                    "de C/N realizada por laboratorio."
                )

                st.write(
                    "*Aserrín:* sus propiedades todavía corresponden "
                    "a valores referenciales y deberán actualizarse "
                    "cuando se disponga de caracterización del material "
                    "real utilizado en planta."
                )

            # ====================================================
            # NOTA SOBRE LIXIVIADO
            # ====================================================

            st.caption(
                "Nota: actualmente el ajuste de humedad se calcula "
                "considerando agua. El posible aprovechamiento del "
                "lixiviado generado durante la deshidratación de "
                "residuos orgánicos queda como alternativa futura "
                "sujeta a caracterización y validación experimental."
            )

        else:

            st.info(
                "Ingrese los materiales disponibles y una cantidad "
                "de lodo mayor a cero para realizar la planificación."
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
