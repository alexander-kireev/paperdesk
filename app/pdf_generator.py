from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.portfolio.portfolio_service import get_portfolio
from app.user.user_service import get_user


NAVY = colors.HexColor("#172033")
STEEL = colors.HexColor("#466A8F")
GREEN = colors.HexColor("#2F6B57")
GREEN_SOFT = colors.HexColor("#E7F1ED")
BURGUNDY = colors.HexColor("#934B4B")
BURGUNDY_SOFT = colors.HexColor("#F6EAEA")
INK = colors.HexColor("#182230")
MUTED = colors.HexColor("#667085")
LINE = colors.HexColor("#D6DCE5")
SURFACE_MUTED = colors.HexColor("#E7ECF2")
TABLE_STRIPE = colors.HexColor("#F7F9FB")


class PaperDeskLogo(Flowable):
    """Small vector wordmark used in report headers."""

    def __init__(self):
        super().__init__()
        self.width = 47 * mm
        self.height = 12 * mm

    def draw(self):
        self.canv.setFillColor(NAVY)
        self.canv.roundRect(0, 0, 11 * mm, 11 * mm, 2.4 * mm, fill=1, stroke=0)

        icon_scale = (11 * mm) / 120
        self.canv.saveState()
        self.canv.translate(0, 11 * mm)
        self.canv.scale(icon_scale, -icon_scale)

        d_shape = self.canv.beginPath()
        d_shape.moveTo(43, 26)
        d_shape.lineTo(71, 26)
        d_shape.curveTo(91, 26, 105, 42, 105, 60)
        d_shape.curveTo(105, 79, 91, 95, 71, 95)
        d_shape.lineTo(43, 95)
        d_shape.close()
        d_shape.moveTo(59, 40)
        d_shape.lineTo(71, 40)
        d_shape.curveTo(82, 40, 91, 49, 91, 60)
        d_shape.curveTo(91, 71, 82, 79, 71, 79)
        d_shape.lineTo(59, 79)
        d_shape.close()

        self.canv.setFillColor(colors.white)
        self.canv.drawPath(d_shape, fill=1, stroke=0, fillMode=0)

        p_shape = self.canv.beginPath()
        p_shape.moveTo(18, 26)
        p_shape.lineTo(45, 26)
        p_shape.curveTo(60, 26, 70, 36, 70, 49)
        p_shape.curveTo(70, 62, 60, 73, 45, 73)
        p_shape.lineTo(34, 73)
        p_shape.lineTo(34, 95)
        p_shape.lineTo(18, 95)
        p_shape.close()
        self.canv.setFillColor(STEEL)
        self.canv.drawPath(p_shape, fill=1, stroke=0)

        p_cutout = self.canv.beginPath()
        p_cutout.moveTo(34, 40)
        p_cutout.lineTo(45, 40)
        p_cutout.curveTo(51, 40, 55, 44, 55, 49)
        p_cutout.curveTo(55, 54, 51, 58, 45, 58)
        p_cutout.lineTo(34, 58)
        p_cutout.close()
        self.canv.setFillColor(NAVY)
        self.canv.drawPath(p_cutout, fill=1, stroke=0)
        self.canv.restoreState()

        self.canv.setFillColor(NAVY)
        self.canv.setFont("Helvetica-Bold", 15)
        self.canv.drawString(14 * mm, 3.2 * mm, "Paper Desk")


