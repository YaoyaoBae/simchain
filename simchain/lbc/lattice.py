
from numpy import (asarray,around,allclose,dot)
from numpy.linalg import (solve,det)
from numpy.random import (uniform,randint)
from math import sqrt,pi,e
class Lattice:

    def __init__(self,basis):
        
        self.basis = asarray(basis)
        _check_basis_type(self.basis)
        self.dim = self.basis.shape[0]
        
    def contains(self,other):
        if self.basis is not None:
            b = asarray(other)
            try:
                x = solve(self.basis,b)
            except Exception:
                return False
            x_r = around(x)
            return allclose(x_r,x)
        return False


    def non_lattice_point(self,lb=-10,ub=10):
        n,basis = self.dim,self.basis
        while True:
            r = uniform(lb,ub,n)
            v = around(dot(basis,r),2)
            if not self.contains(v):
                break
        return v

    def lattice_point(self,lb=-10,ub=10):
        n,basis = self.dim,self.basis
        v = randint(lb,ub,n)
        return dot(basis,v)

    def fundamental_point(self,lb = 0,ub = 1):
        n,basis = self.dim,self.basis
        v = uniform(lb,ub,n)
        return dot(basis,v)

    def det(self):
        return abs(det(self.basis))

    def gaussian_expect(self):
        d,n = self.det(),self.dim
        return sqrt(n/(2*pi*e))*det**(1./n)

def _check_basis_type(basis):
    shape = basis.shape
    assert len(shape) == 2
    assert shape[0] == shape[1]            





if __name__ == "__main__":
    a = [[1,2],[2,1]]
    l = Lattice(a)
    
