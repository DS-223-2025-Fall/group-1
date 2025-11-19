import streamlit as st

def render_filters():
    categories=['All','Coffee','Bakery','Food','Drinks','Dessert']
    items={
        'All':['All items'],
        'Coffee':['Americano','Latte','Cappuccino','Espresso'],
        'Bakery':['Croissant','Bagel','Muffin'],
        'Food':['Sandwich','Salad'],
        'Drinks':['Lemonade','Soda'],
        'Dessert':['Cake','Ice Cream']
    }
    cat=st.sidebar.selectbox('Menu category',categories)
    st.sidebar.selectbox('Menu item',items.get(cat,['All items']))
    st.sidebar.text_input('Location','Yerevan')
    st.sidebar.slider('Radius (km)',1,50,10)
    st.sidebar.multiselect('Age groups',['0-17','18-24','35-44','55+'])
    st.sidebar.multiselect('Cafe type',['restaurant','coffee_house','bar_bistro','bakery_cafe','coffee_chain','cafe'])
    st.sidebar.multiselect('Methods',['Historical data','Forecasting'], default=['Historical data'])
