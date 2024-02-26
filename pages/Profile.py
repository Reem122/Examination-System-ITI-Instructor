import streamlit as st
from streamlit_local_storage import LocalStorage
import pandas as pd
from db import create_connection
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")
from PIL import Image

conn = create_connection()
slocal = LocalStorage()

st.set_page_config(page_title="ITI Learning System",
                   page_icon="https://rb.gy/lgq5oy",
                   layout="wide"
                   )

inst_id = slocal.getItem("inst_id")["storage"]["value"]

st.markdown("""<style>
                    .st-emotion-cache-1kyxreq.e115fcil2 {
                        justify-content: center;
                    }
                    img {
                        border-radius: 50%; 
                        width:11rem;
                        height: 11rem;
                    }
                    [data-testid="stSidebarNavItems"] li:nth-child(1), [data-testid="stSidebarNavSeparator"], [data-testid="StyledFullScreenButton"], footer {
                        display: none;
                    }
                    body .st-emotion-cache-1ihl2qk e1f1d6gn3 {
                        width: 100%;
                    }
                    [data-testid="stForm"] {
                        border: none;
                    }
                </style>""", unsafe_allow_html=True)

# st.sidebar.image("https://rb.gy/stg21m", width=100)

# st.markdown("""<style>
#                     .st-emotion-cache-1n5xqho eczjsme4 {
#                         order: 0 !important;
#                     }
#                     .st-emotion-cache-79elbk eczjsme10 {
#                         order: 10 !important;
#                     }
#                 </style>""", unsafe_allow_html=True)

df_info = pd.read_sql(F"""SELECT Ins_Name AS "Instructor Name", Ins_Gender AS "Gender", Ins_DOB AS "Date of Birth", Ins_Email AS "Email", Ins_City AS "City", Ins_Salary AS "Salary", DEPT_NAME AS "Department", STRING_AGG(STR(Ins_PhoneNo), ',') AS Phones
                        FROM Instructor AS I INNER JOIN Ins_Phone AS P
                        ON I.Ins_ID = P.Ins_ID
                        INNER JOIN Department AS D
                        ON I.Dept_No = D.Dept_No
                        WHERE I.Ins_ID = {inst_id}
                        GROUP BY Ins_Name, Ins_Gender, Ins_DOB, Ins_Email, Ins_City, Ins_Salary, DEPT_NAME""", conn)

cities = pd.read_sql("SELECT DISTINCT Std_City FROM STUDENT", conn).squeeze().tolist()
genders = ["Male", "Female"]
departments = pd.read_sql("SELECT DEPT_NAME FROM Department", conn).squeeze().tolist()
inst_phones = df_info["Phones"].str.split(",", expand=True)
phones_titles = [f"Phone {phone_num}" for phone_num in range(1, len(inst_phones.columns) + 1)]
df_info[phones_titles] = inst_phones
df_info.drop(columns=["Phones"], inplace=True)
st.title("Information")
status_cont = st.container()
with st.container():
    col_info, col_img = st.columns(2)
    with col_info:
        st.table(df_info.T.squeeze().rename("Information"))
    with col_img:
        img_container = st.container()
        inst_img = st.file_uploader("Upload your image", type=["png", "jpg", "jpeg"])
        with img_container:
            if not inst_img:
                st.image("https://pdtxar.com/wp-content/uploads/2019/04/person-placeholder.jpg")
            else:
                with img_container:
                    st.image(inst_img)

with st.form("Profile"):
    tab1, tab2, tab3, tab4 = st.tabs(["Personal Information", "Contact Information", "Address", "Change Password"])
    with tab1:
        inst_name = st.text_input("Name")
        inst_dob = st.date_input("Date of Birth", df_info["Date of Birth"].tolist()[0])
        inst_dob_str = inst_dob.strftime("%Y-%m-%d")
        inst_gender = st.selectbox("Gender", genders, index=genders.index(df_info["Gender"].tolist()[0]))
        inst_dept = st.selectbox("Department", departments, index=departments.index(df_info["Department"].tolist()[0]))
        inst_salary = st.text_input("Salary")
    with tab2:
        inst_old_phone = st.selectbox("Old Phone Number", inst_phones.T)
        inst_updated_phone = st.text_input("Updated Phone Number")
        st.write("Add Phone Number")
        inst_new_phone = st.text_input("New Phone Number")
        st.write("Delete Phone Number")
        inst_del_phone = st.selectbox("Phone Number", ["Select"] + ([inst_phones.T.squeeze()] if len(inst_phones.T) == 1 else inst_phones.T.squeeze().to_list()))
        inst_email = st.text_input("Email")
    with tab3:
        inst_city = st.selectbox("City", cities, index=cities.index(df_info["City"].tolist()[0]))
        inst_street = st.text_input("Street")
    with tab4:
        inst_password = st.text_input("Password", type="password")
        inst_password_confirm = st.text_input("Confirm Password", type="password")

    inst_submit = st.form_submit_button("Update your information", use_container_width=True)
    if inst_submit:
        cursor1 = conn.cursor()
        if inst_name or inst_dob or inst_email or inst_salary or inst_city or inst_street or inst_dept:
            cursor1.execute(
                f"""EXEC UpInstructor @Ins_ID={inst_id}, @Ins_Name={f"'{inst_name}'" if inst_name else "NULL"} , @Ins_DOB={f"'{inst_dob_str}'"}, 
                @Ins_Gender='{inst_gender}', @Ins_Email={f"'{inst_email}'" if inst_email else "NULL"}, @Ins_Salary={inst_salary if inst_salary else "NULL"},
                @Ins_City='{inst_city}', @Ins_Street={f"'{inst_street}'" if inst_street else "NULL"}, @Dept_Name='{inst_dept}'""")
            cursor1.commit()
        if inst_updated_phone:
            cursor1.execute(f"""EXEC UpInsPhone @Ins_ID={inst_id}, @oldphone='{inst_old_phone}', @Newphone='{inst_updated_phone}'""")
            cursor1.commit()
        if inst_new_phone:
            cursor1.execute(f"""EXEC AddInsPhone @Ins_ID={inst_id}, @Ins_phoneNo='{inst_new_phone}'""")
            cursor1.commit()
        if inst_del_phone != "Select":
            cursor1.execute(f"EXEC DelInsPhone @Ins_phoneNo='{inst_del_phone}'")
            cursor1.commit()
        if inst_password == inst_password_confirm:
            if inst_password != "":
                cursor1.execute(f"EXEC UpInstPass {inst_id},'{inst_password}'")
                cursor1.commit()
        else:
            status_cont.error("Password mismatch")

        status_cont.success("Your profile is updated")