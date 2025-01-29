
def extract_since_inception(analysis_table, patient_id, num_measurements, start_date, end_date):
    since_inception_col = next((col for col in analysis_table.columns if "Since Inception" in col), None)
    if since_inception_col:
        extracted_data = analysis_table[[since_inception_col]].copy()
        extracted_data.columns = [f"{patient_id}"]  # Rename column to patient ID with Change label

        num_days = (end_date - start_date).days

        extracted_data.loc['# of Measurements'] = num_measurements
        extracted_data.loc['Start Date'] = start_date.strftime('%m/%d/%y')
        extracted_data.loc['End Date'] = end_date.strftime('%m/%d/%y')
        extracted_data.loc['Total Days'] = num_days

        return extracted_data
    return None
