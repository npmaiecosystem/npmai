FROM searxng/searxng:latest

USER root

RUN mkdir -p /etc/searxng

COPY settings.yml /etc/searxng/settings.yml

ENV SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml
ENV SEARXNG_PORT=10000
ENV SEARXNG_BIND_ADDRESS=0.0.0.0
ENV BASE_URL="/"
ENV INSTANCE_NAME="NPMAI Search"

EXPOSE 10000
