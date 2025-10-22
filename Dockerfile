FROM node:latest
RUN mkdir -p /usr/src/nospambot
WORKDIR /usr/src/nospambot
COPY package.json ./
RUN npm install
COPY . .
CMD ["node", "index.js"]
