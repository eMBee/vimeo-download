FROM python:2.7-slim-stretch
RUN apt update && apt install -y libffi-dev build-essential libssl1.0-dev ffmpeg
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN apt remove -y libffi-dev build-essential libssl1.0-dev
COPY . .
ENTRYPOINT ["python","vimeo-download.py"]