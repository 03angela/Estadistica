from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import os
import io
from starlette.responses import StreamingResponse
import httpx

app = FastAPI()

# Buffers para los gráficos
scatter_buffer = io.BytesIO()
box_buffer = io.BytesIO()

# Ruta para procesar los datos obtenidos desde la API y mostrar el análisis estadístico
@app.get("/analisis", response_class=HTMLResponse)
async def realizar_analisis():
    # Hacer una solicitud a la API de Make
    async with httpx.AsyncClient() as client:
        response = await client.get("https://hook.us2.make.com/5c3ptf8lnr0ykhmj5hhyvvovmm5r7p4g")
        data = response.json()

    # Transformar los datos recibidos para extraer las horas de sueño y calificaciones
    horas_sueno = []
    calificaciones = []

    for item in data:
        # Convertir las horas de sueño a formato numérico
        horas_sueno_raw = item["1"]
        if horas_sueno_raw == "Menos de 4 horas":
            horas_sueno.append(3.5)
        elif horas_sueno_raw == "4-5 horas":
            horas_sueno.append(4.5)
        elif horas_sueno_raw == "5-6 horas":
            horas_sueno.append(5.5)
        elif horas_sueno_raw == "6-7 horas":
            horas_sueno.append(6.5)
        elif horas_sueno_raw == "Más de 7 horas":
            horas_sueno.append(7.5)

        # Convertir las calificaciones a formato numérico
        calificaciones_raw = item["2"]
        if calificaciones_raw == "60-70":
            calificaciones.append(65)
        elif calificaciones_raw == "70-80":
            calificaciones.append(75)
        elif calificaciones_raw == "Más de 80":
            calificaciones.append(85)

    # Convertir listas a arrays de numpy
    horas_sueno = np.array(horas_sueno)
    calificaciones = np.array(calificaciones)

    # Calcular media, mediana y desviación estándar
    media_sueno = np.mean(horas_sueno)
    media_calif = np.mean(calificaciones)
    mediana_sueno = np.median(horas_sueno)
    mediana_calif = np.median(calificaciones)
    std_sueno = np.std(horas_sueno)
    std_calif = np.std(calificaciones)

    # Análisis de correlación
    correlacion, p_value = stats.pearsonr(horas_sueno, calificaciones)

    # Prueba de hipótesis
    t_stat, p_val = stats.ttest_ind(calificaciones[horas_sueno > 7], calificaciones[horas_sueno <= 7])

    # Generar gráficos
    # Gráfico de dispersión
    plt.figure(figsize=(6, 4))
    sns.scatterplot(x=horas_sueno, y=calificaciones)
    plt.title("Relación entre horas de sueño y calificaciones")
    plt.xlabel("Horas de sueño")
    plt.ylabel("Calificaciones")
    plt.tight_layout()
    scatter_buffer.seek(0)
    plt.savefig(scatter_buffer, format="png")
    scatter_buffer.seek(0)

    # Diagrama de caja
    plt.figure(figsize=(6, 4))
    sns.boxplot(x=horas_sueno > 7, y=calificaciones)
    plt.title("Calificaciones según horas de sueño (>7 horas)")
    plt.xlabel("¿Duerme más de 7 horas?")
    plt.ylabel("Calificaciones")
    plt.tight_layout()
    box_buffer.seek(0)
    plt.savefig(box_buffer, format="png")
    box_buffer.seek(0)

    # Renderizar el HTML con Bootstrap
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Análisis de Sueño y Rendimiento Académico</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container">
            <h1 class="text-center my-5">Análisis de Sueño y Rendimiento Académico</h1>
            
            <div class="card my-4">
                <div class="card-body">
                    <div class=row>
                    <h4 class="card-title">Resultados Estadísticos</h4>
                    <a href="http://localhost:8000/analisis">Refrescar Datos</a>
                    </div>
                    
                    <p><strong>Media de horas de sueño:</strong> {media_sueno:.2f}</p>
                    <p><strong>Media de calificaciones:</strong> {media_calif:.2f}</p>
                    <p><strong>Mediana de horas de sueño:</strong> {mediana_sueno:.2f}</p>
                    <p><strong>Mediana de calificaciones:</strong> {mediana_calif:.2f}</p>
                    <p><strong>Desviación estándar de horas de sueño:</strong> {std_sueno:.2f}</p>
                    <p><strong>Desviación estándar de calificaciones:</strong> {std_calif:.2f}</p>
                    <p><strong>Coeficiente de correlación:</strong> {correlacion:.2f}</p>
                    <p><strong>P-value de la correlación:</strong> {p_value:.5f}</p>
                    <p><strong>Resultado prueba T (estudiantes que duermen más de 7 horas):</strong> {t_stat:.2f}</p>
                    <p><strong>P-value prueba T:</strong> {p_val:.5f}</p>
                </div>
            </div>
            
            <h4>Gráficos</h4>
            <div class="row">
                <div class="col-md-6">
                    <img src="/scatter_plot" class="img-fluid" alt="Gráfico de dispersión">
                </div>
                <div class="col-md-6">
                    <img src="/box_plot" class="img-fluid" alt="Diagrama de caja">
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Rutas para servir las imágenes de los gráficos
@app.get("/scatter_plot")
async def get_scatter_plot():
    scatter_buffer.seek(0)
    return StreamingResponse(scatter_buffer, media_type="image/png")

@app.get("/box_plot")
async def get_box_plot():
    box_buffer.seek(0)
    return StreamingResponse(box_buffer, media_type="image/png")
