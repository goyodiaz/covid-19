import unicodedata
import urllib

import pandas as pd
import streamlit as st


def main():
    title = "COVID-19 - Capacidad asistencial"
    st.set_page_config(
        page_title=title,
        layout="wide",
        menu_items={"About": "Hecho por Goyo con mucho trabajo."},
    )

    date = pd.Timestamp("2023-07-14").date()
    url = get_url(date=date)
    st.sidebar.markdown(f"[Datos originales]({url})")
    separator = ";"
    date_format = "%d/%m/%Y"

    group = st.sidebar.checkbox("Agrupar")
    by = st.sidebar.radio(
        label="Agrupar por",
        options=["Provincia", "CCAA"],
        horizontal=True,
        disabled=not group,
        label_visibility="collapsed",
    )

    try:
        data = get_data(url=url, sep=separator, date_format=date_format)
    except urllib.error.HTTPError as e:
        st.error(f"No se pudieron descargar los datos.")
        st.stop()
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
    st.write(data)


class DateFormatError(ValueError):
    pass


def get_url(date):
    formatted_date = date.strftime("%d%m%Y")
    return f"https://www.sanidad.gob.es/areas/alertasEmergenciasSanitarias/alertasActuales/nCov/documentos/Datos_Capacidad_Asistencial_Historico_{formatted_date}.csv"


@st.cache_resource(show_spinner="Downloading and parsing data...")
def get_data(url, sep, date_format):
    data = (
        pd.read_csv(url, sep=sep, encoding="latin")[:-5]
        .drop(["COD_CCAA", "Cod_Provincia"], axis="columns")
        .dropna(how="all")
    )
    try:
        data["Fecha"] = pd.to_datetime(data["Fecha"], format=date_format)
    except ValueError as e:
        raise DateFormatError(e.args[0])
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
        st.area_chart(data)
    elif chart_type == "Barras":
        st.bar_chart(data)


if __name__ == "__main__":
    main()
