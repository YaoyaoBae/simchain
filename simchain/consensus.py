# -*- coding: utf-8 -*-
"""
"""


from .ecc import sha256d
from .datatype import Block,Vin,Vout,Tx


def caculate_target(bits):
    return (1 << (256 - bits))


def mine(block):
    nonce = 0
    target = caculate_target(block.bits)
    while int(sha256d(block.header(nonce)), 16) >= target:
        nonce += 1
    
    return nonce

if __name__ == "__main__":
    block = Block(version=0, 
              prev_block_hash=None,
              merkle_root_hash = b'1111',
              timestamp=12234, 
              bits= 21, 
              nonce=100000,
              txs=[Tx(tx_in=[Vin(to_spend=None, 
                                 signature=b'0', 
                                 pubkey=None)],
                      tx_out=[Vout(to_addr='143UVyz7ooiAv1pMqbwPPpnH4BV9ifJGFF',
                                          value=5000000000)],nlocktime= 111)])
    
    b = mine(block)
