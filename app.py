import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time as timer
from streamlit_extras.stylable_container import stylable_container
from streamlit_autorefresh import st_autorefresh
from get_data import load_data
from utlis import colors, colors_pie_graph, time_interval, status_options


st.set_page_config(layout="wide", page_title="Dashboard de Exames")
pd.set_option('future.no_silent_downcasting', True)

TIMEOUT = 30000

count_timer = st_autorefresh(interval=TIMEOUT, limit=None, key="fizzbuzzcounter")

if "date_type_range" not in st.session_state:
    st.session_state["date_type_range"] = True

if "date_type_interval" not in st.session_state:
    st.session_state["date_type_interval"] = False

if "start_time" not in st.session_state:
    st.session_state["start_time"] = timer.time()


query_modality = "SELECT cs_modality FROM report_examtype WHERE cs_modality NOT LIKE 'SR' GROUP BY cs_modality;"
query_hospital_unit = "SELECT name, city, state FROM hospital_hospitalunit;"
query_status = "SELECT status FROM report_exam GROUP BY status;"
query_min_max_date = "SELECT MIN(entry_date) AS min_date, MAX(entry_date) AS max_date FROM report_exam;"

query_percent_sla = """
    WITH TotalSLA AS (
        SELECT COUNT(*) AS total
        FROM report_report
    ),
    TotalOnSLA AS (
        SELECT COUNT(rr.is_on_sla) AS total
        FROM report_report rr JOIN report_exam re ON rr.exam_id = re.id
        WHERE rr.is_on_sla = TRUE AND re.status LIKE 'CD'
    )
    SELECT
        CASE
            WHEN (SELECT total FROM TotalSLA) > 0
            THEN (CAST((SELECT total FROM TotalOnSLA) AS DECIMAL) / (SELECT total FROM TotalSLA)) * 100
            ELSE 0
        END AS pct_on_sla;
"""
query_percent_cancel = """
    WITH total AS (
        SELECT COUNT(*) AS te
        FROM report_exam
    ),
    cancel AS (
        SELECT COUNT(*) AS tc
        FROM report_exam
        WHERE status LIKE 'CL'
    )
    SELECT
        CASE
            WHEN (SELECT te FROM total) > 0
            THEN (CAST((SELECT tc FROM cancel) AS DECIMAL) / (SELECT te FROM total)) * 100
            ELSE 0
        END AS cancel_pct;
"""

df_modality = load_data(query_modality)
df_hospital_unit = load_data(query_hospital_unit)
df_status_options = load_data(query_status)
df_min_max_date = load_data(query_min_max_date)
df_sla_pct = load_data(query_percent_sla)
df_cancel_pct = load_data(query_percent_cancel)

def on_change_unit():
    pass

def on_change_date_range():
    st.session_state["date_type_range"] = True
    st.session_state["date_type_interval"] = False
    print(f"range: {st.session_state['date_type_range']}, interval: {st.session_state['date_type_interval']}")

def on_change_date_interval():
    st.session_state["date_type_range"] = False
    st.session_state["date_type_interval"] = True
    print(f"range: {st.session_state['date_type_range']}, interval: {st.session_state['date_type_interval']}")

col0, col1, col2, col3, col4 = st.columns([2, 1, .6, 0.5, 0.5])

with col0:
    st.title("Exames")

with col1:
    selected_unit = st.selectbox(
        "Unidade",
        options=["Todas as Unidades"] + sorted(df_hospital_unit["name"].unique().tolist()),
        on_change=on_change_unit,
        )
    if selected_unit == "Todas as Unidades":
        selected_unit = "%"
    else:
        selected_unit = f"%{selected_unit}%"

with col2:
    date_range = st.segmented_control(
        label="Dias",
        options=time_interval.keys(),
        default="D30",
        on_change=on_change_date_range,
    )

    date_range = "D*" if date_range is None else date_range # se o valor for None, atribui "D*"
    
# with col99:
    # st.button(label=":material/filter_alt:")

with col3:
    date_interval_start = st.date_input(
        "Inicio",
        value=None,
        format="DD/MM/YYYY",
        on_change=on_change_date_interval,
        min_value=df_min_max_date["min_date"].iloc[0],
        max_value=df_min_max_date["max_date"].iloc[0],
    )

with col4:
    date_interval_end = st.date_input(
        "Termino",
        disabled=False if date_interval_start else True,
        format="DD/MM/YYYY",
        on_change=on_change_date_interval,
        min_value=df_min_max_date["min_date"].iloc[0],
        max_value=df_min_max_date["max_date"].iloc[0],
    )

def config_query(type, status: tuple = (), modality=None):
    if status:
        status = ",".join([f"'{s}'" for s in status])
    
    if type == "total":
        return (
            "et.cs_modality AS modality, COUNT(et.cs_modality) AS count",
            f"re.status IN ({status})",
            'cs_modality',
        )
    if type == "foreach":
        return (
            "re.status, COUNT(re.status)",
            f"et.cs_modality LIKE %(modality)s",
            "re.status",
        )

