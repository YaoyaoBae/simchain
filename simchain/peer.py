# -*- coding: utf-8 -*-

import random
from  .ecc import VerifyingKey,build_message
from .datatype import Pointer,Vin,Vout,UTXO,Tx,Block,get_merkle_root_of_txs
from .params import Params
from .consensus import mine,caculate_target
from .logger import logger
from .wallet import Wallet
from .script import LittleMachine

class Peer(object):
    
    def __init__(self,coords = None):
        self.coords = coords
        self.network = None
        self.txs = []
        self.candidate_block_txs = []
        self.candidate_block = None
        self.blockchain = []
        self.orphan_block = []
        self.utxo_set = {}
        self.mem_pool = {}
        self.orphan_pool = {}
        self.pid = None
        self.fee = Params.FIX_FEE_PER_TX
        self.tx_choice_method = 'whole'
        self.current_tx = None
        self.machine = LittleMachine()
        self.generate_wallet()
        
        self._is_block_candidate_created = False
        self._is_current_tx_created = False
        self._is_current_tx_sent = False
        self._delayed_tx = None
        self._delayed_block = None
        self._utxos_from_vins = None
        self._pointers_from_vouts = None
        self._utxos_from_vouts = None
        self._txs_removed = None
        
        
        
    
    
    ############################################################
    # peer as wallet
    ############################################################
    """
    Generate wallet
    """
    
    def generate_wallet(self):
        self.wallet = Wallet()


    @property
    def sk(self):
        return self.wallet.keys[-1].sk.to_string() if self.wallet.keys else None

    @property
    def pk(self):
        return self.wallet.keys[-1].pk.to_string() if self.wallet.keys else None


    @property
    def addr(self):
        return self.wallet.addrs[-1] if self.wallet.addrs else None

    @property
    def key_base_len(self):
        return len(self.sk)
        
    """
    your bank balance
    """
    def get_balance(self):
        utxos = self.get_utxo()
        return sum(utxo.vout.value for utxo in utxos)
    
    """
    your output
    """
    
    def get_utxo(self):
        return [utxo for utxo in self.utxo_set.values()
                if (utxo.vout.to_addr in self.wallet.addrs) and utxo.unspent]
        
    def get_unconfirmed_utxo(self):
        utxos = self.get_utxo()
        return [utxo for utxo in utxos if not utxo.confirmed]
    
    def get_confirmed_utxo(self):
        utxos = self.get_utxo()
        return [utxo for utxo in utxos if utxo.confirmed]
    
    def set_fee(self,value):
        self.fee = value
    
    def get_fee(self):
        return self.fee

    def calculate_fees(self,txs):
        fee = 0
        if txs:
            for tx in txs:
                fee += tx.fee
            return fee
        return 0
    
    def get_block_subsidy(self):
        return Params.FIX_BLOCK_SUBSIDY


    """
    create a transaction 
    """
    def create_transaction(self,to_addr,
                           value,
                           tx_type = "normal"):
        
        if tx_type == 'normal':
            outputs = create_normal_tx(self,to_addr,value)
            if outputs:
                tx_in,tx_out,fee = outputs
                self.current_tx = Tx(tx_in,tx_out,fee = fee,nlocktime = 0)
                self.txs.append(self.current_tx)   
                self._is_current_tx_created = True
                
                logger.info('{0}(pid={1}) created a transaction'.format(self,self.pid))
                return True
            return False
        

    """
    if this is a recorder peer, build rewards for self after won
    """
    def create_coinbase(self,value):
        return Tx.create_coinbase(self.wallet.addrs[-1],value = value)
    
    
    
    ############################################################
    # peer as route
    ############################################################
    """
    broadcast a transaction 
    """
    def send_transaction(self):
        if not self.txs:
            return False
        
        if self._is_current_tx_created:
            sign_utxo_from_tx(self.utxo_set,self.current_tx)
            
            add_tx_to_mem_pool(self,self.current_tx) 
            self._is_current_tx_created = False
            self._is_current_tx_sent = True
            
            logger.info("{0}(pid={1}) sent a transaction to network".format(self,self.pid))
            return True
        return False
    
    
    def recieve_transaction(self,tx):
        if tx and (tx not in self.mem_pool):
            if self.verify_transaction(self,tx,self.mem_pool): 
                add_tx_to_mem_pool(self,tx)
                return True
        
        return False

            
    def broadcast_transaction(self,tx = None): 
        if not self._is_current_tx_sent:
            self.send_transaction()
        
        self._is_current_tx_created = False
        self._is_current_tx_sent = False
        
        tx = tx or self.current_tx
        if tx:
            peers = self.network.peers[:]
            peers.remove(self)
            number = broadcast_tx(peers,tx)
            self.current_tx = None
            
            logger.info("{0}(pid={1})'s transaction verified by {2} peers".format(self,self.pid,number))
            return number
        return 0
    
        
    """
    broadcast a transaction 
    """ 
    def broadcast_block(self,block):
        peers = self.network.peers[:]
        peers.remove(self)
        number = broadcast_winner_block(peers,block)
        logger.info('{0} received by {1} peers'.format(block,number))
                
                
    def locate_block(self,block_hash):
       return locate_block_by_hash(self,block_hash)
   
    
    def recieve_block(self,block):
        if not self.verify_block(block):
            return False
        return try_to_add_block(self,block)
    


    
    """
    verify a transaction
    """
    
    def verify_transaction(self,tx,pool={}):
        if tx in self.txs:
            return True
        return verify_tx(self,tx,pool)

    """
    verify a block
    """ 
    
    def verify_block(self,block):
        if self._delayed_tx:
            fill_mem_pool(self)
            
        if self.orphan_pool:
            check_orphan_tx_from_pool(self)
            
        pool = get_unknown_txs_from_block(self.mem_pool,block.txs)
        if block == self.candidate_block:
            return True
        
        if verify_winner_block(self,block,pool):
            return True
        else:
            return False
    
    
    """
    peer links to p2p network
    """
    
    def login(self):
        assert self in self.network.off_peers,(
                "This peer does not connect to network or online"
                )
        repeat_log_in(self,self.network)
        self.update_blockchain()
        
                
    """
    peer logs out 
    """
    def logout(self):
        assert self in self.network.peers,(
                "This peer does not connect to network"
                )
        log_out(self,self.network)
    
    
    
    def update_blockchain(self,other):
        return update_chain(self,other)
                
    
    def update_mem_pool(self,other):
        if other._delayed_tx:
            fill_mem_pool(other)
        return update_pool(self,other.mem_pool)


    def update_utxo_set(self,other):
        self.utxo_set.update(other.utxo_set)
              
    ############################################################
    # peer as recorder
    ############################################################
    
    """
    if u r a consensus peer, u have create a candidate block
    """
    
    def create_candidate_block(self):
        self.choose_tx_candidates()
        txs = self.candidate_block_txs
        value = self.get_block_subsidy() + self.calculate_fees(txs)
        coinbase = self.create_coinbase(value)
        txs = [coinbase]+txs
        
        prev_block_hash = self.blockchain[-1].hash     
        merkle_root_hash = get_merkle_root_of_txs(txs).val if txs else None
        bits = Params.INITIAL_DIFFICULTY_BITS 
        
        self.candidate_block = Block(version=0, 
                                     prev_block_hash=prev_block_hash,
                                     merkle_root_hash = merkle_root_hash,
                                     timestamp= self.network.time[-1],
                                     bits=bits, 
                                     nonce=0,
                                     txs= txs or [])
        
        self._is_block_candidate_created = True
        
    
    '''
    pow used right now
    '''        
    def consensus(self,meth = 'pow'):
        if not self._is_block_candidate_created:
            self.create_candidate_block()
            self._is_block_candidate_created = False
            
        if meth == 'pow':
            return mine(self.candidate_block)

    """
    if this is a recorder peer, we have package the candidate block
    """
    def package_block(self,nonce):
        block = self.candidate_block._replace(nonce = nonce)
        return block

    """
    choose transactions for candidate block 
    """
    def choose_tx_candidates(self):
        if self.tx_choice_method == 'whole':
            if not self.mem_pool:
                self.update_mem_pool(self.network.peers[0])
            self.candidate_block_txs = choose_whole_txs_from_pool(self.mem_pool)
        
        elif self.tx_choice_method == 'random':
            if not self.mem_pool:
                self.update_mem_pool(self.network.peers[0])
            self.candidate_block_txs = choose_raondom_txs_from_pool(self.mem_pool)

    """
    get transactions for candidate block
    """
    def get_tx_candidates(self):  
        return self.candidate_block_txs
    
    def get_height(self):
        return len(self.blockchain)
    
    def roll_back_now(self):
        roll_back(self)

    def __repr__(self):
        return 'peer{0}'.format(self.coords)
    
    
