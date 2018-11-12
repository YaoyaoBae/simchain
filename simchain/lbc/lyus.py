import numpy as np
import hashlib
from . import utils
from math import exp,sqrt

class SigningKey:

    def __init__(self,d,n,m,k,q,sigma,b):
        self.d,self.n,self.m,self.k,self.q,self.b = d,n,m,k,q,b
        self.sigma = sigma
        self._is_pubkey_generate = False

    @classmethod
    def from_numbers(cls,d,n,m,k,q,sigma = 10,b = 3):
        self = cls(d=d,n=n,m=m,k=k,q=q,sigma = sigma,b = b)
        M = utils.rand_matrix(-d,d+1,m,k)
        self.S = utils.convert_to_Zq(M,q)
        return self


    def get_verifying_key(self):
        if not self._is_pubkey_generate:
            d,n,m,k,q,S = self.d,self.n,self.m,self.k,self.q,self.S
            sigma,b = self.sigma,self.b
            self.pubkey = VerifyingKey.from_matrix(S,d,n,m,k,q,sigma,b)
            self._is_pubkey_generate = True
        return self.pubkey

    def sign(self,message):
        M = 1+np.random.rand()
        sigma,m,k,b,q = self.sigma,self.m,self.k,self.b,self.q
        pk = self.get_verifying_key()
        S,A,T = self.S,pk.A,pk.T

        while True:
            y = utils.discrete_normal(m,sigma)
            Ay = np.dot(A,y)
            c = utils.hash_to_baseb(Ay,message,k,b)
            Sc =np.dot(S,c)
            z = Sc + y
            try:
                pxe = -z.dot(z) + y.dot(y)
                val = exp(pxe / (2*sigma**2)) / M
            except OverflowError:
                print ('OF')
                continue

            if np.random.rand() < min(val,1.0):
                break
        return z,c
        

class VerifyingKey:

    def __init__(self,d,n,m,k,q,sigma,b):
        self.d,self.n,self.m,self.k,self.q,self.b = d,n,m,k,q,b
        self.sigma = sigma 

    @classmethod
    def from_matrix(cls,S,d,n,m,k,q,sigma,b):
        self = cls(d=d,n=n,m=m,k=k,q=q,sigma = sigma,b = b)
        M = utils.rand_matrix(-d,d+1,n,m)
        A = utils.convert_to_Zq(M,q)
        T = np.dot(A,S)
        self.A,self.T = A,T
        return self

    def verify(self,signature,message):
        z,c = signature
        sigma,b,k,m = self.sigma,self.b,self.k,self.m
        A,T = self.A,self.T
        AzTc = np.dot(A,z) - np.dot(T,c)
        hc = utils.hash_to_baseb(AzTc,message,k,b)
        if np.linalg.norm(z) <= 2*sigma*sqrt(m) and \
           np.allclose(c,hc):
            return True
        return False
