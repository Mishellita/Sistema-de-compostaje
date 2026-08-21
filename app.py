import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
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
            alternativa_seleccionada = st.selectbox(
                "Seleccione la alternativa que se aplicará",
                [
                    "Solo aserrín",
                    "Solo cartón",
                    "Cartón + aserrín"
                ]
            )
            justificacion = st.text_area(
                "Justificación / observación de la decisión",
                placeholder=(
                    "Ejemplo: Se selecciona cartón + aserrín porque mantiene "
                    "la humedad dentro del rango y permite aprovechar el cartón "
                    "disponible en planta."
                )
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
            "que desea procesar. SAFCO comparará diferentes alternativas "
            "de material estructurante para apoyar la planificación."
        )

        # ========================================================
        # PERIODO
        # ========================================================

        periodo_planificacion = st.selectbox(
            "Periodo de planificación",
            [
                "Diario",
                "Semanal",
                "Mensual",
                "Otro"
            ],
            key="periodo_planificacion"
        )

        st.caption(
            "Todas las cantidades deben corresponder al mismo periodo."
        )

        # ========================================================
        # DATOS DE ENTRADA
        # ========================================================

        ro_obj = st.number_input(
            "Residuos Orgánicos a procesar en el periodo (ton)",
            min_value=0.0,
            value=0.0,
            key="ro_obj"
        )

        rod_obj = st.number_input(
            "Residuos Orgánicos Deshidratados a procesar en el periodo (ton)",
            min_value=0.0,
            value=0.0,
            key="rod_obj"
        )

        ca_obj = st.number_input(
            "Cartón disponible en el periodo (ton)",
            min_value=0.0,
            value=0.0,
            key="ca_obj"
        )

        lodo_obj = st.number_input(
            "Lodo que se desea procesar en el periodo (ton)",
            min_value=0.0,
            value=0.0,
            key="lodo_obj"
        )

        # ========================================================
        # OBJETIVOS
        # ========================================================

        hum_objetivo = (
            hum_min + hum_max
        ) / 2

        cn_objetivo = (
            cn_min + cn_max
        ) / 2

        # ========================================================
        # FUNCIÓN GENERAL DE MEZCLA
        # ========================================================

        def calcular_mezcla(
            ro,
            rod,
            ca,
            ld,
            aserrin=0.0
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

                relacion_cn = (
                    carbono_total
                    / nitrogeno_total
                )

            else:

                relacion_cn = 0

            return {
                "masa": masa_total,
                "carbono": carbono_total,
                "nitrogeno": nitrogeno_total,
                "agua": agua_total,
                "humedad": humedad,
                "cn": relacion_cn
            }

        # ========================================================
        # FUNCIÓN DE MATERIAL NECESARIO PARA C/N OBJETIVO
        # ========================================================

        def material_para_cn(
            carbono_base,
            nitrogeno_base,
            codigo_material
        ):

            humedad_mat = (
                insumos[codigo_material]["humedad"]
                / 100
            )

            carbono_mat = (
                (1 - humedad_mat)
                * insumos[codigo_material]["c"]
                / 100
            )

            nitrogeno_mat = (
                (1 - humedad_mat)
                * insumos[codigo_material]["n"]
                / 100
            )

            denominador = (
                carbono_mat
                - cn_objetivo
                * nitrogeno_mat
            )

            if denominador <= 0:
                return 0

            cantidad = (
                cn_objetivo
                * nitrogeno_base
                - carbono_base
            ) / denominador

            return max(
                0,
                cantidad
            )

        # ========================================================
        # VALIDACIÓN
        # ========================================================

        masa_ingresada = (
            ro_obj
            + rod_obj
            + ca_obj
            + lodo_obj
        )

        if (
            masa_ingresada > 0
            and lodo_obj > 0
        ):

            # ====================================================
            # MEZCLA BASE
            # ====================================================

            mezcla_base = calcular_mezcla(
                ro_obj,
                rod_obj,
                ca_obj,
                lodo_obj,
                0
            )

            # ====================================================
            # REFERENCIA HISTÓRICA 60 / 20 / 20
            # ====================================================

            masa_hist = (
                lodo_obj / 0.20
            )

            ro_hist = (
                masa_hist * 0.60
            )

            ca_hist = (
                masa_hist * 0.20
            )

            ld_hist = (
                lodo_obj
            )

            mezcla_hist = calcular_mezcla(
                ro_hist,
                0,
                ca_hist,
                ld_hist,
                0
            )

            # ====================================================
            # PROPORCIÓN REAL
            # ====================================================

            masa_prop = (
                ro_obj
                + ca_obj
                + lodo_obj
            )

            if masa_prop > 0:

                pct_ro = (
                    ro_obj / masa_prop
                ) * 100

                pct_ca = (
                    ca_obj / masa_prop
                ) * 100

                pct_ld = (
                    lodo_obj / masa_prop
                ) * 100

            else:

                pct_ro = 0
                pct_ca = 0
                pct_ld = 0

            # ====================================================
            # SECCIÓN 1
            # REFERENCIA HISTÓRICA
            # ====================================================

            st.subheader(
                "Referencia histórica de planta"
            )

            col_h1, col_h2, col_h3 = st.columns(3)

            with col_h1:
                st.metric(
                    "RO de referencia",
                    f"{ro_hist:.2f} ton"
                )

            with col_h2:
                st.metric(
                    "Cartón de referencia",
                    f"{ca_hist:.2f} ton"
                )

            with col_h3:
                st.metric(
                    "Lodo",
                    f"{ld_hist:.2f} ton"
                )

            st.caption(
                "La referencia 60/20/20 representa la práctica "
                "histórica de la planta. Se utiliza como comparación "
                "y no como formulación óptima obligatoria."
            )

            # ====================================================
            # SECCIÓN 2
            # PROPORCIÓN REAL
            # ====================================================

            st.subheader(
                "Proporción real ingresada"
            )

            col_p1, col_p2, col_p3 = st.columns(3)

            with col_p1:
                st.metric(
                    "RO",
                    f"{pct_ro:.1f}%"
                )

            with col_p2:
                st.metric(
                    "Cartón",
                    f"{pct_ca:.1f}%"
                )

            with col_p3:
                st.metric(
                    "Lodo",
                    f"{pct_ld:.1f}%"
                )

            if rod_obj > 0:

                st.info(
                    f"Se incluyen adicionalmente "
                    f"{rod_obj:.2f} ton de ROD. "
                    f"El ROD se considera material complementario "
                    f"y no forma parte de la referencia 60/20/20."
                )

            # ====================================================
            # DIFERENCIAS HISTÓRICAS
            # ====================================================

            st.subheader(
                "Diferencia respecto a la referencia histórica"
            )

            diferencia_ro = (
                ro_obj - ro_hist
            )

            diferencia_ca = (
                ca_obj - ca_hist
            )

            col_d1, col_d2 = st.columns(2)

            with col_d1:

                if diferencia_ro >= 0:

                    st.metric(
                        "RO disponible sobre referencia",
                        f"{diferencia_ro:.2f} ton"
                    )

                    st.caption(
                        "Representa material disponible por encima "
                        "de la referencia histórica. No significa "
                        "que deba agregarse."
                    )

                else:

                    st.metric(
                        "RO faltante para referencia",
                        f"{abs(diferencia_ro):.2f} ton"
                    )

            with col_d2:

                if diferencia_ca >= 0:

                    st.metric(
                        "Cartón disponible sobre referencia",
                        f"{diferencia_ca:.2f} ton"
                    )

                else:

                    st.metric(
                        "Cartón faltante para referencia",
                        f"{abs(diferencia_ca):.2f} ton"
                    )

                    st.caption(
                        "Cantidad que faltaría únicamente si se "
                        "quisiera reproducir la proporción histórica."
                    )

            # ====================================================
            # ALTERNATIVA A
            # SOLO ASERRÍN
            # ====================================================

            aserrin_solo = material_para_cn(
                mezcla_base["carbono"],
                mezcla_base["nitrogeno"],
                "AS"
            )

            mezcla_solo_aserrin = calcular_mezcla(
                ro_obj,
                rod_obj,
                ca_obj,
                lodo_obj,
                aserrin_solo
            )

            # ====================================================
            # ALTERNATIVA B
            # SOLO CARTÓN ADICIONAL
            # ====================================================

            carton_adicional = material_para_cn(
                mezcla_base["carbono"],
                mezcla_base["nitrogeno"],
                "CA"
            )

            mezcla_solo_carton = calcular_mezcla(
                ro_obj,
                rod_obj,
                ca_obj + carton_adicional,
                lodo_obj,
                0
            )

            # ====================================================
            # ALTERNATIVA C
            # CARTÓN + ASERRÍN
            # ====================================================

            # Se toma primero el cartón faltante para acercarse
            # a la referencia histórica.
            carton_combinado = max(
                0,
                ca_hist - ca_obj
            )

            mezcla_con_carton_ref = calcular_mezcla(
                ro_obj,
                rod_obj,
                ca_obj + carton_combinado,
                lodo_obj,
                0
            )

            aserrin_combinado = material_para_cn(
                mezcla_con_carton_ref["carbono"],
                mezcla_con_carton_ref["nitrogeno"],
                "AS"
            )

            mezcla_combinada = calcular_mezcla(
                ro_obj,
                rod_obj,
                ca_obj + carton_combinado,
                lodo_obj,
                aserrin_combinado
            )

            # ====================================================
            # PLANIFICACIÓN DE ALTERNATIVAS
            # ====================================================

            st.subheader(
                "Alternativas de material estructurante"
            )

            col_alt1, col_alt2, col_alt3 = st.columns(3)

            with col_alt1:

                st.metric(
                    "Alternativa A - Aserrín",
                    f"{aserrin_solo:.2f} ton"
                )

                st.caption(
                    "Cantidad teórica si el ajuste se realiza "
                    "exclusivamente con aserrín."
                )

            with col_alt2:

                st.metric(
                    "Alternativa B - Cartón adicional",
                    f"{carton_adicional:.2f} ton"
                )

                st.caption(
                    "Cantidad teórica si el ajuste se realiza "
                    "exclusivamente con cartón."
                )

            with col_alt3:

                st.metric(
                    "Alternativa C - Cartón + aserrín",
                    (
                        f"{carton_combinado:.2f} ton CA + "
                        f"{aserrin_combinado:.2f} ton AS"
                    )
                )

                st.caption(
                    "Primero aproxima el cartón a la referencia "
                    "histórica y después calcula el aserrín necesario."
                )
# ====================================================
            # INDICADORES DE ESTRUCTURANTE POR TONELADA DE LODO
            # ====================================================

            if lodo_obj > 0:

                # Alternativa A: solo aserrín
                estructurante_por_ton_aserrin = (
                    aserrin_solo / lodo_obj
                )

                # Alternativa B: solo cartón adicional
                estructurante_por_ton_carton = (
                    carton_adicional / lodo_obj
                )

                # Alternativa C: cartón + aserrín
                estructurante_total_combinado = (
                    carton_combinado
                    + aserrin_combinado
                )

                estructurante_por_ton_combinado = (
                    estructurante_total_combinado
                    / lodo_obj
                )

            else:

                estructurante_por_ton_aserrin = 0
                estructurante_por_ton_carton = 0
                estructurante_total_combinado = 0
                estructurante_por_ton_combinado = 0


            # ====================================================
            # COMPARACIÓN DE ESCENARIOS
            # ====================================================

            st.subheader(
                "Comparación técnica de escenarios"
            )

            df_alternativas = pd.DataFrame({

                "Escenario": [
                    "Mezcla sin ajuste",
                    "Solo aserrín",
                    "Solo cartón adicional",
                    "Cartón + aserrín",
                    "Referencia histórica 60/20/20"
                ],

                "RO (ton)": [
                    ro_obj,
                    ro_obj,
                    ro_obj,
                    ro_obj,
                    ro_hist
                ],

                "ROD (ton)": [
                    rod_obj,
                    rod_obj,
                    rod_obj,
                    rod_obj,
                    0
                ],

                "Cartón total (ton)": [
                    ca_obj,
                    ca_obj,
                    ca_obj + carton_adicional,
                    ca_obj + carton_combinado,
                    ca_hist
                ],

                "Lodo (ton)": [
                    lodo_obj,
                    lodo_obj,
                    lodo_obj,
                    lodo_obj,
                    ld_hist
                ],

                "Aserrín (ton)": [
                    0,
                    aserrin_solo,
                    0,
                    aserrin_combinado,
                    0
                ],

                "Estructurante adicional / ton LD": [
                    0,
                    estructurante_por_ton_aserrin,
                    estructurante_por_ton_carton,
                    estructurante_por_ton_combinado,
                    0
                ],

                "Masa total (ton)": [
                    mezcla_base["masa"],
                    mezcla_solo_aserrin["masa"],
                    mezcla_solo_carton["masa"],
                    mezcla_combinada["masa"],
                    mezcla_hist["masa"]
                ],

                "Humedad (%)": [
                    mezcla_base["humedad"],
                    mezcla_solo_aserrin["humedad"],
                    mezcla_solo_carton["humedad"],
                    mezcla_combinada["humedad"],
                    mezcla_hist["humedad"]
                ],

                "Relación C/N": [
                    mezcla_base["cn"],
                    mezcla_solo_aserrin["cn"],
                    mezcla_solo_carton["cn"],
                    mezcla_combinada["cn"],
                    mezcla_hist["cn"]
                ]
            })

            st.dataframe(
                df_alternativas,
                use_container_width=True
            )


            # ====================================================
            # FUNCIÓN DE ESTADO
            # ====================================================

            def evaluar_estado(mezcla):

                humedad = mezcla["humedad"]
                cn = mezcla["cn"]

                # Primero evaluamos C/N
                cumple_cn = (
                    cn >= cn_min
                    and cn <= cn_max
                )

                if not cumple_cn:
                    return "REFORMULAR"

                # Luego evaluamos humedad

                if humedad < hum_min:
                    return "HUMEDAD BAJA"

                elif humedad <= hum_min + 2:
                    return "VIABLE CERCA DEL LÍMITE MÍNIMO"

                elif humedad > hum_max:
                    return "HUMEDAD ALTA"

                elif humedad >= hum_max - 2:
                    return "VIABLE CERCA DEL LÍMITE MÁXIMO"

                else:
                    return "VIABLE"


            # ====================================================
            # EVALUAR CADA ALTERNATIVA
            # ====================================================

            estado_aserrin = evaluar_estado(
                mezcla_solo_aserrin
            )

            estado_carton = evaluar_estado(
                mezcla_solo_carton
            )

            estado_combinada = evaluar_estado(
                mezcla_combinada
            )


            # ====================================================
            # LECTURA PARA LA TOMA DE DECISIÓN
            # ====================================================

            st.subheader(
                "Lectura para la toma de decisión"
            )

            estados_viables = [
                "VIABLE",
                "VIABLE CERCA DEL LÍMITE MÍNIMO",
                "VIABLE CERCA DEL LÍMITE MÁXIMO"
            ]

            # Priorizamos primero alternativas plenamente VIABLES

            if estado_combinada == "VIABLE":

                st.success(
                    "🟢 La alternativa combinada de cartón + aserrín "
                    "mantiene la humedad y la relación C/N dentro de "
                    "los rangos establecidos con un margen operativo adecuado."
                )

            elif estado_aserrin == "VIABLE":

                st.success(
                    "🟢 La alternativa con aserrín mantiene la humedad "
                    "y la relación C/N dentro de los rangos establecidos "
                    "con un margen operativo adecuado."
                )

            elif estado_carton == "VIABLE":

                st.success(
                    "🟢 La alternativa con cartón adicional mantiene "
                    "la humedad y la relación C/N dentro de los rangos "
                    "establecidos con un margen operativo adecuado."
                )

            # Si ninguna está plenamente viable,
            # mostramos las que cumplen pero están cerca de un límite.

            elif estado_combinada in estados_viables:

                st.warning(
                    f"🟡 La alternativa combinada de cartón + aserrín "
                    f"es técnicamente admisible, pero su estado es: "
                    f"{estado_combinada}. "
                    f"Se recomienda verificar la humedad real antes "
                    f"de aplicar la formulación."
                )

            elif estado_aserrin in estados_viables:

                st.warning(
                    f"🟡 La alternativa con aserrín es técnicamente "
                    f"admisible, pero su estado es: {estado_aserrin}. "
                    f"Se recomienda verificar la humedad real antes "
                    f"de aplicar la formulación."
                )

            elif estado_carton in estados_viables:

                st.warning(
                    f"🟡 La alternativa con cartón es técnicamente "
                    f"admisible, pero su estado es: {estado_carton}. "
                    f"Se recomienda verificar la humedad real antes "
                    f"de aplicar la formulación."
                )

            else:

                st.warning(
                    "⚠️ Ninguna de las alternativas evaluadas alcanza "
                    "simultáneamente condiciones adecuadas de humedad "
                    "y relación C/N. Esto no significa necesariamente "
                    "que exista un error de cálculo; puede indicar que "
                    "la composición inicial requiere redistribuir materiales "
                    "entre lotes o evaluar otra combinación antes de "
                    "definir el abastecimiento."
                )


            # ====================================================
            # DETALLE DE CADA ALTERNATIVA
            # ====================================================

            st.subheader(
                "Resultado de cada alternativa"
            )

            col_r1, col_r2, col_r3 = st.columns(3)


            # ----------------------------------------------------
            # SOLO ASERRÍN
            # ----------------------------------------------------

            with col_r1:

                st.write(
                    "*Solo aserrín*"
                )

                st.metric(
                    "Estructurante adicional",
                    f"{aserrin_solo:.2f} ton"
                )

                st.metric(
                    "Estructurante por ton de lodo",
                    f"{estructurante_por_ton_aserrin:.2f} ton/t LD"
                )

                st.metric(
                    "Humedad",
                    f"{mezcla_solo_aserrin['humedad']:.2f}%"
                )

                st.metric(
                    "C/N",
                    f"{mezcla_solo_aserrin['cn']:.2f}"
                )

                st.write(
                    f"Estado: *{estado_aserrin}*"
                )


            # ----------------------------------------------------
            # SOLO CARTÓN
            # ----------------------------------------------------

            with col_r2:

                st.write(
                    "*Solo cartón*"
                )

                st.metric(
                    "Cartón adicional",
                    f"{carton_adicional:.2f} ton"
                )

                st.metric(
                    "Estructurante por ton de lodo",
                    f"{estructurante_por_ton_carton:.2f} ton/t LD"
                )

                st.metric(
                    "Humedad",
                    f"{mezcla_solo_carton['humedad']:.2f}%"
                )

                st.metric(
                    "C/N",
                    f"{mezcla_solo_carton['cn']:.2f}"
                )

                st.write(
                    f"Estado: *{estado_carton}*"
                )


            # ----------------------------------------------------
            # CARTÓN + ASERRÍN
            # ----------------------------------------------------

            with col_r3:

                st.write(
                    "*Cartón + aserrín*"
                )

                st.metric(
                    "Estructurante adicional total",
                    f"{estructurante_total_combinado:.2f} ton"
                )

                st.metric(
                    "Estructurante por ton de lodo",
                    f"{estructurante_por_ton_combinado:.2f} ton/t LD"
                )

                st.metric(
                    "Humedad",
                    f"{mezcla_combinada['humedad']:.2f}%"
                )

                st.metric(
                    "C/N",
                    f"{mezcla_combinada['cn']:.2f}"
                )

                st.write(
                    f"Estado: *{estado_combinada}*"
                )
# ====================================================
            # SELECCIÓN DE ALTERNATIVA Y REPORTE
            # ====================================================

            st.subheader(
                "Selección de alternativa"
            )

            alternativa_seleccionada = st.selectbox(
                "Seleccione la alternativa que se aplicará",
                [
                    "Solo aserrín",
                    "Solo cartón",
                    "Cartón + aserrín"
                ],
                key="alternativa_seleccionada_capacidad"
            )

            justificacion = st.text_area(
                "Justificación / observación de la decisión",
                placeholder=(
                    "Ejemplo: Se selecciona la alternativa con aserrín "
                    "porque mantiene la humedad y la relación C/N dentro "
                    "de los rangos establecidos y existe disponibilidad "
                    "para gestionar este material."
                ),
                key="justificacion_capacidad"
            )

            # ====================================================
            # DATOS SEGÚN ALTERNATIVA SELECCIONADA
            # ====================================================

            if alternativa_seleccionada == "Solo aserrín":

                estructurante_tipo = "Aserrín"

                estructurante_cantidad = (
                    aserrin_solo
                )

                estructurante_por_ton = (
                    estructurante_por_ton_aserrin
                )

                humedad_reporte = (
                    mezcla_solo_aserrin["humedad"]
                )

                cn_reporte = (
                    mezcla_solo_aserrin["cn"]
                )

                masa_reporte = (
                    mezcla_solo_aserrin["masa"]
                )

                estado_reporte = (
                    estado_aserrin
                )

                detalle_estructurante = (
                    f"Aserrín: {aserrin_solo:.2f} ton"
                )

            elif alternativa_seleccionada == "Solo cartón":

                estructurante_tipo = "Cartón adicional"

                estructurante_cantidad = (
                    carton_adicional
                )

                estructurante_por_ton = (
                    estructurante_por_ton_carton
                )

                humedad_reporte = (
                    mezcla_solo_carton["humedad"]
                )

                cn_reporte = (
                    mezcla_solo_carton["cn"]
                )

                masa_reporte = (
                    mezcla_solo_carton["masa"]
                )

                estado_reporte = (
                    estado_carton
                )

                detalle_estructurante = (
                    f"Cartón adicional: "
                    f"{carton_adicional:.2f} ton"
                )

            else:

                estructurante_tipo = (
                    "Cartón + aserrín"
                )

                estructurante_cantidad = (
                    estructurante_total_combinado
                )

                estructurante_por_ton = (
                    estructurante_por_ton_combinado
                )

                humedad_reporte = (
                    mezcla_combinada["humedad"]
                )

                cn_reporte = (
                    mezcla_combinada["cn"]
                )

                masa_reporte = (
                    mezcla_combinada["masa"]
                )

                estado_reporte = (
                    estado_combinada
                )

                detalle_estructurante = (
                    f"Cartón adicional: "
                    f"{carton_combinado:.2f} ton | "
                    f"Aserrín: "
                    f"{aserrin_combinado:.2f} ton"
                )

            # ====================================================
            # RESUMEN DE LA ALTERNATIVA SELECCIONADA
            # ====================================================

            st.subheader(
                "Resumen de la alternativa seleccionada"
            )

            col_sel1, col_sel2, col_sel3, col_sel4 = (
                st.columns(4)
            )

            with col_sel1:

                st.metric(
                    "Estructurante requerido",
                    f"{estructurante_cantidad:.2f} ton"
                )

            with col_sel2:

                st.metric(
                    "Estructurante / ton LD",
                    f"{estructurante_por_ton:.2f}"
                )

            with col_sel3:

                st.metric(
                    "Humedad estimada",
                    f"{humedad_reporte:.2f}%"
                )

            with col_sel4:

                st.metric(
                    "Relación C/N",
                    f"{cn_reporte:.2f}"
                )

            st.write(
                f"Estado técnico: *{estado_reporte}*"
            )

            # ====================================================
            # FUNCIÓN PARA GENERAR PDF
            # ====================================================

            def generar_reporte_pdf():

                pdf = FPDF()

                pdf.add_page()

                pdf.set_auto_page_break(
                    auto=True,
                    margin=15
                )

                # --------------------------------------------
                # TÍTULO
                # --------------------------------------------

                pdf.set_font(
                    "Helvetica",
                    "B",
                    16
                )

                pdf.cell(
                    0,
                    10,
                    "SAFCO - Reporte de planificación de mezcla",
                    ln=True,
                    align="C"
                )

                pdf.ln(5)

                pdf.set_font(
                    "Helvetica",
                    "",
                    10
                )

                pdf.cell(
                    0,
                    7,
                    f"Fecha de generación: "
                    f"{datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    ln=True
                )

                pdf.cell(
                    0,
                    7,
                    f"Periodo evaluado: "
                    f"{periodo_planificacion}",
                    ln=True
                )

                pdf.ln(5)

                # --------------------------------------------
                # MATERIALES INGRESADOS
                # --------------------------------------------

                pdf.set_font(
                    "Helvetica",
                    "B",
                    12
                )

                pdf.cell(
                    0,
                    8,
                    "1. Materiales ingresados",
                    ln=True
                )

                pdf.set_font(
                    "Helvetica",
                    "",
                    10
                )

                pdf.cell(
                    0,
                    6,
                    f"Residuos organicos (RO): "
                    f"{ro_obj:.2f} ton",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Residuos organicos deshidratados (ROD): "
                    f"{rod_obj:.2f} ton",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Carton disponible: "
                    f"{ca_obj:.2f} ton",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Lodo a procesar: "
                    f"{lodo_obj:.2f} ton",
                    ln=True
                )

                pdf.ln(5)

                # --------------------------------------------
                # REFERENCIA HISTÓRICA
                # --------------------------------------------

                pdf.set_font(
                    "Helvetica",
                    "B",
                    12
                )

                pdf.cell(
                    0,
                    8,
                    "2. Referencia historica 60/20/20",
                    ln=True
                )

                pdf.set_font(
                    "Helvetica",
                    "",
                    10
                )

                pdf.cell(
                    0,
                    6,
                    f"RO de referencia: "
                    f"{ro_hist:.2f} ton",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Carton de referencia: "
                    f"{ca_hist:.2f} ton",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Lodo de referencia: "
                    f"{ld_hist:.2f} ton",
                    ln=True
                )

                pdf.ln(5)

                # --------------------------------------------
                # ALTERNATIVA
                # --------------------------------------------

                pdf.set_font(
                    "Helvetica",
                    "B",
                    12
                )

                pdf.cell(
                    0,
                    8,
                    "3. Alternativa seleccionada",
                    ln=True
                )

                pdf.set_font(
                    "Helvetica",
                    "",
                    10
                )

                pdf.cell(
                    0,
                    6,
                    f"Alternativa: "
                    f"{alternativa_seleccionada}",
                    ln=True
                )

                pdf.multi_cell(
                    0,
                    6,
                    f"Material estructurante: "
                    f"{detalle_estructurante}"
                )

                pdf.cell(
                    0,
                    6,
                    f"Estructurante total: "
                    f"{estructurante_cantidad:.2f} ton",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Estructurante por tonelada de lodo: "
                    f"{estructurante_por_ton:.2f} ton/t LD",
                    ln=True
                )

                pdf.ln(5)

                # --------------------------------------------
                # RESULTADOS
                # --------------------------------------------

                pdf.set_font(
                    "Helvetica",
                    "B",
                    12
                )

                pdf.cell(
                    0,
                    8,
                    "4. Resultado tecnico estimado",
                    ln=True
                )

                pdf.set_font(
                    "Helvetica",
                    "",
                    10
                )

                pdf.cell(
                    0,
                    6,
                    f"Masa total estimada: "
                    f"{masa_reporte:.2f} ton",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Humedad estimada: "
                    f"{humedad_reporte:.2f} %",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Relacion C/N estimada: "
                    f"{cn_reporte:.2f}",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Estado: "
                    f"{estado_reporte}",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Rango humedad: "
                    f"{hum_min:.0f} - {hum_max:.0f} %",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Objetivo de humedad: "
                    f"{hum_objetivo:.1f} %",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Rango C/N: "
                    f"{cn_min:.1f} - {cn_max:.1f}",
                    ln=True
                )

                pdf.cell(
                    0,
                    6,
                    f"Objetivo C/N: "
                    f"{cn_objetivo:.1f}",
                    ln=True
                )

                pdf.ln(5)

                # --------------------------------------------
                # JUSTIFICACIÓN
                # --------------------------------------------

                pdf.set_font(
                    "Helvetica",
                    "B",
                    12
                )

                pdf.cell(
                    0,
                    8,
                    "5. Justificacion de la decision",
                    ln=True
                )

                pdf.set_font(
                    "Helvetica",
                    "",
                    10
                )

                if justificacion.strip():

                    pdf.multi_cell(
                        0,
                        6,
                        justificacion
                    )

                else:

                    pdf.multi_cell(
                        0,
                        6,
                        "No se registro una justificacion adicional."
                    )

                pdf.ln(5)

                # --------------------------------------------
                # NOTAS
                # --------------------------------------------

                pdf.set_font(
                    "Helvetica",
                    "B",
                    12
                )

                pdf.cell(
                    0,
                    8,
                    "6. Consideraciones",
                    ln=True
                )

                pdf.set_font(
                    "Helvetica",
                    "",
                    9
                )

                pdf.multi_cell(
                    0,
                    5,
                    "La referencia 60/20/20 corresponde a la practica "
                    "historica de la planta y no representa una "
                    "formulacion optima obligatoria."
                )

                pdf.multi_cell(
                    0,
                    5,
                    "Las propiedades del aserrin son referenciales "
                    "(20% humedad, 50% carbono y 0.10% nitrogeno) "
                    "hasta disponer de ficha tecnica o caracterizacion."
                )

                pdf.multi_cell(
                    0,
                    5,
                    "La planificacion puede realizarse a nivel diario, "
                    "semanal o mensual. La dosificacion final debe "
                    "verificarse con las condiciones reales de cada lote."
                )

                # --------------------------------------------
                # DEVOLVER PDF
                # --------------------------------------------

                return bytes(
                    pdf.output()
                )

            # ====================================================
            # BOTÓN DE DESCARGA
            # ====================================================

            pdf_reporte = generar_reporte_pdf()

            nombre_pdf = (
                f"SAFCO_planificacion_"
                f"{periodo_planificacion.lower()}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            )

            st.download_button(
                label="📄 Descargar reporte PDF",
                data=pdf_reporte,
                file_name=nombre_pdf,
                mime="application/pdf",
                use_container_width=True
            )

            # ====================================================
            # EXPLICACIÓN DEL INDICADOR
            # ====================================================

            st.info(
                "💡 El indicador 'Estructurante por ton de lodo' "
                "muestra cuántas toneladas de material estructurante "
                "adicional se estiman por cada tonelada de lodo a procesar. "
                "El resultado considera toda la composición ingresada "
                "(RO, ROD, cartón y lodo), por lo que no representa "
                "una relación exclusiva entre el estructurante y el lodo."
            )
            # ====================================================
            # EXPLICACIÓN
            # ====================================================

            with st.expander(
                "¿Cómo interpretar las alternativas?"
            ):

                st.write(
                    "*Solo aserrín:* muestra cuánto aserrín sería "
                    "necesario si se utilizara como único material "
                    "corrector de la relación C/N."
                )

                st.write(
                    "*Solo cartón:* evalúa la cantidad de cartón "
                    "adicional necesaria si se utiliza únicamente "
                    "este material estructurante."
                )

                st.write(
                    "*Cartón + aserrín:* primero aprovecha el cartón "
                    "como material habitual de planta y después utiliza "
                    "aserrín como complemento."
                )

                st.write(
                    "**Una cantidad elevada de material estructurante "
                    "no significa automáticamente que el cálculo esté "
                    "equivocado.** Puede indicar que los materiales "
                    "ingresados se encuentran muy alejados de las "
                    "condiciones objetivo."
                )

                st.write(
                    "*Planificación mensual:* permite estimar necesidades "
                    "de abastecimiento. La aplicación real debe verificarse "
                    "por lote, semana o periodo operativo según las "
                    "condiciones reales de los materiales."
                )

                st.write(
                    f"Rango de humedad utilizado: "
                    f"{hum_min:.0f}% - {hum_max:.0f}%."
                )

                st.write(
                    f"Objetivo operativo de humedad: "
                    f"{hum_objetivo:.1f}%."
                )

                st.write(
                    f"Rango C/N utilizado: "
                    f"{cn_min:.1f} - {cn_max:.1f}."
                )

                st.write(
                    f"Objetivo C/N: "
                    f"{cn_objetivo:.1f}."
                )

            st.warning(
                "Las propiedades del aserrín siguen siendo referenciales. "
                "La planificación debe recalcularse cuando se disponga "
                "de ficha técnica o caracterización del material real."
            )

            st.caption(
                f"Periodo evaluado: {periodo_planificacion}. "
                "La referencia 60/20/20 se utiliza únicamente como "
                "comparación de la práctica histórica de planta."
            )

        else:

            st.info(
                "Ingrese una cantidad de lodo mayor a cero "
                "y los materiales disponibles para realizar "
                "la planificación."
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
