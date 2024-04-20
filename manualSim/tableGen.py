import math
import random 
import sys
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

    def cache_access_l1(self, op, address):
        hit = dirty = False
        compulsory = False
        evicted = None
        #calculate set and tag bits
        set_bits = (address >> self.set_offset) & self.set_mask
        tag_bits = (address >> self.tag_offset)
        
        if self.cache[set_bits][0] == tag_bits:
            hit = True
            #if it is a write, mark dirty
            if op == 1:
                self.cache[set_bits][1] = True
        else:
            if self.cache[set_bits][0] == 0:
                compulsory = True
            dirty = self.cache[set_bits][1]
            evicted = self.cache[set_bits][0] << self.tag_offset | set_bits << self.set_offset
            #code for cache miss
            #evict
            self.cache[set_bits][0] = tag_bits
        
        # Mark valid
        self.cache[set_bits][2] = True


        #runner file should perform calculations based on the output
        return [hit, dirty, compulsory, evicted]

    def cache_access_l2(self, op, address):
        hit = dirty = False
        compulsory = False
        #calculate set and tag bits
        set_bits = ((address >> self.set_offset) & self.set_mask) * self.associativity
        tag_bits = (address >> self.tag_offset)
        # Iterate through cache set
        invalid_block = -1
        for i in range(set_bits, set_bits + self.associativity):
            if not self.cache[i][2]:
                invalid_block = i
            # Cache hit
            elif self.cache[i][0] == tag_bits:
                hit = True
                if op == 1:
                    self.cache[i][1] = True
                break
        
        
        # Cache miss
        else:
            # print(address, tag_bits)
            # Compulsory miss
            if invalid_block >= 0:
                self.cache[invalid_block][0] = tag_bits
                self.cache[invalid_block][2] = True
                compulsory = True
            # Eviction
            else:

                randomVal = random.randint(0, self.associativity - 1)
                idx = set_bits + randomVal
                dirty = self.cache[idx][1]
                self.cache[idx][0] = tag_bits
        #runner file should perform calculations based on the output
        return [hit, dirty, compulsory] 


def main(file_path, associativity):
    
    l1Data = cachesim(32768, 64, 1)
    l1Instructions = cachesim(32768, 64, 1)
    l2 = cachesim(262144, 64, associativity)

    # All measured in ns, penalty in pj
    l1_idle = l1_active = l2_idle = l2_active = dram_idle = dram_active = penalty = 0

    l1_instruction_hits = l1_instruction_total = 0
    l1_data_hits = l1_data_total = 0
    l2_hits = l2_total = 0
    compulsoryCount = 0
    compulsory = False
    evicted = 0

    with open(file_path, 'r') as f:
        for line in f:
            hit = dirty = False
            #parse line
            line = line.split()
            op = int(line[0])
            address = int(line[1], 16)

            # L1 Access
            if (op == 2):
                hit, dirty, compulsory, evicted = l1Instructions.cache_access_l1(op, address)
                if hit:
                    l1_instruction_hits += 1
                l1_instruction_total += 1
            else:
                hit, dirty, compulsory, evicted = l1Data.cache_access_l1(op, address)
                if hit:
                    l1_data_hits += 1
                    
                l1_data_total += 1

            l1_active += 0.5
            l2_active += 0.5
            dram_idle += 0.5
            penalty += 5 if op != 1 else 0

            # Writeback to L2 and DRAM if dirty eviction
            if dirty:
                penalty += 640 if op != 1 else 0 # from l1-dram
                
                hit, dirty, compulsory = l2.cache_access_l2(1, evicted)
                if compulsory:
                    compulsoryCount += 1

                if hit:
                    l2_hits += 1
                l2_total += 1

            # L1 Miss
            if not hit:
                # Access L2
                hit, dirty, compulsory = l2.cache_access_l2(op, address)
                if compulsory:
                    compulsoryCount += 1

                if hit:
                    l2_hits += 1

                l2_total += 1

                l1_idle += 4.5  #may be active still but probably not
                l2_active += 4.5   
                dram_idle += 4.5

                if not hit:
                    #DRAM access
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
    # return [dram_idle + dram_active, l1_instruction_hit_rate, l1_data_hit_rate, l2_hit_rate, total_energy / (10 ** 9)]
    return [total_energy / (10 ** 9), dram_idle + dram_active]



def standard_deviation(data):
    N = len(data)
    mean = sum(data) / N
    return math.sqrt(sum((x - mean) ** 2 for x in data) / N)


if __name__ == '__main__':

    for arg in sys.argv[1:]:
        for assoc in [2, 4, 8]:
            energies, times = [], []
            
            for _ in range(10):
                energy, time = main(arg, assoc)
                energies.append(energy)
                times.append(time)
            
            meanEnergy = sum(energies) / 10
            meanTime = sum(times) / 10
            stddevEnergy = standard_deviation(energies)
            stddevTime = standard_deviation(times)

            with open('results.txt', 'a') as file:
                file.write(f'Test: {arg}; Assoc: {assoc}; Mean Energy: {meanEnergy}; StdDev Energy: {stddevEnergy}; Mean Time: {meanTime}; StdDev Time: {stddevTime}\n')


        

