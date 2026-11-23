import streamlit as st
import mysql.connector
import pandas as pd 
import matplotlib.pyplot as plt

section = st.sidebar.selectbox('Section', ['Business Overview', 'Sales Analysis', 'Customer Analysis', 'Seller & Product Analysis', 
                                           'Delivery Analysis', 'Customer Experience', 'Business Insights'])
connection = mysql.connector.connect(host='localhost', port=3306, database='guvi', user='root', password="Abcd@1234")
cursor = connection.cursor()
if section == 'Business Overview':
    cursor.execute('SELECT SUM(price) FROM order_items')
    revenue = cursor.fetchall()[0][0]
    st.write('Total Revenue:', revenue)
    cursor.execute('SELECT COUNT(*) FROM orders')
    orders = cursor.fetchall()[0][0]
    st.write('Total Orders:', orders)
    cursor.execute('SELECT COUNT(DISTINCT customer_id) FROM orders')
    st.write('Total Customers:', cursor.fetchall()[0][0])
    cursor.execute('SELECT COUNT(*) FROM sellers')
    st.write('Total Sellers:', cursor.fetchall()[0][0])
    st.write('Average Order Value:', round(revenue / orders, 2))
    cursor.execute('SELECT SUM(review_score) / COUNT(*) FROM order_reviews')
    st.write('Average Review Score:', round(cursor.fetchall()[0][0], 2))
elif section == 'Sales Analysis':
    tab1, tab2, tab3, tab4 = st.tabs(['Monthly revenue trend', 'Revenue by category', 'Top-selling products', 'Sales by location'])
    cursor.execute('WITH order_value AS (SELECT order_id, SUM(price) AS total_price FROM order_items GROUP BY order_id) ' \
    'SELECT YEAR(o.order_purchase_timestamp) AS year, MONTH(o.order_purchase_timestamp) AS month, SUM(v.total_price) AS Revenue ' \
    'FROM orders as o LEFT JOIN order_value as v ON o.order_id = v.order_id GROUP BY year, month ORDER BY year, month')
    df1 = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
    df1['Revenue'] = df1['Revenue'].astype(float)
    df1['Month'] = pd.to_datetime(df1[['year', 'month']].assign(day=1))
    tab1.line_chart(df1, x='Month', y='Revenue')
    cursor.execute('WITH prod_rev AS (SELECT product_category_name, SUM(price) AS revenue FROM order_items AS o LEFT JOIN products AS p ' \
    'USING(product_id) GROUP BY product_category_name) SELECT * FROM prod_rev AS p LEFT JOIN translations AS t ' \
    'USING(product_category_name) ORDER BY revenue DESC')
    df2 = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
    tab2.write(df2)
    cursor.execute('SELECT product_id, SUM(price) AS revenue FROM order_items AS o LEFT JOIN products AS p USING(product_id)' \
    ' GROUP BY product_id ORDER BY revenue DESC')
    df3 = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
    tab3.write(df3)
    cursor.execute('WITH cust_orders AS (SELECT * FROM customers AS c INNER JOIN orders AS o USING(customer_id)) ' \
    'SELECT c.customer_zip_code_prefix, SUM(o.price) AS total_price FROM cust_orders AS c INNER JOIN order_items AS o ON ' \
    'c.order_id = o.order_id GROUP BY c.customer_zip_code_prefix ORDER BY total_price DESC')
    df4 = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
    tab4.write(df4)
