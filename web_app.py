"""
Retirement Calculator - Web Version

Run locally:
    streamlit run web_app.py
"""

from datetime import datetime
import math

import matplotlib.pyplot as plt
import streamlit as st


SS_TAXABLE_PCT = 0.85
MONTHS_PER_YEAR = 12
BINARY_SEARCH_ITERATIONS = 50

DEFAULT_VALUES = {
    "start_age": 62,
    "retire_age": 62,
    "start_soc_sec": 62,
    "soc_sec_payment": 3000.0,
    "initial_amount": 1000000.0,
    "monthly_expenditure": 8000.0,
    "annual_reduction_rate": 4.0,
    "interest_rate": 5.0,
    "tax_rate": 18.0,
    "inflation_rate": 2.5,
    "annual_work_amount": 160000.0,
    "max_age": 95,
}


def fmt_dollars(value: float) -> str:
    return f"${math.ceil(value / 1000) * 1000:,.0f}"


def get_current_year() -> int:
    return datetime.now().year


def calculate_year(remaining, current_age, soc_sec_monthly, annual_expenditure, inputs):
    retire_age = inputs["retire_age"]
    start_soc_sec = inputs["start_soc_sec"]
    annual_work_amount = inputs["annual_work_amount"]
    interest = inputs["interest"]
    tax_rate = inputs["tax_rate"]

    work_income_tax = 0.0
    after_tax_work_income = 0.0
    working = current_age < retire_age
    if working:
        work_income_tax = annual_work_amount * (tax_rate / 100)
        after_tax_work_income = annual_work_amount - work_income_tax
        remaining += after_tax_work_income

    annual_raw_gain = remaining * (interest / 100)

    annual_soc_security = 0.0
    if current_age >= start_soc_sec:
        annual_soc_security = MONTHS_PER_YEAR * soc_sec_monthly

    annual_tax_loss = (annual_raw_gain + annual_soc_security * SS_TAXABLE_PCT) * (
        tax_rate / 100
    ) + work_income_tax
    annual_taxed_gain = annual_soc_security + annual_raw_gain - annual_tax_loss
    remaining += annual_taxed_gain - annual_expenditure

    return {
        "remaining": remaining,
        "annual_raw_gain": annual_raw_gain,
        "annual_soc_security": annual_soc_security,
        "annual_tax_loss": annual_tax_loss,
        "annual_taxed_gain": annual_taxed_gain,
        "work_income_tax": work_income_tax,
        "after_tax_work_income": after_tax_work_income,
        "working": working,
    }


def funds_survive_to_max_age(
    budget_value,
    start_age,
    retire_age,
    start_soc_sec,
    soc_sec_payment,
    initial_amount,
    annual_work_amount,
    interest,
    tax_rate,
    inflation,
    max_age,
    use_pct=False,
):
    inputs = {
        "retire_age": retire_age,
        "start_soc_sec": start_soc_sec,
        "annual_work_amount": annual_work_amount,
        "interest": interest,
        "tax_rate": tax_rate,
    }
    remaining = initial_amount
    soc_sec_monthly = soc_sec_payment
    annual_expenditure = (
        initial_amount * (budget_value / 100)
        if use_pct
        else budget_value * MONTHS_PER_YEAR
    )
    current_age = start_age

    while remaining >= annual_expenditure and current_age < max_age:
        year = calculate_year(
            remaining, current_age, soc_sec_monthly, annual_expenditure, inputs
        )
        remaining = year["remaining"]
        annual_expenditure *= 1 + inflation / 100
        soc_sec_monthly *= 1 + inflation / 100
        current_age += 1

    return current_age >= max_age


def binary_search(test_fn, low, high, iterations=BINARY_SEARCH_ITERATIONS):
    for _ in range(iterations):
        mid = (low + high) / 2
        if test_fn(mid):
            low = mid
        else:
            high = mid
    return low


