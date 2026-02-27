from settings import GlobalSettings

class IMSSCalculator:
    """Handles the breakdown of IMSS branches based on SBC and UMA."""

    def __init__(self, sbc, uma_value, days_period=30):
        self.sbc = sbc
        self.uma = uma_value
        self.days = days_period
        
        # Reference rates directly from GlobalSettings
        # This keeps the engine decoupled from hardcoded values
        self.rates = {
            "fixed_fee_er": GlobalSettings.IMSS_RATES.get("E_M_FIXED", 0.204),
            "excess_er": GlobalSettings.IMSS_RATES.get("E_M_EXC_3UMA_ER", 0.011),
            "excess_ee": GlobalSettings.IMSS_RATES.get("E_M_EXC_3UMA_EE", 0.004),
            "money_er": GlobalSettings.IMSS_RATES.get("E_M_DINERO_ER", 0.007),
            "money_ee": GlobalSettings.IMSS_RATES.get("E_M_DINERO_EE", 0.00375),
            "inv_life_er": GlobalSettings.IMSS_RATES.get("I_V_ER", 0.0175),
            "inv_life_ee": GlobalSettings.IMSS_RATES.get("I_V_EE", 0.00625),
            "cv_er": GlobalSettings.IMSS_RATES.get("C_V_ER", 0.0315),
            "cv_ee": GlobalSettings.IMSS_RATES.get("C_V_EE", 0.01125),
            "guarderia_er": GlobalSettings.IMSS_RATES.get("GUARDERIA_ER", 0.01),
            "retirement_er": GlobalSettings.IMSS_RATES.get("RETIRO_ER", 0.02),
            "infonavit_er": GlobalSettings.IMSS_RATES.get("INFONAVIT_ER", 0.05)
        }

    def calculate_excess_3uma(self):
        """Calculates the specific fee for income exceeding 3 UMAs."""
        limit_3uma = self.uma * 3
        if self.sbc > limit_3uma:
            base_excess = self.sbc - limit_3uma
            return {
                "er_excess": base_excess * self.rates["excess_er"] * self.days,
                "ee_excess": base_excess * self.rates["excess_ee"] * self.days
            }
        return {"er_excess": 0.0, "ee_excess": 0.0}

    def get_full_breakdown(self):
        """Generates the complete breakdown for Employer and Employee."""
        excess = self.calculate_excess_3uma()
        
        # Employee (EE) Contributions
        ee_total = (
            excess["ee_excess"] +
            (self.sbc * self.rates["money_ee"] * self.days) +
            (self.sbc * self.rates["inv_life_ee"] * self.days) +
            (self.sbc * self.rates["cv_ee"] * self.days)
        )

        # Employer (ER) Contributions (Costo Patronal)
        er_total = (
            (self.uma * self.rates["fixed_fee_er"] * self.days) + # Fixed fee on UMA
            excess["er_excess"] +
            (self.sbc * self.rates["money_er"] * self.days) +
            (self.sbc * self.rates["inv_life_er"] * self.days) +
            (self.sbc * self.rates["cv_er"] * self.days) +
            (self.sbc * self.rates["guarderia_er"] * self.days) +
            (self.sbc * self.rates["retirement_er"] * self.days) +
            (self.sbc * self.rates["infonavit_er"] * self.days)
        )

        return {
            "employee_deduction": round(ee_total, 2),
            "employer_cost": round(er_total, 2),
            "details": {
                "excess": excess
                # We can expand this later to return the exact deduction per IMSS branch
            }
        }


