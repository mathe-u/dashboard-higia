import streamlit as st
import pandas as pd
from connection import create_connection

@st.cache_data(ttl=25.0)
def load_data(query: str, params: dict = {}) -> pd.DataFrame:
    try:
        with create_connection().connect() as connection:
            print("Conectando ao banco de dados")
            if params:
                print("Executando consulta com parâmetros")
                return pd.read_sql(query, con=connection, params=params)
            else:
                return pd.read_sql(query, con=connection)
    except Exception as e:
        st.error(f"Erro ao executar a consulta: {e}")
        return pd.DataFrame()
