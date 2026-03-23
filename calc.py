"""
Retirement Calculator Application

A GUI application for simulating retirement scenarios including:
- Investment growth calculations
- Social Security benefits
- Tax implications
- Inflation adjustments
- Various budget planning options

Author: Bob Sheehan
Date: 2025
"""

import math
import sys
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime
from pathlib import Path
from typing import List
import matplotlib

matplotlib.use("TkAgg")  # Set backend before importing pyplot
import matplotlib.figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SS_TAXABLE_PCT = 0.85        # IRS rule: 85% of SS benefits are taxable
MONTHS_PER_YEAR = 12
BINARY_SEARCH_ITERATIONS = 50

DEFAULT_VALUES = {
    "start_age": "62",
    "retire_age": "62",
    "start_soc_sec": "62",
    "soc_sec_payment": "3000",
    "initial_amount": "1000000",
    "monthly_expenditure": "8000",
    "annual_reduction_rate": "4.0",
    "interest_rate": "5.0",
    "tax_rate": "18.0",
    "inflation_rate": "2.5",
    "annual_work_amount": "160000",
    "max_age": "95",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_dollars(value: float) -> str:
    """Format a dollar value rounded up to the nearest $1,000 with no cents."""
    return f"${math.ceil(value / 1000) * 1000:,.0f}"


def get_entry_value(entry, default_key):
    """Get value from entry widget, using default if empty."""
    value = entry.get().strip()
    if value:
        return float(value)
    return float(DEFAULT_VALUES[default_key])


def get_current_year():
    """Return the current year number."""
    return datetime.now().year


def get_all_inputs() -> dict:
    """Read all input fields and return as a dict. Raises ValueError on bad input."""
    return {
        "start_age":           get_entry_value(start_age_entry,          "start_age"),
        "retire_age":          get_entry_value(retire_age_entry,         "retire_age"),
        "start_soc_sec":       get_entry_value(start_soc_sec_entry,      "start_soc_sec"),
        "soc_sec_payment":     get_entry_value(soc_sec_payment_entry,    "soc_sec_payment"),
        "initial_amount":      get_entry_value(initial_amount_entry,     "initial_amount"),
        "monthly_expenditure": get_entry_value(monthly_expenditure_entry,"monthly_expenditure"),
        "annual_reduction_rate": get_entry_value(annual_reduction_entry, "annual_reduction_rate"),
        "annual_work_amount":  get_entry_value(annual_work_amount_entry, "annual_work_amount"),
        "interest":            get_entry_value(interest_entry,           "interest_rate"),
        "tax_rate":            get_entry_value(tax_rate_entry,           "tax_rate"),
        "inflation":           get_entry_value(inflation_entry,          "inflation_rate"),
        "max_age":             int(get_entry_value(max_age_entry,        "max_age")),
        "use_pct_budget":      budget_type_val.get() != 0,
    }


def validate_inputs(inputs: dict):
    """Return an error message string if inputs are invalid, else None."""
    if inputs["retire_age"] < inputs["start_age"]:
        return "Error: Retirement age must be >= current age."
    if inputs["start_soc_sec"] < inputs["start_age"]:
        return "Error: Social Security age must be >= current age."
    return None


def display_error(message: str):
    """Clear the detail pane and show an error message."""
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, message + "\n")

# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def calculate_year(remaining, current_age, soc_sec_monthly, annual_expenditure, inputs) -> dict:
    """
    Compute one year of retirement finances.
    Returns a dict with the updated balance and all intermediate values.
    """
    retire_age        = inputs["retire_age"]
    start_soc_sec     = inputs["start_soc_sec"]
    annual_work_amount = inputs["annual_work_amount"]
    interest          = inputs["interest"]
    tax_rate          = inputs["tax_rate"]

    work_income_tax = 0
    after_tax_work_income = 0
    working = current_age < retire_age
    if working:
        work_income_tax = annual_work_amount * (tax_rate / 100)
        after_tax_work_income = annual_work_amount - work_income_tax
        remaining += after_tax_work_income

    annual_raw_gain = remaining * (interest / 100)

    annual_soc_security = 0
    if current_age >= start_soc_sec:
        annual_soc_security = MONTHS_PER_YEAR * soc_sec_monthly

    annual_tax_loss = (
        (annual_raw_gain + annual_soc_security * SS_TAXABLE_PCT) * (tax_rate / 100)
        + work_income_tax
    )
    annual_taxed_gain = annual_soc_security + annual_raw_gain - annual_tax_loss
    remaining += annual_taxed_gain - annual_expenditure

    return {
        "remaining":            remaining,
        "annual_raw_gain":      annual_raw_gain,
        "annual_soc_security":  annual_soc_security,
        "annual_tax_loss":      annual_tax_loss,
        "annual_taxed_gain":    annual_taxed_gain,
        "work_income_tax":      work_income_tax,
        "after_tax_work_income": after_tax_work_income,
        "working":              working,
    }