def query_modality_per_status(type, time, status: tuple = ()):
    if type == "total":
        return f"""
            SELECT et.cs_modality AS modality, COUNT(et.cs_modality) AS count
            FROM report_exam re
            JOIN report_examtype et ON re.exam_type_id = et.id
            JOIN hospital_hospitalunit hu ON re.hospital_id = hu.id
            WHERE re.status IN ({status})
            AND entry_date {time}
            AND hu.name LIKE %(hospital_unit)s
            GROUP BY cs_modality;
        """
    if type == "foreach":
        return f"""
            SELECT re.status, COUNT(re.status)
            FROM report_exam re
            JOIN report_examtype et ON re.exam_type_id = et.id
            JOIN hospital_hospitalunit hu ON re.hospital_id = hu.id
            WHERE et.cs_modality LIKE %(modality)s
            AND entry_date {time}
            AND hu.name LIKE %(hospital_unit)s
            GROUP BY re.status;
        """


def selected_status():
    selec_status = []
    for status in status_sel:
        selec_status.append(status_options[status])
    return tuple(selec_status)


def time_interval_or_range(start=None, end=None, range=None):
    if st.session_state["date_type_interval"]:
        return f"BETWEEN '{start}' AND '{end}'"
    else:
        if range == 0:
            return f"""
                BETWEEN (SELECT MIN(entry_date) FROM report_exam) AND (SELECT MAX(entry_date) FROM report_exam)
                """
        else:
            return f"""
                BETWEEN (SELECT MAX(entry_date) FROM report_exam) - INTERVAL '{range}' DAY
                AND (SELECT MAX(entry_date) FROM report_exam)
                """

st.markdown("""
<style>
    /* Cor do background das opções selecionadas */
    span[data-baseweb="tag"] {
        background-color: #FF702B !important;
    }
</style>
""",
unsafe_allow_html=True
)

status_sel = st.multiselect("Status", options=status_options, default=status_options)

if status_sel:
    df_modality.sort_values(by='cs_modality', inplace=True)
    time = time_interval_or_range(start=date_interval_start, end=date_interval_end, range=time_interval[date_range])
    
    total_columns, total_condition, total_group_by = config_query(type="total", status=selected_status())
    foreach_columns, foreach_condition, foreach_group_by = config_query(type="foreach", modality="%(modality)s")

    query_total_modality_per_status = f"""
    SELECT {total_columns}
    FROM report_exam re
    JOIN report_examtype et ON re.exam_type_id = et.id
    JOIN hospital_hospitalunit hu ON re.hospital_id = hu.id
    WHERE {total_condition}
    AND entry_date {time}
    AND hu.name LIKE %(hospital_unit)s
    GROUP BY {total_group_by};
    """

    query_foreach_modality_per_status = f"""
    SELECT {foreach_columns}
    FROM report_exam re
    JOIN report_examtype et ON re.exam_type_id = et.id
    JOIN hospital_hospitalunit hu ON re.hospital_id = hu.id
    WHERE {foreach_condition}
    AND entry_date {time}
    AND hu.name LIKE %(hospital_unit)s
    GROUP BY {foreach_group_by};
    """

    

    
    

    # query_total_modality_per_status = """
    # SELECT et.cs_modality AS modality, COUNT(et.cs_modality)
    # FROM report_exam re
    # JOIN report_examtype et ON re.exam_type_id = et.id
    # WHERE re.status IN %(status)s AND re.status NOT IN ('XX')
    # GROUP BY et.cs_modality;
    # """

    # query_foreach_modality_per_status = f"""
    # SELECT re.status, COUNT(re.status)
    # FROM report_exam re
    # JOIN report_examtype et ON re.exam_type_id = et.id
    # JOIN hospital_hospitalunit hu ON re.hospital_id = hu.id
    # WHERE et.cs_modality LIKE %(modality)s
    # AND entry_date {time_interval_or_range(start=date_interval_start, end=date_interval_end)}
    # AND hu.name LIKE %(hospital_unit)s
    # GROUP BY re.status;
    # """

    # query_foreach_modality_per_status = f"""
    # SELECT %(columns)s
    # FROM report_exam re
    # JOIN report_examtype et ON re.exam_type_id = et.id
    # JOIN hospital_hospitalunit hu ON re.hospital_id = hu.id
    # WHERE %(condition)s
    # AND entry_date {time_interval_or_range(start=date_interval_start, end=date_interval_end)}
    # AND hu.name LIKE %(hospital_unit)s
    # GROUP BY %(group_by)s;
    # """

    # st.write(selected_unit)

    
    cancel_pct = f"{df_cancel_pct["cancel_pct"].iloc[0]:.2f} %"
    sla_pct = f"{df_sla_pct["pct_on_sla"].iloc[0]:.2f} %"

    delta_sla_percent = 0
    delta_cancel_percent = 0

    total_params = {
        "hospital_unit": selected_unit,
    }
    modality_per_status = load_data(query_total_modality_per_status, params=total_params)
    modality_per_status.sort_values(by="count", ascending=True, inplace=True)

