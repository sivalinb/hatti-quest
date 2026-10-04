FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home --uid 10001 hatti
COPY hatti hatti
COPY static static
COPY templates templates
COPY run.py .
USER hatti
EXPOSE 8765
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8765"]
