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


class PaymentBillPDF(FPDF):
    def header(self):
        self.set_fill_color(30, 64, 175)
        self.rect(0, 0, 210, 30, 'F')
        self.set_xy(10, 7)
        self.set_font('Helvetica', 'B', 17)
        self.set_text_color(255, 255, 255)
        self.cell(190, 8, 'KISAN SLOT - PAYMENT BILL', 0, 1, 'C')
        self.set_font('Helvetica', '', 10)
        self.cell(190, 6, 'Procurement Settlement and DBT Payment Statement', 0, 1, 'C')
        self.ln(7)

    def footer(self):
        self.set_y(-18)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(110, 110, 110)
        self.cell(0, 5, 'Computer-generated payment bill - no physical signature required.', 0, 1, 'C')
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
    pdf = PaymentBillPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    procurement = booking.procurement
    payment = booking.payment
    quantity = _number(getattr(procurement, 'actual_weight', None), _number(booking.expected_quantity))
    rate = _number(getattr(procurement, 'rate', None), 21.50)
    gross_amount = _number(getattr(procurement, 'total_amount', None), quantity * rate)
    paid_amount = _number(getattr(payment, 'amount', None), gross_amount)
    payment_status = 'PENDING'
    transaction_id = 'N/A'
    payment_date = 'N/A'
    if payment:
        payment_status = payment.status.value if hasattr(payment.status, 'value') else str(payment.status)
        transaction_id = payment.transaction_id or 'N/A'
        if payment.payment_date:
            payment_date = payment.payment_date.strftime('%Y-%m-%d %H:%M')

    centre_name = booking.centre.name if booking.centre else 'Procurement Centre'
    farmer_name = booking.farmer.name if booking.farmer else 'Farmer'
    farmer_code = booking.farmer.farmer_id if booking.farmer else 'N/A'

    pdf.set_text_color(30, 41, 59)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(120, 9, f'Bill No: PAY-{booking.booking_id}', 0, 0, 'L')
    pdf.set_fill_color(219, 234, 254)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(70, 9, f'STATUS: {payment_status}', 0, 1, 'C', fill=True)
    pdf.ln(4)

    pdf.set_fill_color(239, 246, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 64, 175)
    pdf.cell(190, 8, '  BOOKING AND FARMER DETAILS', 0, 1, 'L', fill=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(95, 7, f' Booking ID: {booking.booking_id}', 0, 0, 'L')
    pdf.cell(95, 7, f' Token: #{booking.token_number or "N/A"}', 0, 1, 'L')
    pdf.cell(95, 7, f' Farmer: {farmer_name}', 0, 0, 'L')
    pdf.cell(95, 7, f' Farmer ID: {farmer_code}', 0, 1, 'L')
    pdf.cell(95, 7, f' Centre: {centre_name}', 0, 0, 'L')
    pdf.cell(95, 7, f' Procurement Date: {booking.booking_date}', 0, 1, 'L')
    pdf.ln(5)

    pdf.set_fill_color(239, 246, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 64, 175)
    pdf.cell(190, 8, '  PAYMENT CALCULATION', 0, 1, 'L', fill=True)
    pdf.set_fill_color(226, 232, 240)
    pdf.set_text_color(30, 41, 59)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(55, 8, 'Crop', 1, 0, 'C', fill=True)
    pdf.cell(45, 8, 'Accepted Qty', 1, 0, 'C', fill=True)
    pdf.cell(45, 8, 'Rate / kg', 1, 0, 'C', fill=True)
    pdf.cell(45, 8, 'Gross Amount', 1, 1, 'C', fill=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(55, 9, str(booking.crop or 'N/A'), 1, 0, 'C')
    pdf.cell(45, 9, f'{quantity:,.3f} kg', 1, 0, 'C')
    pdf.cell(45, 9, f'Rs. {rate:,.2f}', 1, 0, 'C')
    pdf.cell(45, 9, f'Rs. {gross_amount:,.2f}', 1, 1, 'C')
    pdf.ln(4)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(140, 7, 'Deductions / Mandi Charges', 0, 0, 'R')
    pdf.cell(50, 7, 'Rs. 0.00', 0, 1, 'R')
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(30, 64, 175)
    pdf.cell(140, 9, 'NET PAYABLE', 0, 0, 'R')
    pdf.cell(50, 9, f'Rs. {paid_amount:,.2f}', 0, 1, 'R')
    pdf.ln(5)

    pdf.set_fill_color(239, 246, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(190, 8, '  DBT TRANSACTION DETAILS', 0, 1, 'L', fill=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(95, 8, f' Transaction Reference: {transaction_id}', 0, 0, 'L')
    pdf.cell(95, 8, f' Payment Date: {payment_date}', 0, 1, 'L')
    pdf.cell(95, 8, ' Payment Method: Direct Bank Transfer', 0, 0, 'L')
    pdf.cell(95, 8, f' Settlement Status: {payment_status}', 0, 1, 'L')

    return bytes(pdf.output())