# =============================================================================
#login and logout

def repeat_log_in(peer,net):
    net.off_peers.remove(peer)
    net.peers.append(peer)
    
def log_out(peer,net):
    net.peers.remove(peer)
    net.off_peers.append(peer)
    peer.mem_pool = []

def update_chain(peer,other):
    other_height = other.get_height()
    height = peer.get_height()
    if other_height > height:
        peer.blockchain = []
        for block in other.blockchain:
            peer.blockchain.append(block)
        return True
    return False
    

def update_pool(peer,pool):
    a,b = set(peer.mem_pool),set(pool)
    for tx_id in (b-a):
        tx = pool.get(tx_id)
        peer.mem_pool[tx_id] = tx
    
    if peer._delayed_tx:
        fill_mem_pool(peer)
    
    if peer.orphan_pool:
        check_orphan_tx_from_pool(peer)
        
    return True

    

# =============================================================================         
#create transactions
def create_normal_tx(peer,to_addr,value) :
    utxos,balance = peer.get_utxo(),peer.get_balance()
    fee,addr = peer.fee,peer.wallet.addrs[-1]
    
    tx_in,tx_out = [],[]
    value = value + fee
    if balance  < value:
        logger.info('no enough money for transaction for {0}(pid = {1})'.format(peer,peer.pid))
        return
        
    need_to_spend,n = 0,0
    for i,utxo in enumerate(utxos):
        need_to_spend += utxo.vout.value
        if need_to_spend >= value:
            n = i+1
            break
            
    if need_to_spend > value:
        tx_out +=[Vout(to_addr,value-fee),Vout(addr,need_to_spend-value)]
    else:
        tx_out += [Vout(to_addr,value-fee)]
            
            
    for utxo in utxos[:n]:
        addr = utxo.vout.to_addr
        idx = peer.wallet.addrs.index(addr)
        sk,pk = peer.wallet.keys[idx].sk,peer.wallet.keys[idx].pk
        
        string = str(utxo.pointer) + str(pk.to_string())
        message = build_message(string)
        signature = sk.sign(message)
        tx_in.append(Vin(utxo.pointer,signature,pk.to_string()))
        
    return tx_in,tx_out,fee


