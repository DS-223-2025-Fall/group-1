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
