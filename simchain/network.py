# -*- coding: utf-8 -*-

import time
import random
from .datatype import Vin,Vout,Tx,Block,get_merkle_root_of_txs
from .logger import logger
from .peer import Peer,find_utxos_from_block,add_utxos_to_set

from .consensus import consensus_with_fasttest_minner
from .params import Params
from math import ceil
from itertools import accumulate


#Class p2p Network 
# =============================================================================

class Network(object):

    def __init__(self,nop = None,von = None):
        
        self.peers = []
        self.off_peers = []
        self.consensus_peers = []
        self.current_winner = None
        self.winner = []
        self.init_peers_number = nop or Params.INIT_NUMBER_OF_PEERS
        self.init_value = von or Params.INIT_COIN_PER_PEER
        self.create_genesis_block(self.init_peers_number,self.init_value)
        self.time_spent = [0]
        
        self._is_consensus_peers_chosen = False
        self._not = 0

    
    def init_peers(self,number):
        for _ in range(number):
            coords = generate_random_coords()
            peer = Peer(coords)
            create_peer(self,peer)
    
    def add_peer(self):
        coords = generate_random_coords()
        peer = Peer(coords)
        create_peer(self,peer)
        peer.update_blockchain(self.peers[0])
        peer.update_mem_pool(self.peers[0])
        peer.update_utxo_set(self.peers[0])
        logger.info('A new peer joined in --> {0}(pid={1})'.format(peer,peer.pid))
        
    def create_genesis_block(self,number,value):
        self.init_peers(number = number)
        tx_in =[Vin(to_spend = None,
                    signature = b'I love blockchain',
                    pubkey = None)]
        
        tx_out = [Vout(value = value,to_addr = peer.wallet.addrs[-1])
                  for peer in self.peers]
        
        
        txs = [Tx(tx_in = tx_in,tx_out = tx_out,nlocktime = 0)]
        genesis_block = Block(version=0,
                              prev_block_hash=None,
                              timestamp = 841124,
                              bits = 0,
                              nonce = 0,
                              txs = txs)
        
        logger.info('A blockchain p2p network created,{0} peers joined'.format(self.nop))
        logger.info('genesis block has been generated')
        
        utxos = find_utxos_from_block(txs)
        for peer in self.peers:
            peer.blockchain.append(genesis_block)
            add_utxos_to_set(peer.utxo_set,utxos)
        
            
    def make_random_transactions(self):
        k = random.randint(1,self.nop)
        self._not = k
        for _ in range(k):
            sender = random.choice(self.peers[1:])
            reciever = random.choice(self.peers[1:])
            sender.create_transaction(reciever.wallet.addrs[-1],
                                      tx_random_value())
            
            sender.broadcast_transaction()
            
    
        
    def set_consensus_peers(self,*idx):
        for i in idx:
            self.consensus_peers.append(self.peers[i])
            
        self._is_consensus_peers_chosen = True
    
    def choose_random_consensus_peers(self):
        n = self.nop
        #we suppose we have 20%~60% nodes are consensus node
        ub,lb = Params.UPPER_BOUND_OF_CONSENSUS_PEERS,\
                Params.LOWWER_BOUND_OF_CONSENSUS_PEERS
        k = random.randint(ceil(lb*n),ceil(ub*n))
        self.consensus_peers = random.sample(self.peers,k)     
        self._is_consensus_peers_chosen = True
        
        
    def consensus(self,meth = 'pow'):
        if not self._is_consensus_peers_chosen:
            self.choose_random_consensus_peers()
        
        if meth == 'pow':
            logger.info('{0} peers are mining'.format(len(self.consensus_peers)))
            n,nonce,time = consensus_with_fasttest_minner(self.consensus_peers)
            self.time_spent.append(time)
            self.current_winner = self.consensus_peers[n]
            self.winner.append(self.current_winner)
            
            logger.info('{0}(pid={1}) is winner,{2} secs used'.format(
                    self.current_winner,
                    self.current_winner.pid,
                    time
                    ))
            
            block = self.current_winner.package_block(nonce = nonce)
            self.current_winner.recieve_block(block)
            self.current_winner.broadcast_block(block)
            
    def draw(self):
        pass
    
    @property
    def time(self):
        return _accumulate(self.time_spent)

    def get_time(self):
        return self.time[-1]
 
    @property
    def nop(self):
        return len(self.peers)
    
    def __repr__(self):
        return 'A p2p blockchain network with {0} peers'.format(self.nop)

def create_peer(net,peer):
    peer.pid = net.nop
    peer.network = net
    peer.wallet.generate_keys()
    net.peers.append(peer)


#functions
# =============================================================================



#Iterables 
# =============================================================================
    


def addr_finder(tx):
    return (out.vout.to_addr for out in tx.tx_out)

def _accumulate(l):
    return list(accumulate(l))
    
#random data
# =============================================================================

def tx_random_value():
    return random.randint(0,100)


def generate_random_coords():
    return (random.randint(0,100),random.randint(0,100))

    
if __name__ == "__main__":
    pass

##    net = Network(nop = 2,von = 10000)
##    
##    zhangsan,lisi = net.peers[0],net.peers[1]
##    zhangsan.create_transaction(lisi.wallet.addrs[0],100)
##    zhangsan.broadcast_transaction()
##    lisi.create_transaction(zhangsan.wallet.addrs[0],100)
##    lisi.broadcast_transaction()
    
##
    net = Network()
    net.make_random_transactions()
    net.consensus()
##    b = zhangsan.get_utxo()[0]
##    print(b.pubkey_script)
##    tx = zhangsan.current_tx
##    vin = tx.tx_in[0]
##    vin1 = Vin(vin.to_spend,b'1'*64,vin.pubkey)
##    tx.tx_in[0] = vin1
##    lisi.mem_pool = {}
##    lisi.verify_transaction(tx,lisi.mem_pool)
    
    
##    
##    
##    for _ in range(4):
##        net.make_random_transactions()
##        net.consensus()



        