def funds_survive_to_max_age(budget_value, start_age, retire_age, start_soc_sec,
                              soc_sec_payment, initial_amount, annual_work_amount,
                              interest, tax_rate, inflation, max_age, use_pct=False) -> bool:
    """Return True if funds last to max_age with the given budget value.
    budget_value is monthly dollars when use_pct=False, or annual % rate when use_pct=True.
    """
    # Build a minimal inputs dict for calculate_year
    inputs = {
        "retire_age": retire_age, "start_soc_sec": start_soc_sec,
        "annual_work_amount": annual_work_amount, "interest": interest, "tax_rate": tax_rate,
    }
    remaining = initial_amount
    soc_sec_monthly = soc_sec_payment
    annual_expenditure = (remaining * (budget_value / 100) if use_pct
                          else budget_value * MONTHS_PER_YEAR)
    current_age = start_age

    while remaining >= annual_expenditure and current_age < max_age:
        if use_pct:
            annual_expenditure = remaining * (budget_value / 100)
        year = calculate_year(remaining, current_age, soc_sec_monthly, annual_expenditure, inputs)
        remaining = year["remaining"]
        if not use_pct:
            annual_expenditure *= 1 + inflation / 100
        soc_sec_monthly *= 1 + inflation / 100
        current_age += 1

    return current_age >= max_age


def binary_search(test_fn, low: float, high: float,
                  iterations: int = BINARY_SEARCH_ITERATIONS) -> float:
    """Return the largest value in [low, high] for which test_fn returns True."""
    for _ in range(iterations):
        mid = (low + high) / 2
        if test_fn(mid):
            low = mid
        else:
            high = mid
    return low

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def run_simulation(inputs: dict) -> dict:
    """
    Pure calculation loop — no UI side effects.
    Returns a dict of results and per-year records for display and charting.
    """
    remaining      = inputs["initial_amount"]
    soc_sec_monthly = inputs["soc_sec_payment"]
    use_pct        = inputs["use_pct_budget"]
    annual_expenditure = (
        remaining * (inputs["annual_reduction_rate"] / 100) if use_pct
        else inputs["monthly_expenditure"] * MONTHS_PER_YEAR
    )

    current_age  = inputs["start_age"]
    current_year = get_current_year()
    total_years  = 0
    total_soc_sec = 0
    total_spend  = 0
    years_worked = 0
    ages: List[float] = []
    remaining_amounts: List[float] = []
    year_records = []

    while remaining >= annual_expenditure and current_age < inputs["max_age"]:
        if use_pct:
            annual_expenditure = remaining * (inputs["annual_reduction_rate"] / 100)

        spend_pct = (annual_expenditure / remaining) * 100
        ages.append(current_age)
        remaining_amounts.append(remaining)

        yr = calculate_year(remaining, current_age, soc_sec_monthly, annual_expenditure, inputs)
        remaining = yr["remaining"]

        total_spend   += annual_expenditure
        total_soc_sec += yr["annual_soc_security"]
        if yr["working"]:
            years_worked += 1

        year_records.append({
            "year":               current_year,
            "age":                current_age,
            "spend_pct":          spend_pct,
            "annual_expenditure": annual_expenditure,
            "annual_work_amount": inputs["annual_work_amount"],
            **{k: yr[k] for k in ("working", "work_income_tax", "after_tax_work_income",
                                   "annual_soc_security", "annual_raw_gain",
                                   "annual_tax_loss", "annual_taxed_gain")},
            "remaining":          remaining,
        })

        if not use_pct:
            annual_expenditure *= 1 + inputs["inflation"] / 100
        soc_sec_monthly *= 1 + inputs["inflation"] / 100
        total_years  += 1
        current_age  += 1
        current_year += 1

    return {
        "ages":             ages,
        "remaining_amounts": remaining_amounts,
        "year_records":     year_records,
        "total_years":      total_years,
        "total_soc_sec":    total_soc_sec,
        "total_spend":      total_spend,
        "years_worked":     years_worked,
        "final_age":        current_age,
        "final_year":       current_year,
        "final_remaining":  remaining,
    }


