# -*- coding: utf-8 -*-

import hashlib,hmac
import os
import binascii

from . import base58
from .mnemonics import Mnemonics
from .ecc import (CurveFp,Point,secp256k1,SigningKey,VerifyingKey,
                 orderlen,number_to_bytes,bytes_to_number,INFINITY)

CHAIN_LEN = 32
ORDER = secp256k1.order
MAX_CHILD_NUM = 2**32-1
KEY_BASE_LEN = secp256k1.baselen


class Keys:

    def __init__(self,key,chain,depth = None,pfp = None,child_index = None):
        self.__pubkey = None
        self.__privkey = None
        
        if isinstance(key,Point):
            self.__pubkey = key

        elif isinstance(key,int):
            assert(0 < key < ORDER)
            self.__privkey = key

        else:
            raise TypeError('Unknown key type'.format(key))

        assert(len(chain) == CHAIN_LEN)
        self.__chain = chain
        
        
        if not depth:
            depth = 0
            pfp = b'\x00'*4
            childmum = 0
            
        assert(depth<256)
        self.__depth = depth
        self.__pfp = pfp
        self.__child_index = child_index


    @classmethod
    def from_master_seed(cls, master_seed):
        deriv = hmac.new(key = b'Simchain seed',msg = master_seed,digestmod = hashlib.sha512).digest()
        master_key = bytes_to_number(deriv[:CHAIN_LEN]) % ORDER
        master_chain = deriv[CHAIN_LEN:]
        return cls(master_key,master_chain)
    
    

    @property
    def sk(self):
        if self.__privkey:
            return SigningKey.from_number(self.__privkey)
        return

    @property
    def pk(self):
        return VerifyingKey.from_point(self.point)
    
    @property
    def chain(self):
        return self.__chain

    @property
    def fp(self):
        sha = hashlib.new('ripemd160')
        str_K = self.pk.to_bytes()
        str_K = hashlib.sha256(str_K.encode()).digest()
        sha_K = sha.update(str_K).digest()
        return sha_K[:4]
    
    @property
    def depth(self):
        return self.__depth

    @property
    def pfp(self):
        if self.__depth == 0:
            return b'x00'*4
        return self.__pfp

    @property
    def child_index(self):
        return self.__child_index

    @property
    def point(self):
        if not self.__pubkey:
            self.__pubkey = secp256k1.generator * self.__privkey
        return self.__pubkey

    def child(self,i):
        assert(0 <= i < MAX_CHILD_NUM)
        assert(self.__depth < 0xff)

        len_i = orderlen(MAX_CHILD_NUM)
        str_i = number_to_bytes(i,len_i)

        if self.__privkey:
            str_k = number_to_bytes(self.__privkey,KEY_BASE_LEN)
            deriv = hmac.new(key=self.__chain,
                             msg=b'\x00' + str_k + str_i,
                             digestmod=hashlib.sha512).digest()
        else:
            str_K = self.pk.to_bytes()
            deriv = hmac.new(key=self.__chain,
                             msg=str_K + str_i,
                             digestmod=hashlib.sha512).digest()

        child_chain = deriv[CHAIN_LEN:]
        child_modifier = bytes_to_number(deriv[:CHAIN_LEN])

        if child_modifier >= ORDER:
            child_modifier %= ORDER

        if self.__privkey:
            child_privkey = (self.__privkey + child_modifier) % ORDER
            if child_privkey == 0:
                return

            child_key = child_privkey

        else:
            child_pubkey = self.point + secp256k1.generator * child_modifier
            if child_pubkey == INFINITY:
                return

            child_key = child_pubkey

        return self.__class__(child_key,
                              child_chain,
                              depth = self.__depth + 1,
                              pfp = self.__pfp,
                              child_index = i)

    


if __name__ == '__main__':
    import os
    master_seed = os.urandom(32)
    keys = Keys.from_master_seed(master_seed)
    
    
    
                    

            
