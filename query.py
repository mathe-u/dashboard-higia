QUERY_CS_MODALITY = "SELECT DISTINCT cs_modality FROM report_examtype"

def a(state):
    return f"""
        SELECT COUNT(DISTINCT rd.user_id)
        FROM report_report rr
        JOIN user_radiologistdoctor rd ON rr.radiologist_id = rd.id
        JOIN report_exam re ON rr.exam_id = re.id
        JOIN report_examtype et ON re.exam_type_id = et.id
        WHERE et.cs_modality IN ({state});
        """

query_count_radiologistdoctor = "SELECT COUNT(DISTINCT user_id) FROM user_radiologistdoctor;"
query_count_online = "SELECT COUNT(is_online) FROM user_radiologistdoctor rd WHERE is_online = TRUE;"
query_radio_modalities = "SELECT radio_modalities FROM user_radiologistdoctor;"
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

query_cs_modality = "SELECT cs_modality FROM report_examtype GROUP BY cs_modality;"

