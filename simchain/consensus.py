# -*- coding: utf-8 -*-
"""
"""


from .ecc import sha256d
import time 


def caculate_target(bits):
    return (1 << (256 - bits))

def mine(block):
    nonce = 0
    target = caculate_target(block.bits)
    merkle_root_hash = block.get_merkle_root()
    while int(sha256d(block.header(nonce,merkle_root_hash)), 16) >= target:
        nonce += 1
    
    return nonce


def consensus_with_fasttest_minner(peers):
    l,start = [],time.time()
    for peer in peers:
        l.append(peer.consensus())
    return l.index(min(l)),min(l),time.time()-start






def get_block_reward(height,fees = 0):
##    COIN = int(1e8)
    reward_interval = 210000
    reward = 50
    halvings = height // reward_interval

    if halvings >= 64:
        return fees

    reward >>= halvings
    return reward + fees


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from itertools import accumulate
    plt.rcParams['font.sans-serif']=['SimHei']
    plt.rcParams['axes.unicode_minus']=False
    x = [2009,2013,2017,2021,2025,2029,2033]
    d = 4*365*24*6*50
    y = [0,d,d/2,d/4,d/8,d/16,d/32]
    y = list(accumulate(y))
    plt.plot(x,y,'r-')
    plt.xlim([2009,2033])
    plt.ylim([0,21e6])
    plt.xlabel(u'年份')
    plt.ylabel(u'流通中的比特币总量')
    plt.show()
    
##    from datatype import Block,Vin,Vout,Tx
##    block = Block(version=0, 
##              prev_block_hash=None,
##              timestamp=12234, 
##              bits= 21, 
##              nonce=100000,
##              txs=[Tx(tx_in=[Vin(to_spend=None, 
##                                 signature=b'0', 
##                                 pubkey=None)],
##                      tx_out=[Vout(to_addr='143UVyz7ooiAv1pMqbwPPpnH4BV9ifJGFF',
##                                          value=5000000000)],nlocktime= 111)])
##    
##    b = mine(block)
