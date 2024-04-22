import math
import random 

import pandas as pd
import os
class cachesim:

    def __init__(self, c, bs, a):
        # Declare class cache parameters
        self.capacity = c
        self.block_size = bs
        self.associativity = a
        self.sets = c // (bs * a)
        self.blocks = c // bs
        
        # Calculate masks and offsets needed
        self.set_mask = self.sets - 1
        self.set_offset = self.count_bits((self.block_size - 1))
        self.tag_offset = self.count_bits(self.set_mask) + (self.set_offset)

        # Cache array with tag, dirty, valid for each block
        self.cache = [[0, False, False] for _ in range(self.blocks)]

        # print(f'Sets: {self.sets}; Blocks: {self.blocks}; Set Mask: {self.set_mask}; Set Offset: {self.set_offset}; Tag Offset: {self.tag_offset}')

    def count_bits(self, n):
        count = 0
        while n:
            count += n & 1
            n >>= 1
        return count

    #logic for cache access
    def cache_access(self, op, address):
        hit = dirty = False
        evicted = None

        #calculate set and tag bits
        set_bits = ((address >> self.set_offset) & self.set_mask) * self.associativity
        tag_bits = (address >> self.tag_offset)


        # Iterate through cache set
        invalid_block = -1
        for i in range(set_bits, set_bits + self.associativity):

            #find last invalid block in set
            if not self.cache[i][2]:
                invalid_block = i

            # Cache hit
            elif self.cache[i][0] == tag_bits:
                hit = True

                #if it is a write, mark dirty
                if op == 1:
                    self.cache[i][1] = True
                break
        
        
        # Cache miss (loop did not break)
        else:

            # Compulsory miss -- found an invalid block and no hit
            if invalid_block >= 0:

                #update tag bits to reflect new address
                self.cache[invalid_block][0] = tag_bits

                #mark block as valid
                self.cache[invalid_block][2] = True



            # Eviction -- no invalid blocks, so random replacement
            else:

                #calculate random index in set to evict
                randomVal = random.randint(0, self.associativity - 1)
                idx = set_bits + randomVal

                #get dirty status to see if writeback is needed
                dirty = self.cache[idx][1]

                #reconstruct evicted address by shifting tag bits to the left and adding set bits via OR
                evicted = self.cache[set_bits][0] << self.tag_offset | set_bits << self.set_offset

                #update tag bits to reflect new address
                self.cache[idx][0] = tag_bits


        #runner file should perform calculations based on the output
        return [hit, dirty, evicted] 

def main(file_path, associativity):
    
    l1Data = cachesim(32768, 64, 1)
    l1Instructions = cachesim(32768, 64, 1)
    l2 = cachesim(262144, 64, associativity)

    # All measured in ns, penalty in pj
    l1_idle = l1_active = l2_idle = l2_active = dram_idle = dram_active = penalty = 0

    l1_instruction_hits = l1_instruction_total = 0
    l1_data_hits = l1_data_total = 0
    l2_hits = l2_total = 0

    evicted = 0

    with open(file_path, 'r') as f:

        #read input line
        for line in f:
            hit = dirty = False

            #parse line to get operation and address
            line = line.split()
            op = int(line[0])
            address = int(line[1], 16)


            # L1 Access

            # Instruction Cache
            if (op == 2):
                hit, dirty, evicted = l1Instructions.cache_access(op, address)
                if hit:
                    l1_instruction_hits += 1
                l1_instruction_total += 1

            # Data Cache
            else:
                hit, dirty, evicted = l1Data.cache_access(op, address)
                if hit:
                    l1_data_hits += 1
                l1_data_total += 1

            #costs of L1 access
            l1_active += 0.5
            l2_active += 0.5
            dram_idle += 0.5
            penalty += 5 if op != 1 else 0 #writes are handled below

            # Writeback to L2 and DRAM if dirty eviction
            if dirty:
                
                #writeback to L2 
                hit, dirty, evicted = l2.cache_access(1, evicted)


                if hit:
                    l2_hits += 1
                l2_total += 1

            # L1 Miss -- won't execute if dirty code above has executed, as dirty code only executes on dirty miss evict
            if not hit:


                # Access L2
                hit, dirty, evicted = l2.cache_access(op, address)


                if hit:
                    l2_hits += 1
                l2_total += 1

                l1_idle += 4.5  #may be active still but probably not
                l2_active += 4.5   
                dram_idle += 4.5

                #Miss --> DRAM access
                if not hit:
                    # copy of data DRAM -> L2 and L2 -> DRAM on misses do not take extra time or extra active energy for the writes
                    if op != 1:
                        l1_idle += 45
                        l2_idle += 45
                        dram_active += 45
                    # Penalty applied for all DRAM access including writes
                    penalty += 640
            
                    if dirty:
                        #remove from static add to active
                        dram_idle -= 45
                        dram_active += 45

                        # Writeback to DRAM (penalties apply for writeback assumption)
                        penalty += 640

    l1Energy = l1_idle * 0.5 + l1_active
    l2Energy = l2_idle * 0.8 + l2_active * 2
    total_energy = penalty / 1000 + l1_idle * 0.5 + l1_active + l2_idle * 0.8 + l2_active * 2 + dram_idle + 0.8 + dram_active * 4
    

    l1_instruction_hit_rate = l1_instruction_hits / l1_instruction_total * 100
    l1_data_hit_rate = l1_data_hits / l1_data_total * 100
    l2_hit_rate = l2_hits / l2_total * 100
    # print(f'L1 Instruction Hit Rate: {l1_instruction_hit_rate}%')
    # print(f'L1 Data Hit Rate: {l1_data_hit_rate}%')
    # print(f'L2 Hit Rate: {l2_hit_rate}%')

    # print('Total Energy: ', total_energy / (10 ** 9), 'Joules')
    # print('Compulsory Misses: ', compulsoryCount)

    #for all params, use this
    return [dram_idle + dram_active / 10 ** 9, l1_instruction_hit_rate, l1_data_hit_rate, l2_hit_rate, total_energy / (10 ** 9), l1Energy / (10 ** 9), l2Energy / (10 ** 9)]
    # return [total_energy / (10 ** 9), dram_idle + dram_active]



