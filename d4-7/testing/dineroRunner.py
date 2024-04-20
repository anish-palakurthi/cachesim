import os
import subprocess

# Set the directory path where the files are located
directory_path = '/Users/anishpalakurthi/Desktop/dineroProj/d4-7/testing/preprocessed_dins'
output_directory = '/Users/anishpalakurthi/Desktop/dineroProj/d4-7/testing/dineroOutputs'

# Create the output directory if it does not exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# List all files in the directory
files = os.listdir(directory_path)

# Construct and execute the command for each file
for file_name in files:
    if file_name.endswith('.din'):  # Filter for .din files if needed
        input_path = os.path.join(directory_path, file_name)
        output_path = os.path.join(output_directory, 'res' + file_name.replace('.din', '.txt'))

        # Construct the command
        command = f'../dineroIV -l1-isize 32k  -l1-iassoc 1 -l1-ibsize 64 -l1-ifetch d -l1-irepl r ' \
                  f'-l1-dsize 32k  -l1-dassoc 1 -l1-dbsize 64 -l1-dfetch d -l1-drepl r ' \
                  f'-l2-usize 256k -l2-uassoc 4 -l2-ubsize 64 -l2-ufetch d -l2-urepl r ' \
                  f'-informat D < {input_path} > {output_path}'

        # Execute the command
        subprocess.run(command, shell=True)

print("All commands executed. Outputs are stored in:", output_directory)
