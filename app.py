import unicodedata

import pandas as pd
import streamlit as st

# original data:
# https://www.sanidad.gob.es/areas/alertasEmergenciasSanitarias/alertasActuales/nCov/documentos/Datos_Capacidad_Asistencial_Historico_14072023.csv
DATA_URL = "Datos_Capacidad_Asistencial_Historico_14072023.csv"


def main():
    title = "COVID-19 - Capacidad asistencial"
    st.set_page_config(
        page_title=title,
        layout="wide",
        menu_items={"About": "Hecho por Goyo con mucho trabajo."},
    )

    with open(DATA_URL, "rb") as file:
        st.sidebar.download_button(
            label="Descargar datos",
            data=file,
            file_name=DATA_URL,
            icon=":material/download_2:",
        )

    group = st.sidebar.checkbox("Agrupar")
    by = st.sidebar.radio(
        label="Agrupar por",
        options=["Provincia", "CCAA"],
        horizontal=True,
        disabled=not group,
        label_visibility="collapsed",
    )

    data = get_data()
    options = get_unique(data=data, col_name=by)
    start, end = data["Fecha"].iloc[[0, -1]].dt.date

    region = st.sidebar.selectbox(
        by, options, disabled=not group, label_visibility="collapsed"
    )

    if group:
        data = data[data[by] == region]

    chart_type = st.sidebar.radio(
        label="Tipo de gráfico", options=["Líneas", "Área", "Barras"], horizontal=True
    )

    per_unit = st.sidebar.checkbox(label="Por unidad de hospitalización")

    st.title(title)
    st.markdown(
        "Elaborado a partir de los [datos abiertos de capacidad asistencial]("
        "https://www.sanidad.gob.es/areas/alertasEmergenciasSanitarias/alertasActuales/nCov/capacidadAsistencial.htm"
        ") publicados por el Ministerio de Sanidad."
    )

    start, end = st.slider(
        label="Interval",
        min_value=start,
        max_value=end,
        value=(start, end),
        label_visibility="collapsed",
    )

    data = data[data["Fecha"].between(pd.Timestamp(start), pd.Timestamp(end))]
    col_names = data.columns.drop(["Fecha", "Unidad", "CCAA", "Provincia"])

    if per_unit:
        variable = st.sidebar.selectbox("Variable", options=col_names)
        data = (
            data.groupby(["Fecha", "Unidad"])[variable]
            .sum()
            .reset_index()
            .pivot(index="Fecha", columns="Unidad", values=variable)
        )
    else:
        variables = st.sidebar.multiselect("Variables", options=col_names)
        if not variables:
            st.error("Selecciona una o varias variables.")
            st.stop()
        data = data.groupby("Fecha")[variables].sum(numeric_only=True)

    show_chart(data=data, chart_type=chart_type)
    st.dataframe(data)


@st.cache_resource(show_spinner="Downloading and parsing data...")
def get_data():
    data = (
        pd.read_csv(DATA_URL, sep=";", encoding="latin")[:-5]
        .drop(["COD_CCAA", "Cod_Provincia"], axis="columns")
        .dropna(how="all")
    )
    data["Fecha"] = pd.to_datetime(data["Fecha"], format="%d/%m/%Y")
    return data


@st.cache_resource()
def get_unique(data, col_name):
    return sorted(
        data[col_name].unique(),
        key=lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore"),
    )


def show_chart(data, chart_type):
    if chart_type == "Líneas":
        st.line_chart(data)
    elif chart_type == "Área":
        st.area_chart(data, stack=True)
    elif chart_type == "Barras":
        st.bar_chart(data)


if __name__ == "__main__":
    main()
