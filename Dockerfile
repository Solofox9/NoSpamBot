FROM python:3.10-slim
WORKDIR /app
COPY package.json .
COPY package-lock.json .
RUN apt-get update && apt-get install -y git curl ffmpeg python3-pip wget bash && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY . .
CMD ["main.py"]
