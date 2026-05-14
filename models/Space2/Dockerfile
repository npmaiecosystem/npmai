FROM ollama/ollama:latest

USER root
RUN apt-get update && apt-get install -y python3 python3-pip netcat-openbsd

RUN if id -u 1000 >/dev/null 2>&1; then \
        usermod -l sonu $(id -un 1000); \
        groupmod -n sonu $(id -gn 1000) || true; \
        usermod -d /home/sonu -m sonu; \
    else \
        useradd -m -u 1000 sonu; \
    fi

ENV HOME=/home/sonu \
    PATH=/home/sonu/.local/bin:$PATH
WORKDIR $HOME/app

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

RUN chown -R 1000:1000 $HOME/app && \
    chmod +x entrypoint.sh

RUN mkdir -p $HOME/.ollama && chown -R 1000:1000 $HOME/.ollama
ENV OLLAMA_MODELS=$HOME/.ollama/models

ENV OLLAMA_HOST=127.0.0.1:11434
EXPOSE 7860

USER sonu


ENTRYPOINT []

CMD ["/bin/bash", "entrypoint.sh"]
