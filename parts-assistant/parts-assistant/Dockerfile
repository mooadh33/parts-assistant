FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pandas
COPY . .
RUN python -m app.db && python -m app.ingest
EXPOSE 8000 8501
