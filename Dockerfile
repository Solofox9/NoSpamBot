FROM python:latest
RUN mkdir -p /usr/src/nospambot
WORKDIR /usr/src/nospambot
COPY package.json ./
RUN npm install
RUN package.json
COPY . .

CMD ["node", "index.js"]
