FROM node:8.9.1-alpine

# Global dependencies
RUN apk add --update git && rm -rf /var/cache/apk/*

# App dependencies
WORKDIR /app
COPY package.json ./
RUN npm --allow-root install

# Build assets
COPY . ./

# Default runtime configs and helpers
EXPOSE 8080
CMD sync; /app/docker/start.sh