class ISRCalculator:
    """Handles ISR calculation by locating the correct bracket in the tax table."""

    def __init__(self, taxable_income, isr_table):
        self.taxable_income = taxable_income
        self.isr_table = isr_table # From GlobalSettings.ISR_MONTHLY_TABLE

    def calculate(self):
        """
        Applies the law formula: 
        ISR = ((Income - Lower Limit) * Rate) + Fixed Fee
        """
        bracket = self._find_bracket()
        
        if not bracket:
            return 0.0

        excess = self.taxable_income - bracket['low_limit']
        tax_on_excess = excess * bracket['rate']
        total_isr = tax_on_excess + bracket['fixed_fee']
        
        return round(total_isr, 2)

    def _find_bracket(self):
        """Locates the correct tax bracket based on taxable income."""
        # We iterate through the table to find where the income fits
        # The table must be sorted by low_limit ascending.
        selected_bracket = None
        for bracket in self.isr_table:
            if self.taxable_income >= bracket['low_limit']:
                selected_bracket = bracket
            else:
                break
        return selected_bracket

class FeeCalculator:
    """Handles calculations for Professional Fees under RESICO regime."""

    def __init__(self, gross_amount, settings):
        self.gross_amount = gross_amount
        self.settings = settings # GlobalSettings.RESICO_SETTINGS

    def calculate_invoice(self):
        """
        Calculates VAT, Retentions and Net total.
        Formula: Gross + IVA - Ret_IVA - Ret_ISR = Net
        """
        iva = self.gross_amount * self.settings["IVA_RATE"]
        ret_iva = self.gross_amount * self.settings["RET_IVA_RATE"]
        ret_isr = self.gross_amount * self.settings["RET_ISR_RATE"]
        
        net_to_deposit = self.gross_amount + iva - ret_iva - ret_isr
        
        return {
            "subtotal": round(self.gross_amount, 2),
            "iva": round(iva, 2),
            "ret_iva": round(ret_iva, 2),
            "ret_isr": round(ret_isr, 2),
            "net_total": round(net_to_deposit, 2)
        }

class PayrollEngine:
    """
    Core engine for payroll calculations. 
    It intentionally accesses GlobalSettings to compute parameters 
    so the logic remains decoupled from the actual yearly varying rates.
    """
    
    @staticmethod
    def calculate_sdi(daily_salary: float, years_of_seniority: int) -> float:
        """
        Calculates the Salario Diario Integrado (SDI) based on the daily salary
        and the integration factor corresponding to the employee's seniority.
        """
        # Set a ceiling for seniority if it exceeds our table (e.g., 5+ years uses the max factor)
        max_seniority = max(GlobalSettings.INTEGRATION_FACTORS.keys())
        effective_years = min(years_of_seniority, max_seniority)
        
        # Get the integration factor from our settings
        integration_factor = GlobalSettings.INTEGRATION_FACTORS.get(effective_years, 1.0493)
        
        # Calculate SDI
        sdi = daily_salary * integration_factor
        
        # In Mexico, the SDI has an upper limit of 25 UMAs for IMSS calculations (SBC - Salario Base de Cotización)
        sdi_limit = GlobalSettings.UMA * 25
        
        return min(sdi, sdi_limit)

    @staticmethod
    def calculate_net_pay(daily_salary: float, years_of_seniority: int, days_period: int = 30) -> dict:
        """
        Calculates the complete payroll breakdown (Gross, ISR, IMSS, Net, Employer Cost).
        Includes Subsidio al Empleo (2024 updated rules) and ISN.
        """
        # 1. Gross Income
        gross_income = daily_salary * days_period
        
        # 2. SDI and IMSS
        sdi = PayrollEngine.calculate_sdi(daily_salary, years_of_seniority)
        imss_calc = IMSSCalculator(sbc=sdi, uma_value=GlobalSettings.UMA, days_period=days_period)
        imss_breakdown = imss_calc.get_full_breakdown()
        
        # 3. ISR
        isr_calc = ISRCalculator(taxable_income=gross_income, isr_table=GlobalSettings.ISR_MONTHLY_TABLE)
        isr_deduction = isr_calc.calculate()
        
        # 4. Employment Subsidy (Subsidio al Empleo) - Decreases ISR
        subsidy = 0.0
        if hasattr(GlobalSettings, "SUBSIDIO_EMPLEO"):
            if gross_income <= GlobalSettings.SUBSIDIO_EMPLEO["income_limit"]:
                subsidy = GlobalSettings.SUBSIDIO_EMPLEO["subsidy_amount"]
        
        # After the May 2024 update, the subsidy just offsets ISR. Any remaining subsidy is effectively lost.
        effective_isr = max(0.0, isr_deduction - subsidy)
        subsidy_applied = min(subsidy, isr_deduction) # We only "applied" enough to offset ISR.
        
        # 5. Net Pay
        net_pay = gross_income - effective_isr - imss_breakdown["employee_deduction"]
        
        # 6. ISN (Employer Cost)
        isn_cost = gross_income * getattr(GlobalSettings, "ISN_RATE", 0.03)
        total_employer_cost = gross_income + imss_breakdown["employer_cost"] + isn_cost
        
        return {
            "gross_income": round(gross_income, 2),
            "sdi": round(sdi, 2),
            "imss_deduction": imss_breakdown["employee_deduction"],
            "isr_deduction": isr_deduction,
            "subsidy_applied": round(subsidy_applied, 2),
            "effective_isr": round(effective_isr, 2),
            "net_pay": round(net_pay, 2),
            "employer_imss_cost": imss_breakdown["employer_cost"],
            "isn_cost": round(isn_cost, 2),
            "total_employer_cost": round(total_employer_cost, 2)
        }

