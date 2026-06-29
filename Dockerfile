FROM python:3.9-slim

# تثبيت متصفح كروم الرسمي والاعتماديات الأساسية داخل السيرفر مجاناً
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

CMD ["python", "bot.py"]
