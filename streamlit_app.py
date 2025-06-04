import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Set page configuration
st.set_page_config(page_title="Result Viewer", layout="wide")

# Load the main DataFrames from Parquet using caching
@st.cache_data
def load_main_data():
    df_main = pd.read_parquet("/home/aditya/all_devices_12h_wtd/final_r_f.parquet")
    df_graph_data = pd.read_parquet("/home/aditya/all_devices_12h_wtd/df_for_allgraphs.parquet")
    return df_main, df_graph_data

df_main, df_graph_data = load_main_data()

# Convert date columns in df_main
df_main['next_heat_date'] = pd.to_datetime(df_main['next_heat_date'], errors='coerce')
df_main['next_heat_date_2'] = pd.to_datetime(df_main['next_heat_date_2'], errors='coerce')
df_graph_data['next_heat_date'] = pd.to_datetime(df_graph_data['next_heat_date'], errors='coerce')
df_graph_data['next_heat_date_2'] = pd.to_datetime(df_graph_data['next_heat_date_2'], errors='coerce')
df_graph_data['next_heat_date'] = df_graph_data['next_heat_date'].dt.tz_localize(None)
df_graph_data['next_heat_date_2'] = df_graph_data['next_heat_date_2'].dt.tz_localize(None)

# ---- App Title ----
st.title("📊 Heat Score Viewer")

# ---- Cluster Filter for Table ----
if 'cluster' in df_main.columns and df_main['cluster'].notna().any():
    st.subheader("🔍 Filter by Cluster")
    unique_clusters = sorted(df_main['cluster'].dropna().unique())
    selected_clusters = st.multiselect("Select Cluster(s)", unique_clusters, default=unique_clusters)
    df_main = df_main[df_main['cluster'].isin(selected_clusters)]
else:
    st.warning("No 'cluster' data available to filter.")

# ---- Show Table ----
st.markdown("### 📋 Filtered Table")
st.dataframe(df_main, use_container_width=True)

# ---- Device Selection ----
st.subheader("📈 DeviceID-wise Graph")
device_ids = df_graph_data['deviceid'].unique()
selected_deviceid = st.selectbox("Select a Device ID", device_ids)

# ---- Load Per-Device Data ----
@st.cache_data
def load_device_data(device_id):
    return pd.read_parquet(f"/home/aditya/device_data/{device_id}.parquet")

filtered_graph_data = load_device_data(selected_deviceid)

# Ensure datetime format
filtered_graph_data['cdate_hr'] = pd.to_datetime(filtered_graph_data['cdate_hr'], errors='coerce')
filtered_graph_data['cdate_hr'] = filtered_graph_data['cdate_hr'].dt.tz_localize(None)

# ✅ Use magnified score for visualization
filtered_graph_data['window_heat_score'] = filtered_graph_data['magnified_score'].combine_first(filtered_graph_data['window_heat_score'])

# ---- Plot 1: Plotly Line Plot ----
st.markdown("### 🔥12Hr_ Heat Score Over Time with Next Heat Dates")

if not filtered_graph_data.empty:
    fig1 = px.line(
        filtered_graph_data,
        x='cdate_hr',
        y='window_heat_score',
        title=f"DeviceID {selected_deviceid} - Value Over Time",
        labels={'cdate_hr': 'Timestamp', 'window_heat_score': 'Window Heat Score'}
    )

    # Add vertical lines for heat dates
    selected_row = df_graph_data[df_graph_data['deviceid'] == selected_deviceid]
    if not selected_row.empty:
        heat_dates = selected_row[['next_heat_date', 'next_heat_date_2']].iloc[0]
        for col, color in zip(['next_heat_date', 'next_heat_date_2'], ['green', 'purple']):
            date_val = heat_dates[col]
            if pd.notnull(date_val):
                fig1.add_vline(x=date_val, line_dash='dash', line_color=color)
                fig1.add_annotation(
                    x=date_val,
                    y=filtered_graph_data['window_heat_score'].max(),
                    text=col,
                    showarrow=False,
                    yanchor='bottom',
                    font=dict(color=color)
                )

    # ✅ Add cutoff line
    if 'cutoff' in filtered_graph_data.columns and not filtered_graph_data['cutoff'].isna().all():
        cutoff_val = filtered_graph_data['cutoff'].dropna().iloc[0]
        fig1.add_hline(y=cutoff_val, line_dash='dash', line_color='red',
                       annotation_text="Cutoff", annotation_position="top right")

    # ✅ Highlight magnified peaks
    if 'peak_magnified' in filtered_graph_data.columns:
        magnified_peaks = filtered_graph_data[filtered_graph_data['peak_magnified'] == True]
        fig1.add_scatter(
            x=magnified_peaks['cdate_hr'],
            y=magnified_peaks['window_heat_score'],
            mode='markers',
            marker=dict(color='orange', size=8),
            name='Magnified Peak'
        )

    st.plotly_chart(fig1, use_container_width=True)
else:
    st.warning(f"No graph data found for DeviceID: {selected_deviceid}")

# ---- Feedback Section ----
# st.subheader("✅ Team Feedback on Prediction")

# feedback_option = st.radio("Is the predicted heat date accurate?", ["Yes", "No"], index=0, horizontal=True)
# user_comment = st.text_input("Add optional comment (e.g. observed signs, cycle confirmation):")

# if st.button("Submit Feedback"):
#     feedback_entry = {
#         "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#         "deviceid": selected_deviceid,
#         "is_correct": feedback_option,
#         "comment": user_comment
#     }

#     feedback_file = "/home/aditya/all_devices_12h_wtd/feedback_log.csv"
#     file_exists = os.path.exists(feedback_file)

#     df_feedback = pd.DataFrame([feedback_entry])

#     if file_exists:
#         df_feedback.to_csv(feedback_file, mode='a', header=False, index=False)
#     else:
#         df_feedback.to_csv(feedback_file, index=False)

#     st.success("✅ Feedback saved locally in feedback_log.csv.")
