from numpy import (array,asarray,identity,where,triu,tril,diag,
                   where,dot,prod,around,array_str,)
from numpy.random import (randint,normal,permutation)
from numpy.linalg import (solve,det,norm)
from math import sqrt,isclose
from hashlib import sha512

__all__ = ['rand_matrix','good_basis','bad_basis','hadamard',
           'rand_unimodular_matrix','convert_to_Zq','discrete_normal',
           'hash_to_baseb','solve_cvp']

def good_basis(n,ur = 0.9,d = 4):
    I = identity(n,dtype = 'int')
    A = randint(-d,d+1,(n,n))
    k = int(sqrt(n))*d
    while True:
        good = A + k * I
        if hadamard(good) > ur:
            break
        k *= 2
    return good


    
def bad_basis(good_basis,lr = 0.10,d = 5):
    good = asarray(good_basis)
    _check_basis_type(good)
    n = good.shape[0]
    T = good.T.copy()
    bad = shuffle(T,d)
    while hadamard(bad.T) > 0.1:
        bad = shuffle(T,d)

    return bad.T
    
    
    
def shuffle(A,d = 5):
    n = A.shape[0]
    r = randint(1,d+1,(n,1))
    A += permutation(A)*r
    return A
            
def hadamard(basis):
    basis = asarray(basis)
    _check_basis_type(basis)
    return _calc_hadamard_ratio(basis)

def convert_to_Zq(M,q):
    mq = int((q-1)/2)
    A = where(M % q <= mq,M,M % q - q)
    B = where(M % q > mq,A,M % q)
    return B
    
def rand_matrix(a,b,n,m):
    return randint(a,b,(n,m))

def discrete_normal(m,sigma):
    return normal(0,sigma,m).astype('int')


def rand_unimodular_matrix(n,lb =-1,ub = 10):
    assert n <= 10
    rm,I = randint(lb,ub,(n,n)),\
           randint(-1,2,n)
    
    I = where(I != 0,I,1)
    tu = triu(rm,1) + diag(I)
    tl = tril(rm,-1) + diag(I)
    return dot(tl,tu)

def _check_basis_type(basis):
    shape = basis.shape
    assert len(shape) == 2
    assert shape[0] == shape[1]
    
def _calc_hadamard_ratio(A):
    d = abs(det(A))
    n = A.shape[0]
    mult = prod(norm(A,axis = 0))
    if isclose(mult,0.):
        return 0.
    return (d/mult)**(1./n)

def solve_cvp(basis,w):
    basis,w = asarray(basis),asarray(w)
    x = solve(basis,w)
    rx = around(x).astype('int')
    return dot(basis,rx)

def hash_to_baseb(matrix, message,k,b=3):
    hexval = sha512(array_str(matrix).encode() + message).hexdigest()
    return array(list(map(int, list(b2b(hexval, 16, b)[:k]))))

base_symbols='0123456789abcdefghijklmnopqrstuvwxyz'
def v2r(n, b): 
    digits = ''
    while n > 0:
        digits = base_symbols[n % b] + digits
        n  = n // b
    return digits

def r2v(digits, b): 
    n = 0
    for d in digits:
        n = b * n + base_symbols[:b].index(d)
    return n

def b2b(digits, b1, b2):
    return v2r(r2v(digits, b1), b2)
