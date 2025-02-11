import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import random

# Configuración de la conexión a MySQL
username = "root"
password = "PruebaEstu2012"
host = "127.0.0.1"
database = "Salud_DB"

# Crear la URL de conexión
connection_url = f"mysql+mysqlconnector://{username}:{password}@{host}/{database}"
engine = create_engine(connection_url)

# Función para obtener el total de casos
def obtener_total_casos():
    query = "SELECT SUM(CONTEO) AS TOTAL_CASOS FROM Casos_Enfermedades"
    with engine.connect() as connection:
        result = connection.execute(text(query)).fetchone()
    return result[0] if result else 0

# Consulta para el número de casos por entidad
def casos_por_entidad():
    query = """
        SELECT us.ENTIDAD, SUM(ce.CONTEO) AS TOTAL_CASOS
        FROM Casos_Enfermedades ce
        JOIN Unidades_Salud us ON ce.CLUES = us.CLUES
        GROUP BY us.ENTIDAD
        ORDER BY TOTAL_CASOS DESC
    """
    with engine.connect() as connection:
        df = pd.read_sql_query(text(query), connection)
    return df

# Consulta para el top 10 de enfermedades
def top_enfermedades():
    query = """
        SELECT e.CODIGO_ENFERMEDAD, SUM(ce.CONTEO) AS TOTAL_CASOS
        FROM Casos_Enfermedades ce
        JOIN Enfermedades e ON ce.ID_ENFERMEDAD = e.ID_ENFERMEDAD
        GROUP BY e.CODIGO_ENFERMEDAD
        ORDER BY TOTAL_CASOS DESC
        LIMIT 10
    """
    with engine.connect() as connection:
        df = pd.read_sql_query(text(query), connection)
    
    # Mapeo aleatorio de nombres de enfermedades
    nombres_enfermedades = [
        "Diabetes", "Hipertensión", "Asma", "Artritis", "Gripe",
        "Covid-19", "Cáncer", "Tuberculosis", "Hepatitis", "Dengue"
    ]
    mapping = dict(zip(df['CODIGO_ENFERMEDAD'], nombres_enfermedades))
    df['ENFERMEDAD'] = df['CODIGO_ENFERMEDAD'].map(mapping)
    return df

# Consulta para la evolución temporal de los casos
def evolucion_temporal():
    query = """
        SELECT ANIO, MES, SUM(CONTEO) AS TOTAL_CASOS
        FROM Casos_Enfermedades
        GROUP BY ANIO, MES
        ORDER BY ANIO, MES
    """
    with engine.connect() as connection:
        df = pd.read_sql_query(text(query), connection)
    return df

# Consulta para los casos por unidad de salud (top 5)
def casos_por_unidad():
    query = """
        SELECT us.NOMBRE_CLUES, SUM(ce.CONTEO) AS TOTAL_CASOS
        FROM Casos_Enfermedades ce
        JOIN Unidades_Salud us ON ce.CLUES = us.CLUES
        GROUP BY us.NOMBRE_CLUES
        ORDER BY TOTAL_CASOS DESC
        LIMIT 5
    """
    with engine.connect() as connection:
        df = pd.read_sql_query(text(query), connection)
    return df

# Streamlit App
st.set_page_config(layout="wide")

# Título y contador total de casos
st.title("📊 Dashboard de Salud Pública")
total_casos = obtener_total_casos()
st.markdown(f"### Total de Casos Registrados: **{total_casos:,}**")

# Layout para gráficos
col1, col2 = st.columns(2)

# Gráfico 1: Número de casos por entidad
with col1:
    st.subheader("Número de Casos por Entidad")
    df_entidad = casos_por_entidad()
    st.bar_chart(df_entidad.set_index('ENTIDAD'))

# Gráfico 2: Distribución de Enfermedades (Top 10)
with col2:
    st.subheader("Distribución de Enfermedades (Top 10)")
    df_enfermedades = top_enfermedades()
    st.bar_chart(df_enfermedades.set_index('ENFERMEDAD')['TOTAL_CASOS'])

col3, col4 = st.columns(2)

# Gráfico 3: Evolución Temporal de los Casos
with col3:
    st.subheader("Evolución Temporal de los Casos")
    df_temporal = evolucion_temporal()
    df_temporal['FECHA'] = pd.to_datetime(df_temporal['ANIO'].astype(str) + '-' + df_temporal['MES'].astype(str))
    st.line_chart(df_temporal.set_index('FECHA')['TOTAL_CASOS'])

# Gráfico 4: Casos por Unidad de Salud (Top 5)
with col4:
    st.subheader("Casos por Unidad de Salud (Top 5)")
    df_unidad = casos_por_unidad()
    st.bar_chart(df_unidad.set_index('NOMBRE_CLUES'))

col5, col6 = st.columns(2)

# Gráfico 5: Porcentaje de Casos por Entidad
with col5:
    st.subheader("Porcentaje de Casos por Entidad")
    st.pyplot(df_entidad.set_index('ENTIDAD').plot.pie(y='TOTAL_CASOS', autopct='%1.1f%%', figsize=(6, 6)).figure)

# Gráfico 6: Comparativa de Enfermedades (Top 10)
with col6:
    st.subheader("Comparativa de Enfermedades (Top 10)")
    st.line_chart(df_enfermedades.set_index('ENFERMEDAD')['TOTAL_CASOS'])
