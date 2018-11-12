#!/usr/bin/env python3

import os 
from .ecc import sha256d

#A pointer to a transaction unspent output
class Pointer(tuple):

    def __new__(cls,tx_id,n):
        return super(Pointer,cls).__new__(cls,(tx_id,n))

    @property
    def tx_id(self):
        return self[0]

    @property
    def n(self):
        return self[1]
    
    def __repr__(self):
        return "Pointer(tx_id:{0},n:{1})".format(self[0],self[1])
    
    
    
#value input for a transaction
class Vin(tuple):

    def __new__(cls,to_spend,signature,pubkey):
        return super(cls,Vin).__new__(cls,(to_spend,signature,pubkey))
        
    
    @property
    def to_spend(self):
        return self[0]
    
    @property
    def signature(self):
        return self[1]
    
    @property
    def pubkey(self):
        return self[2]

    @property
    def sig_script(self):
        return self[1]+self[2]

    def __repr__(self):
        return "Vin(to_spend:{0},signature:{1},pubkey:{2})".format(self[0],self[1],self[2])
    

#value output for a transaction
class Vout(tuple):
    
    def __new__(cls,to_addr,value):
        return super(Vout,cls).__new__(cls,(to_addr,value))
        
        
    @property
    def to_addr(self):
        return self[0]
    
    @property
    def value(self):
        return self[1]

    @property
    def pubkey_script(self):
        script = "OP_DUP OP_ADDR {0} OP_EQ OP_CHECKSIG".format(self[0])
        return script

    def __repr__(self):
        return "Vout(to_addr:{0},value:{1})".format(self[0],self[1])

#unspent transation output
class UTXO(tuple):
    
    def __new__(cls,
                vout,
                pointer,
                is_coinbase,
                unspent=True,
                confirmed=False,
                ):
        return super(UTXO,cls).__new__(cls,(vout,
                                            pointer,
                                            is_coinbase,
                                            unspent,
                                            confirmed))
        
    
    @property
    def vout(self):
        return self[0]
    
    @property
    def pointer(self):
        return self[1]
    
    @property
    def is_coinbase(self):
        return self[2]

    @property
    def pubkey_script(self):
        return self[0].pubkey_script

    @property
    def unspent(self):
        return self[3]


    @property
    def confirmed(self):
        return self[4]

    def _replace(self,unspent = True, confirmed = False):
        return UTXO(self[0],self[1],self[2],unspent,confirmed)
    
    def __repr__(self):
        return "UTXO(vout:{0},pointer:{1})".format(self[0],self[1])


#transaction
class Tx(tuple):
    
    def __new__(cls,tx_in,tx_out,fee=0,timestamp=0,nlocktime=0):
        return super(Tx,cls).__new__(cls,(tx_in,
                                          tx_out,
                                          fee,
                                          timestamp,
                                          nlocktime))
        
    @property
    def tx_in(self):
        return self[0]
    
    @property
    def tx_out(self):
        return self[1]
    
    @property
    def fee(self):
        return self[2]
    
    @property
    def nlocktime(self):
        return self[3]
    
    @property
    def is_coinbase(self) -> bool:
        return len(self[0]) == 1 and self[0][0].to_spend is None

    @classmethod
    def create_coinbase(cls, pay_to_addr, value):
        return cls(
            tx_in = [Vin(to_spend=None,
                         signature= str(os.urandom(32)),
                         pubkey=None)],
            tx_out = [Vout(to_addr=pay_to_addr,
                           value=value)]
            )

    @property
    def id(self):
        return sha256d(self.to_string())
    
    def to_string(self):
        return "{0}{1}{2}".format(self[0],
                                  self[1],
                                  self[3])

    def __repr__(self):
        return "Tx(id:{0})".format(self.id)


#block
class Block(tuple): 
    def __new__(cls,version,
                prev_block_hash,
                timestamp,
                bits,
                nonce,
                txs):
        return super(Block,cls).__new__(cls,(version,
                                             prev_block_hash,
                                             timestamp,
                                             bits,
                                             nonce,
                                             txs))
        
    
    @property
    def version(self):
        return self[0]
    
    @property
    def prev_block_hash(self):
        return self[1]
    
    @property
    def timestamp(self):
        return self[2]
    
    @property
    def bits(self):
        return self[3]
    
    @property
    def nonce(self):
        return self[4]
    
    @property
    def txs(self):
        return self[5]

    @property
    def merkle_root_hash(self):
        return self.get_merkle_root()

    def _replace(self,nonce = 0):
        return Block(self[0],
                     self[1],
                     self[2],
                     self[3],
                     nonce,
                     self[5])

    def get_merkle_root(self):
        return get_merkle_root_of_txs(self.txs) if self.txs else None
    
    def header(self,nonce = None,merkle_root_hash = None):
        if merkle_root_hash is None:
            merkle_root_hash = self.get_merkle_root()
            
        return "{0}{1}{2}{3}{4}{5}".format(self[0],
                                           self[1],
                                           self[2],
                                           self[3],
                                           merkle_root_hash,
                                           nonce or self[4])

    @property
    def hash(self):
        return sha256d(self.header())

    def __repr__(self):
        return "Block(hash:{0})".format(self.hash)



def get_merkle_root_of_txs(txs):
    return get_merkle_root([tx.id for tx in txs])


def get_merkle_root(level):
    
    while len(level) != 1:
        odd = None
        if len(level) % 2 == 1:
            odd = level.pop()
            
        level = [sha256d(i1+i2) for i1,i2 in pair_node(level)]

        if odd:
            level.append(odd)
    return level[0]
    
def pair_node(l):
    return (l[i:i + 2] for i in range(0, len(l), 2))


if __name__ == "__main__":
    p = Pointer(1,2)
    vout = Vout(1,2)
    utxo = UTXO((1,2),[2,3],True,1)
    vin = Vin(p,b'1',b'12')
    tx = Tx([vin],[vout])
    block = Block(1,2,3,4,5,[tx])
    
    
