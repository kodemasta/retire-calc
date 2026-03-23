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

# # Social Security payment amounts by age
# # TODO: Make this configurable input
# SOCIAL_SECURITY_PAYMENTS = {
#     0: 0,
#     62: 2534,
#     63: 2741,
#     64: 2967,
#     65: 3254,
#     66: 3541,
#     67: 3822,
#     68: 4099,
#     69: 4421,
#     70: 4789
# }

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


def funds_survive_to_max_age(budget_value, start_age, retire_age, start_soc_sec,
                              soc_sec_payment, initial_amount, annual_work_amount,
                              interest, tax_rate, inflation, max_age, use_pct=False):
    """Return True if funds last to max_age with the given budget value.
    budget_value is monthly dollars when use_pct=False, or annual % rate when use_pct=True.
    """
    remaining = initial_amount
    soc_sec_monthly = soc_sec_payment
    annual_expenditure = remaining * (budget_value / 100) if use_pct else budget_value * 12
    current_age = start_age

    while remaining >= annual_expenditure and current_age < max_age:
        if use_pct:
            annual_expenditure = remaining * (budget_value / 100)

        work_income_tax = 0
        if current_age < retire_age:
            work_income_tax = annual_work_amount * (tax_rate / 100)
            remaining += annual_work_amount - work_income_tax

        annual_raw_gain = remaining * (interest / 100)

        annual_soc_security = 0
        if current_age >= start_soc_sec:
            annual_soc_security = 12 * soc_sec_monthly

        annual_tax_loss = (annual_raw_gain + annual_soc_security * 0.85) * (
            tax_rate / 100
        ) + work_income_tax
        annual_taxed_gain = annual_soc_security + annual_raw_gain - annual_tax_loss

        remaining += annual_taxed_gain - annual_expenditure
        if not use_pct:
            annual_expenditure *= 1 + inflation / 100
        soc_sec_monthly *= 1 + inflation / 100
        current_age += 1

    return current_age >= max_age


def find_optimal_budget():
    """Binary search for the maximum monthly budget where funds survive to max_age."""
    try:
        start_age = get_entry_value(start_age_entry, "start_age")
        retire_age = get_entry_value(retire_age_entry, "retire_age")
        start_soc_sec = get_entry_value(start_soc_sec_entry, "start_soc_sec")
        soc_sec_payment = get_entry_value(soc_sec_payment_entry, "soc_sec_payment")
        initial_amount = get_entry_value(initial_amount_entry, "initial_amount")
        annual_work_amount = get_entry_value(annual_work_amount_entry, "annual_work_amount")
        interest = get_entry_value(interest_entry, "interest_rate")
        tax_rate = get_entry_value(tax_rate_entry, "tax_rate")
        inflation = get_entry_value(inflation_entry, "inflation_rate")
        max_age = get_entry_value(max_age_entry, "max_age")
    except ValueError as e:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"Input error: {e}\nPlease enter valid numeric values.\n")
        return

    use_pct = budget_type_val.get() != 0
    args = (start_age, retire_age, start_soc_sec, soc_sec_payment,
            initial_amount, annual_work_amount, interest, tax_rate, inflation, max_age)

    if use_pct:
        low, high = 0.0, 100.0
        for _ in range(50):
            mid = (low + high) / 2
            if funds_survive_to_max_age(mid, *args, use_pct=True):
                low = mid
            else:
                high = mid
        optimal_pct = round(low, 2)
        annual_reduction_entry.delete(0, tk.END)
        annual_reduction_entry.insert(0, str(optimal_pct))
        annual_reduction_entry.config(bg="plum")
    else:
        low, high = 0.0, initial_amount / 12
        for _ in range(50):
            mid = (low + high) / 2
            if funds_survive_to_max_age(mid, *args, use_pct=False):
                low = mid
            else:
                high = mid
        monthly_expenditure_entry.delete(0, tk.END)
        monthly_expenditure_entry.insert(0, str(math.floor(low)))
        monthly_expenditure_entry.config(bg="plum")

    simulate_retirement()


