import streamlit as st
from streamlit_local_storage import LocalStorage
from streamlit_calendar_semver import calendar
from streamlit_extras.chart_container import chart_container
import pandas as pd
from db import create_connection
import plotly.express as px
import plotly.graph_objects as go
from streamlit_extras.metric_cards import style_metric_cards


conn = create_connection()
slocal = LocalStorage()

st.set_page_config(page_title="ITI Learning System",
                   page_icon="https://rb.gy/lgq5oy",
                   layout="wide"
                   )

inst_id = slocal.getItem("inst_id")["storage"]["value"]
s = style_metric_cards()

courses = pd.read_sql(f"""SELECT CRS_NAME AS "Course Name", CRS_DURATION AS "Course Duration", TOPIC_NAME As "Topic Name" 
                        FROM COURSE AS C INNER JOIN INSTRUCTOR AS I 
                        ON C.Ins_ID = I.Ins_ID 
                        INNER JOIN TOPIC AS T
                        ON C.TOPIC_ID = T.TOPIC_ID
                        WHERE I.Ins_ID = {inst_id}""", conn)

df_attendance = pd.read_sql(f"""SELECT DISTINCT S.STD_ID AS "Student ID", STD_NAME AS "Student Name", CRS_NAME AS "Course Name", CRS_DURATION AS "Course Duration", TOPIC_NAME As "Topic Name", Attend_Status AS "Attendance Status"
                    FROM COURSE AS C INNER JOIN TOPIC AS T
                    ON C.TOPIC_ID = T.TOPIC_ID
                    INNER JOIN INSTRUCTOR AS I
                    ON I.INS_ID = C.INS_ID
                    INNER JOIN Std_CrsAttend AS CA
                    ON CA.CRS_ID = C.CRS_ID
                    INNER JOIN STUDENT AS S
                    ON S.STD_ID = CA.STD_ID
                    WHERE I.INS_ID = {inst_id}""", conn)

df_grades = pd.DataFrame(data=None)
for stud_id in df_attendance["Student ID"]:
    grades = pd.read_sql(f"""GetStudentGrade {stud_id}""", conn, parse_dates=["Ex_Date"])\
        [["Std_Name", "Crs_Name", "Ex_Date", "Ex_Duration", "Ex_Grade", "Grade"]].\
        rename(columns={"Std_Name": "Student Name", "Crs_Name": "Course Name", "Ex_Date": "Exam Date", "Grade": "Exam Score", "Ex_Grade": "Exam Maximum Grade"})
    for _, grade in grades.iterrows():
        grade = grade.to_frame().T
        courses_list = grade["Course Name"].tolist()
        for course in courses_list:
            if course in courses["Course Name"].tolist():
                df_grades = pd.concat([df_grades, grade])

st.title("Dashboard")

with st.container():
    summary1, summary2, summary3 = st.columns(3)
    with summary1:
        with st.container():
            st.metric("Total Days", f"""{courses["Course Duration"].sum()} Days""")
    with summary2:
        with st.container():
            st.metric("Total Courses", f"""{courses["Course Name"].count()} Courses""")
    with summary3:
        with st.container():
            st.metric("Total Students", f"""{df_attendance["Student Name"].unique().__len__()} Student""")

for course in courses["Course Name"].tolist():
    with st.container():
        grades = df_grades[df_grades["Course Name"] == course].groupby(by="Student Name")["Exam Score"].mean().sort_values().reset_index()
        if len(grades):
            avg_score = grades["Exam Score"].mean()
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.bar(grades, x="Exam Score", y="Student Name", orientation="h", title=f"Final Scores in {course}"), theme=None, use_container_width=True)
            with col2:
                st.plotly_chart(go.Figure(go.Pie(labels=["Your Grade", "Maximum Grade"], values=[avg_score, 100-avg_score])).\
                    update_layout(showlegend=False, title=f"Average {course} Score",
                                    annotations = [{"text": f"""{round(avg_score, 2)}%""", "showarrow": False, "font": {
                                    "size": 25}}]).\
                    update_traces(hole=0.7, marker=dict(colors=["#636efa", "#F0F2F6"]), textinfo="none"), theme=None, use_container_width=True)

options = {
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "timeGridDay,timeGridWeek,dayGridMonth",
    }
}
events = []

df_exams = pd.read_sql(f"""SELECT DISTINCT E.EX_DATE AS "Exam Date", C.CRS_NAME AS "Course Name", E.EX_DURATION AS "Exam Duration"
                            FROM dbo.Exam AS E INNER JOIN DBO.COURSE AS C 
                            ON E.CRS_ID = C.CRS_ID
                            WHERE C.CRS_ID IN 
                            (SELECT CRS_ID FROM COURSE WHERE INS_ID = {inst_id})""", conn, parse_dates=["Exam Date"])

for index, exam in df_exams.drop_duplicates().iterrows():
    start_date = pd.Timestamp(exam.loc["Exam Date"])
    end_date = start_date + pd.DateOffset(minutes=exam.loc["Exam Duration"])
    events.append(
        {"title": f"""{exam.loc["Course Name"]} exam""",
         "start": start_date.isoformat(),
         "end": end_date.isoformat(),
         "resourceId": index
         })

calendar(events=events, options=options)

with st.expander("Courses Details"):
    st.table(courses)

with st.expander("Attendance Details"):
    choose_course = st.selectbox("Choose a course", ["Select"] + courses["Course Name"].tolist(), key=1)
    if choose_course == "Select":
        st.table(df_attendance)
    else:
        st.table(df_attendance[df_attendance["Course Name"] == choose_course])

with st.expander("Grades Details"):
    choose_course2 = st.selectbox("Choose a course", ["Select"] + courses["Course Name"].tolist(), key=2)
    if choose_course2 == "Select":
        st.table(df_grades)
    else:
        filtered_grades = df_grades[df_grades["Course Name"] == choose_course2]
        if len(filtered_grades):
            st.table(filtered_grades)
        else:
            st.error("No grades for this course.")

st.markdown("""<style>
                    [data-testid="stMarkdownContainer"] p{
                        font-size: 25px;
                    }
                    [data-testid="stHorizontalBlock"] {
                        gap: 0.5rem;
                    }
                    [data-testid="stSidebarNavItems"] li:nth-child(1), [data-testid="stSidebarNavSeparator"], [data-testid="StyledFullScreenButton"], footer {
                        display: none;
                    }
                    body .st-emotion-cache-1ihl2qk e1f1d6gn3 {
                        width: 100%;
                    }
                </style>""", unsafe_allow_html=True)