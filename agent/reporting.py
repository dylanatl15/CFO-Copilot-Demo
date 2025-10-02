import tempfile
from fpdf import FPDF
import pandas as pd
from . import tools, plotting

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Monthly Financial Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_chart(self, chart_path, width=190):
        self.image(chart_path, x=-5, w=width)
        self.ln(5)

def generate_pdf_report() -> bytes:
    """
    Generates a PDF report with key financial metrics.
    """
    # 1. Load Data
    actuals_df, budget_df, cash_df, fx_df = tools.load_data()

    # 2. Determine Latest Month
    latest_month_period = actuals_df['month_period'].max()
    latest_month_name = latest_month_period.strftime('%B')
    latest_year = latest_month_period.year

    # 3. Get Data for Reports
    rev_data = tools.get_revenue_vs_budget(actuals_df, budget_df, fx_df, latest_month_name, latest_year)
    opex_data = tools.get_opex_breakdown(actuals_df, fx_df, latest_month_name, latest_year)
    cash_trend_data = tools.get_cash_trend(cash_df, last_n_months=6)

    # 4. Generate Plots
    rev_chart = plotting.plot_revenue_vs_budget(rev_data['actual'], rev_data['budget'], latest_month_name, latest_year)
    opex_chart = plotting.plot_opex_breakdown(opex_data, latest_month_name, latest_year)
    cash_chart = plotting.plot_cash_trend(cash_trend_data)

    # 5. Save plots to temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as rev_img, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".png") as opex_img, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".png") as cash_img:
        
        rev_chart.write_image(rev_img.name)
        opex_chart.write_image(opex_img.name)
        cash_chart.write_image(cash_img.name)

        # 6. Create PDF
        pdf = PDF()
        pdf.set_auto_page_break(auto=False, margin=15)
        pdf.add_page()

        # Page 1: Revenue vs Budget
        pdf.chapter_title(f"Revenue vs. Budget - {latest_month_name} {latest_year}")
        actual_rev_m = rev_data['actual'] / 1_000_000
        budget_rev_m = rev_data['budget'] / 1_000_000
        variance_m = (rev_data['actual'] - rev_data['budget']) / 1_000_000
        rev_text = (
            f"- Actual Revenue: ${actual_rev_m:.2f}M\n"
            f"- Budgeted Revenue: ${budget_rev_m:.2f}M\n"
            f"- Variance: ${variance_m:.2f}M"
        )
        pdf.chapter_body(rev_text)
        pdf.add_chart(rev_img.name, width=150)

        # Opex Breakdown
        # A4 height is 297mm. A chart + title needs ~100mm. Check if we need a new page.
        if pdf.get_y() + 100 > 297 - 15:
            pdf.add_page()
        pdf.chapter_title(f"Opex Breakdown - {latest_month_name} {latest_year}")
        total_opex_m = opex_data['Amount (USD)'].sum() / 1_000_000
        opex_text = f"Total Opex for {latest_month_name} {latest_year} was ${total_opex_m:.2f}M."
        pdf.chapter_body(opex_text)
        pdf.add_chart(opex_img.name, width=120)

        # Cash Trend
        if pdf.get_y() + 100 > 297 - 15:
            pdf.add_page()
        pdf.chapter_title("Cash Balance Trend")
        pdf.add_chart(cash_img.name, width=150)

        return bytes(pdf.output(dest='S'))