def create_subtle_tx(nd,to_addr,value):
    pass

def choose_raondom_txs_from_pool(pool):
    n = len(pool)
    n = n if n < Params.MAX_TX_NUMBER_FOR_MINER else Params.MAX_TX_NUMBER_FOR_MINER
    candidates = random.sample(list(pool.keys()),n)
    return [pool.get(t) for t in candidates]

def choose_whole_txs_from_pool(pool):
    return list(pool.values())

# =============================================================================
#broadcast transactions  
# =============================================================================
    
def broadcast_tx(peers,current_tx):    
    rand,idxs,choice = random.uniform(0,1),range(len(peers)),[-1]
    number_of_verification = 0
    
    if rand < Params.SLOW_PEERS_IN_NETWORK:
        choice = [random.choice(idxs)]
    if rand < Params.SLOWER_PEERS_IN_NETWORK:
        choice = random.sample(idxs,k = 2)

    for i,peer in enumerate(peers): 
        if peer._delayed_tx:
            dice = random.uniform(0,1)
            if dice > Params.SLOW_PEERS_IN_NETWORK:
                fill_mem_pool(peer)
            
        if peer.verify_transaction(current_tx,peer.mem_pool):
            if (i in choice) and (not peer._delayed_tx):
                peer._delayed_tx = current_tx
                continue
            
            add_tx_to_mem_pool(peer,current_tx)  
            number_of_verification += 1 
            
        if peer.orphan_pool:
            check_orphan_tx_from_pool(peer)
            
    return number_of_verification


