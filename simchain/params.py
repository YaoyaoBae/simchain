#!/usr/bin/env python3
class Params:
    
    MAX_FUTURE_BLOCK_TIME = 10*6
    
    PERIOD_FOR_ONE_CONSENSUS = 1 * 5 #we hope 10 secs for one consensus
    
    PERIOD_FOR_TOTAL_BLOCKS = 5 * 20 #adjust difficults 20 blocks are found 
    
    TOTAL_BLOCKS = PERIOD_FOR_TOTAL_BLOCKS/PERIOD_FOR_ONE_CONSENSUS
    
    INITIAL_DIFFICULTY_BITS = 18 
    
    FIX_BLOCK_REWARD = 500
    
    MAX_TX_NUMBER_FOR_MINER = 5 
    
    INIT_NUMBER_OF_PEERS = 12
    
    INIT_COIN_PER_PEER = 100000
    
    FIX_FEE_PER_TX = 10
    
    UPPER_BOUND_OF_CONSENSUS_PEERS = 60./100
    
    LOWWER_BOUND_OF_CONSENSUS_PEERS = 20./100
    
    SLOW_PEERS_IN_NETWORK = 20./100
    
    SLOWER_PEERS_IN_NETWORK = 10./100
    
    
