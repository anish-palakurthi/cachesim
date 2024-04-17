input_file = "Spec_Benchmark/008.espresso.din"
output_file = "Spec_Benchmark/008.espress.edited.din"

with open(input_file, "r") as file:
    lines = file.readlines()

filtered_lines = [line.split() for line in lines if not line.startswith("2")]

for line in filtered_lines:
    line[2] = "1"


filtered_lines = [' '.join(line) + '\n' for line in filtered_lines]

with open(output_file, "w") as file:
    file.writelines(filtered_lines)