def run_simulation(inputs):
    remaining = inputs["initial_amount"]
    soc_sec_monthly = inputs["soc_sec_payment"]
    use_pct = inputs["use_pct_budget"]
    annual_expenditure = (
        remaining * (inputs["annual_reduction_rate"] / 100)
        if use_pct
        else inputs["monthly_expenditure"] * MONTHS_PER_YEAR
    )

    current_age = inputs["start_age"]
    current_year = get_current_year()
    total_years = 0
    total_soc_sec = 0.0
    total_spend = 0.0
    years_worked = 0
    ages = []
    remaining_amounts = []
    year_records = []

    while remaining >= annual_expenditure and current_age < inputs["max_age"]:
        spend_pct = (annual_expenditure / remaining) * 100
        ages.append(current_age)
        remaining_amounts.append(remaining)

        yr = calculate_year(
            remaining, current_age, soc_sec_monthly, annual_expenditure, inputs
        )
        remaining = yr["remaining"]

        total_spend += annual_expenditure
        total_soc_sec += yr["annual_soc_security"]
        if yr["working"]:
            years_worked += 1

        year_records.append(
            {
                "year": current_year,
                "age": current_age,
                "spend_pct": spend_pct,
                "annual_expenditure": annual_expenditure,
                "annual_work_amount": inputs["annual_work_amount"],
                "working": yr["working"],
                "work_income_tax": yr["work_income_tax"],
                "after_tax_work_income": yr["after_tax_work_income"],
                "annual_soc_security": yr["annual_soc_security"],
                "annual_raw_gain": yr["annual_raw_gain"],
                "annual_tax_loss": yr["annual_tax_loss"],
                "annual_taxed_gain": yr["annual_taxed_gain"],
                "remaining": remaining,
            }
        )

        annual_expenditure *= 1 + inputs["inflation"] / 100
        soc_sec_monthly *= 1 + inputs["inflation"] / 100
        total_years += 1
        current_age += 1
        current_year += 1

    return {
        "ages": ages,
        "remaining_amounts": remaining_amounts,
        "year_records": year_records,
        "total_years": total_years,
        "total_soc_sec": total_soc_sec,
        "total_spend": total_spend,
        "years_worked": years_worked,
        "final_age": current_age,
        "final_year": current_year,
        "final_remaining": remaining,
    }


def validate_inputs(inputs):
    if inputs["retire_age"] < inputs["start_age"]:
        return "Retirement age must be greater than or equal to current age."
    if inputs["start_soc_sec"] < inputs["start_age"]:
        return "Social Security age must be greater than or equal to current age."
    return None


def find_optimal_budget(inputs):
    use_pct = inputs["use_pct_budget"]
    survive_args = (
        inputs["start_age"],
        inputs["retire_age"],
        inputs["start_soc_sec"],
        inputs["soc_sec_payment"],
        inputs["initial_amount"],
        inputs["annual_work_amount"],
        inputs["interest"],
        inputs["tax_rate"],
        inputs["inflation"],
        inputs["max_age"],
    )

    if use_pct:
        return round(
            binary_search(
                lambda v: funds_survive_to_max_age(v, *survive_args, use_pct=True),
                0.0,
                100.0,
            ),
            2,
        )

    return math.floor(
        binary_search(
            lambda v: funds_survive_to_max_age(v, *survive_args, use_pct=False),
            0.0,
            inputs["initial_amount"] / MONTHS_PER_YEAR,
        )
    )


def draw_chart(ages, remaining_amounts):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_title("Remaining Amount vs Age")
    ax.set_xlabel("Age")
    ax.set_ylabel("Remaining Amount ($)")
    ax.plot(ages, remaining_amounts, marker="o", label="Remaining Amount")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)


