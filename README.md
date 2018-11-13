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


-------
```python
   >>> from simchain import network
   >>> net = Network()
   >>> net.make_randon_transactions()
   >>> net.consensus()
```

------



