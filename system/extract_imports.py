# Path: ./system/extract_imports.py
import os
import re

def find_imports(path):
    """
    Objective: Extract all the packages imported in the project, which was initially developed with Condas. This will allow to setup a pip freeze requirements file.
    """
    imports = set()
    import_pattern = re.compile(r'^\s*(?:import|from)\s+([\w\.]+)')

    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file)) as f:
                    for line in f:
                        match = import_pattern.match(line)
                        if match:
                            imports.add(match.group(1).split('.')[0])

    return sorted(imports)

# Get the directory of the current script
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# Set the project path to one level above the current script directory
project_path = os.path.abspath(os.path.join(current_script_dir, os.pardir))

imports = find_imports(project_path)

with open('imported_packages.txt', 'w') as f:
    for package in imports:
        f.write(f"{package}\n")

print(f"Extracted packages saved to imported_packages.txt")
