FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt

ENV WORKROBOT_DB_PATH /data/workrobot.db
CMD ["python3", "-u", "run.py"]
