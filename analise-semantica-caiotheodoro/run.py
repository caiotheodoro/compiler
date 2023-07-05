import subprocess
import glob

def run_tppsema(file_pattern):
    file_list = glob.glob(file_pattern)  # Get a list of files matching the pattern
    for file_path in file_list:
        command = ["python3", "tppsema.py", file_path]
        subprocess.run(command)

# Example usage
run_tppsema("./tests/sema-*.tpp")  # Run tppsema.py with all files starting with "sema-" and ending with ".tpp" in the "./tests/" directory


