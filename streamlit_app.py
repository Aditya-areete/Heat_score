import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="Result Viewer", layout="wide")

# Load the main DataFrame for the table
df_main = pd.read_csv("final_r_f.csv")

# Load supporting data
df_graph_data = pd.read_csv('df_for_allgraphs.csv')  # for heat date lines
df_graph = pd.read_csv("res_all_graphs.csv")  # main graph data

# Ensure datetime format
df_graph['cdate_hr'] = pd.to_datetime(df_graph['cdate_hr'], errors='coerce')
df_graph_data['next_heat_date'] = pd.to_datetime(df_graph_data['next_heat_date'], errors='coerce')
df_graph_data['next_heat_date_2'] = pd.to_datetime(df_graph_data['next_heat_date_2'], errors='coerce')

df_graph['cdate_hr'] = df_graph['cdate_hr'].dt.tz_localize(None)
df_graph_data['next_heat_date'] = df_graph_data['next_heat_date'].dt.tz_localize(None)
df_graph_data['next_heat_date_2'] = df_graph_data['next_heat_date_2'].dt.tz_localize(None)

# ✅ Use magnified score for visualization
df_graph['window_heat_score'] = df_graph['magnified_score'].combine_first(df_graph['window_heat_score'])

# Convert date columns in df_main
df_main['next_heat_date'] = pd.to_datetime(df_main['next_heat_date'], errors='coerce')
df_main['next_heat_date_2'] = pd.to_datetime(df_main['next_heat_date_2'], errors='coerce')

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

# ---- Plot 1: Plotly Line Plot ----
st.markdown("### 🔥12Hr_ Heat Score Over Time with Next Heat Dates")
filtered_graph_data = df_graph[df_graph['deviceid'] == selected_deviceid]

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

# ---- Plot 2: Matplotlib Line Plot ----
# st.markdown("### 🔥 Heat Score Over Time with Next Heat Dates")

# device_df = df_graph[df_graph['deviceid'] == selected_deviceid]
# date_row = df_graph_data[df_graph_data['deviceid'] == selected_deviceid]

# if not device_df.empty:
#     device_df = device_df.sort_values('cdate_hr')
#     cutoff_value = device_df['cutoff'].iloc[0] if 'cutoff' in device_df.columns else None

#     fig2, ax = plt.subplots(figsize=(10, 4))
#     ax.plot(device_df['cdate_hr'], device_df['window_heat_score'], linestyle='-', color='blue', label='Window Heat Score')

#     if cutoff_value is not None:
#         ax.axhline(y=cutoff_value, color='red', linestyle='--', linewidth=1.5, label='Cutoff')

#     # Heat date lines
#     if not date_row.empty:
#         nhd = date_row['next_heat_date'].values[0]
#         nhd2 = date_row['next_heat_date_2'].values[0]
#         if pd.notnull(nhd):
#             ax.axvline(x=nhd, color='green', linestyle='--', label='Next Heat Date')
#         if pd.notnull(nhd2):
#             ax.axvline(x=nhd2, color='purple', linestyle='--', label='Next Heat Date 2')

#     # ✅ Highlight magnified peaks
#     if 'peak_magnified' in device_df.columns:
#         peaks = device_df[device_df['peak_magnified'] == True]
#         ax.scatter(peaks['cdate_hr'], peaks['window_heat_score'], color='orange', label='Magnified Peak')

#     ax.set_title(f'Window Heat Score Over Time – Device {selected_deviceid}')
#     ax.set_xlabel('Timestamp (cdate_hr)')
#     ax.set_ylabel('Window Heat Score')
#     ax.grid(True)
#     plt.xticks(rotation=45)

#     handles, labels = ax.get_legend_handles_labels()
#     by_label = dict(zip(labels, handles))
#     ax.legend(by_label.values(), by_label.keys())

#     st.pyplot(fig2)
# else:
#     st.warning(f"No heat score data found for DeviceID: {selected_deviceid}")
