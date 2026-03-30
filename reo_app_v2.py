import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Reo Ratio Calculator", layout="wide")
st.title("Wall Reinforcement Ratio: 500N vs SENSE 600")

# --- DATA DICTIONARY ---
bar_pairs = {
    "N12 / S11": {"N_name": "N12", "N_area": 113, "S_name": "S11", "S_area": 94.2},
    "N16 / S15": {"N_name": "N16", "N_area": 201, "S_name": "S15", "S_area": 168.0},
    "N20 / S18": {"N_name": "N20", "N_area": 314, "S_name": "S18", "S_area": 262.0},
    "N24 / S22": {"N_name": "N24", "N_area": 452, "S_name": "S22", "S_area": 377.0},
    "N28 / S26": {"N_name": "N28", "N_area": 616, "S_name": "S26", "S_area": 513.0},
    "N32 / S29": {"N_name": "N32", "N_area": 804, "S_name": "S29", "S_area": 670.0},
    "N36 / S33": {"N_name": "N36", "N_area": 1018, "S_name": "S33", "S_area": 848.0},
    "N40 / S37": {"N_name": "N40", "N_area": 1257, "S_name": "S37", "S_area": 1050.0}
}

thicknesses = list(range(180, 510, 10))
spacings = list(range(100, 400, 50))

# --- HELPER FUNCTIONS ---
def create_ratio_matrix(area, double_layer):
    if double_layer:
        area *= 2
        
    data = []
    for t in thicknesses:
        row = []
        for s in spacings:
            # Calculated as a percentage (%) for easier reading
            ratio = (area / (s * t)) * 100
            row.append(round(ratio, 2))
        data.append(row)
        
    return pd.DataFrame(data, index=thicknesses, columns=spacings)

def plot_heatmap(df, title, min_limit_pct, max_limit_pct):
    # 1. Create a matrix for the colors (Z-values). 
    mask = (df >= min_limit_pct) & (df <= max_limit_pct)
    z_df = df.where(mask, np.nan)
    
    # 2. Create a custom text matrix
    text_df = df.copy()
    for col in text_df.columns:
        text_df[col] = text_df[col].apply(
            lambda x: f"{x:.2f}" if (x >= min_limit_pct and x <= max_limit_pct) else "❌"
        )
    
    # 3. Calculate dynamic height
    calculated_height = len(df.index) * 35 + 120
    
    # 4. Build the Plotly figure
    fig = px.imshow(
        z_df,
        labels=dict(x="Spacing (mm)", y="Wall Thk (mm)", color="Ratio (%)"),
        x=[str(s) for s in spacings],
        y=[str(t) for t in thicknesses],
        aspect="auto",
        title=title,
        color_continuous_scale="greens",
        zmin=min_limit_pct,
        zmax=max_limit_pct,
        height=calculated_height
    )
    
    # 5. Apply the custom text AND the custom hover data
    fig.update_traces(
        text=text_df.values, 
        texttemplate="%{text}",
        customdata=df.values, # Attach the raw, unedited numbers in the background
        hovertemplate="Spacing: %{x} mm<br>Wall Thk: %{y} mm<br>Ratio: %{customdata:.2f}%<extra></extra>"
    )
    
    # 6. Formatting and Layout adjustments
    fig.update_layout(
        coloraxis_showscale=False, 
        plot_bgcolor='rgba(240,240,240,0.8)',
        margin=dict(t=60, b=20, l=60, r=20)
    )
    fig.update_xaxes(side="top")
    fig.update_traces(textfont={"size": 14})
    
    return fig

# --- GUI SIDEBAR CONTROLS ---
st.sidebar.header("Calculation Settings")
selected_pair = st.sidebar.selectbox("Select Bar Pair", list(bar_pairs.keys()))
layer_option = st.sidebar.radio("Reinforcement Layers", ("Single Layer (Central)", "Double Layer (Each Face)"))

st.sidebar.divider()

# New Allowable Steel Ratio Limits
st.sidebar.header("Design Limits")
ratio_options = {
    "0.0015 (0.15%)": 0.15,
    "0.0025 (0.25%)": 0.25,
    "0.0035 (0.35%)": 0.35,
    "0.0060 (0.60%)": 0.60
}
selected_ratio_label = st.sidebar.selectbox("Minimum Steel Ratio", list(ratio_options.keys()))

# Extract the percentage values for our logic
min_pct = ratio_options[selected_ratio_label]
max_pct = min_pct * 5

st.sidebar.caption(f"*Showing valid options between {min_pct:.2f}% and {max_pct:.2f}%*")

# --- CALCULATE MATRICES ---
is_double = layer_option == "Double Layer (Each Face)"
pair_data = bar_pairs[selected_pair]

df_N = create_ratio_matrix(pair_data["N_area"], is_double)
df_S = create_ratio_matrix(pair_data["S_area"], is_double)

# --- RENDER DASHBOARD ---
col1, col2 = st.columns(2)

with col1:
    title_N = f"Standard {pair_data['N_name']} ({pair_data['N_area']} mm²)"
    fig_N = plot_heatmap(df_N, title_N, min_pct, max_pct)
    st.plotly_chart(fig_N, use_container_width=True)

with col2:
    title_S = f"SENSE {pair_data['S_name']} ({pair_data['S_area']} mm²)"
    fig_S = plot_heatmap(df_S, title_S, min_pct, max_pct)
    st.plotly_chart(fig_S, use_container_width=True)
    
# py -3.13 -m streamlit run "C:\Users\HassanAm\Downloads\Concrete Design\reo_app_v2.py"