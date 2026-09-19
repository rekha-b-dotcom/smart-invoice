import json
import pandas as pd
import streamlit as st
from fpdf import FPDF

# ==========================================
# 1. SAMPLE DATA SETUP (Price Sheet)
# ==========================================
# Replace this dictionary with your Google Sheet / CSV data as needed.
PRICE_LIST = {
    "website design": 500.0,
    "logo design": 150.0,
    "seo audit": 200.0,
    "blog post": 75.0,
    "social media post": 30.0,
}


# ==========================================
# 2. PDF GENERATOR HELPER (fpdf2 Compatible)
# ==========================================
def generate_pdf(customer_name, email, items, grand_total):
    pdf = FPDF()
    pdf.add_page()

    # Header
    pdf.set_font("Helvetica", style="B", size=20)
    pdf.cell(0, 10, txt="INVOICE", ln=True, align="C")
    pdf.ln(10)

    # Customer Details
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 7, txt=f"Customer Name: {customer_name}", ln=True)
    pdf.cell(0, 7, txt=f"Email: {email}", ln=True)
    pdf.ln(8)

    # Table Header
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(90, 8, "Item / Service", border=1)
    pdf.cell(25, 8, "Qty", border=1, align="C")
    pdf.cell(35, 8, "Unit Price ($)", border=1, align="R")
    pdf.cell(35, 8, "Total ($)", border=1, align="R")
    pdf.ln()

    # Table Body
    pdf.set_font("Helvetica", size=10)
    for item in items:
        pdf.cell(90, 8, str(item["Service"]), border=1)
        pdf.cell(25, 8, str(item["Quantity"]), border=1, align="C")
        pdf.cell(35, 8, f"{item['Unit Price']:.2f}", border=1, align="R")
        pdf.cell(35, 8, f"{item['Total']:.2f}", border=1, align="R")
        pdf.ln()

    # Grand Total
    pdf.ln(5)
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(150, 10, "Grand Total:", align="R")
    pdf.cell(35, 10, f"${grand_total:.2f}", align="R")

    # Return pure bytes for Streamlit download button
    return bytes(pdf.output())


# ==========================================
# 3. STREAMLIT APP UI
# ==========================================
st.set_page_config(page_title="Smart Invoice Generator", page_icon="🧾", layout="wide")

st.title("🧾 Smart Invoice Generator")
st.caption("AI-powered invoice extractor with price lookup & PDF export")

st.sidebar.header("📋 Reference Price List")
st.sidebar.dataframe(
    pd.DataFrame(list(PRICE_LIST.items()), columns=["Service", "Unit Price ($)"]),
    use_container_width=True,
)

# Step 1: Input Customer Request
st.subheader("1. Enter Customer Request")
default_text = "Hi! I'm Sarah Miller (sarah@example.com). I need 1 Logo Design and 2 Blog Posts written for my website."
customer_text = st.text_area("Customer Message:", value=default_text, height=100)

if st.button("🤖 Process with AI & Lookup Prices", type="primary"):
    # Mock AI Extraction (Simulated for instant testing)
    # Replace this block with your Groq/OpenAI/Gemini API call if active
    extracted_data = {
        "customer_name": "Sarah Miller",
        "email": "sarah@example.com",
        "items": [
            {"service": "Logo Design", "quantity": 1},
            {"service": "Blog Post", "quantity": 2},
        ],
    }

    # Match extracted services against Price Sheet
    matched_items = []
    for line in extracted_data["items"]:
        service_name = line["service"]
        qty = int(line["quantity"])
        lookup_key = service_name.lower().strip()

        unit_price = PRICE_LIST.get(lookup_key, 0.0)
        line_total = unit_price * qty

        matched_items.append(
            {
                "Service": service_name,
                "Quantity": qty,
                "Unit Price": unit_price,
                "Total": line_total,
            }
        )

    # Save to session state so review/download persists on click
    st.session_state["customer_name"] = extracted_data["customer_name"]
    st.session_state["email"] = extracted_data["email"]
    st.session_state["items_df"] = pd.DataFrame(matched_items)
    st.success("Extraction and price matching completed!")


# Step 2: Review & Approve Invoice
if "items_df" in st.session_state:
    st.divider()
    st.subheader("2. Review & Edit Invoice Details")

    col1, col2 = st.columns(2)
    with col1:
        cust_name = st.text_input("Customer Name", value=st.session_state["customer_name"])
    with col2:
        cust_email = st.text_input("Customer Email", value=st.session_state["email"])

    st.write("Edit line items or prices directly in the table below:")
    edited_df = st.data_editor(
        st.session_state["items_df"],
        num_rows="dynamic",
        column_config={
            "Quantity": st.column_config.NumberColumn(min_value=1, step=1),
            "Unit Price": st.column_config.NumberColumn(format="$%.2f"),
            "Total": st.column_config.NumberColumn(format="$%.2f"),
        },
        use_container_width=True,
    )

    # Recalculate Totals
    edited_df["Total"] = edited_df["Quantity"] * edited_df["Unit Price"]
    grand_total = float(edited_df["Total"].sum())

    st.metric(label="Grand Total", value=f"${grand_total:.2f}")

    # Step 3: Export PDF
    st.divider()
    st.subheader("3. Export Invoice")

    items_list = edited_df.to_dict(orient="records")
    pdf_bytes = generate_pdf(cust_name, cust_email, items_list, grand_total)

    st.download_button(
        label="📄 Download Invoice PDF",
        data=pdf_bytes,
        file_name=f"Invoice_{cust_name.replace(' ', '_')}.pdf",
        mime="application/pdf",
        type="primary",
    )