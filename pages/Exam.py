import streamlit as st
import pandas as pd
from db import create_connection
from streamlit_local_storage import LocalStorage
from streamlit_quill import st_quill
from datetime import datetime
from streamlit_modal import Modal
from time import sleep

conn = create_connection()
slocal = LocalStorage()

cursor = conn.cursor()

st.set_page_config(page_title="ITI Learning System",
                   page_icon="https://rb.gy/lgq5oy",
                   layout="wide"
                   )

inst_id = slocal.getItem("inst_id")["storage"]["value"]

courses = pd.read_sql(f"""SELECT CRS_NAME AS "Course Name" FROM COURSE WHERE INS_ID={inst_id}""", conn)
course = st.selectbox("Course", ["Select"] + courses["Course Name"].tolist())
exam_date = st.date_input("Date", format="YYYY-MM-DD")
exam_time = st.time_input("Time")
exam_tot_grade = st.text_input("Total Grade", value=100)
exam_duration = st.text_input("Duration (in minutes)")
no_of_questions = st.text_input("Number of Questions")
# add_exam = st.button("Add an exam", use_container_width=True)

if no_of_questions:
    exam_id = pd.read_sql(
        f"""SELECT EX_NO FROM EXAM WHERE EX_DATE='{exam_date} {exam_time}' AND EX_DURATION={exam_duration} AND EX_GRADE={exam_tot_grade} AND CRS_ID=(SELECT CRS_ID FROM COURSE WHERE CRS_NAME='{course}')""",
        conn)
    if course == "Select" or not exam_duration or not no_of_questions:
        if course == "Select":
            st.error("Please select a course")
        if not exam_duration:
            st.error("Please set the exam duration")
        if not no_of_questions:
            st.error("Please enter the number of questions")

    else:
        if not len(exam_id):
            cursor1 = conn.cursor()
            cursor1.execute(f"""EXEC AddExam @Date='{exam_date} {exam_time}',@Duration={exam_duration},@Grade={exam_tot_grade}, @Crs_name={course}""")
            cursor1.commit()
            st.success("Exam is added successfully")

        else:
            st.error("Exam already exists")

        acc = 0
        for i in range(1, int(no_of_questions)+1):
            with st.expander(f"Question {i}"):
                    st.write("Question")
                    acc += 1
                    ques_text = st_quill(html=True, key=acc)
                    acc += 1
                    ques_type = st.selectbox("Question type", ["True / False", "MCQ"], key=acc)
                    acc += 1
                    if ques_type == "MCQ":
                        choice1_mcq = st.text_input("Choice 1", key=acc)
                        acc += 1
                        choice2_mcq = st.text_input("Choice 2", key=acc)
                        acc += 1
                        choice3_mcq = st.text_input("Choice 3", key=acc)
                        acc += 1
                        choice4_mcq = st.text_input("Choice 4", key=acc)
                        acc += 1
                        correct_ans = st.radio("Correct answer", range(1, 5), key=acc)
                        acc += 1
                        choices = pd.DataFrame({"choices": [choice1_mcq, choice2_mcq, choice3_mcq, choice4_mcq]})
                        choices.index = range(1, 5)
                        choices["is correct"] = [1 if i == correct_ans else 0 for i in range(1, 5)]
                    else:
                        correct_ans = st.radio("Correct answer", ["True", "False"], key=acc)
                        acc += 1
                        choices = pd.DataFrame({"choices": ["TRUE", "FALSE"]})
                        choices["is correct"] = [1 if correct_ans.lower() == i.lower() else 0 for i in choices["choices"]]
                    submit = st.button("Submit", use_container_width=True, key=acc)
                    if submit:
                        q_type = "mcq" if ques_type == "MCQ" else "t/f"
                        cursor2 = conn.cursor()
                        cursor2.execute(f"""EXEC AddQuestion @Q_Text='{ques_text}', @Q_Type='{q_type}', @Q_Mark={int(exam_tot_grade)/int(no_of_questions)}""")
                        cursor2.commit()
                        ques_id = cursor2.execute(f"""SELECT Qus_No FROM QUESTION WHERE Qus_Text='{ques_text}'""").fetchall()[0][0]
                        for _, choice in choices.iterrows():
                            cursor2.execute(f"""EXEC AddChoices @C_Text='{choice.loc["choices"]}', @C_IsCorrect={choice.loc["is correct"]}, @Q_Text='{ques_text}'""")
                            cursor2.commit()
                        cursor2.execute(f"""INSERT INTO Exam_Question VALUES ({exam_id.squeeze()}, {ques_id})""")
                        cursor2.commit()


                        st.success("Question is added")