def simulate_retirement():
    """Main retirement simulation function."""
    # Get input values
    try:
        start_age = get_entry_value(start_age_entry, "start_age")
        retire_age = get_entry_value(retire_age_entry, "retire_age")
        start_soc_sec = get_entry_value(start_soc_sec_entry, "start_soc_sec")
        soc_sec_payment = get_entry_value(soc_sec_payment_entry, "soc_sec_payment")
        initial_amount = get_entry_value(initial_amount_entry, "initial_amount")
        monthly_expenditure = get_entry_value(
            monthly_expenditure_entry, "monthly_expenditure"
        )
        annual_reduction_rate = get_entry_value(
            annual_reduction_entry, "annual_reduction_rate"
        )
        annual_work_amount = get_entry_value(
            annual_work_amount_entry, "annual_work_amount"
        )
        interest = get_entry_value(interest_entry, "interest_rate")
        tax_rate = get_entry_value(tax_rate_entry, "tax_rate")
        inflation = get_entry_value(inflation_entry, "inflation_rate")
        max_age = int(get_entry_value(max_age_entry, "max_age"))
    except ValueError as e:
        result_text.delete(1.0, tk.END)
        result_text.insert(
            tk.END, f"Input error: {e}\nPlease enter valid numeric values.\n"
        )
        return

    if retire_age < start_age:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Error: Retirement age must be >= current age.\n")
        return
    if start_soc_sec < start_age:
        result_text.delete(1.0, tk.END)
        result_text.insert(
            tk.END, "Error: Social Security age must be >= current age.\n"
        )
        return

    remaining_amount = initial_amount
    soc_sec_monthly = soc_sec_payment
    initial_soc_sec_monthly = soc_sec_payment

    # Calculate initial annual expenditure based on budget type
    use_pct_budget = budget_type_val.get() != 0
    if use_pct_budget:
        annual_expenditure = remaining_amount * (annual_reduction_rate / 100)
    else:
        annual_expenditure = monthly_expenditure * 12

    # Initialize tracking variables
    total_years = 0
    total_soc_sec = 0
    total_spend = 0
    start_year = get_current_year()
    current_year = start_year
    current_age = start_age
    years_worked = 0

    # Data for plotting
    years = []
    ages = []
    remaining_amounts = []

    # Clear previous results
    result_text.delete(1.0, tk.END)
    summary_text.delete(1.0, tk.END)
    # Main simulation loop
    while remaining_amount >= annual_expenditure and current_age < max_age:
        if use_pct_budget:
            annual_expenditure = remaining_amount * (annual_reduction_rate / 100)

        spend_pct = (annual_expenditure / remaining_amount) * 100

        years.append(current_year)
        ages.append(current_age)
        remaining_amounts.append(remaining_amount)

        # Add work income if still working (taxed at flat rate)
        work_income_tax = 0
        if current_age < retire_age:
            work_income_tax = annual_work_amount * (tax_rate / 100)
            after_tax_work_income = annual_work_amount - work_income_tax
            remaining_amount += after_tax_work_income
            result_text.insert(
                tk.END,
                f"Working Year: {current_year} Age: {current_age} "
                f"Gross: {fmt_dollars(annual_work_amount)} "
                f"Tax: {fmt_dollars(work_income_tax)} "
                f"Net: {fmt_dollars(after_tax_work_income)}\n",
            )
            years_worked += 1

        # Calculate investment gains
        annual_raw_gain = remaining_amount * (interest / 100)

        # Calculate social security income
        annual_soc_security = 0
        if current_age >= start_soc_sec:
            annual_soc_security = 12 * soc_sec_monthly
            total_soc_sec += annual_soc_security

        # Calculate taxes (on gains, 85% of SS, and work income already taxed above)
        annual_tax_loss = (annual_raw_gain + annual_soc_security * 0.85) * (
            tax_rate / 100
        ) + work_income_tax
        annual_taxed_gain = annual_soc_security + annual_raw_gain - annual_tax_loss

        # Add gains to remaining amount
        remaining_amount += annual_taxed_gain

        # Subtract expenses
        remaining_amount -= annual_expenditure
        total_spend += annual_expenditure
        # Display yearly results
        total_income = annual_soc_security + annual_raw_gain
        net_income = annual_taxed_gain - annual_expenditure

        if current_age >= retire_age:
            soc_sec_str = f" Soc Sec: {fmt_dollars(annual_soc_security)}" if annual_soc_security > 0 else ""
            result_text.insert(
                tk.END,
                f"Year: {current_year} Age: {current_age}{soc_sec_str}"
                f" Monthly Spend: {fmt_dollars(annual_expenditure / 12)} ({spend_pct:.1f}% of portfolio)\n",
            )

        if net_income > 0:
            result_text.insert(
                tk.END,
                f"Remaining: {fmt_dollars(remaining_amount)}, "
                f"Income: {fmt_dollars(total_income)} Tax: {fmt_dollars(annual_tax_loss)} "
                f"Spend: {fmt_dollars(annual_expenditure)} Net: {fmt_dollars(net_income)}\n\n",
            )
        else:
            result_text.insert(
                tk.END,
                f"Remaining: {fmt_dollars(remaining_amount)}, "
                f"Income: {fmt_dollars(total_income)} Tax: {fmt_dollars(annual_tax_loss)} "
                f"Spend: {fmt_dollars(annual_expenditure)} Net: ({fmt_dollars(abs(net_income))})\n\n",
            )

        # Adjust for inflation (fixed-dollar mode only; % mode recalculates each year)
        if not use_pct_budget:
            annual_expenditure *= 1 + inflation / 100

        soc_sec_monthly *= 1 + inflation / 100

        # Update counters
        total_years += 1
        current_age += 1
        current_year += 1

        result_text.yview_moveto(1.0)

    summary_text.insert(
        tk.END,
        f"Current Age: {start_age}  |  Retire Age: {retire_age}  |  "
        f"Soc. Sec. Age: {start_soc_sec} ({fmt_dollars(initial_soc_sec_monthly)}/mo)\n",
    )
    summary_text.insert(
        tk.END,
        f"Initial Investment: {fmt_dollars(initial_amount)}  |  ROI: {interest}%  |  "
        f"Tax Rate: {tax_rate}%  |  Inflation Rate: {inflation}%\n",
    )
    summary_text.insert(
        tk.END, f"Initial Monthly Budget: {fmt_dollars(monthly_expenditure)}\n"
    )

    if annual_work_amount:
        summary_text.insert(
            tk.END,
            f"Annual Work Income: {fmt_dollars(annual_work_amount)}  |  "
            f"Years Worked: {years_worked}\n",
        )

    summary_text.insert(tk.END, "-" * 60 + "\n")

    if current_age >= max_age:
        summary_text.insert(
            tk.END, f"Funds not depleted — simulation stopped at age {max_age}.\n"
        )
    else:
        summary_text.insert(
            tk.END,
            f"Funds depleted after {total_years} years  |  "
            f"Age: {current_age}  |  Year: {current_year}\n",
        )

    summary_text.insert(
        tk.END, f"Total Social Security Earned: {fmt_dollars(total_soc_sec)}\n"
    )
    summary_text.insert(tk.END, f"Total Spend: {fmt_dollars(total_spend)}\n")
    summary_text.insert(tk.END, f"Residual Amount: {fmt_dollars(remaining_amount)}\n")

    # Update output fields
    remaining_entry.delete(0, tk.END)
    remaining_entry.insert(0, fmt_dollars(remaining_amount))
    until_age_entry.delete(0, tk.END)
    until_age_entry.insert(0, f"{current_age}")
    total_spend_entry.delete(0, tk.END)
    total_spend_entry.insert(0, fmt_dollars(total_spend))
    total_remaining_entry.delete(0, tk.END)
    total_remaining_entry.insert(0, fmt_dollars(remaining_amount))



    # Plot the data and display summary
    plot_remaining_amount(ages, remaining_amounts)


