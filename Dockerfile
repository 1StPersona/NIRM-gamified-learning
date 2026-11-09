FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY gamification gamification
COPY services services
EXPOSE 8000
CMD ["uvicorn", "services.gamification_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
