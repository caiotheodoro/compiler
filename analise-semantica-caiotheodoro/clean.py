import os
import glob

def delete_files(pattern):
    file_list = glob.glob(pattern)  # Get a list of files matching the pattern
    for file_path in file_list:
        os.remove(file_path)  # Delete each file

# Example usage
delete_files("./tests/sema-*.tpp.csv")  # Delete all files starting with "sema-" and ending with ".tpp.csv"
delete_files("./tests/sema-*.tpp.podada.unique.ast.png")  # Delete all files starting with "sema-" and ending with ".tpp.podada.unique.ast.png"