# --- Ejercicios de prueba local ---
if __name__ == "__main__":
    salario_diario_ejemplo = 500.00
    antiguedad_ejemplo = 2 # 2 años
    
    print(f"--- Calculadora de Nómina (Neto y Costo Patronal) ---")
    resultados = PayrollEngine.calculate_net_pay(salario_diario_ejemplo, antiguedad_ejemplo, days_period=30)
    
    print(f"Ingreso Bruto Mensual: ${resultados['gross_income']:,.2f}")
    print(f"(-) Retención IMSS Colaborador: ${resultados['imss_deduction']:,.2f}")
    print(f"(-) Retención ISR Efectiva: ${resultados['effective_isr']:,.2f}")
    if resultados['subsidy_applied'] > 0:
        print(f"  * Subsidio al Empleo descontado del ISR: ${resultados['subsidy_applied']:,.2f}")
    print(f"=====================================")
    print(f"NETO A DEPOSITAR (Take-Home Pay): ${resultados['net_pay']:,.2f}\n")
    
    print(f"--- Desglose de Costo Patronal ---")
    print(f"Salario Bruto (Base de nómina): ${resultados['gross_income']:,.2f}")
    print(f"(+) Cuotas Obrero-Patronales IMSS/Infonavit/Retiro: ${resultados['employer_imss_cost']:,.2f}")
    print(f"(+) Impuesto Sobre Nómina (ISN 3%): ${resultados['isn_cost']:,.2f}")
    print(f"=====================================")
    print(f"COSTO REAL DE LA NÓMINA: ${resultados['total_employer_cost']:,.2f}")

    print(f"\n--- Prueba Honorarios RESICO ---")
    honorarios_brutos = 19215.43
    calc_honorarios = FeeCalculator(honorarios_brutos, GlobalSettings.RESICO_SETTINGS)
    res_honorarios = calc_honorarios.calculate_invoice()
    print(f"Subtotal / Monto Bruto: ${res_honorarios['subtotal']:,.2f}")
    print(f"(+) IVA (16%): ${res_honorarios['iva']:,.2f}")
    print(f"(-) Retención IVA (10.67%): ${res_honorarios['ret_iva']:,.2f}")
    print(f"(-) Retención ISR (1.25%): ${res_honorarios['ret_isr']:,.2f}")
    print(f"=====================================")
    print(f"NETO A RECIBIR: ${res_honorarios['net_total']:,.2f}")
