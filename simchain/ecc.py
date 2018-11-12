
import sys
import operator
import math

import struct
import binascii
from random import SystemRandom
from hashlib import sha256,new
from .base58 import b58encode_check,b58decode_check

_K = (0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
      0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
      0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
      0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
      0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
      0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
      0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
      0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
      0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
      0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
      0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
      0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
      0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
      0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
      0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
      0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2)

_H = (0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19)

class sha_256:

    def __init__(self,m = None):
        self.buffer = b''
        self.counter = 0
        self.H = _H
        self.K = _K

        if m:
            self.update(m)


    def rotr(self, x, y):
        return ((x >> y) | (x << (32-y))) & 0xFFFFFFFF
        
    def operate(self,c):
        w = [0]*64
        w[0:16] = struct.unpack('!16L', c)
        
        for i in range(16, 64):
            s0 = self.rotr(w[i-15], 7) ^ self.rotr(w[i-15], 18) ^ (w[i-15] >> 3)
            s1 = self.rotr(w[i-2], 17) ^ self.rotr(w[i-2], 19) ^ (w[i-2] >> 10)
            w[i] = (w[i-16] + s0 + w[i-7] + s1) & 0xFFFFFFFF
        
        a,b,c,d,e,f,g,h = self.H
        
        for i in range(64):
            s0 = self.rotr(a, 2) ^ self.rotr(a, 13) ^ self.rotr(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            t2 = s0 + maj
            s1 = self.rotr(e, 6) ^ self.rotr(e, 11) ^ self.rotr(e, 25)
            ch = (e & f) ^ ((~e) & g)
            t1 = h + s1 + ch + self.K[i] + w[i]
            
            h = g
            g = f
            f = e
            e = (d + t1) & 0xFFFFFFFF
            d = c
            c = b
            b = a
            a = (t1 + t2) & 0xFFFFFFFF
            
        self.H = [(x+y) & 0xFFFFFFFF for x,y in zip(self.H, [a,b,c,d,e,f,g,h])]

    def update(self,m):
        if not m:
            return 
        self.buffer = m
        self.counter = len(m)
        length = struct.pack('!Q', int(self.counter*8))
        
        while len(self.buffer) >= 64:
            self._operate(self.buffer[:64])
            self.buffer = self.buffer[64:]

        mdi = self.counter % 64
        if mdi < 56:
            padlen = 55-mdi
            self.buffer += (b'\x80'+(b'\x00'*padlen) + length)
            self.operate(self.buffer)
        else:
            padlen = 119-mdi
            self.buffer += (b'\x80'+(b'\x00'*padlen) + length)
            for i in range(2):
                self.operate(self.buffer[i*64:(i+1)*64])
        
    def digest(self):
        return struct.pack('!8L',*self.H)
    

    def hexdigest(self):
        return binascii.hexlify(self.digest()).decode()
    

    
def sha256d(string):
    if not isinstance(string, bytes):
        string = string.encode()
        
    return sha256(sha256(string).digest()).hexdigest()

def inv_mod(b, p):
    
    if b < 0 or p <= b:
        b = b % p

    c, d = b, p
    uc, vc, ud, vd = 1, 0, 0, 1
    while c != 0:
        q, c, d = divmod(d, c) + (c,)
        uc, vc, ud, vd = ud - q * uc, vd - q * vc, uc, vc
        
    assert d == 1
    if ud > 0:
        return ud
    else:
        return ud + p


def leftmost_bit(x):
    assert x > 0
    result = 1
    while result <= x:
        result = 2 * result
    return result // 2

class CurveFp(object):
    
    def __init__(self, p, a, b):
        """ y^2 = x^3 + a*x + b (mod p)."""
        self.p = p
        self.a = a
        self.b = b
        

    def contains_point(self, x, y):
        return (y * y - (x * x * x + self.a * x + self.b)) % self.p == 0


    def show_all_points(self):
        return [(x,y) for x in range(self.p) for y in range(self.p) if
                (y * y - (x * x * x + self.a * x + self.b)) % self.p == 0]

    def __repr__(self):
        return "Curve(p={0:d}, a={1:d}, b={2:d})".format(self.p, self.a, self.b)


class Point(object):
    
    def __init__(self, curve, x, y, order=None):
        
        self.curve = curve
        self.x = x
        self.y = y
        self.order = order
        # self.curve is allowed to be None only for INFINITY:
        if self.curve:
            assert self.curve.contains_point(x, y)
        if order:
            assert self * order == INFINITY

    def __eq__(self, other):
        """Is this point equals to another"""
        if self.curve == other.curve \
           and self.x == other.x \
           and self.y == other.y:
            return True
        else:
            return False

    def __add__(self, other):
        """Add one point to another point."""
        
        if other == INFINITY:
            return self
        if self == INFINITY:
            return other
        assert self.curve == other.curve
        
        if self.x == other.x:
            if (self.y + other.y) % self.curve.p == 0:
                return INFINITY
            else:
                return self.double()
        
        p = self.curve.p
        l = ((other.y - self.y) * \
             inv_mod(other.x - self.x, p)) % p

        x3 = (l * l - self.x - other.x) % p
        y3 = (l * (self.x - x3) - self.y) % p

        return Point(self.curve, x3, y3)

    def __mul__(self, other):
        e = other
        if self.order:
            e = e % self.order
        if e == 0:
            return INFINITY
        if self == INFINITY:
            return INFINITY

        e3 = 3 * e
        negative_self = Point(self.curve, self.x, -self.y, self.order)
        i = leftmost_bit(e3) // 2
        result = self
        
        while i > 1:
            result = result.double()
            if (e3 & i) != 0 and (e & i) == 0:
                result = result + self
            if (e3 & i) == 0 and (e & i) != 0:
                result = result + negative_self
            i = i // 2
        return result

    def __rmul__(self, other):
        """Multiply a point by an integer."""
        return self * other

    def __repr__(self):
        if self == INFINITY:
            return "infinity"
        return "({0},{1})".format(self.x, self.y)

    def double(self):
        """the double point."""
        if self == INFINITY:
            return INFINITY
        
        p = self.curve.p
        a = self.curve.a
        l = ((3 * self.x * self.x + a) * \
             inv_mod(2 * self.y, p)) % p
        
        x3 = (l * l - 2 * self.x) % p
        y3 = (l * (self.x - x3) - self.y) % p

        return Point(self.curve, x3, y3)

    def invert(self):
        return Point(self.curve,self.x,-self.y % self.curve.p)
    

INFINITY = Point(None, None, None)

def show_points(p,a,b):
    return [(x, y) for x in range(p) for y in range(p)
            if (y*y-(x*x*x+a*x+b))%p ==0]

def double(x,y,p,a,b):
    l = ((3 * x * x + a) * inv_mod(2 * y,p)) % p
    x3 = (l * l -2 * x) % p
    y3 = (l *(x - x3) - y) % p
    return x3,y3

def add(x1,y1,x2,y2,p,a,b):

    if x1 == x2 and y1 == y2:
        return double(x1,y1,p,a,b)

    l = ((y2 - y1) * inv_mod(x2 - x1,p)) % p
    x3 = (l * l - x1 - x2) % p
    y3 = (l * (x1 - x3) - y1) % p
    return x3,y3


def get_bits(n):
    bits = []
    while n != 0:
        bits.append(n & 1)
        n >>= 1
    return bits


def orderlen(order):
    return (1+len("%x" % order))//2

def bytes_to_number(string):
    return int(binascii.hexlify(string), 16)


def number_to_bytes(num,l):
    fmt_str = "%0" + str(2 * l) + "x"
    string = binascii.unhexlify((fmt_str % num).encode())
    return string


def sigencode_strings(r, s, l):
    r_str = number_to_bytes(r,l)
    s_str = number_to_bytes(s,l)
    return (r_str, s_str)



def sigencode_string(r, s, l):
    r_str, s_str = sigencode_strings(r, s, l)
    return r_str + s_str


def bytes_to_number_fixedlen(string):
    return int(binascii.hexlify(string), 16)

def sigdecode_string(signature, l):
    r = bytes_to_number_fixedlen(signature[:l])
    s = bytes_to_number_fixedlen(signature[l:])
    return r, s



PY3 = sys.version_info[0] == 3

if sys.version_info[1] <= 1:
    def int2byte(i):
        return bytes((i,))
else:
    int2byte = operator.methodcaller("to_bytes", 1, "big")

def b(s):
    return s.encode("latin-1")


class PRNG:
    
    def __init__(self, seed):
        self.generator = self.block_generator(seed)

    def __call__(self, numbytes):
        a = [next(self.generator) for i in range(numbytes)]

        if PY3:
            return bytes(a)
        else:
            return "".join(a)

    def block_generator(self, seed):
        counter = 0
        while True:
            for byte in sha256(("prng-%d-%s" % (counter, seed)).encode()).digest():
                yield byte
            counter += 1


def bits_and_bytes(order):
    bits = int(math.log(order - 1, 2) + 1)
    bytes = bits // 8
    extrabits = bits % 8
    return bits, bytes, extrabits

def lsb_of_ones(numbits):
    return (1 << numbits) - 1

def randrange_from_seed__trytryagain(seed, order):
    bits, bytes, extrabits = bits_and_bytes(order)
    generate = PRNG(seed)
    while True:
        extrabyte = b("")
        if extrabits:
            extrabyte = int2byte(ord(generate(1)) & lsb_of_ones(extrabits))
        guess = bytes_to_number(extrabyte + generate(bytes)) + 1
        if 1 <= guess < order:
            return guess

class Curve:
    def __init__(self, name, curve, generator):
        self.name = name
        self.curvefp = curve
        self.generator = generator
        self.order = generator.order
        self.baselen = orderlen(self.order)



_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_b = 0x0000000000000000000000000000000000000000000000000000000000000007
_a = 0x0000000000000000000000000000000000000000000000000000000000000000
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8

curve_secp256k1 = CurveFp(_p, _a, _b)
generator_secp256k1 = Point(curve_secp256k1, _Gx, _Gy, _r)
secp256k1 = Curve("SECP256k1",curve_secp256k1,generator_secp256k1)



class SigningKey(object):
    
    def __init__(self,curve = secp256k1):
        self.curve = curve
        self.order = curve.order
        self.baselen = curve.baselen
        self.generator = curve.generator
        


    @classmethod
    def from_bytes(cls,string,curve = secp256k1):
        number = bytes_to_number(string) % curve.order
        return cls.from_number(number,curve = secp256k1)
    
    @classmethod
    def from_number(cls,number,curve = secp256k1):
        self = cls(curve = curve)
        self.__number = number
        
        pubkey_point = self.curve.generator*number
        self.__pubkey = VerifyingKey.from_point(pubkey_point)
        return self


    def to_bytes(self):
        s = number_to_bytes(self.__number,self.baselen)
        return s

    def get_verifying_key(self):
        return self.__pubkey
    
    def sign(self,message,sigencode = sigencode_string):
        k,n,G = self.__number,self.order,self.generator
        h = bytes_to_number(message)
        r, s = 0, 0
        while r == 0 or s == 0:
            rk = SystemRandom().randrange(1, n)
            rG = rk*G
            r = rG.x
            s = ((h + (r*k)%n)*inv_mod(rk, n)) % n
        
        return sigencode(r,s,self.baselen)

class VerifyingKey(object):

    def __init__(self,curve = secp256k1):
        self.curve = curve
        self.order = curve.order
        self.baselen = curve.baselen
        self.generator = curve.generator

    @classmethod
    def from_bytes(cls,string,curve = secp256k1):
        l = curve.baselen
        xs = string[:l]
        ys = string[l:]
        x = bytes_to_number(xs)
        y = bytes_to_number(ys)
                             
        if not curve.curvefp.contains_point(x,y):
            return
        point = Point(curve.curvefp,x,y,curve.order)
        return cls.from_point(point)

    @classmethod
    def from_point(cls,point,curve = secp256k1):
        self = cls(curve = curve)
        self.point = point
        return self


    def to_bytes(self):
        order = self.order
        x_str = number_to_bytes(self.point.x,self.baselen)
        y_str = number_to_bytes(self.point.y,self.baselen)
        return x_str + y_str
        

    def verify(self,sig,message,sigdecode = sigdecode_string):
        r,s = sigdecode(sig,self.baselen)
        K,n,G = self.point,self.order,self.generator
        h = bytes_to_number(message)
        w = inv_mod(s,n)
        u1, u2 = (h * w) % n,(r * w) % n
        p = u1 * G + u2 * K
        return r == p.x % n
    

    @staticmethod
    def convert_to_addr(p_str = None):
        p_str = p_str 
        return convert_pubkey_to_addr(p_str)
    

def verify_signature_by_pubkey(pk_str,to_addr,signature,string):
    pubkey_as_addr = convert_pubkey_to_addr(pk_str)
    verifying_key = VerifyingKey.from_string(pk_str)

    if pubkey_as_addr != to_addr:
        logger.info("pubkey does not match")
        return 

    message = build_message(string)
    
    if not verifying_key.verify(signature, message):
        logger.info("signature does not match")
        return 

    return True

def build_message(string):
    return sha256d(string).encode()

def convert_pubkey_to_addr(pubkey_str):
    sha = sha256(pubkey_str).digest()
    ripe = new('ripemd160', sha).digest()
    return b58encode_check(b'\x00' + ripe).decode()

def sign(message,G,k):
    n = G.order
    mess_hash = sha256(message).digest()
    h = bytes_to_number(mess_hash)
    r, s, = 0, 0
    while r == 0 or s == 0:
        rk = SystemRandom().randrange(1, n)
        rG = rk*G
        r = rG.x
        s = ((h + (r*k)%n)*inv_mod(rk, n)) % n
    return r,s

def sign_same_rk(message,G,k,rk):
    n = G.order
    mess_hash = sha256(message).digest()
    h = bytes_to_number(mess_hash)
    r, s, = 0, 0
    while r == 0 or s == 0:
        rG = rk*G
        r = rG.x
        s = ((h + (r*k)%n)*inv_mod(rk, n)) % n
    return r,s

def verify(sig,G,K,message):
    r,s = sig
    n = G.order
    mess_hash = sha256(message).digest()
    h = bytes_to_number(mess_hash)
    w = inv_mod(s,n)
    u1, u2 = (h * w) % n,(r * w) % n
    p = u1 * G + u2 * K
    return r == p.x % n 




#######Try all possibilities

from time import clock
from math import sqrt,ceil
def crack_by_brute_force(G,K):
    start_time = clock()
    for k in range(G.order):
        if k*G == K:
            end_time = clock()
            print ("Priv key: k = " + str(k))
            print ("Time: " + str(round(end_time - start_time, 3)) + " secs")
            
            return k


#######use baby step giant step     
def crack_by_bsgs(G, K):
    start_time = clock()
    m = int(ceil(sqrt(G.order)))
    table = {}
    for i in range(m):
        iG = i*G
        table[str(iG)] = i

    for j in range(m):
        jmG = j*m*G
        R = K - jmG.invert()
        if str(R) in table.keys():
            i = table[str(R)]
            end_time = clock()
            print ("Priv key: k = " + str(() % n))
            print ("Time: " + str(round(end_time - start_time, 3)) + " secs")
            return i + j*m


#######use pollard's rho alg
def crack_by_pollard_rho(G,K,bits):
    start_time = clock()
    R,n = [], G.order
    for i in range(2**bits):
        a, b = SystemRandom().randrange(0,n), SystemRandom().randrange(0,n)
        R.append(a * G + b *K, a, b)

    At, Bt = SystemRandom().randrange(0,n), SystemRandom().randrange(0,n)
    Ah, Bh = At, Bt
    T = At * G + Bt * K
    H = Ah * G + Bh * K
    while True:
        j = int(bin(T.x)[len(bin(T.x)) - bits : len(bin(T.x))], 2)
        T, At, Bt = T + R[j][0], (At + R[j][1]) % n, (Bt + R[j][2]) % n

        j = int(bin(H.x)[len(bin(H.x)) - bits : len(bin(H.x))], 2)
        H, Ah, Bh = H + R[j][0], (Ah + R[j][1]) % n, (Bh + R[j][2]) % n
        
        if(T == H):
            break
    
    if Bh == Bt:
        end_time = clock()
        k = -1
        print ("failed")
        print (str(end_time - start_time) + " secs")
    else:
        end_time = clock()
        k = (At - Ah) * inv_mod((Bh - Bt) % n, n) % n
        print ("Priv key: k = " + str((At - Ah) * inv_mod((Bh - Bt) % n, n) % n))
        print ("Time: " + str(round(end_time - start_time, 3)) + " secs")
    return k


#by signature        
def crack_by_signature_form_same_rk(G,K,message1, sig1, message2, sig2):
    r1, s1 = sig1
    r2, s2 = sig2
    n = G.order
    assert r1 == r2 
    mess1_hash = sha256(message1).digest()
    h1 = bytes_to_number(mess1_hash)
    mess2_hash = sha256(message2).digest()
    h2 = bytes_to_number(mess2_hash)

    rk_candidates = [
        (h1 - h2) * inv_mod((s1 - s2) % n, n) % n,
        (h1 - h2) * inv_mod((s1 + s2) % n, n) % n,
        (h1 - h2) * inv_mod((-s1 - s2) % n, n) % n,
        (h1 - h2) * inv_mod((-s1 + s2) % n, n) % n,
        ]

    for rk in rk_candidates:
        k = inv_mod(r1, n) * ((s1 * rk) % n - h1) % n
        if k * G == K:
            return k
            print ("Priv key: k = " + str(k))
        else:
            print("not found")

        






if __name__ == "__main__":
    G = secp256k1.generator
##    ks = (100,1000,10000,100000)
##    sk = SigningKey.from_number(1111)
##    pk = sk.get_verifying_key()
##    me = b'111'
##    sig = sk.sign(me)
##    flag = pk.verify(sig,me)
##    
##    Ks = [k*G for k in ks]
##    time_spent = []
##    for K in Ks:
##        ts = crack_by_brute_force(G,K)
##        time_spent.append(ts)
##    time_spent = [0.071,1.172,16.45,208.364]
##    import matplotlib.pyplot as plt
##    plt.rcParams['font.sans-serif']=['SimHei']
##    plt.rcParams['axes.unicode_minus']=False
##    plt.plot(ks,time_spent,'r-')
##    plt.xlabel(u'计算私钥k')
##    plt.ylabel(u'计算时间/s')
##    plt.show()
##    

    
    
    
