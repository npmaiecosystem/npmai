FROM ollama/ollama:latest

USER root
RUN apt-get update && apt-get install -y python3 python3-pip netcat-openbsd && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 7860

ENTRYPOINT []
CMD ["/bin/bash", "entrypoint.sh"]
