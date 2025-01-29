import os
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from PyPDF2 import PdfMerger

def save_to_pdf(analysis, extremes, output_file):
    with PdfPages(output_file) as pdf:
        # Analysis table
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.axis('off')
        ax.axis('tight')
        table = ax.table(cellText=analysis.reset_index().values,
                         colLabels=[''] + list(analysis.columns),
                         cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.scale(1.2, 1.2)

        # Adjust cell formatting
        for (row, col), cell in table.get_celld().items():
            if row == 0:  # Wrap text for column headers
                cell.set_text_props(wrap=True)
                cell.set_fontsize(8)
            elif col == 0:  # Wrap text for row headers
                cell.set_text_props(wrap=True)
                cell.set_fontsize(8)
            elif row > 0 and "Since Inception" in analysis.columns[col - 1]:  # Exclude coloring for Since Inception column
                cell.set_facecolor('white')
            else:  # Apply colorization logic
                metric = analysis.index[row - 1] if row > 0 else None
                value = analysis.iloc[row - 1, col - 1] if row > 0 and col > 0 else None

                if metric and value is not None:
                    color = 'white'
                    if isinstance(value, str):
                        # Remove trend arrows and convert to numeric
                        value = pd.to_numeric(value.replace('+', '').replace('-', '').strip(), errors='coerce')

                    if metric == 'Avg Systolic BP (mmHg)' and value is not None:
                        if value < 130:
                            color = 'lightgreen'
                        elif 130 <= value <= 139:
                            color = 'yellow'
                        else:
                            color = 'red'
                    elif metric == 'Avg Diastolic BP (mmHg)' and value is not None:
                        if value < 80:
                            color = 'lightgreen'
                        elif 80 <= value <= 89:
                            color = 'yellow'
                        else:
                            color = 'red'
                    elif metric == 'SBP SD (mmHg)' and value is not None:
                        if value < 7.5:
                            color = 'lightgreen'
                        elif value < 15:
                            color = 'yellow'
                        else:
                            color = 'red'
                    elif metric == 'DBP SD (mmHg)' and value is not None:
                        if value < 5:
                            color = 'lightgreen'
                        elif value < 11.5:
                            color = 'yellow'
                        else:
                            color = 'red'
                    elif metric == 'SBP CV (%)' and value is not None:
                        if value < 5.5:
                            color = 'lightgreen'
                        elif value < 11:
                            color = 'yellow'
                        else:
                            color = 'red'
                    elif metric == 'DBP CV (%)' and value is not None:
                        if value < 6:
                            color = 'lightgreen'
                        elif value < 13:
                            color = 'yellow'
                        else:
                            color = 'red'
                    elif metric == 'Peak SBP² (mmHg)' and value is not None:
                        if value < 170:
                            color = 'lightgreen'
                        else:
                            color = 'red'
                    elif metric == 'Peak DBP² (mmHg)' and value is not None:
                        if value < 110:
                            color = 'lightgreen'
                        else:
                            color = 'red'

                    cell.set_facecolor(color)

        ax.set_title(os.path.basename(output_file).replace('_report.pdf', ' Analysis'))

        # Add note about Peak rows
        ax.text(0, 0, "¹ 'Hypotensive Measurements' indicates the count of systolic BP values <= 95 mmHg with a hypothetical average decrease of 5 mmHg.",
                fontsize=8, transform=ax.transAxes, ha='left', va='top')
        ax.text(0, -0.05, "² 'Peak' values represent the average of the three highest values in the timeframe.",
                fontsize=8, transform=ax.transAxes, ha='left', va='top')
        ax.text(0, -0.10, "³ 'Low' values represent the single lowest value in the timeframe.",
                fontsize=8, transform=ax.transAxes, ha='left', va='top')

        pdf.savefig(fig)
        plt.close(fig)

        # Extremes table with pagination
        rows_per_page = 25  # Define the maximum number of rows per page
        total_rows = len(extremes)
        num_pages = (total_rows // rows_per_page) + (1 if total_rows % rows_per_page != 0 else 0)

        if extremes.empty:
            # Handle empty extremes table
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.axis('off')
            ax.axis('tight')
            ax.text(0.5, 0.5, 'No extreme values found', transform=ax.transAxes, ha='center', va='center')
            ax.set_title(os.path.basename(output_file).replace('_report.pdf', " Extremes"))
            pdf.savefig(fig)
            plt.close(fig)
        else:
            for page in range(num_pages):
                start_row = page * rows_per_page
                end_row = min(start_row + rows_per_page, total_rows)
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.axis('off')
                ax.axis('tight')

                # Create a subset of the extremes table for the current page
                subset = extremes.iloc[start_row:end_row]
                ax.table(cellText=subset.values,
                         colLabels=['Date', 'Systolic BP', 'Diastolic BP'],
                         cellLoc='center', loc='center')
                ax.set_title(os.path.basename(output_file).replace('_report.pdf', f" Extremes (Page {page + 1} of {num_pages})"))
                pdf.savefig(fig)
                plt.close(fig)

def combine_pdfs(pdf_folder, combined_pdf_path):
    """
    Combine all PDFs in a folder into a single PDF.

    :param pdf_folder: Path to the folder containing individual PDFs.
    :param combined_pdf_path: Path to save the combined PDF.
    """
    merger = PdfMerger()

    # Get all PDF files in the folder
    pdf_files = [os.path.join(pdf_folder, f) for f in os.listdir(pdf_folder) if f.endswith('.pdf')]

    # Sort files to maintain order (optional)
    pdf_files.sort()

    # Append each PDF to the merger
    for pdf in pdf_files:
        merger.append(pdf)

    # Write the combined PDF to disk
    merger.write(combined_pdf_path)
    merger.close()

    print(f"Combined PDF saved to {combined_pdf_path}")

def save_aggregate_pdf(aggregate_df, output_file):
    with PdfPages(output_file) as pdf:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.axis('off')
        ax.axis('tight')
        table = ax.table(cellText=aggregate_df.reset_index().values,
                         colLabels=['Metric'] + list(aggregate_df.columns),
                         cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.2)
        ax.set_title("Aggregate Since Inception Analysis")
        pdf.savefig(fig)
        plt.close(fig)
