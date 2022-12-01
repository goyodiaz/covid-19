from dataclasses import dataclass
import unicodedata

import numpy as np
import pandas as pd
import streamlit as st


def main():
    title = "COVID-19 - Capacidad asistencial"
    st.set_page_config(
        page_title=title,
        layout="wide",
        menu_items={"About": "Hecho por Goyo con mucho trabajo."},
    )
    date = st.sidebar.date_input("Fecha")
    
    formatted_date = date.strftime("%d%m%Y")
    url = f"https://www.sanidad.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov/documentos/Datos_Capacidad_Asistencial_Historico_{formatted_date}.csv"

    st.sidebar.markdown(f"[Datos originales]({url})")

    date_formats = {"%d/%m/%Y": "dd/mm/aaaa", "%m/%d/%Y": "mm/dd/aaaa"}
    date_format = st.sidebar.radio(
        label="Formato de fecha",
        options=date_formats,
        format_func=lambda x: date_formats[x],
        horizontal=True,
    )

    group = st.sidebar.checkbox("Agrupar")
    by = st.sidebar.radio(
        label="Agrupar por",
        options=["Provincia", "CCAA"],
        horizontal=True,
        disabled=not group,
        label_visibility="collapsed",
    )

    data = get_data(url=url, date_format=date_format)
    options = get_unique(data=data, col_name=by)

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

    min_date = data["Fecha"].iloc[0].date()
    max_date = data["Fecha"].iloc[-1].date()

    start_date, end_date = st.slider(
        label="Interval",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        label_visibility="collapsed",
    )
    st.text(f"{start_date} - {end_date}")

    data = data[data["Fecha"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))]
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
            st.error("Choose at least one variable.")
            st.stop()
        data = data.groupby("Fecha")[variables].sum(numeric_only=True)

    data = data.astype(int)
    show_chart(data=data, chart_type=chart_type)
    st.write(data)


@st.experimental_memo(show_spinner="Downloading and parsing data...", max_entries=1)
def get_data(url, date_format):
    data = pd.read_csv(url, sep=";", encoding="latin")[:-5].drop(
        ["COD_CCAA", "Cod_Provincia"], axis="columns"
    )
    data = data.dropna(how="all")
    data["Fecha"] = pd.to_datetime(data["Fecha"], format=date_format)
    return data


@st.experimental_memo(max_entries=3)
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
