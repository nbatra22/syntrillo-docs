import os
import re
from io import BytesIO
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors

from syntrillo.system.logger import logger

class BloodPressureReport:
    """
    Generates a PDF report for blood pressure analysis.
    """

    def __init__(self, patient_info_dict, summary_dict, timeframed_df, extremes_df, report_code, logo=None):
        self.patient_info_dict = patient_info_dict
        self.summary_dict = summary_dict
        self.timeframed_df = timeframed_df
        self.extremes_df = extremes_df
        self.report_code = report_code
        self.logo = logo

    def generate_provider_pdf_report(self):
        """
        Build the PDF with header & footer on ALL pages.
        Uses onFirstPage/onLaterPages to render consistently.
        """
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            topMargin=72,     # normal space for header
            bottomMargin=32,  # space for line, footer paragraph, and page number
            leftMargin=32,
            rightMargin=32
        )

        elements = []

        # First page: intro section with access code and message
        elements.extend(self._build_intro_section())

        # Content sections
        elements.extend(self._build_summary_section())
        elements.append(PageBreak())
        elements.extend(self._build_analysis_section())
        elements.extend(self._build_extremes_section())

        # Ensure header/footer on every page
        doc.build(
            elements,
            onFirstPage=self._draw_header_footer,
            onLaterPages=self._draw_header_footer
        )

        pdf_buffer.seek(0)
        return pdf_buffer

    def generate_patient_pdf_report(self):
        """
        Build the PDF report for patients without header/footer.
        Simpler layout.
        """
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            topMargin=72,
            bottomMargin=72,
            leftMargin=32,
            rightMargin=32
        )

        elements = []

        # Content sections
        elements.extend(self._build_summary_section())
        elements.append(PageBreak())
        elements.extend(self._build_analysis_section())
        elements.extend(self._build_extremes_section())

        doc.build(
            elements,
            onFirstPage=self._draw_header_footer,
            onLaterPages=self._draw_header_footer
        )

        pdf_buffer.seek(0)
        return pdf_buffer

    def _build_intro_section(self):
        """
        Build the intro section that appears only on the first page.
        Contains access code, contact info, main message, referral info, and signature.
        """
        story = []
        styles = getSampleStyleSheet()

        # Access code and website (two columns)
        access_style = ParagraphStyle(
            name="Access",
            parent=styles["Normal"],
            fontSize=10,
            leftIndent=0,
            firstLineIndent=0,
        )

        access_code_para = Paragraph(
            f"<b>Access Code:</b> <font name='Courier-Bold'>{self.report_code}</font>",
            access_style
        )
        website_para = Paragraph(
            "<b>Website:</b> https://www.syntrillo.com/providers",
            access_style
        )

        # Phone and email (two columns)
        phone_para = Paragraph("<b>Phone:</b> 434-202-3450", access_style)
        email_para = Paragraph("<b>Email:</b> providers@syntrillo.com", access_style)

        contact_table = Table(
            [
                [access_code_para, website_para],
                [phone_para, email_para]
            ],
            colWidths=[275, 275],
            style=[
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
        story.append(contact_table)
        story.append(Spacer(1, 12))

        # Main message paragraph
        message_style = ParagraphStyle(
            name="IntroMessage",
            parent=styles["Normal"],
            fontSize=10,  # increased from 8
            leftIndent=0,
            firstLineIndent=0,
            leading=12,
        )

        main_message = (
            f"If you would like to continue to receive blood pressure reports, "
            f"you can text us at 434-202-3450 or email us at providers@syntrillo.com with "
            f"the following code <font name='Courier-Bold'>{self.report_code}</font> "
            f"and the frequency you prefer the reports sent (e.g. monthly). "
            f"Please do not share any Personally Identifiable Information in the text or email."
        )

        message_table = Table(
            [[Paragraph(main_message, message_style)]],
            colWidths=[550],
            style=[
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
        story.append(message_table)
        story.append(Spacer(1, 12))

        # Separator line
        separator_line = Table(
            [[""]],
            colWidths=[550],
            style=[
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
        story.append(separator_line)
        story.append(Spacer(1, 18))

        return story

    def _draw_header_footer(self, canvas, doc):
        """
        Draw simple header and footer on every page.
        - Header stays within top margin and does not overlap content
        - Header/footer use doc.leftMargin/doc.width (same as inner content)
        - Page number is centered at bottom
        """
        left = doc.leftMargin
        right = doc.leftMargin + doc.width

        # Header block
        header_block_h = 60
        page_top_y = doc.bottomMargin + doc.height + doc.topMargin
        y1 = page_top_y - header_block_h + 22  # first header line
        y2 = page_top_y - header_block_h + 8   # second header line

        today_str = datetime.now().strftime("%-m/%-d/%Y")
        first = (self.patient_info_dict or {}).get("first_name")
        last = (self.patient_info_dict or {}).get("last_name")
        patient_name = f"{first} {last}" if first and last else None
        dob = (self.patient_info_dict or {}).get("dob") or "N/A"

        canvas.saveState()

        # Line 1: Title and Patient
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(left, y1, "Syntrillo - Blood Pressure Report")
        if patient_name:
            label = "Patient: "
            canvas.setFont("Helvetica-Bold", 10)
            label_width = canvas.stringWidth(label, "Helvetica-Bold", 10)
            value_width = canvas.stringWidth(patient_name, "Helvetica", 10)
            x = right - (label_width + value_width)
            canvas.drawString(x, y1, label)
            canvas.setFont("Helvetica", 10)
            canvas.drawString(x + label_width, y1, patient_name)

        # Line 2: Date and DOB
        canvas.setFont("Helvetica", 10)
        canvas.drawString(left, y2, f"As of {today_str}")
        if patient_name:
            label = "DOB: "
            canvas.setFont("Helvetica-Bold", 10)
            label_width = canvas.stringWidth(label, "Helvetica-Bold", 10)
            value_width = canvas.stringWidth(dob, "Helvetica", 10)
            x = right - (label_width + value_width)
            canvas.drawString(x, y2, label)
            canvas.setFont("Helvetica", 10)
            canvas.drawString(x + label_width, y2, dob)

        canvas.restoreState()

        # Header line below entire header block
        line_y = page_top_y - header_block_h
        canvas.saveState()
        canvas.setLineWidth(0.5)
        canvas.line(left, line_y, right, line_y)
        canvas.restoreState()

        # Centered page number at bottom
        page_num_y = doc.bottomMargin - 16
        page_num_x = left + (doc.width / 2.0)
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(page_num_x, page_num_y, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    def _build_summary_section(self):
        """
        Build the summary section of the report.
        Shows date_range and status as separate paragraphs,
        followed by a table of metrics with targets and actual values.
        """
        story = []
        styles = getSampleStyleSheet()

        # Title with underline - no indent
        summary_title_style = ParagraphStyle(
            name="SummaryTitle",
            parent=styles["Heading2"],
            underlineWidth=1,
            underlineOffset=-2,
            leftIndent=0,
            firstLineIndent=0,
        )
        # Wrap title in table to remove document margin effect
        title_table = Table(
            [[Paragraph("<u>Summary</u>", summary_title_style)]],
            colWidths=[550],
            style=[
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
        story.append(title_table)
        story.append(Spacer(1, 12))

        # Date Range and Status (if present)
        date_range = self.summary_dict.get("date_range")
        status_data = self.summary_dict.get("status")

        normal_style = ParagraphStyle(
            name="NormalNoIndent",
            parent=styles["Normal"],
            leftIndent=0,
            firstLineIndent=0,
        )

        info_rows = []
        if date_range:
            info_rows.append([Paragraph(f"<b>Date Range:</b> {date_range}", normal_style)])

        if status_data:
            status_value = status_data.get("value") if isinstance(status_data, dict) else status_data
            info_rows.append([Paragraph(f"<b>Status:</b> {status_value}", normal_style)])

        if info_rows:
            info_table = Table(
                info_rows,
                colWidths=[550],
                style=[
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
            story.append(info_table)
            story.append(Spacer(1, 12))

        # Define metric labels and targets
        metric_config = {
            "avg_sbp": {
                "label": "Avg SBP (mmHg)",
                "target": "Less than 125 mmHg"
            },
            "avg_dbp": {
                "label": "Avg DBP (mmHg)",
                "target": "Less than 80 mmHg"
            },
            "peak_sbp": {
                "label": "Peak SBP¹ (mmHg)",
                "target": "Less than 165 mmHg"
            },
            "low_sbp": {
                "label": "Low SBP² (mmHg)",
                "target": "Greater than 90 mmHg"
            },
            "symptomatic_hypotension": {
                "label": "Symptomatic Hypotension (# of episodes)",
                "target": "0 episodes"
            },
        }

        # Build table data (exclude date_range and status)
        table_data = [["Metric", "Target", "Actual"]]

        for key, config in metric_config.items():
            if key in self.summary_dict:
                data = self.summary_dict[key]
                value = data.get("value") if isinstance(data, dict) else data
                # Format numeric values
                if isinstance(value, (int, float)):
                    value_str = f"{value:.1f}" if isinstance(value, float) else str(value)
                else:
                    value_str = str(value)

                table_data.append([
                    config["label"],
                    config["target"],
                    value_str
                ])

        # Create and style table (match header width of 550)
        summary_table = Table(table_data, colWidths=[220, 220, 110])
        summary_table.setStyle(TableStyle([
            # Header row: light gray background with rounded corners
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ROUNDEDCORNERS', [6, 6, 0, 0]),  # top-left, top-right rounded
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONT', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            # Header alignment matches data rows
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),    # Metric header
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),    # Target header
            ('ALIGN', (2, 0), (2, 0), 'CENTER'),  # Actual header
            # Data row alignment
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 12))

        # Add footnotes
        footnote_style = ParagraphStyle(
            name="Footnote",
            parent=styles["Normal"],
            fontSize=8,
            leftIndent=2,
            firstLineIndent=0,
        )
        footnotes = [
            "¹Peak values represent the average of the three highest values in the timeframe.",
            "²Low values represent the average of the three lowest values in the timeframe.",
            "³Hypotensive Count indicates the number of systolic BP values ≤ 90 mmHg."
        ]

        for footnote in footnotes:
            footnote_table = Table(
                [[Paragraph(f"{footnote}", footnote_style)]],
                colWidths=[550],
                style=[
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
            story.append(footnote_table)


        return story

    def _build_analysis_section(self):
        """
        Build the analysis section of the report with detailed metrics across timeframes.
        """
        story = []
        styles = getSampleStyleSheet()

        # Title with underline - no indent
        analysis_title_style = ParagraphStyle(
            name="AnalysisTitle",
            parent=styles["Heading2"],
            underlineWidth=1,
            underlineOffset=-2,
            leftIndent=0,
            firstLineIndent=0,
        )
        # Wrap title in table to remove document margin effect
        title_table = Table(
            [[Paragraph("<u>Analysis</u>", analysis_title_style)]],
            colWidths=[550],
            style=[
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
        story.append(title_table)
        story.append(Spacer(1, 18))

        # Prepare the dataframe for the table
        if self.timeframed_df is None or self.timeframed_df.empty:
            no_data_para = Paragraph("No detailed metrics available.", styles["Normal"])
            story.append(no_data_para)
            return story

        # Create a copy and clean it up
        df = self.timeframed_df.copy()

        # Drop "Since" columns and unwanted rows
        cols_to_drop = [c for c in df.columns if "Since" in c]
        df.drop(columns=cols_to_drop, inplace=True, errors='ignore')

        rows_delete_keywords = ['Progress', 'Engagement', 'Near', 'Overall']
        rows_to_drop = [idx for idx in df.index if any(kw in str(idx) for kw in rows_delete_keywords)]
        df.drop(index=rows_to_drop, inplace=True, errors='ignore')

        # Clean footnote markers from column names and values
        _FOOTNOTE_CHARS_PATTERN = re.compile(r'[\*\†\‡\¹\²\³\⁴\⁵\⁶\⁷\⁸\⁹\⁰]+')

        def clean_cell(v):
            if v is None:
                return ""
            if isinstance(v, str):
                # Don't clean - keep original string
                return str(v).strip()
            elif isinstance(v, (int, float)):
                v = f"{v:.1f}".rstrip('0').rstrip('.')
            return str(v)

        # Clean column headers
        cleaned_columns = [_FOOTNOTE_CHARS_PATTERN.sub('', str(c)).strip() for c in df.columns]

        # Build table data
        table_data = [["Metric"] + cleaned_columns]

        for idx in df.index:
            row_label = self._clean_metric_name(idx)
            row_values = [clean_cell(df.loc[idx, col]) for col in df.columns]
            table_data.append([row_label] + row_values)

        # Calculate column widths dynamically based on number of timeframes
        num_columns = len(cleaned_columns)
        total_width = 550
        metric_col_width = 180
        remaining_width = total_width - metric_col_width
        timeframe_col_width = remaining_width / num_columns if num_columns > 0 else 100

        col_widths = [metric_col_width] + [timeframe_col_width] * num_columns

        # Create and style table
        analysis_table = Table(table_data, colWidths=col_widths)
        analysis_table.setStyle(TableStyle([
            # Header row: light gray background with rounded corners
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ROUNDEDCORNERS', [6, 6, 0, 0]),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONT', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            # Header alignment
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),     # Metric header left-aligned
            ('ALIGN', (1, 0), (-1, 0), 'CENTER'),  # Timeframe headers centered
            # Data row alignment
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),    # Metric names left-aligned
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'), # Data values centered
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))

        story.append(analysis_table)
        story.append(Spacer(1, 12))

        # Add footnotes
        footnote_style = ParagraphStyle(
            name="Footnote",
            parent=styles["Normal"],
            fontSize=8,
            leftIndent=2,
            firstLineIndent=0,
        )
        footnotes = [
            "¹Peak values represent the average of the three highest values in the timeframe.",
            "²Low values represent the average of the three lowest values in the timeframe.",
            "³Hypotensive Count indicates the number of systolic BP values ≤ 90 mmHg."
        ]

        for footnote in footnotes:
            footnote_table = Table(
                [[Paragraph(f"{footnote}", footnote_style)]],
                colWidths=[550],
                style=[
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
            story.append(footnote_table)

        story.append(Spacer(1, 24))

        return story

    def _build_extremes_section(self):
        """
        Build the extremes section of the report showing extreme BP values.
        This section starts on a new page.
        """
        story = []
        styles = getSampleStyleSheet()

        # Title with underline - no indent
        extremes_title_style = ParagraphStyle(
            name="ExtremesTitle",
            parent=styles["Heading2"],
            underlineWidth=1,
            underlineOffset=-2,
            leftIndent=0,
            firstLineIndent=0,
        )
        # Wrap title in table to remove document margin effect
        title_table = Table(
            [[Paragraph("<u>Extremes</u>", extremes_title_style)]],
            colWidths=[550],
            style=[
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
        story.append(title_table)
        story.append(Spacer(1, 18))

        # Check if extremes data exists
        if self.extremes_df is None or self.extremes_df.empty:
            no_data_para = Paragraph("No extreme measurements found.", styles["Normal"])
            story.append(no_data_para)
            return story

        # Prepare dataframe
        df = self.extremes_df.copy()

        # Clean footnote markers pattern
        _FOOTNOTE_CHARS_PATTERN = re.compile(r'[\*\†\‡\¹\²\³\⁴\⁵\⁶\⁷\⁸\⁹\⁰]+')

        def clean_cell(v):
            if v is None:
                return ""
            if isinstance(v, str):
                v = _FOOTNOTE_CHARS_PATTERN.sub('', v).strip()
            elif isinstance(v, (int, float)):
                v = f"{v:.1f}".rstrip('0').rstrip('.')
            return str(v)

        # Clean column headers
        cleaned_columns = [_FOOTNOTE_CHARS_PATTERN.sub('', str(c)).strip() for c in df.columns]

        # Build table data
        table_data = [cleaned_columns]

        for idx in df.index:
            row_values = [clean_cell(df.loc[idx, col]) for col in df.columns]
            table_data.append(row_values)

        # Calculate column widths dynamically
        num_columns = len(cleaned_columns)
        total_width = 550
        col_width = total_width / num_columns if num_columns > 0 else 100
        col_widths = [col_width] * num_columns

        # Create and style table
        extremes_table = Table(table_data, colWidths=col_widths)
        extremes_table.setStyle(TableStyle([
            # Header row: light gray background with rounded corners
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ROUNDEDCORNERS', [6, 6, 0, 0]),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONT', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            # All headers and data centered
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))

        story.append(extremes_table)
        story.append(Spacer(1, 12))

        return story

    @staticmethod
    def _clean_metric_name(metric_name):
        """Clean and add footnotes to metric names in first column"""
        _FOOTNOTE_CHARS_PATTERN = re.compile(r'[\*\†\‡\¹\²\³\⁴\⁵\⁶\⁷\⁸\⁹\⁰]+')
        # Remove existing footnotes first
        cleaned = _FOOTNOTE_CHARS_PATTERN.sub('', str(metric_name)).strip()
        # Map to add footnotes back
        metric_footnote_map = {
            "Peak SBP (mmHg)": "Peak SBP¹ (mmHg)",
            "Peak DBP (mmHg)": "Peak DBP¹ (mmHg)",
            "Low SBP (mmHg)": "Low SBP² (mmHg)",
            "Low DBP (mmHg)": "Low DBP² (mmHg)",
            "Hypotensive Count": "Hypotensive Count³"
        }
        return metric_footnote_map.get(cleaned, cleaned)
