import streamlit as st
from settings import GlobalSettings
from motor_calculo import PayrollEngine, FeeCalculator

# Page Config
st.set_page_config(page_title="Antigravity Payroll", page_icon="💸", layout="wide")

st.title("💸 Calculadora de Nómina y Honorarios")
st.markdown("Plataforma paramétrica para el cálculo de sueldos y salarios en México.")

# --- SIDEBAR: Configuración (Tablas de Referencia) ---
st.sidebar.header("⚙️ Tablas de Referencia")
with st.sidebar.expander("Parámetros Globales (Editables)", expanded=True):
    new_uma = st.number_input("Valor UMA ($)", value=GlobalSettings.UMA, step=1.0)
    new_min_wage = st.number_input("Salario Mínimo ($)", value=GlobalSettings.MINIMUM_WAGE, step=1.0)
    new_isn = st.number_input("Tasa ISN (%)", value=GlobalSettings.ISN_RATE * 100, step=0.1) / 100.0

# Apply overridden settings dynamically without modifying the code!
GlobalSettings.UMA = new_uma
GlobalSettings.MINIMUM_WAGE = new_min_wage
GlobalSettings.ISN_RATE = new_isn

# --- MAIN DASHBOARD: Tablas de Selección ---
tab1, tab2, tab3 = st.tabs(["Nómina (Sueldos)", "Honorarios (RESICO)", "Asimilados a Salarios"])

with tab1:
    st.header("Cálculo de Nómina")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        salario_diario = st.number_input("Salario Diario ($)", value=500.0, step=50.0)
    with col2:
        dias_periodo = st.number_input("Días del Periodo", value=30, step=1)
    with col3:
        antiguedad = st.number_input("Años de Antigüedad", value=2, step=1, min_value=1)
    
    st.markdown("---")
    
    resultados = PayrollEngine.calculate_net_pay(salario_diario, antiguedad, dias_periodo)
    
    st.subheader("Visualización de Resultados")
    r_col1, r_col2 = st.columns(2)
    
    with r_col1:
        st.success(f"### NETO A DEPOSITAR: ${resultados['net_pay']:,.2f}")
        st.caption("Take-Home Pay para el Colaborador")
        st.write(f"**Ingreso Bruto:** ${resultados['gross_income']:,.2f}")
        st.write(f"**Retención IMSS:** ${resultados['imss_deduction']:,.2f}")
        st.write(f"**Retención ISR:** ${resultados['effective_isr']:,.2f}")
        if resultados['subsidy_applied'] > 0:
            st.info(f"Subsidio al Empleo Aplicado: ${resultados['subsidy_applied']:,.2f}")
            
    with r_col2:
        st.error(f"### COSTO TOTAL EMPRESA: ${resultados['total_employer_cost']:,.2f}")
        st.caption("Costo Real de la Nómina (Administración)")
        st.write(f"**Salario Bruto (Base):** ${resultados['gross_income']:,.2f}")
        st.write(f"**Cargas Sociales (IMSS/Infonavit):** ${resultados['employer_imss_cost']:,.2f}")
        st.write(f"**Impuesto Sobre Nómina (ISN {new_isn * 100}%):** ${resultados['isn_cost']:,.2f}")

with tab2:
    st.header("Cálculo de Honorarios (RESICO)")
    bruto_honorarios = st.number_input("Monto Bruto a Facturar ($)", value=20000.0, step=1000.0)
    
    st.markdown("---")
    
    calc = FeeCalculator(bruto_honorarios, GlobalSettings.RESICO_SETTINGS)
    res = calc.calculate_invoice()
    
    st.subheader("Desglose de Factura")
    r_col1, r_col2 = st.columns(2)
    
    with r_col1:
        st.success(f"### NETO A RECIBIR: ${res['net_total']:,.2f}")
        st.caption("Monto que ingresa a la cuenta bancaria")
        st.write(f"**Subtotal (Servicios):** ${res['subtotal']:,.2f}")
        st.write(f"**(+) IVA (16%):** ${res['iva']:,.2f}")
    with r_col2:
        st.warning("### Retenciones")
        st.write(f"**(-) Retención IVA (10.67%):** ${res['ret_iva']:,.2f}")
        st.write(f"**(-) Retención ISR (1.25%):** ${res['ret_isr']:,.2f}")

with tab3:
    st.header("Cálculo de Asimilados a Salarios")
    st.info("🚧 Módulo estructuralmente listo. Cálculos de retención de ISR pendientes por integrar en la siguiente fase.")