def main():
    st.set_page_config(page_title="Retirement Calculator", layout="wide")
    st.markdown(
        """<style>
        div.block-container { padding-top: 1rem; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0; }
        </style>""",
        unsafe_allow_html=True,
    )
    st.title("Retirement Calculator")

    if "mode" not in st.session_state:
        st.session_state.mode = "simulate"

    def set_mode(mode):
        st.session_state.mode = mode

    if st.session_state.mode == "simulate":
        top_col1, top_col2 = st.columns(2)
        with top_col1:
            budget_mode = st.radio(
                "Budget Mode",
                options=["Initial Monthly Budget ($)", "Annual Budget Rate (%)"],
                horizontal=False,
            )
        with top_col2:
            if budget_mode == "Annual Budget Rate (%)":
                use_pct_budget = True
                annual_reduction_rate = st.number_input(
                    "Annual Budget Rate (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=DEFAULT_VALUES["annual_reduction_rate"],
                )
                monthly_expenditure = DEFAULT_VALUES["monthly_expenditure"]
            else:
                use_pct_budget = False
                monthly_expenditure = st.number_input(
                    "Initial Monthly Budget ($)",
                    min_value=0.0,
                    value=DEFAULT_VALUES["monthly_expenditure"],
                    step=100.0,
                )
                annual_reduction_rate = DEFAULT_VALUES["annual_reduction_rate"]
    else:
        use_pct_budget = False
        monthly_expenditure = DEFAULT_VALUES["monthly_expenditure"]
        annual_reduction_rate = DEFAULT_VALUES["annual_reduction_rate"]

    with st.sidebar:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.button(
                "Simulate Retirement",
                use_container_width=True,
                type="primary" if st.session_state.mode == "simulate" else "secondary",
                on_click=set_mode,
                args=("simulate",),
            )
        with btn_col2:
            st.button(
                "Maximize Spend",
                use_container_width=True,
                type="primary" if st.session_state.mode == "maximize" else "secondary",
                on_click=set_mode,
                args=("maximize",),
            )
        start_age = st.number_input(
            "Current Age", min_value=0, max_value=120, value=DEFAULT_VALUES["start_age"]
        )
        retire_age = st.number_input(
            "Retirement Age",
            min_value=start_age,
            max_value=120,
            value=max(DEFAULT_VALUES["retire_age"], start_age),
        )
        max_age = st.number_input(
            "End of Life", min_value=1, max_value=130, value=DEFAULT_VALUES["max_age"]
        )
        if retire_age != start_age:
            annual_work_amount = st.number_input(
                "Annual Work Income ($)",
                min_value=0.0,
                value=DEFAULT_VALUES["annual_work_amount"],
                step=5000.0,
            )
        else:
            annual_work_amount = 0.0
        initial_amount = st.number_input(
            "Initial Investment ($)",
            min_value=0.0,
            value=DEFAULT_VALUES["initial_amount"],
            step=10000.0,
        )
        interest = st.number_input(
            "ROI (%)",
            min_value=0.0,
            max_value=100.0,
            value=DEFAULT_VALUES["interest_rate"],
        )
        inflation = st.number_input(
            "Inflation Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=DEFAULT_VALUES["inflation_rate"],
        )
        tax_rate = st.number_input(
            "Tax Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=DEFAULT_VALUES["tax_rate"],
        )
        start_soc_sec = st.number_input(
            "Social Security Age",
            min_value=start_age,
            max_value=120,
            value=max(DEFAULT_VALUES["start_soc_sec"], start_age),
        )
        soc_sec_payment = st.number_input(
            "Social Security Monthly Payment ($)",
            min_value=0.0,
            value=DEFAULT_VALUES["soc_sec_payment"],
            step=100.0,
        )

    inputs = {
        "start_age": float(start_age),
        "retire_age": float(retire_age),
        "start_soc_sec": float(start_soc_sec),
        "soc_sec_payment": float(soc_sec_payment),
        "initial_amount": float(initial_amount),
        "monthly_expenditure": float(monthly_expenditure),
        "annual_reduction_rate": float(annual_reduction_rate),
        "annual_work_amount": float(annual_work_amount),
        "interest": float(interest),
        "tax_rate": float(tax_rate),
        "inflation": float(inflation),
        "max_age": int(max_age),
        "use_pct_budget": use_pct_budget,
    }

    error = validate_inputs(inputs)
    if error:
        st.error(error)
        return

    if st.session_state.mode == "maximize":
        optimal_monthly = math.floor(
            binary_search(
                lambda v: funds_survive_to_max_age(v, *(
                    inputs["start_age"], inputs["retire_age"], inputs["start_soc_sec"],
                    inputs["soc_sec_payment"], inputs["initial_amount"],
                    inputs["annual_work_amount"], inputs["interest"],
                    inputs["tax_rate"], inputs["inflation"], inputs["max_age"],
                ), use_pct=False),
                0.0,
                inputs["initial_amount"] / MONTHS_PER_YEAR,
            )
        )
        optimal_rate = round(
            binary_search(
                lambda v: funds_survive_to_max_age(v, *(
                    inputs["start_age"], inputs["retire_age"], inputs["start_soc_sec"],
                    inputs["soc_sec_payment"], inputs["initial_amount"],
                    inputs["annual_work_amount"], inputs["interest"],
                    inputs["tax_rate"], inputs["inflation"], inputs["max_age"],
                ), use_pct=True),
                0.0,
                100.0,
            ),
            2,
        )
        st.info(f"Maximum Starting Monthly Budget: ${optimal_monthly:,}   |   Annual Budget Rate: {optimal_rate}%")
        inputs["monthly_expenditure"] = float(optimal_monthly)

    results = run_simulation(inputs)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Final Age", f"{results['final_age']}")
    c2.metric("Residual Amount", fmt_dollars(results["final_remaining"]))
    c3.metric("Total Spend", fmt_dollars(results["total_spend"]))
    c4.metric("Total Social Security", fmt_dollars(results["total_soc_sec"]))

    if results["final_age"] >= inputs["max_age"]:
        st.success(
            f"Funds not depleted. Simulation reached age {inputs['max_age']}."
        )
    else:
        st.warning(
            f"Funds depleted after {results['total_years']} years (age {results['final_age']}, year {results['final_year']})."
        )

    draw_chart(results["ages"], results["remaining_amounts"])

    with st.expander("Year-by-Year Detail", expanded=False):
        dollar_cols = {
            "annual_expenditure", "work_income_tax", "after_tax_work_income",
            "annual_soc_security", "annual_raw_gain", "annual_tax_loss",
            "annual_taxed_gain", "remaining", "annual_work_amount",
        }
        display_records = [
            {
                k: round(0 if k == "annual_work_amount" and not row["working"] else v)
                if k in dollar_cols else v
                for k, v in row.items()
            }
            for row in results["year_records"]
        ]
        st.dataframe(display_records, use_container_width=True)


if __name__ == "__main__":
    main()
