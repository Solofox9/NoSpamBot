FROM python:25.1.1 -> 25.2
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "nospam_bot.py"]
