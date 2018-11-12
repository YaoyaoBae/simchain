

from .logger import logger
from .ecc import convert_pubkey_to_addr,VerifyingKey,sha256d

class Stack(list):
    
    push = list.append
    
    def peek(self):
        return self[-1]

    
class LittleMachine(object):

    def __init__(self):
        self.stack = Stack()
        self._map = {
            "OP_ADD":          self.add,
            "OP_MINUS":        self.minus,
            "OP_MUL":          self.mul,
            "OP_EQ":           self.equal_check,
            "OP_EQUAL"    :    self.equal,
            "OP_CHECKSIG":     self.check_sig,
            "OP_ADDR":         self.calc_addr,
            "OP_DUP"      :    self.dup,
            "OP_NDUP"     :    self.ndup,
            "OP_CHECKMULSIG" : self.check_mulsig,
            "OP_MULHASH":      self.calc_mulhash,
            }


    def set_script(self,script,message = b''):
        self.clear()
        self.result = True
        self.pointer = 0
        self.message = message
        self.script = script
        

    def clear(self):
        self.stack.clear()
        
    def peek(self):
        return self.stack.peek()
    
    def pop(self):
        return self.stack.pop()

    def push(self,value):
        self.stack.push(value)

    def evaluate(self,op):
        if op in self._map:
            self._map[op]()

        elif isinstance(op,str) or\
             isinstance(op,bytes)or\
             isinstance(op,int) or\
             isinstance(op,bool):
            self.push(op)
        else:
            logger.info('Uknow opcode: '.format(op))

    def add(self):
        self.push(self.pop() + self.pop())

    def minus(self):
        last = self.pop()
        self.push(self.pop() - last)

    def mul(self):
        self.push(self.pop() * self.pop())

    def dup(self):
        self.push(self.peek())

    def ndup(self):
        n = self.pop()
        for val in self.stack[-n:]:
            self.push(val)
        self.push(n)

    def equal_check(self):
        flag = self.pop() == self.pop()
        if not flag:
            self.result = False

    def equal(self):
        self.push(self.pop()==self.pop())

    def calc_mulhash(self):
        n = self.pop()
        pk_strs = [self.pop() for _ in range(n)]
        s = b''
        for val in pk_strs[::-1]:
            s += val
        self.push(sha256d(s))
        

    def check_sig(self):
        pk_str = self.pop()
        sig = self.pop()
        verifying_key = VerifyingKey.from_bytes(pk_str)
        
        try:
            flag = verifying_key.verify(sig,self.message)
        except Exception:
            flag = False
        self.push(flag)

    def check_mulsig(self):
        n = self.pop()
        pk_strs = [self.pop() for _ in range(n)]
        m = self.pop()
        sigs = [self.pop() for _ in range(m)]
        pk_strs = pk_strs[-m:]
        for i in range(m):
            verifying_key = VerifyingKey.from_bytes(pk_strs[i])
            try:
                flag = verifying_key.verify(sigs[i],self.message)
            except Exception:
                flag = False
            if not flag:
                falg = False
                break
        self.push(flag)
        

    def calc_addr(self):
        pk_str = self.pop()
        self.push(convert_pubkey_to_addr(pk_str))
        
    def run(self):
        while (self.pointer < len(self.script)):
            op = self.script[self.pointer]
            self.pointer += 1
            self.evaluate(op)
            
        if not self.result:
            return False
        else:
            return self.peek()


if __name__ == "__main__":
    from datatype import Vin,Vout
    from ecc import SigningKey,convert_pubkey_to_addr
##    k = 12356
##    k1 = 23464
##    sk = SigningKey.from_number(k)
##    pk = sk.get_verifying_key()
##
##    sk1 = SigningKey.from_number(k1)
##    pk1 = sk1.get_verifying_key()
##    addr = convert_pubkey_to_addr(pk.to_bytes())
##    addr1 = convert_pubkey_to_addr(pk1.to_bytes())
##    
##    m1 = b'hello'
##    m2 = b'go away'
##    sig = sk.sign(m1)
##    sig1 = sk1.sign(m2)
##    vin = Vin(None,sig1,pk1.to_bytes())
##    vout = Vout(addr,10)
##    
##    sig_script = [vin.sig_script[:64],vin.sig_script[64:]]
##    pubkey_script = vout.pubkey_script.split(' ')


    kA = 3453543
    kB = 2349334
    skA = SigningKey.from_number(kA)
    skB = SigningKey.from_number(kB)
    pkA = skA.get_verifying_key()
    pkB = skB.get_verifying_key()
    message = b'I love blockchain'

    sigA = skA.sign(message)
    sigB = skB.sign(message)
    Hash = sha256d(pkA.to_bytes()+pkB.to_bytes())
    sig_script = [sigA,sigB,2,pkA.to_bytes(),pkB.to_bytes(),2]
    pubkey_script = ['OP_NDUP','OP_MULHASH',Hash,'OP_EQ',2,'OP_CHECKMULSIG']
    script = sig_script + pubkey_script
    machine = LittleMachine()
    machine.set_script(script,message)
    print (machine.run())
    
##    script = [a,1,2,'OP_DUP','OP_ADD','OP_EQ']
##    machine = LittleMachine()
##    machine.set_script(script)
##    print(machine.run())

    

            

    


    
        
        
