FROM python:3.11-slim

# чтобы логи сразу писались, а не буферились
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# код
COPY . .

CMD ["python", "main.py"]
