from fpdf import FPDF
from datetime import datetime

class JFormPDF(FPDF):
    def header(self):
        # Header banner
        self.set_fill_color(11, 61, 46) # #0B3D2E Dark Green
        self.rect(0, 0, 210, 28, 'F')
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 6)
        self.cell(190, 8, 'KISAN SLOT - MANDI J-FORM (FORM J)', 0, 1, 'C')
        self.set_font('Helvetica', '', 10)
        self.cell(190, 6, 'Official Agricultural Produce Sale & Payment Receipt', 0, 1, 'C')
        self.ln(6)

    def footer(self):
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, 'This is a computer-generated Mandi J-Form Receipt under Kisan Slot Procurement System.', 0, 1, 'C')
        self.cell(0, 5, f'Page {self.page_no()}', 0, 0, 'C')

def _number(value, fallback=0.0) -> float:
    try:
        return float(value) if value is not None else fallback
    except (TypeError, ValueError):
        return fallback


def generate_jform_pdf(booking, document_title='J-FORM RECEIPT') -> bytes:
    pdf = JFormPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # Title Section
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(11, 61, 46)
    reference_prefix = 'JFORM' if document_title == 'J-FORM RECEIPT' else 'BILL'
    pdf.cell(190, 8, f'{document_title}: {reference_prefix}-{booking.booking_id}', 0, 1, 'L')
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(80, 80, 80)
    date_str = str(booking.booking_date) if booking.booking_date else datetime.utcnow().strftime('%Y-%m-%d')
    pdf.cell(190, 6, f'Date of Issue: {date_str}  |  Token No: #{booking.token_number or "N/A"}', 0, 1, 'L')
    pdf.ln(4)

    # 1. Centre & Government Details
    pdf.set_fill_color(240, 244, 241)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(11, 61, 46)
    pdf.cell(190, 7, '  1. PROCUREMENT CENTRE DETAILS', 0, 1, 'L', fill=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(40, 40, 40)
    
    centre_name = booking.centre.name if booking.centre else "Procurement Centre"
    district = booking.centre.district if booking.centre else "N/A"
    state = booking.centre.state if booking.centre else "N/A"
    
    pdf.cell(95, 6, f' Centre Name: {centre_name}', 0, 0, 'L')
    pdf.cell(95, 6, f' District: {district}, {state}', 0, 1, 'L')
    pdf.cell(190, 6, f' Operating Code: CENTRE-{booking.centre_id}', 0, 1, 'L')
    pdf.ln(4)

    # 2. Farmer Details
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(11, 61, 46)
    pdf.cell(190, 7, '  2. FARMER INFORMATION', 0, 1, 'L', fill=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(40, 40, 40)
    
    farmer_name = booking.farmer.name if booking.farmer else "Farmer"
    farmer_id = booking.farmer.farmer_id if booking.farmer else "N/A"
    farmer_mobile = booking.farmer.mobile if booking.farmer else "N/A"
    village = booking.farmer.village if booking.farmer else "N/A"

    pdf.cell(95, 6, f' Farmer Name: {farmer_name}', 0, 0, 'L')
    pdf.cell(95, 6, f' Farmer ID: {farmer_id}', 0, 1, 'L')
    pdf.cell(95, 6, f' Mobile No: {farmer_mobile}', 0, 0, 'L')
    pdf.cell(95, 6, f' Village/Location: {village}', 0, 1, 'L')
    pdf.ln(4)

    # 3. Produce & Procurement Breakdown
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(11, 61, 46)
    pdf.cell(190, 7, '  3. PRODUCE & WEIGHMENT DETAILS', 0, 1, 'L', fill=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(40, 40, 40)

    crop = booking.crop or "Paddy"
    qty = _number(booking.expected_quantity)
    moisture = "N/A"
    grade = "Grade A Standard"
    rate = 21.50

    if booking.procurement:
        qty = _number(booking.procurement.actual_weight, qty)
        grade = booking.procurement.quality_status or grade
        rate = _number(booking.procurement.rate, rate)

    pdf.cell(95, 6, f' Commodity / Crop: {crop}', 0, 0, 'L')
    pdf.cell(95, 6, f' Verified Weight: {qty:,.3f} kg', 0, 1, 'L')
    pdf.cell(95, 6, f' Quality Grade: {grade}', 0, 0, 'L')
    pdf.cell(95, 6, f' Moisture Content: {moisture}', 0, 1, 'L')
    pdf.cell(95, 6, f' Procurement Rate: Rs. {rate:,.2f} / kg', 0, 1, 'L')
    pdf.ln(4)

    # 4. Payment & Settlement Summary
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(11, 61, 46)
    pdf.cell(190, 7, '  4. PAYMENT & DIRECT BENEFIT TRANSFER (DBT) SUMMARY', 0, 1, 'L', fill=True)
    
    total_val = _number(getattr(booking.procurement, 'total_amount', None), qty * rate) if booking.procurement else qty * rate
    pay_status = "PENDING"
    txn_id = "N/A"
    pay_date = "N/A"

    if booking.payment:
        total_val = _number(booking.payment.amount, total_val)
        pay_status = booking.payment.status.value if hasattr(booking.payment.status, 'value') else str(booking.payment.status)
        txn_id = booking.payment.transaction_id or "N/A"
        if booking.payment.payment_date:
            pay_date = booking.payment.payment_date.strftime('%Y-%m-%d %H:%M')

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(95, 6, f' Gross Payable Amount: Rs. {total_val:,.2f}', 0, 0, 'L')
    pdf.cell(95, 6, f' Payment Status: {pay_status}', 0, 1, 'L')
    pdf.cell(95, 6, f' Transaction Ref (UTR): {txn_id}', 0, 0, 'L')
    pdf.cell(95, 6, f' Transfer Date: {pay_date}', 0, 1, 'L')
    pdf.ln(6)

    # Signature Block
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(11, 61, 46)
    pdf.cell(95, 15, '_________________________\nFarmer Signature', 0, 0, 'C')
    pdf.cell(95, 15, '_________________________\nCentre Officer Seal & Sign', 0, 1, 'C')

    return bytes(pdf.output())

def generate_bill_pdf(booking) -> bytes:
    return generate_jform_pdf(booking, document_title='PROCUREMENT PAYMENT BILL')
