import pandas as pd
import streamlit as st
import plotly.express as px
from get_data import load_data

st.set_page_config(layout='wide')
st.header('Higia Report')

query_exam_type = "SELECT description FROM report_examtype GROUP BY description"

query_radiologist = """
SELECT user_systemuser.name
FROM report_report
JOIN user_radiologistdoctor ON report_report.radiologist_id = user_radiologistdoctor.id
JOIN user_systemuser ON user_radiologistdoctor.user_id = user_systemuser.id
GROUP BY user_systemuser.name;
"""

if "exam_type" not in st.session_state:
    st.session_state["exam_type"] = "SELECT description FROM report_examtype GROUP BY description"

if "radiologist" not in st.session_state:
    st.session_state["radiologist"] = """
    SELECT user_systemuser.name
    FROM report_report 
    JOIN user_radiologistdoctor ON report_report.radiologist_id = user_radiologistdoctor.id
    JOIN user_systemuser ON user_radiologistdoctor.user_id = user_systemuser.id
    GROUP BY user_systemuser.name;
    """


data_exam_type = load_data(query_exam_type)
data_radiologist = load_data(query_radiologist)

st.sidebar.title("Filtros")
selected_exam_type = st.sidebar.selectbox('Selecione um tipo de exame', data_exam_type['description'], index=None)
selected_radiologist = st.sidebar.selectbox('Selecione um medico', data_radiologist['name'], index=None)

if selected_exam_type:
    st.session_state["exam_type"] = f"'{selected_exam_type}'"
else:
    st.session_state["exam_type"] = "SELECT description FROM report_examtype GROUP BY description"

if selected_radiologist:
   st.session_state["radiologist"] = selected_radiologist
else:
    st.session_state["radiologist"] = query_radiologist

query = """
SELECT report_report.id, report_report.closed_date, report_exam.study_uid, report_examtype.description AS exam_type, user_systemuser.name AS radiologist_name
FROM report_report
JOIN report_exam ON report_report.exam_id = report_exam.id 
JOIN report_examtype ON report_exam.exam_type_id = report_examtype.id 
JOIN user_radiologistdoctor ON report_report.radiologist_id = user_radiologistdoctor.id 
JOIN user_systemuser ON user_radiologistdoctor.user_id = user_systemuser.id
WHERE closed_date BETWEEN (SELECT MAX(closed_date) FROM report_report) - INTERVAL '1 month'
AND (SELECT MAX(closed_date) FROM report_report);
"""
query_metric_count_report = f"""
SELECT COUNT(report_report.id)
FROM report_report
JOIN report_exam ON report_report.exam_id = report_exam.id
JOIN report_examtype ON report_exam.exam_type_id = report_examtype.id
JOIN user_radiologistdoctor ON report_report.radiologist_id = user_radiologistdoctor.id
JOIN user_systemuser ON user_radiologistdoctor.user_id = user_systemuser.id
WHERE closed_date BETWEEN
    (SELECT MIN(closed_date) FROM report_report) AND
    (SELECT MAX(closed_date) FROM report_report)
AND report_examtype.description IN
    ({st.session_state["exam_type"]});
"""

query_radiologist_report = "SELECT us.name AS radiologist_name, COUNT(*) AS reports FROM report_report rr INNER JOIN user_radiologistdoctor urd ON rr.radiologist_id = urd.user_id INNER JOIN user_systemuser us ON urd.user_id = us.id GROUP BY us.name ORDER BY reports;"
query_report_examtype = "SELECT report_examtype.description AS exam_description, COUNT(report_exam.study_uid) AS reports FROM report_exam INNER JOIN report_examtype ON report_exam.exam_type_id = report_examtype.id GROUP BY report_examtype.id;"

query_report_liberated = """
SELECT COUNT(liberated_report) FROM report_report rr WHERE rr.liberated_report = TRUE;
"""


count_report = load_data(query_metric_count_report)
df = load_data(query)
df['closed_date'] = df['closed_date'].dt.date
start = df['closed_date'].min()
end = df['closed_date'].max()

liberated_report = load_data(query_report_liberated)


def sec_date_range(df_time, col):
    if str(df_time[col].min()) != 'nan':
        return pd.date_range(start=df_time[col].min(), end=df_time[col].max()).date
    return pd.date_range(start=start, end=end)


def fill_days(df_days):
    all_days = sec_date_range(df_days, 'closed_date')
    all_days_df = pd.DataFrame({'closed_date': all_days, 'occurrence': 0})
    report_day_filled = pd.merge(all_days_df, df_days, on='closed_date', how='left')
    report_day_filled['occurrence'] = report_day_filled['occurrence_y'].fillna(0)
    report_day_filled = report_day_filled[['closed_date', 'occurrence']].head(30)
    return report_day_filled

#report_radiologist = pd.read_sql(query_radiologist_report, conn).head()
#report_examtype = pd.read_sql(query_report_examtype, conn).sort_values(by='reports', ascending=False)

#st.sidebar.title("Filtros")
#selected_exam_type = st.sidebar.selectbox('Selecione um tipo de exame', data_exam_type['exam_type'], index=None)
#selected_radiologist = st.sidebar.selectbox('Selecione um medico', df['radiologist_name'].unique(), index=None)

#if selected_radiologist:
#    df = df[df['radiologist_name'] == selected_radiologist]
#    
#if selected_exam_type:
#    df = df[df['exam_type'] == selected_exam_type]

report_day = df[['closed_date', 'id']].groupby('closed_date').count().reset_index()
report_day.rename(columns={'id': 'occurrence'}, inplace=True)
#count_report = df[['id']].count().iloc[0]
count_exam = df['study_uid'].nunique()
count_radiologist = df['radiologist_name'].nunique()
report_radiologist = df.groupby('radiologist_name').count().reset_index().sort_values(by='id')
report_radiologist.rename(columns={'id': 'count'}, inplace=True)
report_examtype = df.groupby('exam_type').count().reset_index().sort_values(by='id')
report_examtype.rename(columns={'id': 'count'}, inplace=True)
report_day_filled = fill_days(report_day)

#st.write(report_examtype)
#st.write(df['study_uid'])

col1, col2, col3, col4 = st.columns(4)
col5, col6 = st.columns(2)
col7 = st.columns(1)[0]

with col1:
    st.metric(label='Consultas', value=count_report.iloc[0])

with col2:
    st.metric(label='Exames', value=count_exam)

with col3:
    st.metric(label='Medicos', value=count_radiologist)

with col4:
    st.metric(label='Liberados', value=liberated_report.iloc[0])

with col5:
    fig = px.bar(
        report_radiologist.tail(),
        x='count',
        y='radiologist_name',
        title='Laudos Por Medico',
        orientation='h',
    )
    st.plotly_chart(fig, use_container_width=True)

with col6:
    fig = px.bar(
        report_examtype.tail(5),
        x='count',
        y='exam_type',
        title='Laudos Por Exame',
        orientation='h',
    )
    st.plotly_chart(fig, use_container_width=True)

with col7:
    fig = px.line(
        report_day_filled,
        x='closed_date',
        y='occurrence',
        title='Laudos Por Dia',
    )
    st.plotly_chart(fig)

