FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt

ENV PYTHONUNBUFFERED=1
ENV WORKROBOT_DB_PATH=/data/workrobot.db
CMD ["python3", "run.py"]
