

def save_to_csv(df, output_file):
    df.to_csv(output_file, index=True)
    print(f"Aggregate analysis saved to {output_file}")
