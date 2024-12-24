FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libx11-xcb1 \
    libxcb-xinerama0 \
    libfontconfig1 \
    libxrender1

COPY ./src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TRAFFIC_RECORD_DIR=/app/TrafficRecord

CMD ["python", "main.py"]
