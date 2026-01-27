import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Ebury Revenue Ops Dashboard", layout="wide")

# --- LOAD DATA ---
clients = pd.read_csv('clients.csv', parse_dates=['last_contact_date'])
transactions = pd.read_csv('transactions.csv', parse_dates=['transaction_date'])
cpms = pd.read_csv('cpms.csv')
pipeline = pd.read_csv('pipeline.csv', parse_dates=['last_update'])
kpis = pd.read_csv('kpis.csv', parse_dates=['month'])
calls = pd.read_csv('calls.csv', parse_dates=['call_date'])

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filters")
country_filter = st.sidebar.multiselect("Country", clients['country'].unique())
segment_filter = st.sidebar.multiselect("Segment", clients['segment'].unique())
industry_filter = st.sidebar.multiselect("Industry", clients['industry'].unique())
cpm_filter = st.sidebar.multiselect("CPM", cpms['name'].unique())

# --- APPLY FILTERS ---
filtered_clients = clients.copy()
filtered_transactions = transactions.copy()

if country_filter:
    filtered_clients = filtered_clients[filtered_clients['country'].isin(country_filter)]
    filtered_transactions = filtered_transactions[filtered_transactions['client_id'].isin(filtered_clients['client_id'])]
if segment_filter:
    filtered_clients = filtered_clients[filtered_clients['segment'].isin(segment_filter)]
    filtered_transactions = filtered_transactions[filtered_transactions['client_id'].isin(filtered_clients['client_id'])]
if industry_filter:
    filtered_clients = filtered_clients[filtered_clients['industry'].isin(industry_filter)]
    filtered_transactions = filtered_transactions[filtered_transactions['client_id'].isin(filtered_clients['client_id'])]
if cpm_filter:
    selected_cpms = cpms[cpms['name'].isin(cpm_filter)]['cpm_id']
    filtered_clients = filtered_clients[filtered_clients['portfolio_manager_id'].isin(selected_cpms)]
    filtered_transactions = filtered_transactions[filtered_transactions['cpm_id'].isin(selected_cpms)]

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", 
    "🏆 CPM Performance", 
    "📈 Portfolio / Pipeline", 
    "💸 Transactions / Usage", 
    "📞 Calls / Cross-Sell"
])

# --- 1️⃣ Overview Tab ---
with tab1:
    st.header("📊 Executive Summary")
    
    total_clients = len(filtered_clients)
    total_client_revenue = filtered_clients['revenue'].sum()
    total_tx_revenue = filtered_transactions['revenue'].sum()
    total_booked_volume = filtered_transactions['booked_amount'].sum()
    
    st.metric("Total Clients", total_clients)
    st.metric("Total Client Revenue (€)", f"{total_client_revenue:,.0f}")
    st.metric("Total Transaction Revenue (€)", f"{total_tx_revenue:,.0f}")
    st.metric("Total Booked Volume (€)", f"{total_booked_volume/1e6:,.1f}M")
    
    # Monthly booked volume trend
    monthly_tx = filtered_transactions.groupby(filtered_transactions['transaction_date'].dt.to_period('M')).sum(numeric_only=True)
    monthly_tx.index = monthly_tx.index.to_timestamp()
    fig = px.line(monthly_tx, x=monthly_tx.index, y='booked_amount', title="Monthly Booked Volume")
    st.plotly_chart(fig, use_container_width=True)

# --- 2️⃣ CPM Performance Tab ---
with tab2:
    st.header("🏆 CPM Performance Overview")
    # Example: CPM leaderboard
    leaderboard = filtered_transactions.groupby('cpm_id').agg(
        total_revenue=('revenue','sum'),
        booked_volume=('booked_amount','sum'),
        num_clients=('client_id','nunique')
    ).reset_index()
    leaderboard = leaderboard.merge(cpms, on='cpm_id')
    st.dataframe(leaderboard.sort_values('total_revenue', ascending=False))

# --- 3️⃣ Portfolio / Pipeline Tab ---
with tab3:
    st.header("📈 Portfolio / Pipeline")
    pipeline_summary = pipeline.merge(filtered_clients[['client_id']], on='client_id')
    stage_counts = pipeline_summary['opportunity_stage'].value_counts().reset_index()
    stage_counts.columns = ['Stage','Count']
    fig2 = px.bar(stage_counts, x='Stage', y='Count', title="Pipeline Stage Distribution")
    st.plotly_chart(fig2, use_container_width=True)

# --- 4️⃣ Transactions / Usage Tab ---
with tab4:
    st.header("💸 Transactions Overview")
    product_summary = filtered_transactions.groupby('product').agg(
        booked_volume=('booked_amount','sum'),
        revenue=('revenue','sum')
    ).reset_index()
    st.dataframe(product_summary)

# --- 5️⃣ Calls / Cross-Sell Tab ---
with tab5:
    st.header("📞 Calls & Cross-Sell Insights")
    calls_summary = calls.merge(filtered_clients[['client_id']], on='client_id')
    calls_per_product = calls_summary.groupby('product_discussed').size().reset_index(name='num_calls')
    st.bar_chart(calls_per_product.set_index('product_discussed'))