# if course:
#     try:
#         no_of_questions = len(cursor.execute(f"SELECT QUS_NO FROM Exam_Question WHERE EX_NO = {exam_id}").fetchall())
#     except Exception:
#         st.info("There is no exam for today")
#     else:
#         try:
#             exam_details = pd.read_sql(f"SELECT * FROM EXAM WHERE EX_NO={exam_id}", conn)
#             exam_sec = exam_details["Ex_Duration"].tolist()[0] * 60
#
#             with st.container():
#                 col_exam_name, col_tot_grade, _, _, timer_container = st.columns(5)
#                 with col_exam_name:
#                     st.metric("Exam Name", course)
#
#                 with col_tot_grade:
#                     st.metric("Grade", exam_details["Ex_Grade"].tolist()[0])
#
#                 with timer_container:
#                     col_icon, col_timer = st.columns(2)
#                     with col_timer:
#                         modal = Modal("Timer", "timer")
#                         modal_timer_btn = st.button("Timer")
#
#             st.markdown("""<style>
#                                 [data-testid="stAlert"] {
#                                     display: none;
#                                 }
#                             </style>""", unsafe_allow_html=True)
#
#             for question_no in range(1, no_of_questions+1):
#                 exam = pd.read_sql(f"EXEC GetExCrsQus @Ex_Date='2024-02-24', @Number_Qus={question_no}, @Crs_Name='{course}'", conn)
#                 for question in exam["Qus_Text"].unique().tolist():
#                     answers = exam[exam["Qus_Text"] == question].iloc[:, 1:]
#                     choice = st.radio(question, answers["Choice_Text"], index=None)
#                     if choice != None:
#                         choice_is_correct = answers[answers["Choice_Text"] == choice]["Is_Correct"].values[0]
#                         no_choice = answers[answers["Choice_Text"] == choice]["Number_Choice"].values[0]
#                         if cursor.execute(f"SELECT * FROM Std_ExAnswer WHERE EX_NO={exam_id} AND Qus_No={question_no}").fetchall() != []:
#                             cursor.execute(f"EXEC UpExAnswer @stdID={stud_id}, @exnum={exam_id}, @qusnum={question_no}, @stdAnswer={no_choice}, @stdscore={choice_is_correct}")
#                             cursor.commit()
#                         else:
#                             cursor.execute(f"EXEC AddExAnswer @std_ID={stud_id}, @Ex_No={exam_id}, @Qus_No={question_no}, @Answer={no_choice}, @Score={choice_is_correct}")
#                             cursor.commit()
#
#                     if choice is None or choice_is_correct == 0:
#                         st.error(f"""Wrong answer. The correct answer: {answers[answers["Is_Correct"] == 1]["Choice_Text"].values[0]}""")
#                     else:
#                         st.success("Correct answer")
#
#
#         except KeyError:
#             st.error("There is no exam for this course")
#         else:
#             submit_exam = st.button("Submit your exam", use_container_width=True)
#             if submit_exam:
#                 st.markdown("""<style>
#                                 div[data-testid="element-container"] *,
#                                 div[data-testid="element-container"] *:active
#                                 div[data-testid="element-container"] *:focus:not(:active),
#                                 div[data-testid="element-container"] *:hover{
#                                     pointer-events: none;
#                                     cursor: not-allowed;
#                                 }
#
#                                 button[data-testid="baseButton-secondary"].st-emotion-cache-1umgz6k,
#                                 button[data-testid="baseButton-secondary"].st-emotion-cache-1umgz6k:active,
#                                 button[data-testid="baseButton-secondary"].st-emotion-cache-1umgz6k:focus:not(:active),
#                                 button[data-testid="baseButton-secondary"].st-emotion-cache-1umgz6k:hover {
#                                     border-color: rgba(49, 51, 63, 0.2);
#                                     background-color: transparent;
#                                     color: rgba(49, 51, 63, 0.4);
#                                     cursor: not-allowed;
#                                 }
#
#                                 [data-testid="stAlert"] {
#                                     display: block;
#                                 }
#                             </style>""", unsafe_allow_html=True)


st.markdown("""<style>
                    div[data-testid="stHorizontalBlock"] {
                        height: 75px;
                    }
                    [data-testid="stSidebarNavItems"] li:nth-child(1), [data-testid="stSidebarNavSeparator"], [data-testid="StyledFullScreenButton"], footer {
                        display: none;
                    }
                    body .st-emotion-cache-1ihl2qk e1f1d6gn3 {
                        width: 100%;
                    }
                </style>""", unsafe_allow_html=True)