class NumberedCanvas(canvas.Canvas):
    """Add a consistent footer and Page X of Y numbering."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)

        for page_state in self._saved_page_states:
            self.__dict__.update(page_state)
            self._draw_footer(page_count)
            super().showPage()

        super().save()

    def _draw_footer(self, page_count):
        page_width, _ = self._pagesize
        left = 18 * mm
        right = page_width - 18 * mm

        self.setStrokeColor(LINE)
        self.setLineWidth(0.5)
        self.line(left, 15 * mm, right, 15 * mm)

        self.setFillColor(MUTED)
        self.setFont("Helvetica", 8)
        self.drawString(left, 9.5 * mm, "Paper Desk")
        self.drawRightString(
            right,
            9.5 * mm,
            f"Page {self._pageNumber} of {page_count}",
        )


def _styles():
    sample_styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=sample_styles["Heading1"],
            alignment=TA_RIGHT,
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=20,
            textColor=NAVY,
            spaceAfter=0,
        ),
        "meta_label": ParagraphStyle(
            "MetaLabel",
            parent=sample_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=MUTED,
            spaceAfter=2,
            textTransform="uppercase",
        ),
        "meta_value": ParagraphStyle(
            "MetaValue",
            parent=sample_styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=INK,
        ),
        "section": ParagraphStyle(
            "SectionTitle",
            parent=sample_styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=STEEL,
            spaceBefore=0,
            spaceAfter=9,
            textTransform="uppercase",
        ),
        "summary_label": ParagraphStyle(
            "SummaryLabel",
            parent=sample_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=MUTED,
        ),
        "summary_value": ParagraphStyle(
            "SummaryValue",
            parent=sample_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=NAVY,
        ),
        "normal": ParagraphStyle(
            "ReportNormal",
            parent=sample_styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=INK,
        ),
        "note": ParagraphStyle(
            "ReportNote",
            parent=sample_styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
        ),
        "empty": ParagraphStyle(
            "EmptyState",
            parent=sample_styles["Normal"],
            alignment=TA_CENTER,
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=MUTED,
            spaceBefore=18,
            spaceAfter=18,
        ),
        "table_left": ParagraphStyle(
            "TableLeft",
            parent=sample_styles["Normal"],
            alignment=TA_LEFT,
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=INK,
        ),
        "table_right": ParagraphStyle(
            "TableRight",
            parent=sample_styles["Normal"],
            alignment=TA_RIGHT,
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=INK,
        ),
        "table_bold": ParagraphStyle(
            "TableBold",
            parent=sample_styles["Normal"],
            alignment=TA_LEFT,
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=NAVY,
        ),
        "table_bold_right": ParagraphStyle(
            "TableBoldRight",
            parent=sample_styles["Normal"],
            alignment=TA_RIGHT,
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=NAVY,
        ),
        "buy": ParagraphStyle(
            "BuyLabel",
            parent=sample_styles["Normal"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=GREEN,
        ),
        "sell": ParagraphStyle(
            "SellLabel",
            parent=sample_styles["Normal"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=BURGUNDY,
        ),
    }


def _money(value):
    return f"${Decimal(str(value)):,.2f}"


def _format_datetime(value):
    if not value:
        return "-"

    return value.strftime("%d %b %Y, %H:%M")


def _format_date(value):
    if not value:
        return None

    if isinstance(value, str):
        value = date.fromisoformat(value)

    return value.strftime("%d %b %Y")


def _report_period(start_date=None, end_date=None):
    if start_date and end_date:
        return f"{_format_date(start_date)} to {_format_date(end_date)}"

    return "All recorded activity"


def _default_filename(report_name):
    report_date = datetime.now().strftime("%Y-%m-%d")
    return f"paper-desk-{report_name}-{report_date}.pdf"


def _metadata_cell(label, value, styles):
    return [
        Paragraph(label, styles["meta_label"]),
        Paragraph(escape(str(value)), styles["meta_value"]),
    ]


def _report_header(user, title, period=None):
    styles = _styles()
    generated = datetime.now().strftime("%d %B %Y, %H:%M")

    title_table = Table(
        [[PaperDeskLogo(), Paragraph(escape(title.upper()), styles["title"])]],
        colWidths=[90 * mm, None],
    )
    title_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7 * mm),
                ("LINEBELOW", (0, 0), (-1, -1), 1, STEEL),
            ]
        )
    )

    metadata = [
        [
            _metadata_cell(
                "Account holder",
                f"{user.first_name.title()} {user.last_name.title()}",
                styles,
            ),
            _metadata_cell("Generated", generated, styles),
        ],
        [
            _metadata_cell("Account reference", f"Account {user.id}", styles),
            _metadata_cell(
                "Reporting period",
                period or "Current portfolio",
                styles,
            ),
        ],
    ]

    metadata_table = Table(metadata, colWidths=[80 * mm, 80 * mm])
    metadata_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
            ]
        )
    )

    return [title_table, metadata_table, Spacer(1, 7 * mm)]


def _summary_cards(items, available_width):
    styles = _styles()
    cell_width = available_width / len(items)
    cells = []

    for label, value, colour in items:
        value_style = ParagraphStyle(
            f"SummaryValue{len(cells)}",
            parent=styles["summary_value"],
            textColor=colour,
        )
        cells.append(
            [
                Paragraph(escape(label), styles["summary_label"]),
                Spacer(1, 1.5 * mm),
                Paragraph(escape(value), value_style),
            ]
        )

    cards = Table([cells], colWidths=[cell_width] * len(items))
    cards.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.7, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.7, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ]
        )
    )

    return cards


def _table_style(right_aligned_columns=None):
    right_aligned_columns = right_aligned_columns or []
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), SURFACE_MUTED),
        ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.4, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, TABLE_STRIPE]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6 * mm),
    ]

    for column in right_aligned_columns:
        commands.append(("ALIGN", (column, 0), (column, -1), "RIGHT"))

    return TableStyle(commands)


def _section_title(text):
    return Paragraph(escape(text.upper()), _styles()["section"])


def _report_note(text):
    styles = _styles()
    note_table = Table([[Paragraph(escape(text), styles["note"])]])
    note_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE_MUTED),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]
        )
    )
    return note_table


def _empty_state(message):
    return Table(
        [[Paragraph(escape(message), _styles()["empty"])]],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), TABLE_STRIPE),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10 * mm),
            ]
        ),
    )


def _build_pdf(elements, page_size=A4):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=page_size,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=22 * mm,
        title="Paper Desk report",
        author="Paper Desk",
    )
    doc.build(elements, canvasmaker=NumberedCanvas)
    pdf_buffer.seek(0)
    return pdf_buffer


def generate_portfolio_statement(user_id, filename=None):
    """Generate an in-memory PDF containing the current portfolio."""

    user = get_user(user_id)
    portfolio_result = get_portfolio(user_id)

    if not user or not portfolio_result["success"]:
        return None

    portfolio = portfolio_result["message"]
    filename = filename or _default_filename("portfolio")
    available_width = A4[0] - (36 * mm)

    elements = _report_header(user, "Portfolio statement")
    elements.extend(
        [
            _section_title("Portfolio summary"),
            _summary_cards(
                [
                    ("Cash balance", _money(portfolio.cash_balance), NAVY),
                    ("Holdings value", _money(portfolio.positions_value), NAVY),
                    ("Total value", _money(portfolio.portfolio_value), STEEL),
                ],
                available_width,
            ),
            Spacer(1, 8 * mm),
            _section_title("Open positions"),
        ]
    )

    if not portfolio.positions:
        elements.append(_empty_state("You currently hold no equities."))
    else:
        styles = _styles()
        table_data = [
            [
                "Symbol",
                "Company",
                "Average cost",
                "Current price",
                "Shares",
                "Current value",
            ]
        ]

        for position in portfolio.positions.values():
            table_data.append(
                [
                    Paragraph(escape(position.symbol.upper()), styles["table_bold"]),
                    Paragraph(escape(position.company_name.title()), styles["table_left"]),
                    Paragraph(_money(position.price_per_share), styles["table_right"]),
                    Paragraph(_money(position.last_price_per_share), styles["table_right"]),
                    Paragraph(str(position.number_of_shares), styles["table_right"]),
                    Paragraph(_money(position.total_value), styles["table_bold_right"]),
                ]
            )

        positions_table = Table(
            table_data,
            colWidths=[18 * mm, 46 * mm, 28 * mm, 28 * mm, 18 * mm, 31 * mm],
            repeatRows=1,
        )
        positions_table.setStyle(_table_style([2, 3, 4, 5]))
        elements.append(positions_table)

    elements.extend(
        [
            Spacer(1, 8 * mm),
            _report_note(
                "Values use simulated funds. Position values reflect the latest "
                "market information available when this statement was generated."
            ),
        ]
    )

    return _build_pdf(elements), filename


def generate_trade_statement(
    user_id,
    trades,
    filename=None,
    start_date=None,
    end_date=None,
):
    """Generate an in-memory PDF containing recorded buy and sell activity."""

    user = get_user(user_id)
    if not user:
        return None

    filename = filename or _default_filename("trade-history")
    period = _report_period(start_date, end_date)
    styles = _styles()

    elements = _report_header(user, "Trade history", period)
    elements.extend(
        [
            _summary_cards(
                [
                    ("Reporting period", period, NAVY),
                    ("Recorded trades", str(len(trades)), STEEL),
                ],
                A4[0] - (36 * mm),
            ),
            Spacer(1, 8 * mm),
            _section_title("Recorded trades"),
        ]
    )

    if not trades:
        elements.append(_empty_state("No trades were found for the selected period."))
    else:
        table_data = [
            [
                "Date and time",
                "Type",
                "Symbol",
                "Company",
                "Shares",
                "Price per share",
                "Total",
            ]
        ]

        for trade in trades:
            trade_type = trade.trade_type.upper()
            label_style = styles["buy"] if trade_type == "BUY" else styles["sell"]
            table_data.append(
                [
                    Paragraph(_format_datetime(trade.timestamp), styles["table_left"]),
                    Paragraph(trade_type, label_style),
                    Paragraph(escape(trade.symbol.upper()), styles["table_bold"]),
                    Paragraph(escape(trade.company_name.title()), styles["table_left"]),
                    Paragraph(str(trade.number_of_shares), styles["table_right"]),
                    Paragraph(_money(trade.price_per_share), styles["table_right"]),
                    Paragraph(_money(trade.trade_total), styles["table_bold_right"]),
                ]
            )

        trades_table = Table(
            table_data,
            colWidths=[
                31 * mm,
                17 * mm,
                18 * mm,
                38 * mm,
                17 * mm,
                25 * mm,
                28 * mm,
            ],
            repeatRows=1,
        )
        table_style = _table_style([4, 5, 6])
        table_style.add("BACKGROUND", (1, 1), (1, -1), colors.white)

        for row_number, trade in enumerate(trades, start=1):
            background = (
                GREEN_SOFT
                if trade.trade_type.upper() == "BUY"
                else BURGUNDY_SOFT
            )
            table_style.add("BACKGROUND", (1, row_number), (1, row_number), background)

        trades_table.setStyle(table_style)
        elements.append(trades_table)

    elements.extend(
        [
            Spacer(1, 8 * mm),
            _report_note(
                "This report records simulated orders only. No real market orders "
                "were placed."
            ),
        ]
    )

    return _build_pdf(elements), filename


def generate_transaction_statement(
    user_id,
    transactions,
    filename=None,
    start_date=None,
    end_date=None,
):
    """Generate an in-memory PDF containing deposits and withdrawals."""

    user = get_user(user_id)
    if not user:
        return None

    filename = filename or _default_filename("account-activity")
    period = _report_period(start_date, end_date)
    styles = _styles()

    deposits = sum(
        (
            transaction.amount
            for transaction in transactions
            if transaction.transaction_type.upper() == "DEPOSIT"
        ),
        Decimal("0.00"),
    )
    withdrawals = sum(
        (
            transaction.amount
            for transaction in transactions
            if transaction.transaction_type.upper() == "WITHDRAW"
        ),
        Decimal("0.00"),
    )
    net_movement = deposits - withdrawals
    net_text = _money(net_movement)
    if net_movement > 0:
        net_text = f"+{net_text}"

    elements = _report_header(user, "Account activity", period)
    elements.extend(
        [
            _section_title("Period summary"),
            _summary_cards(
                [
                    ("Deposits", _money(deposits), GREEN),
                    ("Withdrawals", _money(withdrawals), BURGUNDY),
                    ("Net movement", net_text, NAVY),
                ],
                A4[0] - (36 * mm),
            ),
            Spacer(1, 8 * mm),
            _section_title("Transactions"),
        ]
    )

    if not transactions:
        elements.append(
            _empty_state("No transactions were found for the selected period.")
        )
    else:
        table_data = [["Date and time", "Type", "Amount"]]

        for transaction in transactions:
            transaction_type = transaction.transaction_type.upper()
            label_style = (
                styles["buy"]
                if transaction_type == "DEPOSIT"
                else styles["sell"]
            )
            table_data.append(
                [
                    Paragraph(
                        _format_datetime(transaction.timestamp),
                        styles["table_left"],
                    ),
                    Paragraph(transaction_type, label_style),
                    Paragraph(
                        _money(transaction.amount),
                        styles["table_bold_right"],
                    ),
                ]
            )

        transactions_table = Table(
            table_data,
            colWidths=[68 * mm, 46 * mm, 53 * mm],
            repeatRows=1,
        )
        table_style = _table_style([2])

        for row_number, transaction in enumerate(transactions, start=1):
            background = (
                GREEN_SOFT
                if transaction.transaction_type.upper() == "DEPOSIT"
                else BURGUNDY_SOFT
            )
            table_style.add("BACKGROUND", (1, row_number), (1, row_number), background)

        transactions_table.setStyle(table_style)
        elements.append(transactions_table)

    elements.extend(
        [
            Spacer(1, 8 * mm),
            _report_note(
                "Amounts in this report use simulated funds and relate only to "
                "activity recorded in this Paper Desk account."
            ),
        ]
    )

    return _build_pdf(elements), filename
