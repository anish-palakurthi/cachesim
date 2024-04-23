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
    
    def invalidate(self, address):
        set_bits = ((address >> self.set_offset) & self.set_mask) * self.associativity
        tag_bits = (address >> self.tag_offset)


        # Iterate through cache set
        for i in range(set_bits, set_bits + self.associativity):

            #find valid match if exists
            if not self.cache[i][2] and self.cache[i][0] == tag_bits:
                self.cache[i][2] = False
                break
        return
    

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
    
    # Initialize cache objects
    l1Data = cachesim(32768, 64, 1)
    l1Instructions = cachesim(32768, 64, 1)
    l2 = cachesim(262144, 64, associativity)


    # All measured in ns, penalty in pj
    l1_idle = l1i_active = l1d_active = l2_idle = l2_active = dram_idle = dram_active = 0
    dram_penalty = l2_penalty = 0

    # Hit and total counters
    l1_instruction_hits = l1_instruction_total = 0
    l1_data_hits = l1_data_total = 0
    l2_hits = l2_total = 0
    dram_accesses = 0
    # Eviction counter
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

                l1i_active += 0.5

            # Data Cache
            else:
                hit, dirty, evicted = l1Data.cache_access(op, address)
                if hit:
                    l1_data_hits += 1
                l1_data_total += 1

                l1d_active += 0.5

            #costs of L1 access
            l2_active += 0.5
            dram_idle += 0.5
            l2_penalty += 5 if op != 1 else 0 #writes are handled below

            # Writeback to L2 and DRAM if dirty eviction
            if dirty:
                
                #writeback to L2 
                hit, dirty, evicted = l2.cache_access(1, evicted)

                # Asynchronous active time added
                l2_active += 5
                dram_active += 50

                # Penalty applied for all DRAM access including writes
                dram_penalty += 640
                dram_accesses += 1
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
                    dram_penalty += 640
                    dram_accesses += 1

                    if dirty:
                        # Invalidate block in L1 cache
                        l1Data.invalidate(evicted)

                        # Asynchronous active time added
                        dram_active += 50

                        # Writeback to DRAM (penalties apply for writeback assumption)
                        dram_penalty += 640
                        dram_accesses += 1

    l1i_energy = l1_idle * 0.25 + l1i_active
    l1d_energy = l1_idle * 0.25 + l1d_active
    l2_energy = l2_idle * 0.8 + l2_active * 2 + l2_penalty / 1000
    dram_energy = dram_idle + 0.8 + dram_active * 4 + dram_penalty / 1000

    total_energy =  l1i_energy + l1d_energy + l2_energy + dram_energy
    # Overall totals
    print(f'Total Time: {max(l2_idle + l2_active, dram_idle + dram_active)}  ns')
    print('Total Energy: ', total_energy / (10 ** 9), 'Joules')
    # L1 Instruction totals
    print(f'L1 Instruction total accesses: {l1_instruction_total}')
    print(f'L1 Instruction misses: {l1_instruction_total - l1_instruction_hits}')
    print(f'L1 Instruction energy: {l1i_energy / (10 ** 9)} Joules')
    # L1 Data totals
    print(f'L1 Data total accesses: {l1_data_total}')
    print(f'L1 Data misses: {l1_data_total - l1_data_hits}')
    print(f'L1 Data energy: {l1d_energy / (10 ** 9)} Joules')
    # L2 totals
    print(f'L2 total accesses: {l2_total}')
    print(f'L2 misses: {l2_total - l2_hits}')
    print(f'L2 energy: {l2_energy / (10 ** 9)} Joules')
    # DRAM totals
    print(f'DRAM total accesses: {dram_accesses}')
    print(f'DRAM energy: {dram_energy / (10 ** 9)} Joules')
    # Hit Rates
    print(f'L1 Instruction Hit Rate: {l1_instruction_hits / l1_instruction_total * 100}%')
    print(f'L1 Data Hit Rate: {l1_data_hits / l1_data_total * 100}%')
    print(f'L2 Hit Rate: {l2_hits / l2_total * 100}%')

    
    return





if __name__ == '__main__':

    for arg in sys.argv[1:]:
        for assoc in [2,4,8]:
            print(f'Running {arg} with associativity {assoc}')
            main(arg, 2)
            print('------\n')
        print('---------------------------------\n')
    
        

