import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Slab Reo Ratio Calculator", layout="wide")
st.title("Slab Reinforcement Ratio: 500N vs SENSE 600®")
st.markdown("Evaluates viable steel ratios based on direction, restraint, and exposure.")

# --- DATA DICTIONARY ---
bar_pairs = {
    "N12 / S11": {"N_name": "N12", "N_area": 113, "S_name": "S11", "S_area": 94.2},
    "N16 / S15": {"N_name": "N16", "N_area": 201, "S_name": "S15", "S_area": 168.0},
    "N20 / S18": {"N_name": "N20", "N_area": 314, "S_name": "S18", "S_area": 262.0},
    "N24 / S22": {"N_name": "N24", "N_area": 452, "S_name": "S22", "S_area": 377.0},
}

# Base Secondary Ratios Mapping
SECONDARY_RATIOS = {
    "Unrestrained": {
        "All": {
            "Minor": 0.00175,
            "Moderate": 0.00175,
            "Strong": 0.00175
        }
    },
    "Restrained": {
        "Enclosed A1": {
            "Minor": 0.00175,
            "Moderate": 0.0035,
            "Strong": 0.0060 
        },
        "Other A1 and A2": {
            "Moderate": 0.0035,
            "Strong": 0.0060
        },
        "B and C": {
            "Strong": 0.0060
        }
    }
}

base_spacings = [100, 150, 200, 250, 300]
thicknesses = np.arange(180, 330, 10) 

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("Slab Configuration")
selected_pair = st.sidebar.selectbox("Select Bar Pair", list(bar_pairs.keys()))
layer_option = st.sidebar.radio("Reinforcement Layers", ("Single Layer (Central)", "Double Layer (Each Face)"))

st.sidebar.divider()

# --- NEW DECISION TREE LOGIC ---
st.sidebar.header("Design Parameters")

# 1. Choose Direction
direction = st.sidebar.radio("Direction", ("Secondary", "Primary"))

# 2. Choose Restraint
restraint = st.sidebar.radio("Restraint Condition", ("Unrestrained", "Restrained"))

# 3 & 4. Cascading Exposure and Crack Control
if restraint == "Unrestrained":
    exposure = st.sidebar.selectbox("Exposure Class Category", ["All"])
    crack_control = st.sidebar.selectbox("Degree of Crack Control", ["Minor", "Moderate", "Strong"])
else:
    exposure = st.sidebar.selectbox("Exposure Class Category", ["Enclosed A1", "Other A1 and A2", "B and C"])
    
    if exposure == "Enclosed A1":
        crack_control = st.sidebar.selectbox("Degree of Crack Control", ["Minor", "Moderate", "Strong"])
    elif exposure == "Other A1 and A2":
        crack_control = st.sidebar.selectbox("Degree of Crack Control", ["Moderate", "Strong"])
    else: # B and C
        crack_control = st.sidebar.selectbox("Degree of Crack Control", ["Strong"])

# --- CALCULATE BASE RATIOS ---
base_secondary_ratio = SECONDARY_RATIOS[restraint][exposure][crack_control]

# Apply the 75% rule for the Primary direction
if direction == "Primary":
    final_base_ratio = base_secondary_ratio * 0.75
else:
    final_base_ratio = base_secondary_ratio

# Set the required minimums for the different steel grades
min_ratio_N = final_base_ratio
min_ratio_S = final_base_ratio

# --- SPACING LIMIT LOGIC ---
# Dynamically limit maximum spacing based on crack control rules
if crack_control in ["Minor", "Moderate"]:
    max_spacing = 300
elif crack_control == "Strong":
    max_spacing = 200 
else:
    max_spacing = 300

# Filter the available spacings
current_spacings = [s for s in base_spacings if s <= max_spacing]