def plot_remaining_amount(years: List[int], remaining_amounts: List[float]) -> None:
    """Draw remaining amount chart embedded in the main window."""
    try:
        chart_ax.clear()
        chart_ax.set_title("Remaining Amount vs Age")
        chart_ax.set_xlabel("Age")
        chart_ax.set_ylabel("Remaining Amount ($)")
        chart_ax.plot(years, remaining_amounts, marker="o", label="Remaining Amount")
        chart_ax.grid(True)
        chart_ax.legend()
        chart_canvas.draw()
    except Exception as e:
        print(f"Warning: Could not display plot - {e}")


def save_inputs_to_json():
    """Save current input values to JSON file."""
    inputs = {
        "start_age": start_age_entry.get(),
        "retire_age": retire_age_entry.get(),
        "start_soc_sec": start_soc_sec_entry.get(),
        "soc_sec_payment": soc_sec_payment_entry.get(),
        "initial_amount": initial_amount_entry.get(),
        "monthly_expenditure": monthly_expenditure_entry.get(),
        "annual_reduction_rate": annual_reduction_entry.get(),
        "interest_rate": interest_entry.get(),
        "tax_rate": tax_rate_entry.get(),
        "inflation_rate": inflation_entry.get(),
        "annual_work_amount": annual_work_amount_entry.get(),
        "max_age": max_age_entry.get(),
    }
    with open(Path(__file__).parent / "inputs.json", "w") as json_file:
        json.dump(inputs, json_file, indent=2)
    print("Inputs saved to 'inputs.json'")