def display_results(inputs: dict, results: dict):
    """Update all UI text areas and output fields with simulation results."""
    result_text.delete(1.0, tk.END)
    summary_text.delete(1.0, tk.END)

    # --- Year-by-year detail ---
    for rec in results["year_records"]:
        if rec["working"]:
            result_text.insert(tk.END,
                f"Working Year: {rec['year']} Age: {rec['age']} "
                f"Gross: {fmt_dollars(rec['annual_work_amount'])} "
                f"Tax: {fmt_dollars(rec['work_income_tax'])} "
                f"Net: {fmt_dollars(rec['after_tax_work_income'])}\n")

        if rec["age"] >= inputs["retire_age"]:
            soc_sec_str = (f" Soc Sec: {fmt_dollars(rec['annual_soc_security'])}"
                           if rec["annual_soc_security"] > 0 else "")
            result_text.insert(tk.END,
                f"Year: {rec['year']} Age: {rec['age']}{soc_sec_str}"
                f" Monthly Spend: {fmt_dollars(rec['annual_expenditure'] / MONTHS_PER_YEAR)}"
                f" ({rec['spend_pct']:.1f}% of portfolio)\n")

        total_income = rec["annual_soc_security"] + rec["annual_raw_gain"]
        net_income   = rec["annual_taxed_gain"] - rec["annual_expenditure"]
        net_str = (fmt_dollars(net_income) if net_income > 0
                   else f"({fmt_dollars(abs(net_income))})")
        result_text.insert(tk.END,
            f"Remaining: {fmt_dollars(rec['remaining'])}, "
            f"Income: {fmt_dollars(total_income)} Tax: {fmt_dollars(rec['annual_tax_loss'])} "
            f"Spend: {fmt_dollars(rec['annual_expenditure'])} Net: {net_str}\n\n")
        result_text.yview_moveto(1.0)

    # --- Summary ---
    summary_text.insert(tk.END,
        f"Current Age: {inputs['start_age']}  |  Retire Age: {inputs['retire_age']}  |  "
        f"Soc. Sec. Age: {inputs['start_soc_sec']} ({fmt_dollars(inputs['soc_sec_payment'])}/mo)\n")
    summary_text.insert(tk.END,
        f"Initial Investment: {fmt_dollars(inputs['initial_amount'])}  |  ROI: {inputs['interest']}%  |  "
        f"Tax Rate: {inputs['tax_rate']}%  |  Inflation Rate: {inputs['inflation']}%\n")
    summary_text.insert(tk.END,
        f"Initial Monthly Budget: {fmt_dollars(inputs['monthly_expenditure'])}\n")

    if inputs["annual_work_amount"]:
        summary_text.insert(tk.END,
            f"Annual Work Income: {fmt_dollars(inputs['annual_work_amount'])}  |  "
            f"Years Worked: {results['years_worked']}\n")

    summary_text.insert(tk.END, "-" * 60 + "\n")

    if results["final_age"] >= inputs["max_age"]:
        summary_text.insert(tk.END,
            f"Funds not depleted — simulation stopped at age {inputs['max_age']}.\n")
    else:
        summary_text.insert(tk.END,
            f"Funds depleted after {results['total_years']} years  |  "
            f"Age: {results['final_age']}  |  Year: {results['final_year']}\n")

    summary_text.insert(tk.END, f"Total Social Security Earned: {fmt_dollars(results['total_soc_sec'])}\n")
    summary_text.insert(tk.END, f"Total Spend: {fmt_dollars(results['total_spend'])}\n")
    summary_text.insert(tk.END, f"Residual Amount: {fmt_dollars(results['final_remaining'])}\n")

    # --- Output fields ---
    for entry, value in [
        (remaining_entry,      fmt_dollars(results["final_remaining"])),
        (until_age_entry,      str(results["final_age"])),
        (total_spend_entry,    fmt_dollars(results["total_spend"])),
        (total_remaining_entry, fmt_dollars(results["final_remaining"])),
    ]:
        entry.delete(0, tk.END)
        entry.insert(0, value)


def simulate_retirement():
    """Orchestrate input reading, validation, simulation, and display."""
    try:
        inputs = get_all_inputs()
    except ValueError as e:
        display_error(f"Input error: {e}\nPlease enter valid numeric values.")
        return

    error = validate_inputs(inputs)
    if error:
        display_error(error)
        return

    results = run_simulation(inputs)
    display_results(inputs, results)
    plot_remaining_amount(results["ages"], results["remaining_amounts"])


