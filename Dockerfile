FROM python:3.10-slim
WORKDIR /app
COPY package.json .
COPY package-lock.json .
RUN package-lock.json .
COPY ...
CMD ["main.py" "package-lock.json" " package.json"]
