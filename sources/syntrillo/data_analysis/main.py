import os
import pandas as pd

from functions.process_csv import read_csv_file, preprocess_data
from functions.calculate_analysis import calculate_analysis
from functions.calculate_extremes import calculate_extremes
from functions.calculate_timeframes import calculate_timeframes
from functions.pdf_generator import save_to_pdf, combine_pdfs, save_aggregate_pdf
from functions.extract_since_inception import extract_since_inception
from functions.csv_generator import save_aggregate_csv

# Main program
if __name__ == "__main__":
    data_folder = 'data'
    output_folder = 'output'
    aggregate_pdf_file = os.path.join(output_folder, "aggregate-analysis.pdf")
    aggregate_csv_file = os.path.join(output_folder, "aggregate-analysis.csv")
    combined_reports_file = os.path.join(output_folder, "combined-reports.pdf")
    os.makedirs(output_folder, exist_ok=True)

    # Check if the aggregate analysis PDF exists, and remove it if it does
    if os.path.exists(combined_reports_file):
        print(f"Aggregate analysis file '{combined_reports_file}' already exists. Replacing it.")
        os.remove(combined_reports_file)

    aggregate_data = []

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

            # Calculate timeframes and analysis
            timeframes = calculate_timeframes(bp_data)
            analysis_table = calculate_analysis(timeframes)

            # Add Since Inception column to aggregate data
            extracted_data = extract_since_inception(analysis_table, patient_id, num_measurements, start_date, end_date)
            if extracted_data is not None:
                aggregate_data.append(extracted_data)

            # Calculate extremes
            extremes_table = calculate_extremes(bp_data)

            # Save results to a unique PDF
            save_to_pdf(analysis_table, extremes_table, output_file)

            print(f"Report saved to {output_file}")

    # Combine all PDFs into one
    combine_pdfs(output_folder, combined_reports_file)

    if aggregate_data:
        aggregate_df = pd.concat(aggregate_data, axis=1)
        save_aggregate_csv(aggregate_df, aggregate_csv_file)
        save_aggregate_pdf(aggregate_df, aggregate_pdf_file)
        print(f"Aggregate analysis saved to {aggregate_csv_file} and {aggregate_pdf_file}")
