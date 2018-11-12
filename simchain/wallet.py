# -*- coding: utf-8 -*-

import os
from .ecc import (SigningKey,VerifyingKey,randrange_from_seed__trytryagain,sha256d,
                 convert_pubkey_to_addr,secp256k1)
from .logger import logger



class Keys(tuple):
    
    def __new__(cls,sk,pk):
        return super(Keys,cls).__new__(cls,(sk,pk))
    
    @property
    def sk(self):
        return self[0]
    
    @property
    def pk(self):
        return self[1]
    
    def __repr__(self):
        return "keys pair"
    


class Wallet(object):  
    
    def __init__(self,keys_generation_method ='ecc'):
        self.keys_generation_method = keys_generation_method
        self.keys = []
        self.addrs = []
    
    def generate_keys(self):
        if self.keys_generation_method == 'ecc':
            sk,pk = generate_keys_by_ecdsa()
            keys = Keys(sk,pk)
            addr = convert_pubkey_to_addr(pk.to_bytes())
            self.keys.append(keys)
            self.addrs.append(addr)


    @property
    def nok(self):
        return len(self.keys)

    def __repr__(self):
        return "wallet"

def make_key(seed):
    number = randrange_from_seed__trytryagain(seed,secp256k1.order)
    return SigningKey.from_number(number)

def generate_keys_by_ecdsa():
    seed = os.urandom(secp256k1.baselen)
    signkey = make_key(seed)
    pubkey = signkey.get_verifying_key()
    return signkey,pubkey



if __name__ == '__main__':
    w = Wallet()
    w.generate_keys()
    
    
