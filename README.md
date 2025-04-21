# Usa una imagen oficial de Python
FROM python:3.10-slim

# Crea y entra en un directorio de trabajo
WORKDIR /app

# Copia los archivos necesarios
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expón el puerto usado por Uvicorn
EXPOSE 8080

# Comando para ejecutar la app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]