def extract_since_inception(analysis_table, patient_id):
    since_inception_col = next((col for col in analysis_table.columns if "Since Inception" in col), None)
    if since_inception_col:
        extracted_data = analysis_table[[since_inception_col]].copy()
        extracted_data.columns = [patient_id]  # Rename column to patient ID
        return extracted_data
    return None
