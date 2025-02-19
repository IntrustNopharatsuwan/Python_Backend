from dateutil.relativedelta import relativedelta
from datetime import datetime as dt
from sqlalchemy import create_engine
import streamlit as st 
import pandas as pd

def FilterSidebar(start_datetime,end_datetime,division_list,report_list,md_list):
    st.sidebar.header('Filter')
    select_start_date = st.sidebar.date_input("**Start Date**", value=start_datetime)
    select_end_date = st.sidebar.date_input('**End date**:', value = end_datetime)
    select_division = st.sidebar.multiselect("**Division**",division_list)
    select_repost = [st.sidebar.selectbox("**Channel Type**",report_list)]
    if "Offline" in select_repost:
        select_repost.remove("Offline")
        off_type = st.sidebar.selectbox("Source Select",['Order Data System','Modern Trade System'])
        st.sidebar.write(off_type)
        select_repost.append(off_type)
        if off_type == 'Modern Trade System':
            select_repost.remove("Modern Trade System")
            off_report = st.sidebar.multiselect("**MD Channel**",md_list,default=md_list)
            if len(off_report) > 0:
                select_repost.extend(off_report)
    return select_repost, select_start_date, select_end_date, select_division
def transform_data(raw_data):
    def weighted_mode(group):
        weighted_freq = group.groupby(['unit_price']).apply(lambda x: (x['qty'] * 1).sum())
        return weighted_freq.idxmax()

    mode_price = raw_data.groupby(["channel", "mat_no"]).apply(weighted_mode).reset_index(name='mode_price')
    normal = raw_data.groupby(["channel","mat_no"]).agg(
        min_price=("unit_price", "min"),
        avg_price=("unit_price", "mean"),
        median_price=("unit_price", "median"),
        max_price=("unit_price", "max")
        ).reset_index()
    result = normal.merge(mode_price,how='left',on=["channel", "mat_no"])
    result[['min_price','avg_price','median_price','max_price','mode_price']] = result[['min_price','avg_price','median_price','max_price','mode_price']].round(2)
    return result
def online_data(select_start_date,select_end_date):
    dwms_conn = create_engine("mysql+pymysql://username:password@hostname/database")
    on_query = """
SELECT 
    WEB_NAME AS channel,
    MAT_NO AS mat_no, 
    PRICE AS unit_price, 
    ORDER_CDATE AS sale_date, 
    QUANTITY AS qty 
FROM order_data 
WHERE (date(ORDER_CDATE) BETWEEN %s AND %s) 
    AND AMOUNT > 0 
    AND ONLINE = 1
"""
    raw_data = pd.read_sql(on_query, dwms_conn, params=(select_start_date,select_end_date))
    data = transform_data(raw_data)
    return data
def offline_data(select_start_date,select_end_date):
    dwms_conn = create_engine("mysql+pymysql://username:password@hostname/database")
    off_query = """
SELECT 
    'Offline' AS channel,
    MAT_NO AS mat_no, 
    PRICE AS unit_price, 
    ORDER_CDATE AS sale_date, 
    QUANTITY AS qty 
FROM order_data 
WHERE (date(ORDER_CDATE) BETWEEN %s AND %s) 
    AND AMOUNT > 0 
    AND ONLINE = 0
"""
    raw_data = pd.read_sql(off_query, dwms_conn, params=(select_start_date, select_end_date))
    data = transform_data(raw_data)
    data['channel'] = 'Offline'
    return data
def moderntrade_data(select_start_date,select_end_date):
    md_conn = create_engine("mysql+pymysql://username:password@hostname/database")
    so_query = f"""
SELECT 
    'Sell-Out' AS channel,
    mat_no AS mat_no, 
    unit_price AS unit_price, 
    sale_date AS sale_date, 
    qty AS qty
FROM md_sell_out 
WHERE (sale_date BETWEEN '{select_start_date}' AND '{select_end_date}') 
    AND unit_price > 0"""
    raw_data = pd.read_sql(so_query,md_conn)
    data = transform_data(raw_data)
    data['channel'] = 'Sell-Out'
    return data
