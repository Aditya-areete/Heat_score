import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# Set page configuration
st.set_page_config(page_title="Result Viewer", layout="wide")

# Load the main DataFrame
df_main = pd.read_csv("/home/aditya/Heat_final/final_r_f.csv")

# Load the graph data
df_graph = pd.read_csv("/home/aditya/Heat_final/res.csv")

# Ensure timestamp columns are datetime
df_graph['cdate_hr'] = pd.to_datetime(df_graph['cdate_hr'], errors='coerce')

# Fill missing window_heat_score with heat_score
df_graph['window_heat_score'] = df_graph['window_heat_score'].combine_first(df_graph['heat_score'])

# Convert next_heat_date columns in df_main to datetime
df_main['next_heat_date'] = pd.to_datetime(df_main['next_heat_date'], errors='coerce')
df_main['next_heat_date_2'] = pd.to_datetime(df_main['next_heat_date_2'], errors='coerce')

# App title
st.title("📊 Heat Score")

# Display the main DataFrame
#st.subheader("Main Data")
st.dataframe(df_main, use_container_width=True)

# DeviceID selection
st.subheader("📈 DeviceID-wise Graph")
device_ids = df_main['deviceid'].unique()
selected_deviceid = st.selectbox("Select a Device ID", device_ids)

# ---- Plot 1: Line Plot from res.csv ----
st.markdown("### 📉 Value Over Time")
filtered_graph_data = df_graph[df_graph['deviceid'] == selected_deviceid]

if not filtered_graph_data.empty:
    fig1 = px.line(
        filtered_graph_data,
        x='cdate_hr',
        y='window_heat_score',
        title=f"DeviceID {selected_deviceid} - Value Over Time",
        labels={'cdate_hr': 'Timestamp', 'window_heat_score': 'Window Heat Score'}
    )

    # Add vertical lines for next_heat_date and next_heat_date_2
    selected_row = df_main[df_main['deviceid'] == selected_deviceid]
    if not selected_row.empty:
        heat_dates = selected_row[['next_heat_date', 'next_heat_date_2']].iloc[0]
        for col, color in zip(['next_heat_date', 'next_heat_date_2'], ['green', 'purple']):
            date_val = heat_dates[col]
            if pd.notnull(date_val):
                fig1.add_vline(
                    x=date_val,
                    line_dash='dash',
                    line_color=color
                )

    st.plotly_chart(fig1, use_container_width=True)
else:
    st.warning(f"No data found in res.csv for DeviceID: {selected_deviceid}")

# ---- Plot 2: Heat Score Plot with next_heat_date lines (Matplotlib) ----
st.markdown("### 🔥 Heat Score Over Time with Next Heat Dates (res.csv & final_r_f.csv)")

device_df = df_graph[df_graph['deviceid'] == selected_deviceid]
device_main_df = df_main[df_main['deviceid'] == selected_deviceid]

if not device_df.empty:
    device_df = device_df.sort_values('cdate_hr')
    cutoff_value = device_df['cutoff'].iloc[0]

    fig2, ax = plt.subplots(figsize=(10, 4))
    ax.plot(device_df['cdate_hr'], device_df['window_heat_score'], linestyle='-', color='blue', label='Window Heat Score')
    ax.axhline(y=cutoff_value, color='red', linestyle='--', linewidth=1.5, label='Cutoff')

    # Plot vertical lines for next_heat_date and next_heat_date_2
    for _, row in device_main_df.iterrows():
        nhd = row['next_heat_date']
        nhd2 = row['next_heat_date_2']
        if pd.notnull(nhd):
            ax.axvline(x=nhd, color='green', linestyle='--', label='Next Heat Date')
        if pd.notnull(nhd2):
            ax.axvline(x=nhd2, color='purple', linestyle='--', label='Next Heat Date 2')

    ax.set_title(f'Window Heat Score Over Time – Device {selected_deviceid}')
    ax.set_xlabel('Timestamp (cdate_hr)')
    ax.set_ylabel('Window Heat Score')
    ax.grid(True)
    plt.xticks(rotation=45)

    # Remove duplicate labels in legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())

    st.pyplot(fig2)
else:
    st.warning(f"No heat score data found for DeviceID: {selected_deviceid}")
