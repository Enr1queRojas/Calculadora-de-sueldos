import pandas as pd
import streamlit as st
from settings import GlobalSettings
from motor_calculo import PayrollEngine, FeeCalculator

# Page Config
st.set_page_config(page_title="Innoverse Payroll", page_icon="💸", layout="wide")

st.title("💸 Calculadora de Nómina y Honorarios")
st.markdown("Plataforma paramétrica para el cálculo de sueldos y salarios en México.")

# --- PERSISTENCE LOGIC (SESSION STATE) ---
if 'custom_settings' not in st.session_state:
    st.session_state.custom_settings = {
        "uma": GlobalSettings.UMA,
        "min_wage": GlobalSettings.MINIMUM_WAGE,
        "isn_rate": GlobalSettings.ISN_RATE,
        "isr_table": GlobalSettings.ISR_MONTHLY_TABLE,
        "imss_rates": GlobalSettings.IMSS_RATES,
    }

# Sync explicit settings so that any decoupled code looking at GlobalSettings gets updated dynamically 
GlobalSettings.UMA = st.session_state.custom_settings["uma"]
GlobalSettings.MINIMUM_WAGE = st.session_state.custom_settings["min_wage"]
GlobalSettings.ISN_RATE = st.session_state.custom_settings["isn_rate"]
GlobalSettings.ISR_MONTHLY_TABLE = st.session_state.custom_settings["isr_table"]
GlobalSettings.IMSS_RATES = st.session_state.custom_settings["imss_rates"]

# --- MAIN DASHBOARD: Tablas de Selección ---
tab1, tab2, tab3 = st.tabs(["Nómina (Esquema Mixto)", "Honorarios (RESICO)", "Plantilla Mensual"])

with tab1:
    st.header("Cálculo de Nómina (Esquema Mixto)")
    modo_entrada = st.radio("Modo de Cálculo", ["Sueldo Diario", "Neto Objetivo"], horizontal=True)
    st.write("") # Espaciador
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if modo_entrada == "Sueldo Diario":
            salario_diario = st.number_input("Salario Diario ($)", value=500.0, step=50.0)
        else:
            neto_objetivo = st.number_input("Neto Mensual Objetivo ($)", value=20000.0, step=1000.0)
    with col2:
        dias_periodo = st.number_input("Días del Periodo", value=30, step=1)
    with col3:
        antiguedad = st.number_input("Años de Antigüedad", value=2, step=1, min_value=1)
    with col4:
        asimilados = st.number_input("Monto Asimilados ($)", value=0.0, step=500.0)
    
    st.markdown("---")
    
    if modo_entrada == "Neto Objetivo":
        salario_diario = PayrollEngine.calculate_daily_from_net(neto_objetivo, antiguedad, dias_periodo)
        st.info(f"Salario Diario calculado para Neto de Nómina **${neto_objetivo:,.2f}**: **${salario_diario:,.2f}** | Total a depositar (+ Asimilados): **${neto_objetivo + asimilados:,.2f}**")
    
    resultados = PayrollEngine.calculate_net_pay(salario_diario, antiguedad, asimilados, dias_periodo)
    
    st.subheader("Visualización de Resultados")
    r_col1, r_col2 = st.columns(2)
    
    with r_col1:
        st.success(f"### NETO A DEPOSITAR: ${resultados['net_total_deposit']:,.2f}")
        st.caption("Take-Home Pay Total para el Colaborador")
        st.write(f"**Ingreso Bruto (Nómina):** ${resultados['gross_income']:,.2f}")
        st.write(f"**(-) Retención IMSS:** ${resultados['imss_deduction']:,.2f}")
        st.write(f"**(-) Retención ISR:** ${resultados['effective_isr']:,.2f}")
        st.write(f"**= Neto Nómina Fiscal:** ${resultados['net_pay_payroll']:,.2f}")
        if resultados.get('subsidy_applied', 0) > 0:
            st.info(f"Subsidio al Empleo Aplicado: ${resultados['subsidy_applied']:,.2f}")
        st.write(f"**(+) Monto Asimilados:** ${resultados['asimilados_amount']:,.2f}")
            
    with r_col2:
        st.error(f"### COSTO TOTAL EMPRESA: ${resultados['total_employer_cost']:,.2f}")
        st.caption("Costo Real de la Nómina (Administración)")
        st.write(f"**Salario Bruto (Base Fiscal):** ${resultados['gross_income']:,.2f}")
        st.write(f"**(+) Cargas Sociales (IMSS/Infonavit/RCV):** ${resultados['employer_imss_cost']:,.2f}")
        st.write(f"**(+) Impuesto Sobre Nómina (ISN {st.session_state.custom_settings['isn_rate'] * 100}%):** ${resultados['isn_cost']:,.2f}")
        st.write(f"**(+) Monto Asimilados Depositado:** ${resultados['asimilados_amount']:,.2f}")
        st.write(f"**(+) Comisión Asimilados (8%):** ${resultados['asimilados_fee_cost']:,.2f}")

    with st.expander("Ver JSON Completo"):
        st.json(resultados)

