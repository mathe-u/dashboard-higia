import streamlit as st
import pandas as pd
import plotly.express as px
from connection import create_connection
from get_data import load_data


st.set_page_config(page_title='Dashboard de Pacientes', layout='wide')
st.title('Pacientes')


def get_min_max(df, filter):
    row = df[df['range'] == filter]
    return (row.iloc[0]['min'], row.iloc[0]['max'])


if 'time_interval' not in st.session_state:
    st.session_state['time_interval'] = 6

if 'age_range' not in st.session_state:
    st.session_state['age_range'] = (
        "(SELECT MIN(DATE_PART('year', AGE(birth_date))) FROM user_patient)",
        "(SELECT MAX(DATE_PART('year', AGE(birth_date))) FROM user_patient)",
    )


time_interval = {
    'name': ['Dia', 'Semana', 'Mês', 'Ano'],
    'time': [1, 7, 30, 365]
}
age_range = {
    'range': ['Criança', 'Adolescente', 'Adulto', 'Idoso'],
    'min': [0, 12, 19, 65],
    'max': [
        11,
        18,
        64,
        "(SELECT MAX(DATE_PART('year', AGE(birth_date))) FROM user_patient)",
    ],
}

df_time_interval = pd.DataFrame(time_interval)
df_age_range = pd.DataFrame(age_range)

st.sidebar.title('Filtros')
selected_time = st.sidebar.selectbox("Intervalo de Tempo", df_time_interval['name'], index=None)
selected_age = st.sidebar.selectbox("Faixa Etária", df_age_range['range'], index=None)

if selected_time:
    st.session_state['time_interval'] = df_time_interval[df_time_interval['name'] == selected_time]['time'].iloc[0]
else:
    st.session_state['time_interval'] = 6

if selected_age:
    st.session_state['age_range'] = get_min_max(df_age_range, selected_age)
else:
    st.session_state['age_range'] = (
        "(SELECT MIN(DATE_PART('year', AGE(birth_date))) FROM user_patient)",
        "(SELECT MAX(DATE_PART('year', AGE(birth_date))) FROM user_patient)",
    )

query_count_total_patients = """
SELECT COUNT(DISTINCT "patientID") AS total FROM user_patient WHERE "patientID" IS NOT NULL;
"""

query_count_ongoing_patients = """
SELECT COUNT(DISTINCT up."patientID") AS ongoing
FROM user_patient up
JOIN report_exam re ON up.id = re.patient_id
WHERE re.status = 'OP';
"""

query_status_patient = f"""
SELECT
    COUNT(DISTINCT up."patientID") AS count,
    re.status,
    DATE(re.study_time) AS study_date
FROM user_patient up
JOIN report_exam re ON up.id = re.patient_id
WHERE up."patientID" IS NOT NULL
    AND re.status IN ('CD', 'OP')
    AND re.study_time BETWEEN
    (SELECT MAX(study_time)::date FROM report_exam) - INTERVAL '{st.session_state['time_interval']} days' AND
    (SELECT MAX(study_time) FROM report_exam)
GROUP BY DATE(re.study_time), re.status;
"""

query_info_patient = f"""
SELECT DISTINCT 
    up."patientID" AS id, 
    up.name, 
    DATE_PART('year', AGE(up.birth_date)) AS age, 
    re.status, 
    re.study_time
FROM user_patient up 
JOIN report_exam re ON up.id = re.patient_id 
WHERE DATE_PART('year', AGE(up.birth_date)) BETWEEN {st.session_state['age_range'][0]} AND {st.session_state['age_range'][1]}
ORDER BY re.study_time DESC 
LIMIT 5;
"""

engine = create_connection()

total_patients = load_data(query_count_total_patients, engine)
ongoing_patients = load_data(query_count_ongoing_patients, engine)
status_patient = load_data(query_status_patient, engine)
info_patient = load_data(query_info_patient, engine)

engine.dispose()

col1, col2, col3, col4 = st.columns(4)
col5 = st.columns(1)[0]
col6 = st.columns(1)[0]

with col1:
    st.metric(label='Pacientes Totais', value=total_patients['total'].iloc[0])

with col2:
    st.metric(label='Pacientes em Andamento', value=ongoing_patients['ongoing'].iloc[0])

with col3:
    st.metric(label='A', value=999)

with col4:
    st.metric(label='B', value=999)

with col5:
    fig = px.bar(
        status_patient,
        x="study_date",
        y="count",
        color="status",
        barmode="group",
        title="Pacientes ao Longo do Tempo"
    )
    st.plotly_chart(fig)

with col6:
    st.dataframe(info_patient, use_container_width=True)

