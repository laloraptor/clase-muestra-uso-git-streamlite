from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import numpy as np
import os


# Cargar el modelo entrenado cambiar ubicacion por la suya propia
with open(r"C:\Users\edupe\OneDrive\Documentos\GitHub\clase muestra uso git streamlite\Modelos\clasificación\Logit prueba API\logit_model_result.pkl", 'rb') as file:
    model = pickle.load(file)

# Crear la aplicación FastAPI
app = FastAPI(title="Predicciones SNI", description="API para predecir la probabilidad de ingresar al Sistema Nacional de Investigadores (SNI)")

# Modelo para los datos de entrada
class SNIInput(BaseModel):
    anios_desde_doctorado: float
    numero_publicaciones: int
    indice_h_promedio: float
    anios_docente: float
    ha_ganado_premios: int
    horas_clase_semana: float

# Endpoint para predicciones
@app.post("/predict", tags=["Predicción"])
def predict_sni(data: SNIInput):
    """
    Calcula la probabilidad de ingresar al SNI basado en los datos de entrada.
    """
    try:
        # Crear el array de entrada para el modelo
        input_data = np.array([1,  # Intercepto
                               data.anios_desde_doctorado,
                               data.numero_publicaciones,
                               data.indice_h_promedio,
                               data.anios_docente,
                               data.ha_ganado_premios,
                               data.horas_clase_semana])

        # Generar la predicción
        prob = model.predict([input_data])[0]
        prob_percentage = round(prob * 100, 2)

        return {"probability": prob_percentage, 
                "message": f"La probabilidad de ingresar al SNI es del {prob_percentage}%."}
    except Exception as e:
        return {"error": str(e)}

# Endpoint de bienvenida
@app.get("/", tags=["Bienvenida"])
def home():
    """
    Bienvenida a la API de Predicción SNI.
    """
    return {
        "message": "Bienvenido a la API de Predicción SNI. Envía datos al endpoint /predict para obtener predicciones.",
        "documentation": "/docs",
    }

# Ejecutar la aplicación
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


# al ingresar ir a /docs para ver la interfaz de prueba
