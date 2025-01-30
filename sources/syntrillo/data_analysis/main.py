import os
import pandas as pd

from functions.process_csv import read_csv_file, preprocess_data
from functions.calculate_analysis import calculate_analysis
from functions.calculate_extremes import calculate_extremes
from functions.calculate_since_inception import calculate_since_inception
from functions.calculate_timeframes import calculate_timeframes
from functions.calculate_total_counts import calculate_total_counts
from functions.pdf_generator import save_to_pdf, combine_pdfs, save_aggregate_pdf
from functions.extract_since_inception import extract_since_inception
from functions.csv_generator import save_aggregate_csv

# Main program
if __name__ == "__main__":
    data_folder = 'data'
    output_folder = 'output'
    aggregate_pdf_file = os.path.join(output_folder, "aggregate-analysis.pdf")
    aggregate_change_csv_file = os.path.join(output_folder, "aggregate-change-analysis.csv")
    aggregate_totals_csv_file = os.path.join(output_folder, "aggregate-totals-analysis.csv")
    combined_reports_file = os.path.join(output_folder, "combined-reports.pdf")
    os.makedirs(output_folder, exist_ok=True)

    # Check if the aggregate analysis PDF exists, and remove it if it does
    if os.path.exists(combined_reports_file):
        print(f"Aggregate analysis file '{combined_reports_file}' already exists. Replacing it.")
        os.remove(combined_reports_file)

    aggregate_change_data = []
    aggregate_totals_data = []

    # Process each CSV file individually
    for filename in os.listdir(data_folder):
        if filename.endswith('.csv'):
            filepath = os.path.join(data_folder, filename)
            patient_id = os.path.splitext(filename)[0]
            output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_report.pdf")

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
            analysis_table_with_inception = calculate_since_inception(total_counts, analysis_table_without_inception)

            # Add Since Inception (Unit Change) column to aggregate data
            extracted_change_data = extract_since_inception(analysis_table_with_inception, patient_id, num_measurements, start_date, end_date, type="(Unit Change)")
            if extracted_change_data is not None:
                aggregate_change_data.append(extracted_change_data)

            # Add Since Inception (Total) column to aggregate data
            extracted_total_data = extract_since_inception(analysis_table_with_inception, patient_id, num_measurements, start_date, end_date, type="(Total)")
            if extracted_total_data is not None:
                aggregate_totals_data.append(extracted_total_data)

            # Calculate extremes
            extremes_table = calculate_extremes(bp_data)

            # Save results to a unique PDF
            save_to_pdf(analysis_table_with_inception, extremes_table, output_file)

            print(f"Report saved to {output_file}")

    # Combine all PDFs into one
    combine_pdfs(output_folder, combined_reports_file)

    if aggregate_change_data:
        aggregate_df = pd.concat(aggregate_change_data, axis=1)
        save_aggregate_csv(aggregate_df, aggregate_change_csv_file)
        # save_aggregate_pdf(aggregate_df, aggregate_pdf_file)
        # print(f"Aggregate analysis saved to {aggregate_csv_file} and {aggregate_pdf_file}")

    if aggregate_totals_data:
        aggregate_df = pd.concat(aggregate_totals_data, axis=1)
        save_aggregate_csv(aggregate_df, aggregate_totals_csv_file)