def mtts_data(select_start_date,select_end_date):
    md_conn = create_engine("mysql+pymysql://username:password@hostname/database")
    so_query = f"""
SELECT
    'Mattress' AS channel,
    mat_no, 
    unit_price, 
    order_cdate AS sale_date, 
    qty 
FROM mtts_order 
WHERE (date(order_cdate) BETWEEN '{select_start_date}' AND '{select_end_date}') 
    AND unit_price > 0
"""
    raw_data = pd.read_sql(so_query,md_conn)
    data = transform_data(raw_data)
    data['channel'] = 'Mattress'
    return data
def stf_data(select_start_date,select_end_date):
    md_conn = create_engine("mysql+pymysql://username:password@hostname/database")
    so_query = f"""
SELECT 
    'Stroefront' AS channel,
    bill_mat_no AS mat_no, 
    bill_unit_price AS unit_price, 
    bill_date AS sale_date, 
    bill_qty AS qty
FROM stf_order 
WHERE (bill_date BETWEEN '{select_start_date}' AND '{select_end_date}') 
    AND bill_unit_price > 0"""
    raw_data = pd.read_sql(so_query,md_conn)
    data = transform_data(raw_data)
    return data

st.set_page_config(
        page_title="Price Structure Report",
        layout="wide"
    )

start_datetime = (dt.today() - relativedelta(months=1)).strftime("%Y-%m-%d")
end_datetime = dt.today().strftime("%Y-%m-%d")
report_list = ["Online","Offline"]
md_list = ["Sell-Out","Mattress","Stroefront"]
pm_conn = create_engine("mysql+pymysql://username:password@hostname/database")
division_df = pd.read_sql("SELECT DIVISION_NAME FROM division",pm_conn)
division_list = division_df['DIVISION_NAME'].unique().tolist()

st.header('Price Structure Report')
select_repost, select_start_date, select_end_date, select_division = FilterSidebar(start_datetime,end_datetime,division_list,report_list,md_list)
file_date = select_start_date.strftime("%Y%m%d")+"_"+select_end_date.strftime("%Y%m%d")

if len(select_division) == 0:
    select_division = division_list
    division_str = 'All'
else:
    division_str = ','.join(select_division)
st.write(f"**report**: :green[{','.join(select_repost)}] **division**: :green[{division_str}] **start date**: :green[{select_start_date}] **end date**: :green[{select_end_date}]")

if len(select_repost) > 0:
    data = pd.DataFrame()
    if "Online" in select_repost:
        online = online_data(select_start_date, select_end_date)
        data = pd.concat([data,online],ignore_index=True)
    if "Order Data System" in select_repost:
        offline = offline_data(select_start_date, select_end_date)
        data = pd.concat([data,offline],ignore_index=True)
    if "Sell-Out" in select_repost:
        so = moderntrade_data(select_start_date, select_end_date)
        data = pd.concat([data,so],ignore_index=True)
    if "Mattress" in select_repost:
        mtts = mtts_data(select_start_date, select_end_date)
        data = pd.concat([data,mtts],ignore_index=True)
    if "Stroefront" in select_repost:
        stf = stf_data(select_start_date, select_end_date)
        data = pd.concat([data,stf],ignore_index=True)

    pm_query = """
SELECT SKU_ID AS mat_no,
    DIVISION_NAME AS division,
    SHORTNAME AS mat_desc
FROM product_master
"""
    pm_df = pd.read_sql(pm_query,pm_conn)
    data = data.merge(pm_df,how='left',on='mat_no')
    data = data[data['division'].apply(lambda div: div in select_division)]
    data = data[['channel','division','mat_no','mat_desc','min_price','max_price','avg_price','median_price','mode_price']]

    st.write(data)
    report = "_".join(select_repost)
    file_name=f'{report}_{file_date}.csv'
    st.download_button(
        label=f":red[Download] {file_name}",
        data=data .to_csv(),
        file_name=file_name,
        mime='text/csv',
    )
