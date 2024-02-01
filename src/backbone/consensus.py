# backbone/consensus.py

from datetime import datetime
import json
from abstractions.block import Blockchain, Block
from abstractions.transaction import Transaction
from backbone.merkle import MerkleTree
from utils.cryptographic import double_hash
from utils.flask_utils import flask_call
from server import SELF, REQUEST_TXS, GET_BLOCKCHAIN
from utils.view import get_difficulty_from_hash

TXS_TO_INCLUDE = 4


def get_txs() -> list[str]:
    """ 
    Fetch transactions to insert into block 
    Returns list of hashes
    """
    _, txs, code = flask_call('GET', REQUEST_TXS)
    if code != 200:
        return

    # Could find the transactions with maximum fee here
    selected = txs[:TXS_TO_INCLUDE]
    hashes = []
    for t in selected:
        t_ = Transaction.load_json(json.dumps(t))
        hashes.append(t_)

    return hashes


def select_ancestor(chain: Blockchain) -> str:
    """
    Select ancestor block and return the hash
    """
    if not chain.is_valid:
        raise ValueError

    # Always select longest branch
    block = chain.block_list[0]
    for b in chain.block_list:
        if b.height > block.height:
            block = b

    return block.hash, block.height + 1


def solve_pow(prev_hash: str, merkle_root: str, difficulty: int) -> (str, int, float):
    """
    Solve the pow given previous block hash and merkle root hash
    """
    solved = False
    nonce = 0
    while True:
        ts = datetime.now().timestamp()
        hash_ = double_hash(bytes(prev_hash) + bytes(ts) +
                            bytes(merkle_root) + bytes(nonce))

        for c in hash_[difficulty:]:
            solved = True if c == '0' else False

        if solved:
            return hash_, nonce, ts

        nonce += 1


def create_block(prev_hash: str, height: int):
    """
    Create a block
    """
    # Get difficulty
    difficulty = get_difficulty_from_hash(prev_hash)

    txs = get_txs()

    # Get merkle root
    tree = MerkleTree(txs)
    root = tree.get_root()

    # Solve PoW
    new_hash, nonce, ts = solve_pow(prev_hash, root, difficulty)

    new_block = Block(new_hash, nonce, ts, 0, height,
                      prev_hash, txs, mined_by=SELF)


def mine_block():
    """
    Mine a block and propose it to the network
    """
    _, blockchain, code = flask_call('GET', GET_BLOCKCHAIN)
    if code != 200:
        print("Unable to fetch blockchain")
        return

    parsed_chain = Blockchain.load_json(json.dumps(blockchain))
    ancestor_hash, new_height = select_ancestor(parsed_chain)

    create_block(ancestor_hash, new_height)