# Display the required metrics in the sidebar
st.sidebar.info(
    f"**Direction Factor:** {'75% (Primary)' if direction == 'Primary' else '100% (Secondary)'}\n\n"
    f"**Base 500N Required:** {min_ratio_N*100:.3f}%\n\n"
    f"**SENSE 600® Required:** {min_ratio_S*100:.3f}%\n\n"
    f"**Max Spacing:** {max_spacing}mm"
)

# --- CALCULATE MATRICES ---
is_double = layer_option == "Double Layer (Each Face)"
pair_data = bar_pairs[selected_pair]

def create_ratio_matrix(bar_area, is_double):
    matrix_data = []
    multiplier = 2 if is_double else 1
    
    for T in thicknesses:
        row = {"Thickness (mm)": T}
        for space in current_spacings:
            ast_prov = (bar_area / space) * 1000 * multiplier
            ratio_val = ast_prov / (1000 * T)
            
            # Calculating and storing ALL values for the heatmap display
            row[f"@{space}mm"] = round(ratio_val * 100, 2) 
            
        matrix_data.append(row)
        
    return pd.DataFrame(matrix_data).set_index("Thickness (mm)")

df_N = create_ratio_matrix(pair_data["N_area"], is_double)
df_S = create_ratio_matrix(pair_data["S_area"], is_double)


# --- GENERATE CUSTOM TEXT LABELS ---
# Creates a mirror of the dataframe but replaces failing numbers with an 'X'
text_N = df_N.copy().astype(str)
for col in df_N.columns:
    text_N[col] = df_N[col].apply(lambda x: f"{x:.2f}" if x >= min_ratio_N * 100 else "❌")

text_S = df_S.copy().astype(str)
for col in df_S.columns:
    text_S[col] = df_S[col].apply(lambda x: f"{x:.2f}" if x >= min_ratio_S * 100 else "❌")


# --- RENDER DASHBOARD ---
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Conventional 500N ({pair_data['N_name']})")
    fig_N = px.imshow(
        df_N,
        aspect="auto",
        color_continuous_scale="Blues",
        zmin=min_ratio_N * 100,
        zmax=min_ratio_N * 500, # Visually washes out excessive over-design
        labels=dict(x="Bar Spacing", y="Slab Thickness (mm)", color="Steel Ratio (%)")
    )
    # Apply custom text matrix
    fig_N.update_traces(text=text_N, texttemplate="%{text}")
    fig_N.update_xaxes(side="top")
    st.plotly_chart(fig_N, use_container_width=True)

with col2:
    st.subheader(f"SENSE 600® ({pair_data['S_name']})")
    fig_S = px.imshow(
        df_S,
        aspect="auto",
        color_continuous_scale="Greens", 
        zmin=min_ratio_S * 100,
        zmax=min_ratio_S * 500, 
        labels=dict(x="Bar Spacing", y="Slab Thickness (mm)", color="Steel Ratio (%)")
    )
    # Apply custom text matrix
    fig_S.update_traces(text=text_S, texttemplate="%{text}")
    fig_S.update_xaxes(side="top")
    st.plotly_chart(fig_S, use_container_width=True)
    
# --- SUMMARY METRICS ---
st.divider()

# Mathematically count viable options between the acceptable bounds
valid_N = ((df_N >= min_ratio_N * 100) & (df_N <= min_ratio_N * 500)).sum().sum()
valid_S = ((df_S >= min_ratio_S * 100) & (df_S <= min_ratio_S * 500)).sum().sum()

m1, m2, m3 = st.columns(3)
m1.metric("Valid 500N Configurations", valid_N)
m2.metric("Valid SENSE 600® Configurations", valid_S)

if valid_S > valid_N:
    m3.metric("SENSE 600® Advantage", f"+{valid_S - valid_N}", "More viable options")
elif valid_N > valid_S:
    m3.metric("500N Advantage", f"+{valid_N - valid_S}", "More viable options", delta_color="inverse")
else:
    m3.metric("Difference", "0", "Equal options")
# py -3.13 -m streamlit run "C:\Users\HassanAm\Downloads\Concrete Design\Scripts\Slab_reo_app_v2.py"