#     order = ["F. GERAL", "DIGITAÇÃO", "F. DIGITADOR", "F. MEDICA", "CONCLUIDO", "CANCELADO"]     

    modalities = []
    
    for modality in df_modality["cs_modality"]:
        foreach_params = {
            "modality": f"%{modality}%",
            "hospital_unit": selected_unit,
        }
        df_modality_per_status_base = load_data(query_foreach_modality_per_status, params=foreach_params)
        df_all_status = pd.DataFrame(list(status_options.values()), columns=["status"])
        df_modality_per_status_base = df_all_status.merge(df_modality_per_status_base, on="status", how="left")
        df_modality_per_status_base["count"] = df_modality_per_status_base["count"].fillna(0).infer_objects(copy=False)
        df_modality_per_status_base["count"] = df_modality_per_status_base["count"].astype(int)
        modalities.append(df_modality_per_status_base)

    col5, col6, col7, col8 = st.columns([2, 1, 1, 1])

    with col5:
        fig = go.Figure(
            data=[go.Bar(
                x=modality_per_status["count"],
                y=modality_per_status["modality"],
                text=modality_per_status["count"],
                textposition="auto",
                orientation="h",
                marker=dict(
                    color=colors,
                ),
                width=[0.7] * len(modality_per_status),
            ),    
            ],
            layout=dict(
                barcornerradius=15,
                title="Totais",
            ),
        )
        fig.update_layout(
            xaxis=dict(showticklabels=False),
            height=200,
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=False)

    with col6:
        st.metric(label="SLA%", value=sla_pct, delta=f"{delta_sla_percent} %", border=True)

    with col7:
        st.metric(label="Cancelamentos", value=cancel_pct, delta=f"{delta_cancel_percent} %", delta_color="inverse", border=True)

    with col8:
        st.metric(label="R$", value=0, delta=1, border=True)

    
        
    i = 0

    for col in st.columns(len(df_modality), ):
        with col:
            st.html(
                f"""
                 <body style="display: flex; justify-content: center; align-items: center; gap: 40px; height: 100vh; background-color: #fff;">
                     <div style="width: 60px; height: 60px; border: 1px solid #ccc; border-radius: 12px; display: flex; justify-content: center; align-items: center; font-family: Arial, sans-serif; font-size: 20px; font-weight: bold;" class="item">{df_modality['cs_modality'].iloc[i]}</div>
                 </body>
                 """,
            )
            i += 1
        
    i = 0

    columns = zip(st.columns(len(df_modality)), st.columns(len(df_modality)))

    for col_bar, col_pie in columns:
        with col_bar:
            df_modality_per_status = modalities[i]
            df_modality_per_status.sort_values(by="count", inplace=True)

            fig = go.Figure(
                    data=[go.Bar(
                        x=df_modality_per_status["count"],
                        y=df_modality_per_status["status"],
                        text=df_modality_per_status["count"],
                        textposition="auto",
                        orientation="h",
                        marker=dict(
                            color=colors,
                        ),
                        width=[0.6] * len(df_modality_per_status),
                        hovertemplate="<b>%{y}</b>: %{x}<extra></extra>",
                    )],
                    layout=dict(
                        barcornerradius=15,
                    ),
                )
            fig.update_layout(
                    xaxis=dict(showticklabels=False),
                    yaxis=dict(showticklabels=True),
                    height=200,
                    margin=dict(t=0, b=0, r=0, l=0),
                )
            st.plotly_chart(
                    fig,
                    key=f"fig_{i}",
                    use_container_width=True,
                    config=dict(
                        displayModeBar=False,
                    ),
                )
        with col_pie:
            df_modality_per_status = modalities[i]
            conclud = df_modality_per_status[df_modality_per_status["status"] == "CD"]["count"]
            total = df_modality_per_status["count"].sum()
            if conclud.any():
                conclud = conclud.iloc[0]
            else:
                conclud = 0
            if total == 0:
                total = 1

            pct = conclud / total * 100
            pct = max(0, min(100, pct))

            color_index = min(7, int(pct / 11.1))
            selected_color = colors_pie_graph[color_index]

            fig_donut = go.Figure(
                data=[
                    go.Pie(
                        labels=["Concluído", "Outros"],
                        values=[conclud, total - conclud],
                        hole=.7,
                        textinfo="none",
                        marker_colors=[selected_color, "lightgray"],
                        rotation=0,
                        direction="counterclockwise",
                        sort=False,
                        showlegend=False,
                        hoverinfo="label+percent",
                        textfont=dict(color="black", size=12),
                    )
                ],
            )
            fig_donut.update_layout(
                showlegend=False,
                annotations=[
                    dict(
                        text=f"{pct:.0f}%",
                        x=0.5,
                        y=0.5,
                        font=dict(size=34, color="black", weight="bold"),
                        showarrow=False,
                    ),
                ],
                margin=dict(t=0, b=0, l=10, r=10),
                height=150,
            )
            st.plotly_chart(
                fig_donut,
                use_container_width=True,
                key=f"fig_donut_{i}",
                config=dict(
                    displayModeBar=False,
                ),
            )
        i += 1

else:
    st.warning("Nenhum status selecionado")
