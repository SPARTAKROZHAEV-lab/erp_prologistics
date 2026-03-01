FROM python:3.11-slim

# Устанавливаем системные зависимости для WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libgirepository-1.0-1 \
    gir1.2-glib-2.0 \
    gir1.2-pango-1.0 \
    gir1.2-gdkpixbuf-2.0 \
    gir1.2-rsvg-2.0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Указываем команду запуска
CMD ["flask", "run", "--host=0.0.0.0"]