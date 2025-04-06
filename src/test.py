import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

with st.sidebar:
    pdf_viewer("Report.pdf", width=800, height=600)
