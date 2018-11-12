

from .logger import logger

from .ecc import convert_pubkey_to_addr,VerifyingKey
class Stack(list):
    push = list.append
    def top(self):
        return self[-1]

    
class LittleMachine(object):

    def __init__(self):
        self.data_stack = Stack()
        self._map = {
            "OP_ADD":          self.add,
            "OP_MINUS":        self.minus,
            "OP_MUL":          self.mul,
            "OP_EQ":           self.equal_check,
            "OP_CHECKSIG":     self.check_sig,
            "OP_CHECKADDR":    self.check_addr,
            "OP_DUP"      :    self.dup,
            }


    def set_script(self,script,message = b''):
        self.result = True
        self.pointer = 0
        self.message = message
        self.script = script
        
    
    def top(self):
        return self.data_stack.top()
    
    def pop(self):
        return self.data_stack.pop()

    def push(self,value):
        self.data_stack.push(value)

    def judge(self,op):
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
        self.push(self.top())

    def equal_check(self):
        flag = self.pop() == self.pop()
        if not flag:
            self.result = False

    def check_sig(self):
        pk_str = self.pop()
        sig = self.pop()
        verifying_key = VerifyingKey.from_string(pk_str)
        flag = verifying_key.verify(sig,self.message)
        self.push(flag)

    def check_addr(self):
        pk_str = self.pop()
        self.push(convert_pubkey_to_addr(pk_str))
        
    def run(self):
        while (self.pointer < len(self.script)):
            op = self.script[self.pointer]
            self.pointer += 1
            self.judge(op)
            
        if not self.result:
            return False
        else:
            return self.top()


if __name__ == "__main__":
    from datatype import Vin,Vout
    from ecc import SigningKey,convert_pubkey_to_addr
    k = 12356
    k1 = 23464
    sk = SigningKey.from_number(k)
    pk = sk.get_verifying_key()

    sk1 = SigningKey.from_number(k1)
    pk1 = sk1.get_verifying_key()
    addr = convert_pubkey_to_addr(pk.to_string())
    addr1 = convert_pubkey_to_addr(pk1.to_string())
    
    m1 = b'hello'
    m2 = b'go away'
    sig1 = sk.sign(m1)
    sig2 = sk1.sign(m2)
    vin = Vin(None,sig2,pk1.to_string())
    vout = Vout(addr1,10)
    
    sig_script = [vin.sig_script[:64],vin.sig_script[64:]]
    pubkey_script = vout.pubkey_script.split(' ')

    machine = LittleMachine()
    machine.set_script(sig_script+pubkey_script,m2)
    print (machine.run())
    
##    script = [a,1,2,'OP_DUP','OP_ADD','OP_EQ']
##    machine = LittleMachine()
##    machine.set_script(script)
##    print(machine.run())

    

            

    


    
        
        