def check_orphan_tx_from_pool(peer)->bool:
    available_value = 0
    copy_pool = peer.orphan_pool.copy()
    for tx in copy_pool.values():
        if tx.id in peer.mem_pool:
            del peer.orphan_pool[tx.id]
            add_tx_to_mem_pool(peer,tx)
            continue

        for vin in tx.tx_in:
            utxo = peer.utxo_set.get(vin.to_spend)
            
            if not utxo:
                return False

            if not verify_signature_for_vin(vin,utxo,peer.key_base_len):
                return False
            
            available_value += utxo.vout.value
            
        if available_value < sum(vout.value for vout in tx.tx_out):
            return False
        
        add_tx_to_mem_pool(peer,tx)
        del peer.orphan_pool[tx.id]
        
    return True
            
# =============================================================================
#broadcast_block
# =============================================================================
    
def broadcast_winner_block(peers,block): 
    number_of_verification = 0
    for peer in peers: 
        if peer.verify_block(block):
            try_to_add_block(peer,block)
            number_of_verification += 1
    
    return number_of_verification
    
        
# =============================================================================
#UTXO functions
# =============================================================================

def find_utxos_from_txs(txs):
    return [UTXO(vout,Pointer(tx.id,i),tx.is_coinbase,vout.pubkey_script)
            for tx in txs for i,vout in enumerate(tx.tx_out)]
    
def find_utxos_from_block(txs):
    return [UTXO(vout,Pointer(tx.id,i),tx.is_coinbase,vout.pubkey_script,True,True)
            for tx in txs for i,vout in enumerate(tx.tx_out)]
    
def find_utxos_from_tx(tx):
    return [UTXO(vout,Pointer(tx.id,i),tx.is_coinbase,vout.pubkey_script)
            for i,vout in enumerate(tx.tx_out)]

def find_vout_pointer_from_txs(txs):
    return [Pointer(tx.id,i) for tx in txs for i,vout in enumerate(tx.tx_out)]
    
def find_vin_pointer_from_txs(txs):
    return [vin.to_spend for tx in txs for vin in tx.tx_in]
            
def confirm_utxos_from_txs(utxo_set,txs,allow_utxo_from_pool):
    if allow_utxo_from_pool:
        utxos = find_utxos_from_txs(txs[1:])
        add_utxos_from_tx_to_set(utxo_set,txs[0])
        pointers = find_vout_pointer_from_txs(txs)
        confirm_utxo_by_pointers(utxo_set,pointers)
        return pointers,utxos
    else:
        utxos = find_utxos_from_block(txs)
        pointers = find_vout_pointer_from_txs(txs)
        add_utxos_to_set(utxo_set,utxos)
        return pointers,utxos
        
def remove_spent_utxo_from_txs(utxo_set,txs):
    pointers = find_vin_pointer_from_txs(txs)
    utxos = delete_utxo_by_pointers(utxo_set,pointers)
    return utxos

def delete_utxo_by_pointers(utxo_set,pointers):
    utxos_from_vins = []
    for pointer in pointers:
        if pointer in utxo_set:
            utxos_from_vins.append(utxo_set[pointer])
            del utxo_set[pointer]
    return utxos_from_vins

def confirm_utxo_by_pointers(utxo_set,pointers):
    for pointer in pointers:
        if pointer in utxo_set:
            utxo = utxo_set[pointer]
            utxo = utxo._replace(confirmed = True)
            utxo_set[pointer] = utxo
            
def sign_utxo_from_tx(utxo_set,tx):
    for vin in tx.tx_in:
        pointer = vin.to_spend
        utxo = utxo_set[pointer]
        utxo = utxo._replace(unspent = False)
        utxo_set[pointer] = utxo

                    
def add_utxos_from_tx_to_set(utxo_set,tx):
    utxos = find_utxos_from_tx(tx)
    for utxo in utxos:
        utxo_set[utxo.pointer] = utxo
        
        
def add_utxo_from_txs_to_set(utxo_set,txs):
    utxos = find_utxos_from_txs(txs)
    add_utxos_to_set(utxo_set,utxos)

def add_utxos_to_set(utxo_set,utxos):
    if isinstance(utxos,dict):
        utxos = utxos.values()
        
    for utxo in utxos:
        if utxo.pointer not in utxo_set:
            utxo_set[utxo.pointer] = utxo

