Simchain
========

Simchain is a blockchain simulator for education and research purpose by Dr.Pei at the sponsor of Hubei University of technology.



Version
=======
Current:1.0.0

Requirements:
=======
Python 2 and 3

Installation
=======
$ pip install simchain

Or

$ python setup.py install


Usage
========
* It can be used as a simulator of bitcoin system right away. The users can directly understand the data flowing for peers to peers.
* It can be used as a test tool for noval algrithms.
*  It can be used as a education and reseach tool.
*  It will be used as a network delay and pressure testing tools in the future.

Algorithm
========
* Hash function: double sha256 algorithm
* DSA: ECDSA
* Lattice-based cryptography is discussed

Data type defination
========
Simchain only support the function of bitcoin system by far, so the user-defined data types are similar with bitcoin.
* Pointer ---A pointer to a transaction unspent output
* Vin    --- value input unit
* Vout   --- value output unit
* UTXO   ---- unspent transaction output
* Tx     ---- transaction
* Block  ---- block
* MerkleTree ----- MerkleTree object


Code example
========
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
   >>> satoshi.create_transaction(john.addr,100)
   >>> satoshi.broadcast_transaction()
```
------
We named two peers satoshi and john. They both got 10000 fen at the beggining. Let satoshi create a transaction which sends 100 fen to john and broadcast it. 'addr' means address same as in bitcoin.
```python
   >>> satoshi.get_balance()
   99890
   >>> john.get_balance()
   100100
```
------
It seems that the transaction succeeded. However, why 99890 not 99900? where is the lost 10 fen?