def load_inputs_from_json():
    """Load input values from JSON file or use defaults."""
    try:
        with open(Path(__file__).parent / "inputs.json", "r") as json_file:
            inputs = json.load(json_file)
        print("Inputs loaded from 'inputs.json'")
    except FileNotFoundError:
        print("No saved inputs found. Using default values.")
        inputs = DEFAULT_VALUES

    # Update entry fields with loaded data
    entry_mappings = [
        (start_age_entry, "start_age"),
        (retire_age_entry, "retire_age"),
        (start_soc_sec_entry, "start_soc_sec"),
        (soc_sec_payment_entry, "soc_sec_payment"),
        (initial_amount_entry, "initial_amount"),
        (monthly_expenditure_entry, "monthly_expenditure"),
        (annual_reduction_entry, "annual_reduction_rate"),
        (interest_entry, "interest_rate"),
        (tax_rate_entry, "tax_rate"),
        (inflation_entry, "inflation_rate"),
        (annual_work_amount_entry, "annual_work_amount"),
        (max_age_entry, "max_age"),
    ]

    for entry, key in entry_mappings:
        entry.delete(0, tk.END)
        entry.insert(0, inputs.get(key, DEFAULT_VALUES[key]))


def toggle_reduction_state(entry1, entry2, var, *_):
    """Toggle between annual and monthly budget entry states."""
    if var.get():  # Annual budget type selected
        entry1.config(state="normal")
        entry2.config(state="disabled")
        entry1.delete(0, tk.END)
        entry1.insert(0, DEFAULT_VALUES["annual_reduction_rate"])
    else:  # Monthly budget type selected
        entry1.config(state="disabled")
        entry2.config(state="normal")


