FROM python:3.12-bullseye

RUN pip install poetry==1.6.1

WORKDIR /code

COPY . /code/

RUN poetry install --no-interaction --no-ansi

EXPOSE 8502
CMD poetry run streamlit run app/dashboard/streamlit_app.py --server.address 0.0.0.0 --server.port 8502