def remove_utxos_from_set(utxo_set,pointers):
    for pointer in pointers:
        if pointer in utxo_set:
            del utxo_set[pointer]
    
# =============================================================================
#verify transaction
# =============================================================================
        
def verify_tx(peer,tx,pool,is_coinbase = False):
    
    if not verify_basics(tx,is_coinbase = is_coinbase):
        return False
    
    if double_payment(pool,tx):
        logger.info('{0} double payment'.format(tx))
        return False
    
    available_value = 0

    for vin in tx.tx_in:
        utxo = peer.utxo_set.get(vin.to_spend)
        
        if not utxo:
            logger.info(
                    '{0}(pid={1}) find a orphan transaction {2}'.format(peer,peer.pid,tx)
                    )
            peer.orphan_pool[tx.id] = tx
            return False

        if not verify_signature(peer,vin,utxo):
            logger.info('singature does not math for {0}'.format(tx))
            return False
    
        available_value += utxo.vout.value
        
    if available_value < sum(vout.value for vout in tx.tx_out):
        logger.info(
                '{0} no enought available value to spend by {1}(pid={2})'.format(tx,peer,peer.pid)
                )
        return False

    return True

def verify_signature(peer,vin,utxo):
    script = check_script_for_vin(vin,utxo,peer.key_base_len)
    if not script:
        return False
    string = str(vin.to_spend) + str(vin.pubkey)
    message = build_message(string)
    peer.machine.set_script(script,message)
    return peer.machine.run()


def check_script_for_vin(vin,utxo,baselen):
    sig_script,pubkey_script = vin.sig_script,utxo.pubkey_script
    double,fourfold = int(baselen*2),int(baselen*4)
    if len(sig_script) != fourfold:
        return False
    sig_scrip = [sig_script[:double],sig_script[double:]]
    try:
        pubkey_script = pubkey_script.split(' ')
    except Exception:
        return False

    return sig_scrip+pubkey_script

    
    
##def verify_signature_for_vin(vin,utxo,baselen):
##    pk,signature = vin.pubkey,vin.signature
##    if len(pk) != baselen*2 or len(signature) != baselen*2:
##        logger.info('pubkey or signature length does not match for {0}'.format(vin))
##        return False
##    
##    to_addr = utxo.vout.to_addr
##    string = str(vin.to_spend) + str(pk)
##    return verify_signature_by_pubkey(pk,to_addr,signature,string)

    
def verify_basics(tx, is_coinbase=False):
    if (not tx.tx_out) or (not tx.tx_in and not is_coinbase):
        logger.info('{0} Missing tx_out or tx_in'.format(tx))
        return 
    if len(str(tx)) > Params.MAX_BLOCK_SERIALIZED_SIZE:
        logger.info('{0} transaction is too large'.format(tx))
        return 
    return True

def double_payment(pool,tx):
    if tx.id in pool:
        return True
    a = {vin.to_spend for vin in tx.tx_in}
    b = {vin.to_spend for tx in pool.values() for vin in tx.tx_in}
    return a.intersection(b)

def verify_coinbase(tx,subsidy):
    if not isinstance(tx,Tx):
        return False
    if not tx.is_coinbase:
        return False
    if (not (len(tx.tx_out) ==1))  or (tx.tx_out[0].value != subsidy):
        return False
    return True

# =============================================================================
#verify block
# =============================================================================
    
def verify_winner_block(peer,block,pool):
    
    if block in (peer.blockchain+peer.orphan_block):
        logger.info('{0} has been seen'.format(block))
        return  False
    
    if not block.txs:
        logger.info('no transactions in this block{0}'.format(block))
        return False
        
    if int(block.hash, 16) > caculate_target(block.bits):
        logger.info('{0} wrong answer'.format(block))
        return False
    
    subsidy = peer.get_block_subsidy()+peer.calculate_fees(block.txs[1:])
    if not verify_coinbase(block.txs[0],subsidy):
        logger.info('{0} coinbase incorrect'.format(block))
        return False
    
    if get_merkle_root_of_txs(block.txs).val != block.merkle_root_hash:
        logger.info('Merkle hash invalid {0}'.format(block))
        return False
    
    for tx in block.txs[1:]:
        if not peer.verify_transaction(tx,pool):
            return False
    
    return True


# =============================================================================
#try to recieve a block
# =============================================================================
    