def create_ui():
    """Create and configure the main user interface."""
    global root, summary_text, result_text, remaining_entry, until_age_entry, total_spend_entry, total_remaining_entry
    global start_age_entry, retire_age_entry, start_soc_sec_entry, soc_sec_payment_entry
    global initial_amount_entry, monthly_expenditure_entry, annual_reduction_entry
    global annual_work_amount_entry, interest_entry, tax_rate_entry, inflation_entry
    global max_age_entry, budget_type_val
    global chart_canvas, chart_ax

    root = tk.Tk()
    root.title("Retirement Simulator")

    # Create main frames
    input_frame = ttk.Frame(root)
    input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    button_frame = ttk.Frame(root)
    button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    summary_frame = ttk.LabelFrame(root, text="Summary")
    summary_frame.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="nsew")

    detail_container = ttk.Frame(root)
    detail_container.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="nsew")

    detail_toggle_btn = ttk.Button(detail_container, text="▶ Year-by-Year Detail")
    detail_toggle_btn.grid(row=0, column=0, sticky="w")

    console_frame = ttk.Frame(detail_container)
    # collapsed by default — not gridded yet

    def toggle_detail():
        if console_frame.winfo_ismapped():
            console_frame.grid_remove()
            detail_toggle_btn.config(text="▶ Year-by-Year Detail")
        else:
            console_frame.grid(row=1, column=0, sticky="nsew")
            detail_toggle_btn.config(text="▼ Year-by-Year Detail")

    detail_toggle_btn.config(command=toggle_detail)

    chart_frame = ttk.LabelFrame(root, text="Portfolio Chart")
    chart_frame.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="nsew")
    fig = matplotlib.figure.Figure(figsize=(10, 4))
    chart_ax = fig.add_subplot(111)
    chart_canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    chart_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    output_frame = ttk.Frame(root)
    output_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    # Create input fields
    row = 0

    # --- Ages ---
    ttk.Label(input_frame, text="Current Age:").grid(
        row=row, column=0, padx=5, pady=5, sticky="e"
    )
    start_age_entry = ttk.Entry(input_frame)
    start_age_entry.grid(row=row, column=1, padx=5, pady=5)
    ttk.Label(input_frame, text="Retirement Age:").grid(
        row=row, column=2, padx=5, pady=5, sticky="e"
    )
    retire_age_entry = ttk.Entry(input_frame)
    retire_age_entry.grid(row=row, column=3, padx=5, pady=5)
    row += 1

    # --- Social Security ---
    ttk.Label(input_frame, text="Social Security Age:").grid(
        row=row, column=0, padx=5, pady=5, sticky="e"
    )
    start_soc_sec_entry = ttk.Entry(input_frame)
    start_soc_sec_entry.grid(row=row, column=1, padx=5, pady=5)
    ttk.Label(input_frame, text="Social Security Payment ($):").grid(
        row=row, column=2, padx=5, pady=5, sticky="e"
    )
    soc_sec_payment_entry = ttk.Entry(input_frame)
    soc_sec_payment_entry.grid(row=row, column=3, padx=5, pady=5)
    row += 1

    # --- Assets & Income ---
    ttk.Label(input_frame, text="Initial Investment ($):").grid(
        row=row, column=0, padx=5, pady=5, sticky="e"
    )
    initial_amount_entry = ttk.Entry(input_frame)
    initial_amount_entry.grid(row=row, column=1, padx=5, pady=5)
    ttk.Label(input_frame, text="Annual Work Income ($):").grid(
        row=row, column=2, padx=5, pady=5, sticky="e"
    )
    annual_work_amount_entry = ttk.Entry(input_frame)
    annual_work_amount_entry.grid(row=row, column=3, padx=5, pady=5)
    row += 1

    # --- Rates ---
    ttk.Label(input_frame, text="ROI (%):").grid(
        row=row, column=0, padx=5, pady=5, sticky="e"
    )
    interest_entry = ttk.Entry(input_frame)
    interest_entry.grid(row=row, column=1, padx=5, pady=5)
    ttk.Label(input_frame, text="Tax Rate (%):").grid(
        row=row, column=2, padx=5, pady=5, sticky="e"
    )
    tax_rate_entry = ttk.Entry(input_frame)
    tax_rate_entry.grid(row=row, column=3, padx=5, pady=5)
    row += 1

    ttk.Label(input_frame, text="Inflation Rate (%):").grid(
        row=row, column=0, padx=5, pady=5, sticky="e"
    )
    inflation_entry = ttk.Entry(input_frame)
    inflation_entry.grid(row=row, column=1, padx=5, pady=5)
    ttk.Label(input_frame, text="Max Age:").grid(
        row=row, column=2, padx=5, pady=5, sticky="e"
    )
    max_age_entry = ttk.Entry(input_frame)
    max_age_entry.grid(row=row, column=3, padx=5, pady=5)
    row += 1

    # --- Budget ---
    budget_type_val = tk.IntVar(value=0)
    budget_type = tk.Checkbutton(
        input_frame,
        text="Use Annual % Budget (checked) / Monthly $ Budget (unchecked)",
        variable=budget_type_val,
    )
    budget_type.grid(row=row, column=0, columnspan=4, padx=5, pady=5, sticky="w")
    row += 1

    ttk.Label(input_frame, text="Annual Budget Rate (%):").grid(
        row=row, column=0, padx=5, pady=5, sticky="e"
    )
    annual_reduction_entry = tk.Entry(input_frame)
    annual_reduction_entry.grid(row=row, column=1, padx=5, pady=5)
    annual_reduction_entry.config(state="disabled")
    _annual_default_bg = annual_reduction_entry.cget("bg")
    annual_reduction_entry.bind("<Key>", lambda _: annual_reduction_entry.config(bg=_annual_default_bg))
    budget_type.config(
        command=lambda: toggle_reduction_state(
            annual_reduction_entry, monthly_expenditure_entry, budget_type_val
        )
    )
    ttk.Label(input_frame, text="Monthly Budget ($):").grid(
        row=row, column=2, padx=5, pady=5, sticky="e"
    )
    monthly_expenditure_entry = tk.Entry(input_frame)
    monthly_expenditure_entry.grid(row=row, column=3, padx=5, pady=5)
    _monthly_default_bg = monthly_expenditure_entry.cget("bg")
    monthly_expenditure_entry.bind("<Key>", lambda _: monthly_expenditure_entry.config(bg=_monthly_default_bg))

    # Buttons
    ttk.Button(
        button_frame, text="Simulate Retirement", command=simulate_retirement
    ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
    ttk.Button(button_frame, text="Reset", command=load_inputs_from_json).grid(
        row=0, column=1, padx=5, pady=10, sticky="w"
    )
    ttk.Button(button_frame, text="Save", command=save_inputs_to_json).grid(
        row=0, column=2, padx=5, pady=10, sticky="w"
    )
    ttk.Button(button_frame, text="Optimal Budget", command=find_optimal_budget).grid(
        row=0, column=3, padx=5, pady=10, sticky="w"
    )

    # Summary text area
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

    # Year-by-year detail text area
    result_text = tk.Text(console_frame, height=30, width=100)
    scrollbar = tk.Scrollbar(console_frame, command=result_text.yview)
    result_text["yscrollcommand"] = scrollbar.set
    result_text.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    # Output fields
    ttk.Label(output_frame, text="Remaining:").grid(
        row=0, column=0, padx=5, pady=5, sticky="e"
    )
    remaining_entry = tk.Entry(output_frame, bg="lightgreen")
    remaining_entry.grid(row=0, column=1, padx=5, pady=15)

    ttk.Label(output_frame, text="Until Age:").grid(
        row=0, column=2, padx=5, pady=5, sticky="e"
    )
    until_age_entry = tk.Entry(output_frame, bg="lightgreen")
    until_age_entry.grid(row=0, column=3, padx=5, pady=15)

    ttk.Label(output_frame, text="Total Spend:").grid(
        row=0, column=4, padx=5, pady=5, sticky="e"
    )
    total_spend_entry = tk.Entry(output_frame, bg="lightgreen")
    total_spend_entry.grid(row=0, column=5, padx=5, pady=15)


def main():
    """Main function to run the application."""
    create_ui()
    load_inputs_from_json()
    simulate_retirement()
    root.mainloop()


if __name__ == "__main__":
    main()