def find_optimal_budget():
    """Binary search for the maximum budget where funds survive to max_age."""
    try:
        inputs = get_all_inputs()
    except ValueError as e:
        display_error(f"Input error: {e}\nPlease enter valid numeric values.")
        return

    use_pct = inputs["use_pct_budget"]
    survive_args = (
        inputs["start_age"], inputs["retire_age"], inputs["start_soc_sec"],
        inputs["soc_sec_payment"], inputs["initial_amount"], inputs["annual_work_amount"],
        inputs["interest"], inputs["tax_rate"], inputs["inflation"], inputs["max_age"],
    )

    if use_pct:
        optimal = round(binary_search(
            lambda v: funds_survive_to_max_age(v, *survive_args, use_pct=True),
            0.0, 100.0), 2)
        annual_reduction_entry.delete(0, tk.END)
        annual_reduction_entry.insert(0, str(optimal))
        annual_reduction_entry.config(bg="plum")
    else:
        optimal = math.floor(binary_search(
            lambda v: funds_survive_to_max_age(v, *survive_args, use_pct=False),
            0.0, inputs["initial_amount"] / MONTHS_PER_YEAR))
        monthly_expenditure_entry.delete(0, tk.END)
        monthly_expenditure_entry.insert(0, str(optimal))
        monthly_expenditure_entry.config(bg="plum")

    simulate_retirement()

# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

def plot_remaining_amount(ages: List[float], remaining_amounts: List[float]) -> None:
    """Draw remaining amount chart embedded in the main window."""
    try:
        chart_ax.clear()
        chart_ax.set_title("Remaining Amount vs Age")
        chart_ax.set_xlabel("Age")
        chart_ax.set_ylabel("Remaining Amount ($)")
        chart_ax.plot(ages, remaining_amounts, marker="o", label="Remaining Amount")
        chart_ax.grid(True)
        chart_ax.legend()
        chart_canvas.draw()
    except Exception as e:
        print(f"Warning: Could not display plot - {e}")

# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_inputs_to_json():
    """Save current input values to JSON file."""
    inputs = {
        "start_age":           start_age_entry.get(),
        "retire_age":          retire_age_entry.get(),
        "start_soc_sec":       start_soc_sec_entry.get(),
        "soc_sec_payment":     soc_sec_payment_entry.get(),
        "initial_amount":      initial_amount_entry.get(),
        "monthly_expenditure": monthly_expenditure_entry.get(),
        "annual_reduction_rate": annual_reduction_entry.get(),
        "interest_rate":       interest_entry.get(),
        "tax_rate":            tax_rate_entry.get(),
        "inflation_rate":      inflation_entry.get(),
        "annual_work_amount":  annual_work_amount_entry.get(),
        "max_age":             max_age_entry.get(),
    }
    with open(Path(sys.executable).parent / "inputs.json", "w") as json_file:
        json.dump(inputs, json_file, indent=2)
    print("Inputs saved to 'inputs.json'")


def load_inputs_from_json():
    """Load input values from JSON file or use defaults."""
    try:
        with open(Path(sys.executable).parent / "inputs.json", "r") as json_file:
            inputs = json.load(json_file)
        print("Inputs loaded from 'inputs.json'")
    except FileNotFoundError:
        print("No saved inputs found. Using default values.")
        inputs = DEFAULT_VALUES

    entry_mappings = [
        (start_age_entry,           "start_age"),
        (retire_age_entry,          "retire_age"),
        (start_soc_sec_entry,       "start_soc_sec"),
        (soc_sec_payment_entry,     "soc_sec_payment"),
        (initial_amount_entry,      "initial_amount"),
        (monthly_expenditure_entry, "monthly_expenditure"),
        (annual_reduction_entry,    "annual_reduction_rate"),
        (interest_entry,            "interest_rate"),
        (tax_rate_entry,            "tax_rate"),
        (inflation_entry,           "inflation_rate"),
        (annual_work_amount_entry,  "annual_work_amount"),
        (max_age_entry,             "max_age"),
    ]
    for entry, key in entry_mappings:
        entry.delete(0, tk.END)
        entry.insert(0, inputs.get(key, DEFAULT_VALUES[key]))


