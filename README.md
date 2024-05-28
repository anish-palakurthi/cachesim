##Cache Simulator
d4-7 uses the official dinero cache simulator as a baseline to compare to our custom implementation.
We implement our timing simulator with a write-back cache policy, with L1 (unified), L2 (instructions and data separate), and DRAM. 
See manualSim/cachesim.py for implementation and discussion of design decisions.
