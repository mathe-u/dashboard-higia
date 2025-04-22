import streamlit as st
#import pandas as pd
import plotly.express as px
from connection import create_connection
from get_data import load_data


st.set_page_config(page_title='Dashboard de Medicos', layout='wide')
st.title('Medicos')


def get_selected_checkboxes():
    return [i.replace('check_modality_', '') for i in st.session_state.keys() if i.startswith('check_modality_') and st.session_state[i]]

def cb(data):
    for element in data:
        st.checkbox(element, key='check_modality_' + element)

selected_modality = get_selected_checkboxes()

if 'modality' not in st.session_state:
    st.session_state['modality'] = "SELECT DISTINCT cs_modality FROM report_examtype"

if selected_modality:
    selected_list = " ,".join("'"+m+"'" for m in selected_modality)
    st.session_state['modality'] = selected_list
else:
    st.session_state['modality'] = "SELECT DISTINCT cs_modality FROM report_examtype"


query_cs_modality = "SELECT cs_modality FROM report_examtype GROUP BY cs_modality;"

query_count_radiologistdoctor = f"""
SELECT COUNT(DISTINCT rd.user_id)
FROM report_report rr
JOIN user_radiologistdoctor rd ON rr.radiologist_id = rd.id
JOIN report_exam re ON rr.exam_id = re.id
JOIN report_examtype et ON re.exam_type_id = et.id
WHERE et.cs_modality IN ({st.session_state['modality']});
"""

a = "SELECT COUNT(DISTINCT user_id) FROM user_radiologistdoctor;"
query_count_online = "SELECT COUNT(is_online) FROM user_radiologistdoctor rd WHERE is_online = TRUE;"
query_radio_modalities = "SELECT radio_modalities FROM user_radiologistdoctor;"
query_report_modality = f"""
SELECT
    (rr.closed_date)::date AS date,
    COUNT(rr.liberated_report) AS count
FROM report_report rr
JOIN report_exam re ON rr.exam_id = re.id
JOIN report_examtype et ON re.exam_type_id = et.id
WHERE et.cs_modality IN ({st.session_state['modality']})
    AND rr.liberated_report = TRUE
    AND rr.closed_date IS NOT NULL
    AND rr.closed_date BETWEEN 
    (SELECT MAX(closed_date)::date FROM report_report) - INTERVAL '1 month' AND
    (SELECT MAX(closed_date) FROM report_report)
GROUP BY date ORDER BY date DESC;
"""

query_list_online_doctors = """
SELECT
    rd.id, su.name,
    DATE_PART('year',
    AGE(su.birth_date)) AS age,
    su.gender,
    rd.radio_modalities,
    AGE(last_login) AS active_time
FROM user_radiologistdoctor rd
JOIN user_systemuser su ON rd.user_id = su.id
WHERE rd.is_online = TRUE;
"""




cs_modality = load_data(query_cs_modality)


with st.sidebar:
    st.title('⚙️ Filtros')
    with st.expander('Modalidades'):
        data = cs_modality['cs_modality'].tolist()
        for element in data:
            st.checkbox(element, key='check_modality_' + element)
        # cb(cs_modality['cs_modality'].tolist())



total_doctors = load_data(query_count_radiologistdoctor)
online_doctors = load_data(query_count_online)
radio_modality = load_data(query_radio_modalities)
report_modality = load_data(query_report_modality)

radio_modality['split'] = radio_modality['radio_modalities'].str.split(',')
df_xpld = radio_modality.explode('split')
df_xpld = df_xpld[df_xpld['split'].str.strip() != ""]
m_count = df_xpld['split'].value_counts().reset_index()
m_count.columns = ['modality', 'count']

#df_split.columns = [f"radio_modalities_{i+1}" for i in range(df_split.shape[1])]

list_online = load_data(query_list_online_doctors)

col1, col2, col3 = st.columns(3)
col4, col5 = st.columns(2)
col6 = st.columns(1)[0]


with col1:
    st.metric(label="Medicos", value=total_doctors.iloc[0])

with col2:
    st.metric(label="Online", value=online_doctors.iloc[0])

with col3:
    st.metric(label="Metric", value=999)

with col4:
    fig = px.line(
        report_modality,
        x='date',
        y='count',
        title="Laudos por Dia",
    )
    st.plotly_chart(fig)

with col5:
    fig = px.pie(
        m_count,
        names='modality',
        values='count',
        title="Distribuição por Especialista",
        hole=0.5,
    )
    st.plotly_chart(fig)

with col6:
    st.markdown("##### Medicos online")
    st.table(list_online)
    
