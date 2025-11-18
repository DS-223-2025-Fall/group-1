import streamlit as st
from components.filters import render_filters

def render_sidebar():
    st.sidebar.title('Filters')
    render_filters()
    st.sidebar.markdown('---')
    st.sidebar.radio('Pages', ['Home','Historical Data','Forecasting','Settings'], key='nav')
