FROM python:3.10

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Requerimiento de Hugging Face: Usar un usuario no-root (ID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copiar todo el código a la imagen (respetando .gitignore si usamos Git)
COPY --chown=user . $HOME/app

# Ejecutar el bot
CMD ["python", "main.py"]
