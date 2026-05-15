FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install uvicorn

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 7860

ENTRYPOINT []
CMD ["/bin/bash", "entrypoint.sh"]
