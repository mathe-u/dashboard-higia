# import psycopg2
# from psycopg2 import sql, OperationalError
import os
from dotenv import load_dotenv
import streamlit as st
from sqlalchemy import create_engine, Engine

load_dotenv()

@st.cache_resource
def create_connection() -> (Engine | None):
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados.: {e}")
        return None

# def create_connection1():
#     try:
#         conn = psycopg2.connect(
#             dbname=os.getenv('DB_NAME'),
#             user=os.getenv('DB_USER'),
#             password=os.getenv('DB_PASSWORD'),
#             host=os.getenv('DB_HOST'),
#             port=os.getenv('DB_PORT'),
#         )
#         return conn
#     except OperationalError as e:
#         print(f"Erro ao conectar ao banco de dados.: {e}")
#         #st.stop()
