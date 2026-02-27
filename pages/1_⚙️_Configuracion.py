import streamlit as st
import pandas as pd
from settings import GlobalSettings

st.set_page_config(page_title="Configuración de Ley", page_icon="⚙️", layout="wide")

st.title("⚙️ Configuración de Parámetros de Ley")
st.info("Nota: Los cambios realizados aquí afectarán todos los cálculos de la sesión actual.")

# --- PERSISTENCE LOGIC (SESSION STATE) ---
if 'custom_settings' not in st.session_state:
    st.session_state.custom_settings = {
        "uma": GlobalSettings.UMA,
        "min_wage": GlobalSettings.MINIMUM_WAGE,
        "isn_rate": GlobalSettings.ISN_RATE,
        "isr_table": GlobalSettings.ISR_MONTHLY_TABLE,
        "imss_rates": GlobalSettings.IMSS_RATES,
    }

# Sync
GlobalSettings.UMA = st.session_state.custom_settings["uma"]
GlobalSettings.MINIMUM_WAGE = st.session_state.custom_settings["min_wage"]
GlobalSettings.ISN_RATE = st.session_state.custom_settings["isn_rate"]
GlobalSettings.ISR_MONTHLY_TABLE = st.session_state.custom_settings["isr_table"]
GlobalSettings.IMSS_RATES = st.session_state.custom_settings["imss_rates"]

tab_general, tab_isr, tab_imss = st.tabs(["General (UMA/ISN)", "Tabla ISR", "Tasas IMSS"])

with tab_general:
    st.subheader("Indicadores Económicos")
    st.session_state.custom_settings["uma"] = st.number_input(
        "Valor de la UMA ($)", value=float(st.session_state.custom_settings["uma"]), step=1.0
    )
    st.session_state.custom_settings["min_wage"] = st.number_input(
        "Salario Mínimo ($)", value=float(st.session_state.custom_settings["min_wage"]), step=1.0
    )
    temp_isn = st.number_input(
        "Tasa ISN (%)", value=float(st.session_state.custom_settings["isn_rate"] * 100), step=0.1
    )
    st.session_state.custom_settings["isn_rate"] = temp_isn / 100.0

with tab_isr:
    st.subheader("Tabla de ISR Mensual")
    st.markdown("Edita las celdas directamente o añade nuevas filas según lo indique el SAT.")
    df_isr = pd.DataFrame(st.session_state.custom_settings["isr_table"])
    
    # Render editable dataframe
    edited_isr = st.data_editor(df_isr, num_rows="dynamic", use_container_width=True)
    st.session_state.custom_settings["isr_table"] = edited_isr.to_dict('records')

with tab_imss:
    st.subheader("Tasas de Cotización IMSS (%)")
    st.markdown("Edita los porcentajes de retención para el Patrón (ER) y el Empleado (EE). *Ej. 0.05 equivale a 5%*")
    
    # Convert dictionary to a DataFrame for easier editing in Streamlit
    imss_list = [{"Rama (Branch)": k, "Tasa (Rate)": v} for k, v in st.session_state.custom_settings["imss_rates"].items()]
    df_imss = pd.DataFrame(imss_list)
    
    # Render editable dataframe vertically
    edited_imss_df = st.data_editor(df_imss, use_container_width=True, hide_index=True)
    
    updated_imss_dict = {row["Rama (Branch)"]: float(row["Tasa (Rate)"]) for _, row in edited_imss_df.iterrows()}
    st.session_state.custom_settings["imss_rates"] = updated_imss_dict
