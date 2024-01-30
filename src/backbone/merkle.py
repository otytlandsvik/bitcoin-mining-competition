from utils.cryptographic import hash_function
from abstractions.transaction import Transaction


class Node:
    def __init__(self, left, right, tx, _hash) -> None:
        self.left = left
        self.right = right
        self.tx = tx
        self.hash = _hash

    def __str__(self) -> str:
        if self.tx != None:
            return f"[{self.tx} -> {self.hash}]"
        elif self.left != None and self.right != None:
            return f"[{self.left.hash} + {self.right.hash} -> {self.hash}]"
        else:
            return "Invalid merkle node"


class MerkleTree:
    def __init__(self, txs: list[Transaction]) -> None:
        self.data = None
        self.leaf_nodes: list[Node] = self.insert_leaves(txs)
        self.root = None
        self.build_tree()

    def insert_leaves(self, txs: list[Transaction]) -> list[Node]:
        nodes = []
        for tx in txs:
            nodes.append(Node(None, None, tx, tx.hash))
        return nodes

    def build_tree(self) -> None:
        self.root = self.__rec_build_tree(self.leaf_nodes)

    def __rec_build_tree(self, nodes: list[Node]) -> Node:
        # Handle odd number of nodes
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1].copy())

        if len(nodes) == 2:
            l = nodes[0]
            r = nodes[1]
            return Node(l, r, None, hash_function(l.hash + r.hash))

        # Divide and conquer
        middle = len(nodes) // 2
        l = self.__rec_build_tree(nodes[:middle])
        r = self.__rec_build_tree(nodes[middle:])

        return Node(l, r, None, hash_function(l.hash + r.hash))

    def get_root(self) -> Node:
        return self.root

    def __str__(self) -> str:
        leaves = ""
        for l in self.leaf_nodes:
            leaves += l.__str__()

        root = self.root.__str__() if self.root != None else "[ ]"

        return f"Root: {root}\n" + leaves
