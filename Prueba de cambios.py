# %%writefile app.py
import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA Y BANNER
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard de Salud - Análisis Exploratorio",
    layout="wide",
    initial_sidebar_state="collapsed"
)

banner_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXlJYfQJi6EHpzwP6115nt1LYMURK9VaCXrw&s"
st.image(banner_url, use_column_width=True)

# ---------------------------------------------------------------------------
# CONEXIÓN Y CARGA DE DATOS
# ---------------------------------------------------------------------------
# Conexión a la base de datos MySQL (health_db)
conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="PruebaEstu2012",
    database="health_db"
)

# Consulta para obtener la información de pacientes y sus estados (con coordenadas)
query_patients = """
SELECT p.id, p.name, p.age, p.sex, s.name as state, s.latitude, s.longitude,
       p.palabras, p.registration_date
FROM patients p
JOIN states s ON p.state_id = s.id
"""
df_patients = pd.read_sql(query_patients, conn)

# Consulta para obtener las patologías de cada paciente
query_pathologies = """
SELECT pp.patient_id, pt.name as pathology
FROM patient_pathologies pp
JOIN pathologies pt ON pp.pathology_id = pt.id
"""
df_pathologies = pd.read_sql(query_pathologies, conn)
conn.close()

# Agrupar las patologías por paciente (concatenadas en una cadena separada por comas)
df_path = df_pathologies.groupby("patient_id")["pathology"].apply(lambda x: ", ".join(x)).reset_index()
df = pd.merge(df_patients, df_path, how="left", left_on="id", right_on="patient_id")
df.drop("patient_id", axis=1, inplace=True)

# Convertir la columna de fecha a datetime (para la evolución de registros)
df["registration_date"] = pd.to_datetime(df["registration_date"])

# ---------------------------------------------------------------------------
# SIDEBAR - FILTROS (selectboxes desplegables)
# ---------------------------------------------------------------------------
st.sidebar.header("Filtros")

# 1. Filtro por Estado: Lista desplegable con "Todos" por defecto.
states_options = ["Todos"] + sorted(df["state"].unique())
selected_state = st.sidebar.selectbox("Estado:", options=states_options, index=0)

# 2. Filtro por Rango Etario: Lista desplegable con "Todas" por defecto.
age_group_options = ["Todas", "18-30", "31-45", "46-60", "61-90"]
selected_age_group = st.sidebar.selectbox("Rango Etario:", options=age_group_options, index=0)

# 3. Filtro por Enfermedad: Lista desplegable con "Todas" por defecto.
disease_options = ["Todas", "Cáncer", "Diabetes", "Obesidad", "Hipertensión", "Asma", "Enfermedad Cardiovascular"]
selected_disease = st.sidebar.selectbox("Enfermedad:", options=disease_options, index=0)

# Aplicar filtros (si se selecciona "Todos" se muestran todos los datos)
filtered_df = df.copy()

if selected_state != "Todos":
    filtered_df = filtered_df[filtered_df["state"] == selected_state]

if selected_age_group != "Todas":
    def age_in_group(age, group):
        if group == "18-30":
            return 18 <= age <= 30
        elif group == "31-45":
            return 31 <= age <= 45
        elif group == "46-60":
            return 46 <= age <= 60
        elif group == "61-90":
            return 61 <= age <= 90
        else:
            return True
    filtered_df = filtered_df[filtered_df["age"].apply(lambda x: age_in_group(x, selected_age_group))]

if selected_disease != "Todas":
    filtered_df = filtered_df[filtered_df["pathology"].apply(lambda x: selected_disease in x if pd.notnull(x) else False)]

# ---------------------------------------------------------------------------
# TÍTULO DEL DASHBOARD Y RESUMEN SUPERIOR
# ---------------------------------------------------------------------------
st.title("Dashboard de Salud - Análisis Exploratorio")

# Primera fila: Información resumen
col1, col2 = st.columns(2)
with col1:
    total_patients = filtered_df.shape[0]
    st.subheader("Resumen General")
    st.metric("Total de Pacientes", total_patients)
    if not filtered_df.empty:
        min_date = filtered_df["registration_date"].min().date()
        max_date = filtered_df["registration_date"].max().date()
        st.markdown(f"**Rango de Observaciones:** {min_date} a {max_date}")
    else:
        st.markdown("**Rango de Observaciones:** N/A")
    st.markdown("**Enfermedades (6):** Cáncer, Diabetes, Obesidad, Hipertensión, Asma, Enfermedad Cardiovascular")