with tab2:
    st.header("Cálculo de Honorarios (RESICO)")
    fee_input = st.number_input("Monto de Honorarios (Bruto)", value=19215.43, step=1000.0)
    
    st.markdown("---")
    
    fee_engine = FeeCalculator(fee_input)
    results = fee_engine.calculate_invoice()
    
    st.subheader("Desglose de Factura")
    r_col1, r_col2 = st.columns(2)
    
    with r_col1:
        st.success(f"### NETO A RECIBIR: ${results['net_total']:,.2f}")
        st.caption("Monto que ingresa a la cuenta bancaria")
        st.write(f"**Honorario Base:** ${results['gross_amount']:,.2f}")
        st.write(f"**(+) IVA (16%):** ${results['iva']:,.2f}")
        st.write(f"**Subtotal:** ${results['subtotal']:,.2f}")
    with r_col2:
        st.warning("### Retenciones")
        st.write(f"**(-) Retención IVA (10.67%):** ${results['ret_iva']:,.2f}")
        st.write(f"**(-) Retención ISR (1.25%):** ${results['ret_isr']:,.2f}")
        
    with st.expander("Ver JSON Completo"):
        st.json(results)

MONTHS = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
          "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

with tab3:
    st.header("Plantilla Mensual de Empleados")
    st.caption("Define el esquema de cada empleado y marca los meses en que estará activo.")

    if 'roster' not in st.session_state:
        st.session_state.roster = pd.DataFrame({
            "Empleado": ["Empleado 1"],
            "Neto Nómina ($)": [10000.0],
            "Asimilados ($)": [0.0],
            "Antigüedad (años)": [1],
            **{m: False for m in MONTHS}
        })

    roster = st.data_editor(
        st.session_state.roster,
        num_rows="dynamic",
        width='stretch',
        column_config={
            "Empleado": st.column_config.TextColumn("Empleado", width="medium"),
            "Neto Nómina ($)": st.column_config.NumberColumn("Neto Nómina ($)", min_value=0, step=500.0, format="$%.2f"),
            "Asimilados ($)": st.column_config.NumberColumn("Asimilados ($)", min_value=0, step=500.0, format="$%.2f"),
            "Antigüedad (años)": st.column_config.NumberColumn("Antigüedad", min_value=1, max_value=5, step=1, width="small"),
            **{m: st.column_config.CheckboxColumn(m, width="small") for m in MONTHS},
        },
        key="roster_editor"
    )

    # --- Calculate per employee ---
    calc_rows = []
    for _, row in roster.iterrows():
        neto = float(row.get("Neto Nómina ($)") or 0)
        asim = float(row.get("Asimilados ($)") or 0)
        antig = max(1, int(row.get("Antigüedad (años)") or 1))
        nombre = str(row.get("Empleado") or "")

        if neto > 0:
            sd = PayrollEngine.calculate_daily_from_net(neto, antig, 30)
            res = PayrollEngine.calculate_net_pay(sd, antig, asim, 30)
            neto_dep = res["net_total_deposit"]
            costo = res["total_employer_cost"]
        else:
            neto_dep = asim
            costo = round(asim * 1.08, 2)

        calc_rows.append({
            "Empleado": nombre,
            "Neto Nómina ($)": neto,
            "Asimilados ($)": asim,
            "NETO A DEPOSITAR": neto_dep,
            "COSTO TOTAL EMPRESA": costo,
            **{m: bool(row.get(m, False)) for m in MONTHS}
        })

    if not calc_rows:
        st.info("Agrega empleados en la tabla para ver los resultados.")
    else:
        result_df = pd.DataFrame(calc_rows)

        st.markdown("---")
        st.subheader("Resumen por Empleado")

        summary_display = result_df[["Empleado","Neto Nómina ($)","Asimilados ($)","NETO A DEPOSITAR","COSTO TOTAL EMPRESA"]].copy()
        st.dataframe(
            summary_display.style.format({
                "Neto Nómina ($)": "${:,.2f}",
                "Asimilados ($)": "${:,.2f}",
                "NETO A DEPOSITAR": "${:,.2f}",
                "COSTO TOTAL EMPRESA": "${:,.2f}",
            }),
            width='stretch',
            hide_index=True
        )

        st.markdown("---")
        st.subheader("Proyección de Costo Mensual")

        # Build display matrix: rows=employees, cols=months (show cost if active, blank if not)
        matrix_rows = []
        for _, row in result_df.iterrows():
            matrix_row = {"Empleado": row["Empleado"]}
            for m in MONTHS:
                matrix_row[m] = f"${row['COSTO TOTAL EMPRESA']:,.2f}" if row[m] else ""
            matrix_rows.append(matrix_row)

        # Totals row
        totals_row = {"Empleado": "TOTAL"}
        for m in MONTHS:
            total = result_df.loc[result_df[m] == True, "COSTO TOTAL EMPRESA"].sum()
            totals_row[m] = f"${total:,.2f}" if total > 0 else ""
        matrix_rows.append(totals_row)

        matrix_df = pd.DataFrame(matrix_rows)
        st.dataframe(matrix_df, width='stretch', hide_index=True)
