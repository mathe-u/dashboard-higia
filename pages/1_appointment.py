import streamlit as st
#import pandas as pd
from connection import create_connection
from get_data import load_data
from render import status_colors, render_table

st.set_page_config(page_title='Dashboard de Medicos', layout='wide')
st.title('Agendamento')

query_count_radiologistdoctor = "SELECT COUNT(DISTINCT user_id) FROM user_radiologistdoctor;"
query_list_appointment = """
SELECT 
    su.name AS doctor,
    up.name AS patient,
    (re.study_time)::date AS date,
    et.description,
    re.status
FROM report_exam re
JOIN report_examtype et ON re.exam_type_id = et.id
JOIN user_systemuser su ON et.user_id = su.id
JOIN user_patient up ON re.patient_id = up.id
WHERE re.study_time BETWEEN
    (SELECT MAX(study_time)::date FROM report_exam) - INTERVAL '6 day' AND
    (SELECT MAX(study_time) FROM report_exam)
ORDER BY date DESC;
"""


#total_doctors = load_data(query_count_radiologistdoctor, engine)
list_appointment = load_data(query_list_appointment)
list_appointment['color'] = list_appointment['status'].map(status_colors)



col1, col2, col3, col4 = st.columns(4)
col5 = st.columns(1)[0]


with col1:
    st.metric(label="Metric", value=999)

with col2:
    st.metric(label="Metric", value=999)

with col3:
    st.metric(label="Metric", value=999)

with col4:
    st.metric(label="Metric", value=999)

with col5:
    st.write("Agendamentos")
    st.caption("Todos os agendamentos desta semana")
    table = render_table(list_appointment)
    st.markdown(table, unsafe_allow_html=True)

