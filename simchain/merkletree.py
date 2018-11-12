
from .ecc import sha256d
class Node(object):

    def __init__(self, data, prehashed=False):
        if prehashed:
            self.val = data
        else:
            self.val = sha256d(data)
            
        self.left_child = None
        self.right_child = None
        self.parent = None
        self.bro = None
        self.side = None

    def __repr__(self):
        return "MerkleTreeNode('{0}')".format(self.val)



class MerkleTree(object):

    def __init__(self,leaves = []):
        self.leaves = [Node(leaf,True) for leaf in leaves]
        self.root = None

    def add_node(self,leaf):
        self.leaves.append(Node(leaf))


    def clear(self):
        self.root = None
        for leaf in self.leaves:
            leaf.parent,leaf.bro,leaf.side = (None,)*3


    def get_root(self):
        if not self.leaves:
            return None

        level = self.leaves[::]
        while len(level) != 1:
            level = self._build_new_level(level)
        self.root = level[0]
        return self.root.val
        
    def _build_new_level(self, leaves):
        new, odd = [], None
        if len(leaves) % 2 == 1:
            odd = leaves.pop(-1)
        for i in range(0, len(leaves), 2):
            newnode = Node(leaves[i].val + leaves[i + 1].val)
            newnode.lelf_child, newnode.right_child = leaves[i], leaves[i + 1]
            leaves[i].side, leaves[i + 1].side,  = 'LEFT', 'RIGHT'
            leaves[i].parent, leaves[i + 1].parent = newnode, newnode
            leaves[i].bro, leaves[i + 1].bro = leaves[i + 1], leaves[i]
            new.append(newnode)
        if odd:
            new.append(odd)
        return new

    def get_path(self, index):
        path = []
        this = self.leaves[index]
        path.append((this.val, 'SELF'))
        while this.parent:
            path.append((this.bro.val, this.bro.side))
            this = this.parent
        path.append((this.val, 'ROOT'))
        return path

    