elif section == 'Customer Analysis':
    tab1, tab2, tab3, tab4 = st.tabs(['Customer distribution', 'Customer spending', 'Repeat vs new customers', 'Top customers'])
    cursor.execute('SELECT l.geolocation_lat AS latitude, l.geolocation_lng AS longitude FROM customers AS c INNER JOIN locations as l ' \
    'ON c.customer_zip_code_prefix = l.geolocation_zip_code_prefix')
    df1 = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
    fig, (ax1, ax2) = plt.subplots(2, 1, layout='constrained')
    ax1.hist(df1['latitude'], bins=100)
    ax1.set_title('Latitude')
    ax2.hist(df1['longitude'], bins=100)
    ax2.set_title('Longitude')
    tab1.pyplot(fig)
    cursor.execute('WITH order_value AS (SELECT o.order_id, SUM(i.price) AS total_price, o.customer_id FROM order_items AS i ' \
    'INNER JOIN orders AS o USING(order_id) GROUP BY o.order_id, o.customer_id) SELECT c.customer_unique_id, SUM(o.total_price) ' \
    'AS customer_spend FROM order_value AS o INNER JOIN customers AS c USING(customer_id) GROUP BY c.customer_unique_id ' \
    'ORDER BY customer_spend DESC')
    df2 = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
    fig, ax = plt.subplots()
    ax.hist(df2['customer_spend'], bins=100, range=(0, 2000))
    tab2.pyplot(fig)
    tab4.write(df2)
    cursor.execute('WITH ord_cust AS (SELECT * FROM orders AS o INNER JOIN customers AS c USING(customer_id)) SELECT c.customer_unique_id, ' \
    'SUM(i.price) AS price FROM ord_cust AS c INNER JOIN order_items AS i USING(order_id) GROUP BY order_id, c.customer_unique_id ' \
    'ORDER BY order_purchase_timestamp')
    df3new = []
    df3rep = []
    s = set()
    for i in cursor.fetchall():
        if i[0] in s: df3rep.append(list(i))
        else:
            df3new.append(list(i))
            s.add(i[0])
    df3new = pd.DataFrame(df3new, columns=[col[0] for col in cursor.description])
    df3rep = pd.DataFrame(df3rep, columns=[col[0] for col in cursor.description])
    fig, (ax1, ax2) = plt.subplots(2, 1, layout='constrained')
    ax1.hist(df3new['price'], bins=100, range=[0, 2000])
    ax1.set_title('New customers')
    ax2.hist(df3rep['price'], bins=100, range=[0, 2000])
    ax2.set_title('Repeating customers')
    tab3.write(fig)
    tab3.text(f'Orders from new customers: {len(df3new)}')
    tab3.text(f'Orders from repeating customers: {len(df3rep)}')
elif section == 'Seller & Product Analysis':
    tab1, tab2, tab3, tab4 = st.tabs(['Top sellers', 'Seller revenue', 'Product/category performance', 'Seller ratings'])
    cursor.execute('SELECT seller_id, COUNT(*) AS items_sold, SUM(price) AS total_price FROM order_items ' \
    'GROUP BY seller_id ORDER BY total_price DESC')
    df1 = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
    tab1.write(df1)
    fig, ax = plt.subplots()
    ax.hist(df1['total_price'], bins=100, range=(0, 20000))
    tab2.write(fig)
    cursor.execute('WITH prod_rev AS (WITH prod_items AS (SELECT * FROM products AS p INNER JOIN order_items AS o USING(product_id)) ' \
    'SELECT p.product_category_name, AVG(r.review_score) AS review, COUNT(*) AS count FROM prod_items AS p INNER JOIN order_reviews AS r ' \
    'USING(order_id) GROUP BY p.product_category_name) SELECT * FROM prod_rev AS p LEFT JOIN translations AS t USING(product_category_name)')
    df3 = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
    tab3.write(df3)
    cursor.execute('WITH ord_sell AS (SELECT * FROM order_items AS o INNER JOIN sellers AS s USING(seller_id)) SELECT s.seller_id, ' \
    'AVG(r.review_score) AS review, COUNT(*) AS count FROM ord_sell AS s INNER JOIN order_reviews AS r USING(order_id) GROUP BY s.seller_id')
    df4 = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
    tab4.write(df4)
