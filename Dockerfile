FROM python:3.12-alpine
LABEL authors="tholzheim"

COPY . .

COPY pyproject.toml .

RUN python -m pip install --upgrade pip

RUN pip install .
EXPOSE 8000

CMD ["python", "src/ceur_graph/main.py"]