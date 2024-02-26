import streamlit as st
from st_keyup import st_keyup
from db import *
from streamlit.components.v1 import html
from streamlit_local_storage import LocalStorage
import warnings
warnings.filterwarnings("ignore")
import webbrowser

conn = create_connection()
slocal = LocalStorage()

def redirect():
    html("""
        <script>
            console.log("hi")
            window.open("http://localhost:8501/Profile")
            console.log("bye")
        </script>""")


def login_interface():
    if email and password:
        result = login(conn, email, password)
        if result:
            if not isinstance(result, int):
                with status_container:
                    st.error(result)
            else:
                slocal.setItem("inst_id", result)
                redirect()

st.set_page_config(page_title="ITI Learning System",
                   page_icon="https://rb.gy/lgq5oy",
                   )

st.markdown("""<style>
                [data-testid="stSidebar"], [data-testid="baseButton-headerNoPadding"], footer {
                    display: none;
                }
            </style>""", unsafe_allow_html=True)

st.markdown("""<div style="display: flex; justify-content:center;">
                <img src="https://rb.gy/stg21m" width=100/>
            </div>""", unsafe_allow_html=True)

email = st_keyup("Email")
password = st.text_input("Password", type="password")
status_container = st.container()

login_button = st.button("login", use_container_width=True, disabled=False if email and password else True)

if login_button:
    login_interface()

