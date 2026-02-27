# Configuration and Law Factors Section
# This section allows easy updates when tax or labor laws change.

class GlobalSettings:
    # Basic Economic Indicators (Update annually)
    UMA = 108.57  # Daily UMA value
    MINIMUM_WAGE = 248.93  # General minimum wage
    ISN_RATE = 0.03  # Payroll tax (Example: 3% for most states)

    # Integration Factors Table (Years of seniority: Factor)
    # Calculated as: (365 + Aguinaldo_days + (Vacation_days * Vacation_bonus)) / 365
    INTEGRATION_FACTORS = {
        1: 1.0493,
        2: 1.0507,
        3: 1.0521,
        4: 1.0534,
        5: 1.0548
    }

    # IMSS Contribution Rates (Percentage decimals)
    # Employer (ER) and Employee (EE)
    IMSS_RATES = {
        "E_M_FIXED": 0.204,        # Fixed fee based on UMA (Employer)
        "E_M_EXC_3UMA_ER": 0.011,  # Excess of 3 UMA (Employer)
        "E_M_EXC_3UMA_EE": 0.004,  # Excess of 3 UMA (Employee)
        "E_M_DINERO_ER": 0.007,    # Money benefits (Employer)
        "E_M_DINERO_EE": 0.00375,  # Money benefits (Employee)
        "I_V_ER": 0.0175,          # Disability and Life (Employer)
        "I_V_EE": 0.00625,         # Disability and Life (Employee)
        "RETIRO_ER": 0.02,         # Retirement (Employer only)
        "C_V_ER": 0.0315,          # Severance/Old Age (Employer - Varies by SBC)
        "C_V_EE": 0.01125,         # Severance/Old Age (Employee)
        "GUARDERIA_ER": 0.01,      # Daycare/Social (Employer only)
        "INFONAVIT_ER": 0.05       # Housing (Employer only)
    }

    # Monthly ISR Table (Lower Limit, Fixed Fee, Rate)
    # These values are examples; update with the current SAT published table.
    ISR_MONTHLY_TABLE = [
        {"low_limit": 0.01, "fixed_fee": 0.00, "rate": 0.0192},
        {"low_limit": 746.05, "fixed_fee": 14.32, "rate": 0.0640},
        {"low_limit": 6332.06, "fixed_fee": 371.83, "rate": 0.1088},
        {"low_limit": 11128.02, "fixed_fee": 894.00, "rate": 0.1600},
        {"low_limit": 12935.83, "fixed_fee": 1183.13, "rate": 0.1792},
        {"low_limit": 15487.72, "fixed_fee": 1640.18, "rate": 0.2136},
        {"low_limit": 31236.50, "fixed_fee": 5004.12, "rate": 0.2352},
        {"low_limit": 49233.01, "fixed_fee": 9236.89, "rate": 0.3000}
    ]

    # RESICO (Honorarios) Retention Rates
    RESICO_SETTINGS = {
        "IVA_RATE": 0.16,
        "RET_IVA_RATE": 0.1067,
        "RET_ISR_RATE": 0.0125
    }

    # Employment Subsidy (Subsidio al Empleo) - Updated formula 2024
    # Max subsidy is 11.82% of monthly UMA (UMA * 30.4 * 0.1182)
    SUBSIDIO_EMPLEO = {
        "income_limit": 9081.00,
        "subsidy_amount": 390.12  
    }

