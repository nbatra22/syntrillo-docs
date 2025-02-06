import os
import pandas as pd

from functions.process_csv import read_csv_file, preprocess_data
from functions.calculate_analysis import calculate_analysis
from functions.calculate_extremes import calculate_extremes
from syntrillo.data_analysis.functions.calculate_since_baseline import calculate_since_baseline
from functions.calculate_timeframes import calculate_timeframes
from functions.calculate_total_counts import calculate_total_counts
from functions.pdf_generator import save_to_pdf, combine_pdfs, save_aggregate_pdf
from functions.extract_since_inception import extract_since_inception
from functions.csv_generator import save_to_csv

# Main program
if __name__ == "__main__":
    data_folder = 'data'
    output_folder = 'output'

    # Define subdirectories for organizing files
    pdf_folder = os.path.join(output_folder, 'pdfs')
    csv_folder = os.path.join(output_folder, 'csvs')
    reports_folder = os.path.join(output_folder, 'reports')

    # Ensure all folders exist before writing files
    for folder in [pdf_folder, csv_folder, reports_folder]:
        os.makedirs(folder, exist_ok=True)

    # Define file paths inside respective folders
    aggregate_pdf_file = os.path.join(pdf_folder, "aggregate-analysis.pdf")
    aggregate_change_csv_file = os.path.join(csv_folder, "aggregate-change-analysis.csv")
    aggregate_percent_csv_file = os.path.join(csv_folder, "aggregate-percent-analysis.csv")
    aggregate_totals_csv_file = os.path.join(csv_folder, "aggregate-totals-analysis.csv")
    combined_reports_file = os.path.join(reports_folder, "combined-reports.pdf")
    os.makedirs(output_folder, exist_ok=True)

    # Check if the aggregate analysis PDF exists, and remove it if it does
    if os.path.exists(combined_reports_file):
        print(f"Aggregate analysis file '{combined_reports_file}' already exists. Replacing it.")
        os.remove(combined_reports_file)

    aggregate_change_data = []
    aggregate_percent_data = []
    aggregate_totals_data = []

    # Process each CSV file individually
    for filename in os.listdir(data_folder):
        if filename.endswith('.csv'):
            filepath = os.path.join(data_folder, filename)
            patient_id = os.path.splitext(filename)[0]
            pdf_output_file = os.path.join(reports_folder, f"{os.path.splitext(filename)[0]}_report.pdf")
            csv_output_file = os.path.join(csv_folder, f"{os.path.splitext(filename)[0]}.csv")
            csv_data = []

            # Load and preprocess data
            data = read_csv_file(filepath)
            bp_data = preprocess_data(data)

            # Extract metadata
            num_measurements = len(bp_data)  # Count number of rows
            start_date = bp_data['Time stamp'].min()  # Earliest date
            end_date = bp_data['Time stamp'].max()  # Latest date
            total_counts = calculate_total_counts(bp_data) # Total counts for SBP and DBP

            # Calculate timeframes and analysis
            timeframes = calculate_timeframes(bp_data)
            analysis_table_without_inception = calculate_analysis(timeframes)
            analysis_table_with_inception = calculate_since_baseline(total_counts, analysis_table_without_inception)

            # Create CSV
            csv_data.append(analysis_table_without_inception)
            patient_df = pd.concat(csv_data)
            save_to_csv(patient_df, csv_output_file)

            # Add Since Inception (Δ Unit) column to aggregate data
            extracted_change_data = extract_since_inception(analysis_table_with_inception, patient_id, num_measurements, start_date, end_date, type="(Δ Unit)")
            if extracted_change_data is not None:
                aggregate_change_data.append(extracted_change_data)

            # Add Since Inception (Δ Percent) column to aggregate data
            extracted_percent_data = extract_since_inception(analysis_table_with_inception, patient_id, num_measurements, start_date, end_date, type="(Δ Percent)")
            if extracted_percent_data is not None:
                aggregate_percent_data.append(extracted_percent_data)

            # Add Since Inception (Total) column to aggregate data
            extracted_total_data = extract_since_inception(analysis_table_with_inception, patient_id, num_measurements, start_date, end_date, type="(Total)")
            if extracted_total_data is not None:
                aggregate_totals_data.append(extracted_total_data)

            # Calculate extremes
            extremes_table = calculate_extremes(bp_data)

            # Save results to a unique PDF
            save_to_pdf(analysis_table_with_inception, extremes_table, pdf_output_file)

            print(f"Report saved to {pdf_folder}")

    # Combine all PDFs into one
    combine_pdfs(output_folder, combined_reports_file)

    if aggregate_change_data:
        aggregate_df = pd.concat(aggregate_change_data, axis=1)
        save_to_csv(aggregate_df, aggregate_change_csv_file)
        # save_aggregate_pdf(aggregate_df, aggregate_pdf_file)
        # print(f"Aggregate analysis saved to {aggregate_csv_file} and {aggregate_pdf_file}")

    if aggregate_percent_data:
        aggregate_df = pd.concat(aggregate_percent_data, axis=1)
        save_to_csv(aggregate_df, aggregate_percent_csv_file)
        # save_aggregate_pdf(aggregate_df, aggregate_pdf_file)
        # print(f"Aggregate analysis saved to {aggregate_csv_file} and {aggregate_pdf_file}")

    if aggregate_totals_data:
        aggregate_df = pd.concat(aggregate_totals_data, axis=1)
        save_to_csv(aggregate_df, aggregate_totals_csv_file)
