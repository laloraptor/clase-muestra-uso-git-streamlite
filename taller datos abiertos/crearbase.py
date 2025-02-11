import mysql.connector
from mysql.connector import errorcode

# Datos de conexión a MySQL
config = {
    'host': "127.0.0.1",
    'user': "root",
    'password': "PruebaEstu2012"
}

# Nombre de la base de datos
database_name = "Salud_DB"

# Conectar a MySQL
try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    print("Conexión exitosa a MySQL.")
except mysql.connector.Error as err:
    print(f"Error de conexión: {err}")
    exit()

# Crear la base de datos si no existe
try:
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
    print(f"Base de datos '{database_name}' creada o ya existente.")
except mysql.connector.Error as err:
    print(f"Error al crear la base de datos: {err}")
    exit()

# Conectar a la base de datos creada
conn.database = database_name

# Definición de tablas
tables = {
    "Unidades_Salud": (
        """
        CREATE TABLE IF NOT EXISTS Unidades_Salud (
            CLAVE_ENTIDAD VARCHAR(5),
            ENTIDAD VARCHAR(255),
            CLAVE_MUNICIPIO VARCHAR(5),
            MUNICIPIO VARCHAR(255),
            CLUES VARCHAR(20) PRIMARY KEY,
            NOMBRE_CLUES VARCHAR(255)
        )
        """
    ),
    "Enfermedades": (
        """
        CREATE TABLE IF NOT EXISTS Enfermedades (
            ID_ENFERMEDAD INT PRIMARY KEY,
            CODIGO_ENFERMEDAD VARCHAR(20)
        )
        """
    ),
    "Casos_Enfermedades": (
        """
        CREATE TABLE IF NOT EXISTS Casos_Enfermedades (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            CLUES VARCHAR(20),
            ID_ENFERMEDAD INT,
            MES INT,
            ANIO INT,
            CONTEO INT,
            FOREIGN KEY (CLUES) REFERENCES Unidades_Salud(CLUES),
            FOREIGN KEY (ID_ENFERMEDAD) REFERENCES Enfermedades(ID_ENFERMEDAD)
        )
        """
    )
}

# Crear tablas en la base de datos
for table_name, ddl in tables.items():
    try:
        cursor.execute(ddl)
        print(f"Tabla '{table_name}' creada o ya existente.")
    except mysql.connector.Error as err:
        print(f"Error al crear la tabla '{table_name}': {err}")

# Cerrar la conexión
cursor.close()
conn.close()
print("\nBase de datos y tablas creadas exitosamente.")
