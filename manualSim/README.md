# Cache Simulator

## Usage Instruction

Run `./run.sh` to output for all 15 test cases for associativites 2, 4, and 8
To run a single test, run `cachesim.py` with the dinero trace file path as a parameter in the command line

To generate a more comprehensive data table for each run, run `tableGen.py`. This will output a .xlsx file to view the data.

`cachesim.py` runs our main cache logic and is what should be used/examined.
`tableGen.py` is similar but generates a pandas dataframe with all the output included via an .xlsx file.