def locate_block_by_hash(peer,block_hash):
    for height,block in enumerate(peer.blockchain):
        if block.hash == block_hash:
            return height+1
    return None
        
def try_to_add_block(peer,block):  
    prev_hash = block.prev_block_hash                                                  
    height = locate_block_by_hash(peer,prev_hash)
    if not height:
        logger.info('{0}(pid={1} find a orphan {2})'.format(peer,peer.pid,block))
        peer.orphan_block.append(block)
        return False
    
    if peer.get_height() == 1:
        peer.blockchain.append(block)
        recieve_new_prev_hash_block(peer,block.txs)
        return True
    
    if height == peer.get_height():
        peer.blockchain.append(block)
        recieve_new_prev_hash_block(peer,block.txs)
        return True
    
    elif height == peer.get_height()-1:
        b1,b2 = peer.blockchain[-1],block
        a,b = (b1.nonce,b1.timestamp),(b2.nonce,b2.timestamp)
        flag = compare_block_by_nonce_and_time(a,b)
        if flag == 1:
            return False
        elif flag == 2:
            peer.blookchian.pop
            peer.blockchain.append(block)
            recieve_exist_prev_hash_block(peer,block.txs)
        elif flag == -1:
            roll_back(peer)
    
def check_orphan_block(peer):
    pass

def recieve_new_prev_hash_block(peer,txs):
    utxo_set,pool = peer.utxo_set,peer.mem_pool
    allow_utxo_from_pool = peer.network.allow_utxo_from_pool
    peer._utxos_from_vins = remove_spent_utxo_from_txs(utxo_set,txs)
    peer._pointers_from_vouts,peer._utxos_from_vouts = confirm_utxos_from_txs(
            utxo_set,txs,allow_utxo_from_pool
            )
    peer._txs_removed = remove_txs_from_pool(pool,txs)
    
    
def recieve_exist_prev_hash_block(peer,txs):
    roll_back(peer)
    recieve_new_prev_hash_block(peer,txs)

def roll_back(peer):
    peer.mem_pool.update(peer._txs_removed)
    add_utxos_to_set(peer.utxo_set,peer._utxos_from_vins)
    remove_utxos_from_set(peer.utxo_set,peer._pointers_from_vouts)
    add_utxos_to_set(peer.utxo_set,peer._utxos_from_vouts)
    peer._utxos_from_vins = []
    peer._pointers_from_vouts = []
    peer._utxos_from_vouts = []
    peer._txs_removed = {}
    
def compare_block_by_nonce_and_time(a,b):
    pass
        
# =============================================================================
#transactions functions
# =============================================================================
    
def get_unknown_txs_from_block(mem_pool,txs):
    substraction = {}
    for tx in txs:
        if tx not in mem_pool.values():
            substraction[tx.id] = tx
    return substraction


def fill_mem_pool(peer):
    add_tx_to_mem_pool(peer,peer._delayed_tx)
    peer._delayed_tx = None
        

def remove_txs_from_pool(pool,txs):
    n_txs = {}
    for tx in txs:
        if tx.id in pool:
            n_txs[tx.id] = tx
            del pool[tx.id]
    return n_txs
                
def add_txs_to_pool(pool,txs):
    for tx in txs:
        pool[tx.id] = tx
           
def add_tx_to_mem_pool(peer,tx):
    peer.mem_pool[tx.id] = tx
    if peer.network.allow_utxo_from_pool:
        add_utxos_from_tx_to_set(peer.utxo_set,tx)

def calculate_next_block_bits(local_time,prev_height,prev_bits):
    flag = (prev_height + 1) % Params.TOTAL_BLOCKS
    if flag != 0:
        return prev_bits
    
    count = int(round((prev_height + 1)/Params.TOTAL_BLOCKS)*Params.TOTAL_BLOCKS)
    actual_time_taken = local_time[:prev_height] - local_time[:count]
    
    if actual_time_taken < Params.PERIOD_FOR_TOTAL_BLOCKS:
        return prev_bits + 1
    elif actual_time_taken > Params.PERIOD_FOR_TOTAL_BLOCKS:
        return prev_bits - 1
    else:
        return prev_bits


          
if __name__ == '__main__':
    a,b = Peer(),Peer()