with col2:
    # Histograma de Edades con gradiente de color (usando barras y un color continuo)
    st.subheader("Histograma de Edades")
    if not filtered_df.empty:
        bins = 20
        hist_counts, bin_edges = np.histogram(filtered_df["age"], bins=bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        df_hist = pd.DataFrame({"Edad": bin_centers, "Cantidad": hist_counts})
        fig_age = px.bar(
            df_hist,
            x="Edad",
            y="Cantidad",
            title="Distribución de Edades",
            color="Edad",
            color_continuous_scale="RdYlBu"
        )
        st.plotly_chart(fig_age, use_container_width=True)
    else:
        st.info("No hay datos para mostrar el histograma.")

# ---------------------------------------------------------------------------
# ROW 2: Evolución de Registros y Nube de Palabras
# ---------------------------------------------------------------------------
col3, col4 = st.columns(2)
with col3:
    st.subheader("Evolución de Registros")
    if not filtered_df.empty:
        df_time = filtered_df.groupby(filtered_df["registration_date"].dt.date).size().reset_index(name="count")
        df_time = df_time.sort_values("registration_date")
        fig_time = px.line(
            df_time,
            x="registration_date",
            y="count",
            markers=True,
            title="Tendencia de Registros Diarios",
            labels={"registration_date": "Fecha", "count": "Número de Registros"},
            color_discrete_sequence=["#2ca02c"]
        )
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("No hay datos para mostrar la evolución de registros.")

with col4:
    st.subheader("Nube de Palabras - Experiencia Tratamiento")
    all_text = " ".join(filtered_df["palabras"].dropna().tolist())
    if all_text.strip():
        wc = WordCloud(width=800, height=400, background_color="white").generate(all_text)
        fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
        ax_wc.imshow(wc, interpolation="bilinear")
        ax_wc.axis("off")
        st.pyplot(fig_wc)
    else:
        st.info("No hay texto suficiente para generar la nube de palabras.")

# ---------------------------------------------------------------------------
# ROW 3: Mapa de México y Distribución por Género
# ---------------------------------------------------------------------------
col5, col6 = st.columns(2)
with col5:
    st.subheader("Mapa de México - Distribución de Enfermos")
    state_counts = filtered_df.groupby("state").size().reset_index(name="patient_count")
    states_coords = df_patients[["state", "latitude", "longitude"]].drop_duplicates()
    map_df = pd.merge(state_counts, states_coords, on="state", how="left")
    if not map_df.empty:
        fig_map = px.scatter_mapbox(
            map_df,
            lat="latitude",
            lon="longitude",
            size="patient_count",
            color="patient_count",
            hover_name="state",
            zoom=3,
            mapbox_style="carto-positron",
            title="Pacientes por Estado"
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No hay datos para mostrar en el mapa.")

with col6:
    st.subheader("Distribución por Género")
    gender_counts = filtered_df["sex"].value_counts().reset_index()
    gender_counts.columns = ["sex", "count"]
    gender_color_map = {"M": "#1f77b4", "F": "#e377c2"}
    if not gender_counts.empty:
        fig_gender = px.pie(
            gender_counts,
            names="sex",
            values="count",
            title="Género de Pacientes",
            color="sex",
            color_discrete_map=gender_color_map
        )
        st.plotly_chart(fig_gender, use_container_width=True)
    else:
        st.info("No hay datos para mostrar la distribución por género.")

# ---------------------------------------------------------------------------
# ROW 4: Top 5 Estados con más Enfermedades y Distribución de Enfermedades
# ---------------------------------------------------------------------------
st.subheader("Top 5 Estados y Distribución de Enfermedades")
col7, col8 = st.columns(2)
with col7:
    def count_pathologies(x):
        if pd.isna(x):
            return 0
        return len(x.split(", "))
    # Se añade la columna de número de patologías
    filtered_df["num_pathologies"] = filtered_df["pathology"].apply(count_pathologies)
    top_states = (filtered_df.groupby("state")["num_pathologies"]
                  .sum()
                  .reset_index()
                  .sort_values(by="num_pathologies", ascending=False)
                  .head(5))
    if not top_states.empty:
        fig_top = px.bar(
            top_states,
            x="state",
            y="num_pathologies",
            title="Top 5 Estados con más Enfermedades",
            labels={"state": "Estado", "num_pathologies": "Número de Enfermedades"},
            color="state",
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        st.plotly_chart(fig_top, use_container_width=True)
    else:
        st.info("No hay datos para mostrar el top de estados.")

with col8:
    all_diseases = filtered_df["pathology"].dropna().str.split(", ").explode()
    disease_counts = all_diseases.value_counts().reset_index()
    disease_counts.columns = ["enfermedad", "count"]
    if not disease_counts.empty:
        fig_disease = px.pie(
            disease_counts,
            names="enfermedad",
            values="count",
            title="Distribución de Enfermedades",
            color="enfermedad",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_disease, use_container_width=True)
    else:
        st.info("No hay datos para mostrar la distribución de enfermedades.")

# ---------------------------------------------------------------------------
# ROW 5: Distribución por Grupo Etario
# ---------------------------------------------------------------------------
st.subheader("Distribución por Grupo Etario")
def assign_age_group(age):
    if 18 <= age <= 30:
        return "18-30"
    elif 31 <= age <= 45:
        return "31-45"
    elif 46 <= age <= 60:
        return "46-60"
    else:
        return "61-90"
filtered_df["age_group"] = filtered_df["age"].apply(assign_age_group)
age_group_counts = filtered_df["age_group"].value_counts().reset_index()
age_group_counts.columns = ["age_group", "count"]
if not age_group_counts.empty:
    fig_age_group = px.bar(
        age_group_counts,
        x="age_group",
        y="count",
        title="Distribución por Grupo Etario",
        labels={"age_group": "Grupo Etario", "count": "Número de Pacientes"},
        color="age_group",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig_age_group, use_container_width=True)
else:
    st.info("No hay datos para mostrar la distribución por grupo etario.")

# ---------------------------------------------------------------------------
# ROW 6: Tabla de Datos Filtrados (primeras 10 filas)
# ---------------------------------------------------------------------------
st.subheader("Datos Filtrados (Primeras 10 filas)")
st.dataframe(filtered_df.head(10))
