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
    
            if masa_seca_total > 0:
    
                carbono_pct = (
                    carbono_total
                    / masa_seca_total
                ) * 100
    
                nitrogeno_pct = (
                    nitrogeno_total
                    / masa_seca_total
                ) * 100
    
            else:
    
                carbono_pct = 0
                nitrogeno_pct = 0
    
            if nitrogeno_total > 0:
    
                relacion_cn = (
                    carbono_total
                    / nitrogeno_total
                )
    
            else:
    
                relacion_cn = 0
    
            fila_mesofila = df_parametros[
                df_parametros["fase"] == "Mesofila I"
            ].iloc[0]
    
            hum_min = fila_mesofila["humedad_min"]
            hum_max = fila_mesofila["humedad_max"]
            cn_min = fila_mesofila["cn_min"]
            cn_max = fila_mesofila["cn_max"]
    
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
                "ro": ro,
                "rod": rod,
                "ld": ld,
                "ca": ca,
                "masa_total": masa_total,
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
                "Formulación calculada y registrada correctamente"
            )
    
            # =========================
            # RESULTADOS
            # =========================
    
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
    
            # =========================
            # RECOMENDACIONES
            # =========================
    
            clave_humedad = (
                f"HUMEDAD INICIAL|{estado_humedad}"
            )
    
            fila_humedad = df_reglas[
                df_reglas["clave"] == clave_humedad
            ]
    
            clave_cn = (
                f"RELACION C/N|{estado_cn}"
            )
    
            fila_cn = df_reglas[
                df_reglas["clave"] == clave_cn
            ]
    
            if not fila_humedad.empty:
                st.info(
                    f"Recomendación humedad: "
                    f"{fila_humedad.iloc[0]['recomendacion']}"
                )
    
            if not fila_cn.empty:
                st.info(
                    f"Recomendación C/N: "
                    f"{fila_cn.iloc[0]['recomendacion']}"
                )
    
        else:
    
            st.warning(
                "Ingrese al menos una cantidad de material "
                "para realizar la formulación."
            )

    st.subheader("Historial de formulaciones")
    
    df_form_hist = pd.read_csv("formulaciones.csv")
    
    if not df_form_hist.empty:
    
        lotes_disponibles = sorted(
            df_form_hist["codigo_lote"]
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
            df_form_filtrado = df_form_hist
        else:
            df_form_filtrado = df_form_hist[
                df_form_hist["codigo_lote"].astype(str)
                == lote_filtro
            ]
    
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
        lodo_por_humedad = max(0, lodo_por_humedad)
        
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
