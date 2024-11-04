import pandas as pd
import json
import io

class DataStructureHealthieDump:
    def retrieve_dump(self, dump_data_type):
        """
        Generates a small dummy dataset and returns it in the requested format.

        Args:
            dump_data_type (str): The format of the dump ('json' or 'xlsx').

        Returns:
            tuple: A tuple containing the file bytes, the full name of the file,
                   the MIME type, and a log message.
        """
        # Generate a dummy dataset
        data = {
            'ID': [1, 2, 3],
            'Name': ['Alice', 'Bob', 'Charlie'],
            'Age': [25, 30, 35],
            'Occupation': ['Engineer', 'Doctor', 'Artist']
        }

        # Depending on the requested type, return the corresponding format
        if dump_data_type == 'json':
            # Convert to JSON
            json_data = json.dumps(data, indent=4)

            # encode() is used to convert the string to bytes
            json_data_bytes = json_data.encode()

            log = {
                'success': True,
                'message': 'JSON data generated successfully.'
            }

            return (json_data_bytes , 'data_dump.json', 'application/txt', log)

        elif dump_data_type == 'xlsx':
            # Convert to DataFrame and then to Excel
            df = pd.DataFrame(data)
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)  # Move cursor to the beginning of the BytesIO object
            log = {
                'success': True,
                'message': 'XLSX data generated successfully.'
            }
            return (output.read(), 'data_dump.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', log)

        else:
            log = {
                'success': False,
                'message': 'Unsupported dump_data_type.'
            }
            return (None, None, None, log)

# Example usage:
if __name__ == "__main__":
    manager = DataStructureHealthieDump()
    dump_data_type = 'xlsx'  # or 'xlsx'
    dump_bytes, full_name, mimetype, log = manager.retrieve_dump(dump_data_type)

    # Print results for demonstration
    print(f"Log: {log}")
    print(f"Filename: {full_name}, MIME type: {mimetype}")
    if dump_data_type == 'json':
        print(dump_bytes.decode('utf-8'))  # Print JSON content
    elif dump_data_type == 'xlsx':
        print(f"Generated {full_name} with {len(dump_bytes)} bytes.")
