import streamlit as st
from components.sidebar import render_sidebar

st.set_page_config(page_title='Pricing UI', layout='wide')

def main():
    render_sidebar()
    st.title('Pricing Optimization — UI Skeleton (Final)')
    st.write('Front page placeholder. Select pages from sidebar.')
    st.button('Apply Filters (placeholder)')

if __name__ == '__main__':
    main()
