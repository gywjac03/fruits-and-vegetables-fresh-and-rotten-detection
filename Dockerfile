FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# Upgrade pip and build tools
RUN pip install --upgrade pip setuptools wheel

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "./main.py"]