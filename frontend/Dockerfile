FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Baked into the bundle: browser error reports go to this Sentry project. Empty turns them off.
ARG VITE_SENTRY_DSN=""
ENV VITE_SENTRY_DSN=$VITE_SENTRY_DSN
# Type checking and tests run in CI; the image only needs the bundle.
RUN npx vite build

FROM nginx:1.29-alpine
# Only an HTTPS proxy in front (docker-compose.prod.yml) may report client addresses.
ENV TRUSTED_PROXY=127.0.0.1
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY security-headers.conf api-proxy.conf /etc/nginx/
COPY --from=build /app/dist /usr/share/nginx/html
