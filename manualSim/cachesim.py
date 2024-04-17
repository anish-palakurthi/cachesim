import random 

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
        self.tag_offset = self.count_bits(self.set_offset + (self.set_mask))

        # Cache array with tag, dirty, valid for each block
        self.cache = [[0] * 4 for _ in range(self.blocks)]

    def count_bits(self, n):
        count = 0
        while n:
            count += n & 1
            n >>= 1
        return count

    def cache_access_l1(self, op, address):
        hit = dirty = False

        #calculate set and tag bits
        set_bits = (address >> self.set_offset) & self.set_mask
        tag_bits = (address >> self.tag_offset)
        
        if self.cache[set_bits][0] == tag_bits:
            hit = True
            #if it is a write, mark dirty
            if op == 1:
                self.cache[set_bits][1] = True
        else:
            dirty = self.cache[set_bits][1]
            
            #code for cache miss
            #evict
            self.cache[set_bits][0] = tag_bits
        
        # Mark valid
        self.cache[set_bits][2] = True


        #runner file should perform calculations based on the output
        return [hit, dirty]

    def cache_access_l2(self, op, address):
        hit = dirty = False

        #calculate set and tag bits
        set_bits = (address >> self.set_offset) & self.set_mask
        tag_bits = (address >> self.tag_offset)
        
        # Iterate through cache set
        invalid_block = -1
        for i in range(set_bits, set_bits + self.associativity + 1):
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
            # Compulsory miss
            if invalid_block >= 0:
                self.cache[invalid_block][0] = tag_bits
                self.cache[invalid_block][2] = True
            # Eviction
            else:
                idx = set_bits + random.randint(0, self.associativity - 1)
                dirty = self.cache[idx][1]
                self.cache[idx][0] = tag_bits
                self.cache[idx][2] = True
                
        #runner file should perform calculations based on the output
        return [hit, dirty] 


def main(file_path):
    
    l1Data = cachesim(32768, 64, 1)
    l1Instructions = cachesim(32768, 64, 1)
    l2 = cachesim(262144, 64, 4)

    # All measured in ns, penalty in pj
    l1_idle = l1_active = l2_idle = l2_active = dram_idle = dram_active = penalty = 0

    with open(file_path, 'r') as f:
        for line in f:
            hit = dirty = False
            #parse line
            line = line.split()
            op = int(line[0])
            address = int(line[1], 16)
            
            # L1 Access
            if (op == 2):
                hit, dirty = l1Instructions.cache_access_l1(op, address)
            else:
                hit, dirty = l1Data.cache_access_l1(op, address)
                
            l1_active += 0.5
            l2_active += 0.5
            penalty += 5 # from l1-l
            dram_idle += 0.5
            
            # Writeback to L2 and DRAM if dirty eviction
            if dirty:
                penalty += 5 # from l1-l2
                penalty += 640 # from l1-dram
                l1_idle += 50
                l2_active += 5
                l2_idle += 45
                dram_active += 50

            # L1 Miss
            if not hit:
                # Access L2
                hit, dirty = l2.cache_access_l2(op, address)
            
                l1_idle += 4.5  #may be active still but probably not
                l2_active += 4.5   
                dram_idle += 4.5

                if not hit:
                    #DRAM access
                    l1_idle += 50
                    l2_idle += 50
                    dram_active += 50
                    penalty += 640
            
                    if dirty:
                        # Writeback to DRAM
                        penalty += 640
                        l1_idle += 50
                        l2_idle += 50
                        dram_active += 50
            
    total_energy = penalty / 1000 + l1_idle * 0.5 + l1_active + l2_idle * 0.8 + l2_active * 2 + dram_idle + 0.8 + dram_active * 4
    
    print(f'L1 Idle: {l1_idle} ns; L1 Active: {l1_active} ns; L1 Total: {l1_idle + l1_active} ns')
    print(f'L2 Idle: {l2_idle} ns; L2 Active: {l2_active} ns; L2 Total: {l2_idle + l2_active} ns')
    print(f'DRAM Idle: {dram_idle} ns; DRAM Active: {dram_active} ns; DRAM Total: {dram_idle + dram_active} ns')

    print('Total Energy: ', total_energy / (10 ** 9), 'Joules')
    return

if __name__ == '__main__':
    file_path = "Spec_Benchmark/008.espresso.din"
    main(file_path)
        