elif section == 'Delivery Analysis':
    cursor.execute('SELECT AVG(TIME_TO_SEC(TIMEDIFF(order_delivered_customer_date, order_purchase_timestamp))) / 60 / 60 / 24, ' \
    'SUM(order_delivered_customer_date > order_estimated_delivery_date) / COUNT(*) FROM ORDERS')
    result = cursor.fetchall()
    st.write('Average delivery duration in days:', round(result[0][0], 2))
    st.write('% of orders delayed:', round(result[0][1] * 100, 2))
    cursor.execute('WITH ord_cust AS (SELECT TIME_TO_SEC(TIMEDIFF(o.order_delivered_customer_date, o.order_purchase_timestamp)) '
    '/ 60 / 60 / 24 AS duration, o.order_delivered_customer_date > o.order_estimated_delivery_date AS delay, c.customer_zip_code_prefix ' \
    'FROM ORDERS AS o INNER JOIN customers AS c USING(customer_id)) SELECT customer_zip_code_prefix, AVG(duration) AS avg_duration, ' \
    'SUM(delay) / COUNT(*) * 100 AS delay_rate, COUNT(*) AS count FROM ord_cust GROUP BY customer_zip_code_prefix ' \
    'HAVING count >= 20 ORDER BY delay_rate DESC')
    df1 = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
    st.write(df1)
    st.text('Difference between actual delivery date - estimated delivery date vs. review score')
    cursor.execute('SELECT AVG(r.review_score) AS review, (DATEDIFF(o.order_delivered_customer_date, o.order_estimated_delivery_date)) ' \
    'AS days_diff, COUNT(*) AS count FROM order_reviews AS r INNER JOIN orders AS o ON r.order_id = o.order_id GROUP BY days_diff')
    df2 = pd.DataFrame(cursor.fetchall(), columns = [i[0] for i in cursor.description])
    df2 = df2[df2['count'] >= 20]
    df2['review'] = df2['review'].astype(float)
    st.line_chart(df2, x='days_diff', y='review')
elif section == 'Customer Experience':
    cursor.execute('SELECT review_score, COUNT(*) AS count FROM order_reviews GROUP BY review_score')
    df1 = pd.DataFrame(cursor.fetchall(), columns = [i[0] for i in cursor.description])
    st.text('Frequency of each review score')
    st.bar_chart(df1, x='review_score', y='count')
    cursor.execute('WITH ord_rev AS (SELECT r.review_score, (DATEDIFF(o.order_delivered_customer_date, o.order_estimated_delivery_date)) ' \
    'AS days_diff FROM orders AS o INNER JOIN order_reviews AS r USING(order_id)) SELECT review_score, AVG(days_diff) AS avg_diff ' \
    'FROM ord_rev GROUP BY review_score')
    df2 = pd.DataFrame(cursor.fetchall(), columns = [i[0] for i in cursor.description])
    df2['avg_diff'] = df2['avg_diff'].astype(float)
    st.text('Average difference between actual delivery date - estimated delivery date for each review score')
    st.bar_chart(df2, x='review_score', y='avg_diff')
else:
    st.text('The average review score drops sharply between on time delivery and 6 days late, from 4.04 to 1.80. ' \
    'This shows that every day of delay causes the review score to drop about 0.37 points on average during this window. ' \
    'Reducing the percentage of delayed orders by targeting locations with 20%+ delay rate will likely improve customer satisfaction.')
    st.text('The customers are heavily concentrated around a small geographic region between latitude -25 and -23 and longitude -48 and -46. ' \
    'The business could greatly benefit from expanding its services in nearby locations, between latitude -30 and -15 and ' \
    'longitude -55 and -40 where there are a small amount of customers.')
    st.text('The vast majority of customers have spent below 250 while very few have spent above 500. Additionally, more than 95% ' \
    'of customers have only ordered once as only about 3000 orders came from repeating customers out of almost 95000 orders total. ' \
    'The business could increase customer retention and the average spending of customers by providing more offers to existing customers.')