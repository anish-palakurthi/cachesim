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

    #logic for l1 cache access
    def cache_access_l1(self, op, address):
        hit = dirty = compulsory = False
        evicted = None

        #shift set bits all the way to the right and mask tag bits(remaining) to get set bits
        set_bits = (address >> self.set_offset) & self.set_mask

        #shift tag bits all the way to the right to get tag bits
        tag_bits = (address >> self.tag_offset)
        
        #hit
        if self.cache[set_bits][0] == tag_bits:
            hit = True
            
            #if it is a write, mark dirty
            if op == 1:
                self.cache[set_bits][1] = True
        
        #miss
        else:
            #not valid block
            if self.cache[set_bits][0] == 0:
                compulsory = True
            
            #get dirty status
            dirty = self.cache[set_bits][1]

            #reconstruct evicted address by shifting tag bits to the left and adding set bits via OR
            evicted = self.cache[set_bits][0] << self.tag_offset | set_bits << self.set_offset
            
            #update block tag bits to reflect new tag bits
            self.cache[set_bits][0] = tag_bits
        
        # Mark valid
        self.cache[set_bits][2] = True


        #runner file should perform calculations based on the output
        return [hit, dirty, compulsory, evicted]


    #logic for l2 cache access
    def cache_access_l2(self, op, address):
        hit = dirty = False
        compulsory = False

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

                #indicate a compulsory miss happened
                compulsory = True


            # Eviction -- no invalid blocks, so random replacement
            else:

                #calculate random index in set to evict
                randomVal = random.randint(0, self.associativity - 1)
                idx = set_bits + randomVal

                #get dirty status to see if writeback is needed
                dirty = self.cache[idx][1]

                #update tag bits to reflect new address
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
    

    print(f'L1 Instruction Hit Rate: {l1_instruction_hits / l1_instruction_total * 100}%')
    print(f'L1 Data Hit Rate: {l1_data_hits / l1_data_total * 100}%')
    print(f'L2 Hit Rate: {l2_hits / l2_total * 100}%')

    print('Total Energy: ', total_energy / (10 ** 9), 'Joules')
    print('Compulsory Misses: ', compulsoryCount)
    return





if __name__ == '__main__':

    for arg in sys.argv[1:]:
        for assoc in [2,4,8]:
            print(f'Running {arg} with associativity {assoc}')
            main(arg, assoc)
            print('------\n')
        print('---------------------------------\n')
    
        