def toggle_reduction_state(entry1, entry2, var, *_):
    """Toggle between annual % and monthly $ budget entry states."""
    if var.get():
        entry1.config(state="normal")
        entry2.config(state="disabled")
        entry1.delete(0, tk.END)
        entry1.insert(0, DEFAULT_VALUES["annual_reduction_rate"])
    else:
        entry1.config(state="disabled")
        entry2.config(state="normal")

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def create_ui():
    """Create and configure the main user interface."""
    global root, summary_text, result_text, remaining_entry, until_age_entry
    global total_spend_entry, total_remaining_entry
    global start_age_entry, retire_age_entry, start_soc_sec_entry, soc_sec_payment_entry
    global initial_amount_entry, monthly_expenditure_entry, annual_reduction_entry
    global annual_work_amount_entry, interest_entry, tax_rate_entry, inflation_entry
    global max_age_entry, budget_type_val
    global chart_canvas, chart_ax

    root = tk.Tk()
    root.title("Retirement Simulator")

    # Main frames
    input_frame  = ttk.Frame(root)
    input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    button_frame = ttk.Frame(root)
    button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    output_frame = ttk.Frame(root)
    output_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    summary_frame = ttk.LabelFrame(root, text="Summary")
    summary_frame.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="nsew")

    detail_container = ttk.Frame(root)
    detail_container.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="nsew")

    chart_frame = ttk.LabelFrame(root, text="Portfolio Chart")
    chart_frame.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="nsew")

    # Collapsible year-by-year detail
    detail_toggle_btn = ttk.Button(detail_container, text="▶ Year-by-Year Detail")
    detail_toggle_btn.grid(row=0, column=0, sticky="w")
    console_frame = ttk.Frame(detail_container)

    def toggle_detail():
        if console_frame.winfo_ismapped():
            console_frame.grid_remove()
            detail_toggle_btn.config(text="▶ Year-by-Year Detail")
        else:
            console_frame.grid(row=1, column=0, sticky="nsew")
            detail_toggle_btn.config(text="▼ Year-by-Year Detail")

    detail_toggle_btn.config(command=toggle_detail)

    # Embedded chart
    fig = matplotlib.figure.Figure(figsize=(10, 4))
    chart_ax = fig.add_subplot(111)
    chart_canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    chart_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    # --- Input fields ---
    row = 0

    # Ages
    ttk.Label(input_frame, text="Current Age:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
    start_age_entry = ttk.Entry(input_frame)
    start_age_entry.grid(row=row, column=1, padx=5, pady=5)
    ttk.Label(input_frame, text="Retirement Age:").grid(row=row, column=2, padx=5, pady=5, sticky="e")
    retire_age_entry = ttk.Entry(input_frame)
    retire_age_entry.grid(row=row, column=3, padx=5, pady=5)
    row += 1

    # Social Security
    ttk.Label(input_frame, text="Social Security Age:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
    start_soc_sec_entry = ttk.Entry(input_frame)
    start_soc_sec_entry.grid(row=row, column=1, padx=5, pady=5)
    ttk.Label(input_frame, text="Social Security Payment ($):").grid(row=row, column=2, padx=5, pady=5, sticky="e")
    soc_sec_payment_entry = ttk.Entry(input_frame)
    soc_sec_payment_entry.grid(row=row, column=3, padx=5, pady=5)
    row += 1

    # Assets & Income
    ttk.Label(input_frame, text="Initial Investment ($):").grid(row=row, column=0, padx=5, pady=5, sticky="e")
    initial_amount_entry = ttk.Entry(input_frame)
    initial_amount_entry.grid(row=row, column=1, padx=5, pady=5)
    ttk.Label(input_frame, text="Annual Work Income ($):").grid(row=row, column=2, padx=5, pady=5, sticky="e")
    annual_work_amount_entry = ttk.Entry(input_frame)
    annual_work_amount_entry.grid(row=row, column=3, padx=5, pady=5)
    row += 1

    # Rates
    ttk.Label(input_frame, text="ROI (%):").grid(row=row, column=0, padx=5, pady=5, sticky="e")
    interest_entry = ttk.Entry(input_frame)
    interest_entry.grid(row=row, column=1, padx=5, pady=5)
    ttk.Label(input_frame, text="Tax Rate (%):").grid(row=row, column=2, padx=5, pady=5, sticky="e")
    tax_rate_entry = ttk.Entry(input_frame)
    tax_rate_entry.grid(row=row, column=3, padx=5, pady=5)
    row += 1

    ttk.Label(input_frame, text="Inflation Rate (%):").grid(row=row, column=0, padx=5, pady=5, sticky="e")
    inflation_entry = ttk.Entry(input_frame)
    inflation_entry.grid(row=row, column=1, padx=5, pady=5)
    ttk.Label(input_frame, text="Max Age:").grid(row=row, column=2, padx=5, pady=5, sticky="e")
    max_age_entry = ttk.Entry(input_frame)
    max_age_entry.grid(row=row, column=3, padx=5, pady=5)
    row += 1

    # Budget toggle
    budget_type_val = tk.IntVar(value=0)
    budget_type = tk.Checkbutton(
        input_frame,
        text="Use Annual % Budget (checked) / Monthly $ Budget (unchecked)",
        variable=budget_type_val,
    )
    budget_type.grid(row=row, column=0, columnspan=4, padx=5, pady=5, sticky="w")
    row += 1

    ttk.Label(input_frame, text="Annual Budget Rate (%):").grid(row=row, column=0, padx=5, pady=5, sticky="e")
    annual_reduction_entry = tk.Entry(input_frame)
    annual_reduction_entry.grid(row=row, column=1, padx=5, pady=5)
    annual_reduction_entry.config(state="disabled")
    _annual_default_bg = annual_reduction_entry.cget("bg")
    annual_reduction_entry.bind("<Key>", lambda _: annual_reduction_entry.config(bg=_annual_default_bg))
    budget_type.config(command=lambda: toggle_reduction_state(
        annual_reduction_entry, monthly_expenditure_entry, budget_type_val))

    ttk.Label(input_frame, text="Monthly Budget ($):").grid(row=row, column=2, padx=5, pady=5, sticky="e")
    monthly_expenditure_entry = tk.Entry(input_frame)
    monthly_expenditure_entry.grid(row=row, column=3, padx=5, pady=5)
    _monthly_default_bg = monthly_expenditure_entry.cget("bg")
    monthly_expenditure_entry.bind("<Key>", lambda _: monthly_expenditure_entry.config(bg=_monthly_default_bg))

    # Buttons
    ttk.Button(button_frame, text="Simulate Retirement", command=simulate_retirement).grid(
        row=0, column=0, padx=10, pady=10, sticky="w")
    ttk.Button(button_frame, text="Reset",          command=load_inputs_from_json).grid(
        row=0, column=1, padx=5,  pady=10, sticky="w")
    ttk.Button(button_frame, text="Save",           command=save_inputs_to_json).grid(
        row=0, column=2, padx=5,  pady=10, sticky="w")
    ttk.Button(button_frame, text="Optimal Budget", command=find_optimal_budget).grid(
        row=0, column=3, padx=5,  pady=10, sticky="w")

    # Output fields
    for col, (label, attr) in enumerate([
        ("Remaining:",   "remaining_entry"),
        ("Until Age:",   "until_age_entry"),
        ("Total Spend:", "total_spend_entry"),
    ]):
        ttk.Label(output_frame, text=label).grid(row=0, column=col * 2,     padx=5, pady=5, sticky="e")
        e = tk.Entry(output_frame, bg="lightgreen")
        e.grid(                                    row=0, column=col * 2 + 1, padx=5, pady=15)
        globals()[attr] = e

    # Summary area
    summary_text = tk.Text(summary_frame, height=8, width=100)
    summary_scrollbar = tk.Scrollbar(summary_frame, command=summary_text.yview)
    summary_text["yscrollcommand"] = summary_scrollbar.set
    summary_text.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
    summary_scrollbar.grid(row=0, column=1, sticky="ns")

    summary_fields_frame = ttk.Frame(summary_frame)
    summary_fields_frame.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=(4, 4))
    ttk.Label(summary_fields_frame, text="Total Remaining:").grid(row=0, column=0, padx=5, sticky="e")
    total_remaining_entry = ttk.Entry(summary_fields_frame)
    total_remaining_entry.grid(row=0, column=1, padx=5)

    # Year-by-year detail area
    result_text = tk.Text(console_frame, height=30, width=100)
    scrollbar = tk.Scrollbar(console_frame, command=result_text.yview)
    result_text["yscrollcommand"] = scrollbar.set
    result_text.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")


def main():
    """Main function to run the application."""
    create_ui()
    load_inputs_from_json()
    simulate_retirement()
    root.mainloop()


if __name__ == "__main__":
    main()