def standard_deviation(data):
    N = len(data)
    mean = sum(data) / N
    return math.sqrt(sum((x - mean) ** 2 for x in data) / N)




# After all simulations
if __name__ == '__main__':
    results = []
    headers = ['Filename', 'Associativity', 'Mean Energy (J)', 'StdDev Energy (J)',
               'Mean Time (s)', 'StdDev Time (s)', 'Mean L1 Instruction Hit Rate (%)', 
               'StdDev L1 Instruction Hit Rate (%)', 'Mean L1 Data Hit Rate (%)',
               'StdDev L1 Data Hit Rate (%)', 'Mean L2 Hit Rate (%)', 'StdDev L2 Hit Rate (%)',
               'Mean L1 Energy (J)', 'StdDev L1 Energy (J)', 'Mean L2 Energy (J)', 'StdDev L2 Energy (J)']

    base_dir = os.path.join(os.getcwd(), 'Spec_Benchmark')

    files = [
        os.path.join(base_dir, '008.espresso.din'),
        os.path.join(base_dir, '013.spice2g6.din'),
        os.path.join(base_dir, '015.doduc.din'),
        os.path.join(base_dir, '022.li.din'),
        os.path.join(base_dir, '023.eqntott.din'),
        os.path.join(base_dir, '026.compress.din'),
        os.path.join(base_dir, '034.mdljdp2.din'),
        os.path.join(base_dir, '039.wave5.din'),
        os.path.join(base_dir, '047.tomcatv.din'),
        os.path.join(base_dir, '048.ora.din'),
        os.path.join(base_dir, '085.gcc.din'),
        os.path.join(base_dir, '089.su2cor.din'),
        os.path.join(base_dir, '090.hydro2d.din'),
        os.path.join(base_dir, '093.nasa7.din'),
        os.path.join(base_dir, '094.fpppp.din')
]
    for arg in files:
        for assoc in [2, 4, 8]:
            # Assume `main` function and other necessary parts are defined as shown above
            # Collecting data in lists
            energies, times, l1_instruction_hit_rates, l1_data_hit_rates, l2_hit_rates, l1Energies, l2Energies = [], [], [], [], [], [], []
            
            for _ in range(10):
                time, l1_I_HR, l1_D_HR, l2_HR, energy, l1Energy, l2Energy = main(arg, assoc)
                energies.append(energy)
                times.append(time)
                l1_instruction_hit_rates.append(l1_I_HR)
                l1_data_hit_rates.append(l1_D_HR)
                l2_hit_rates.append(l2_HR)
                l1Energies.append(l1Energy)
                l2Energies.append(l2Energy)
            
            # Calculating mean and stddev
            meanEnergy = sum(energies) / 10
            meanTime = sum(times) / 10 
            meanL1InstructionHitRate = sum(l1_instruction_hit_rates) / 10
            meanL1DataHitRate = sum(l1_data_hit_rates) / 10
            meanL2HitRate = sum(l2_hit_rates) / 10
            meanL1Energy = sum(l1Energies) / 10
            meanL2Energy = sum(l2Energies) / 10

            stddevEnergy = standard_deviation(energies)
            stddevTime = standard_deviation(times) 
            stddevL1InstructionHitRate = standard_deviation(l1_instruction_hit_rates)
            stddevL1DataHitRate = standard_deviation(l1_data_hit_rates)
            stddevL2HitRate = standard_deviation(l2_hit_rates)
            stddevL1Energy = standard_deviation(l1Energies)
            stddevL2Energy = standard_deviation(l2Energies)

            # Store results in list for DataFrame
            results.append([
                arg, assoc, meanEnergy, stddevEnergy, meanTime, stddevTime,
                meanL1InstructionHitRate, stddevL1InstructionHitRate, meanL1DataHitRate,
                stddevL1DataHitRate, meanL2HitRate, stddevL2HitRate, meanL1Energy, stddevL1Energy,
                meanL2Energy, stddevL2Energy
            ])

    # Create DataFrame
    df = pd.DataFrame(results, columns=headers)

    # Export to Excel
    df.to_excel('simulation_results.xlsx', index=False)
