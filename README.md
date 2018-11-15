Simchain
========

Simchain is a blockchain simulator for education and research purpose by Dr.Pei at the sponsor of Hubei University of technology.



Version
=======
Current:1.0.0

Requirements
=======
Python 3

Installation
=======
$ pip install simchain

Or

$ python setup.py install


Usage
========
* Education. Like a bitcoin simulator,the users can directly understand the data flowing for peers to peers.
* Research. Reseachers can use it for algrithms testing. It will be also used as a network delay and pressure testing tools in the future.

Algorithm
========
* Hash function: double sha256 algorithm
* DSA: ECDSA
* Lattice-based cryptography is discussed

Data type defination
========
Simchain is more likely a bitcoin simulator by far, so the user-defined data types are similar with bitcoin.
* Pointer ---A pointer to a transaction unspent output
* Vin    --- value input unit
* Vout   --- value output unit
* UTXO   ---- unspent transaction output
* Tx     ---- transaction
* Block  ---- block
* MerkleTree ----- MerkleTree object
* SigningKey ------ privite key
* VerifyingKey ----- publick key
* Wallet ----- wallet


Code example
========

1 General 
-------
```python
   >>> from simchain import Network
   >>> net = Network()
```
-------
The code above created a blockchain network. The default peers number is 12 and every peer obtain equal money 100000 fen (yuan,jiao,fen) at the very begining.We can check the peers number and balance as follows.
```python
   >>> net.nop
   12
   >>> net.peers
   [peer(100, 51), peer(7, 13), peer(65, 74), peer(0, 95), peer(46, 59), peer(12, 5), peer(37, 76), peer(78, 71), peer(28, 75), peer(48, 51), peer(66, 44), peer(41, 75)]
   >>> net.peers[0].get_balance()
   >>> 100000
```
------
Now,we can let the peers make transactions each other like this.
```python
   >>> satoshi = net.peers[0]
   >>> john = net.peers[4]
   >>> satoshi.get_balance() == john.get_balance() == 100000
   True
   >>> len(satoshi.get_utxo()) == len(john.get_utxo()) == 1
   True
   >>> satoshi.create_transaction(john.addr,100)
   >>> satoshi.broadcast_transaction()
```
------
We named two peers satoshi and john respectively. They both got 10000 fen and one UTXO at the beggining. Let satoshi create a transaction which sends 100 fen to john and broadcast it. 'addr' means address same as in bitcoin.
```python
   >>> satoshi.get_balance()
   99890
   >>> john.get_balance()
   100100
```
------
It seems that the transaction succeeded. However, why 99890 not 99900? where is the lost 10 fen?
```python
   >>> satoshi.get_utxo()
   [UTXO(vout:Vout(to_addr:1BwmfFdQwnAz78PcdrzSgBUpRYZbbMSY7L,value:99890),pointer:Pointer(tx_id:d7208876508ddeca918bdf930cc6d35eaf859487fec5d5d0146305dd5ac1950c,n:1))]
   99890
   >>> john.get_utxo()
   [UTXO(vout:Vout(to_addr:1KP1TUiWJStHmUwgvZQmgd3GwDtExr3kFH,value:100000),pointer:Pointer(tx_id:4703858c430626c430f1947c8c1217b6eec1840cfd0b42ab5bd66067cb52eb49,n:4)), UTXO(vout:Vout(to_addr:1KP1TUiWJStHmUwgvZQmgd3GwDtExr3kFH,value:100),pointer:Pointer(tx_id:d7208876508ddeca918bdf930cc6d35eaf859487fec5d5d0146305dd5ac1950c,n:0))]
   >>> satoshi.get_unconfirmed_utxo()
   [UTXO(vout:Vout(to_addr:1BwmfFdQwnAz78PcdrzSgBUpRYZbbMSY7L,value:99890),pointer:Pointer(tx_id:d7208876508ddeca918bdf930cc6d35eaf859487fec5d5d0146305dd5ac1950c,n:1))]
   >>> john.get_unconfirmed_utxo()
   [UTXO(vout:Vout(to_addr:1KP1TUiWJStHmUwgvZQmgd3GwDtExr3kFH,value:100),pointer:Pointer(tx_id:d7208876508ddeca918bdf930cc6d35eaf859487fec5d5d0146305dd5ac1950c,n:0))]
```
------
We found satoshi got only one UTXO with 99890 fen, but unconfirmed. john had two UTXOs, 10000 fen and 100 fen (unconfirmed) respectively. The unconfirmed 100 fen UTXO came from satoshi. Why was that? Where is the lost 10 fen? 
```python
   >>> net.consensus()
   2018-11-13 16:16:28,002 - 7 peers are mining
   2018-11-13 16:16:36,401 - peer(90, 8)(pid=10) is winner,8.335185527801514 secs used
   2018-11-13 16:16:37,643 - Block(hash:000017b37e84cfb6f8f251edf089e2b48723edf0aaef27092b048b40d0952e23) received by 11 peers)
   >>> satoshi.get_unconfirmed_utxo()
   []
   >>> john.get_unconfirmed_utxo()
   []
   >>> satoshi.get_balance()
   99890
   >>> john.get_balance()
   100100
   >>> ben = net.peers[10]
   >>> ben.get_balance()
   100510
```
------
After the consensus reached, we found both satoshi and john had uncomfirmed UTXO no more.The mining winner --ben (pid = 10) got 510 fen increased,500 mining reward and 10 transaction fee (The lost 10 fen). The transaction finished untill the consensus reached.
```python
   >>> net.make_random_transactions()
   >>> net.consensus()
```
------
We can also use two lines above to make random transactions and reach one consensus.
```python
   >>> alice = net.peers[-1]
   >>> alice.get_balance()
   0
   >>> alice.get_utxo()
   []
   >>> alice.blockchain == satoshi.blockchain
   True
   >>> len(alice.blockchain)
   3
```
------
We can also add new user (peer) into the network. However, the newer(alice) got no money.Satoshi and john got money since the system gave them money in  the genesis block at the begining. alice had the same blockchain as satoshi had because when a new peer joins in the system, it has to update the blockchain according to the old full peer.Meanwhile, the blockchain increased to 3 since two consensuses reached by far.

