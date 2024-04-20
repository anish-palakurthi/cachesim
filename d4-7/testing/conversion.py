import os
# Specify the path to your text file
source_dir_path = "/Users/anishpalakurthi/Desktop/dineroProj/manualSim/Spec_Benchmark"
output_dir_path = "/Users/anishpalakurthi/Desktop/dineroProj/d4-7/testing/preprocessed_dins"

def preprocess(file_path, output_file):

    map = {0: 'r', 1: 'w', 2: 'i'}
    # Open the file in read mode
    res = []
    with open(file_path, 'r') as file:
        # Iterate through each line in the file
        for line in file:
            # Strip any leading/trailing whitespace
            chunks = line.strip().split(' ')
            if (chunks[0] == '3'):
                continue

            chunks[0] = map[int(chunks[0])]
            chunks[2] = '4'
            res.append(" ".join(chunks))

    with open(output_file, 'w') as file:
        file.write("\n".join(res))


def main():
    # Iterate through each file in the directory
    for file_name in os.listdir(source_dir_path):
        # Check if the file is a text file
        if file_name.endswith('.din'):
            # Preprocess the file
            source_file_path = os.path.join(source_dir_path, file_name)
            output_file_path = os.path.join(output_dir_path, file_name)
            preprocess(source_file_path, output_file_path)


if __name__ == '__main__':
    main()