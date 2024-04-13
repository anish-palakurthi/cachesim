# Specify the path to your text file
file_path = '/Users/anishpalakurthi/Desktop/d4-7/testing/008.espresso.din'
output_file = '/Users/anishpalakurthi/Desktop/d4-7/testing/ones.din'

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
        if chunks[0] == '4':
            print("penis\n")
        chunks[0] = map[int(chunks[0])]
        chunks[2] = '4' if len(chunks[2]) > 1 else '1'
        res.append(" ".join(chunks))

with open(output_file, 'w') as file:
    file.write("\n".join(res))