-----
2 Wallet and keys
-----
```python
   >>> satoshi.wallet.keys
   [keys pair]
   >>> satoshi.wallet.keys[0]
   keys pair
   >>> satoshi.wallet.keys[0].sk
   <simchain.ecc.SigningKey object at 0x0000016329813DA0>
   >>> satoshi.wallet.keys[0].sk.to_bytes()
   b'\xad\xd5\xea\xd9\x89&_\x1aH\xbd\xd4dl\xde\xe4\xbc\xc4\xe5J\xbeyw|\xf5&\xa76%Y\xe1\x9a\xc4'
   >>> satoshi.wallet.keys[0].pk.to_bytes()
   b'\x0b.\xc4&CLP\xf7\xbb\x92~\xcd\x10\xf91\xb8\xe5)\x15^)\xcb\x8b\x13\xe4\x7f\x1d\xa1)v\xe5\xe1\xb9Q\xbf\xa2\x1fc\x1f#\xef\xa1\xe2L\xdb\x12\xe4\xa0\xc8\x8d$\x9f4\x8a\xf9\x02\x18iIV_\xa4\xd4p'
   >>> type(satoshi.wallet.keys[0].sk)
   <class 'simchain.ecc.SigningKey'>
   >>> type(satoshi.wallet.keys[0].pk)
   <class 'simchain.ecc.VerifyingKey'>
   >>> satoshi.wallet.addrs[0]
   '1DnxfAWqMPW2nvQug2x2ocPvrM7Fjf2g55'
```
-----
Every peer has a Wallet attribute.Wallet consists of key pair (SigningKey and VerifyingKey object) and adrress list. 
```python
   >>> len(satoshi.wallet.keys)
   1
   >>> satoshi.wallet.generate_keys()
   >>> len(satoshi.wallet.keys)
   2
   >>> len(satoshi.wallet.addrs)
   2
```
-----
