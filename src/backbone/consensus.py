# backbone/consensus.py

from datetime import datetime
import json
from typing import Tuple, Union
import rsa
from abstractions.block import Blockchain, Block
from abstractions.transaction import Transaction
from backbone.merkle import MerkleTree
from utils.cryptographic import double_hash, load_private, save_signature
from utils.flask_utils import flask_call
from server import SELF, REQUEST_TXS, GET_BLOCKCHAIN
from utils.view import get_difficulty_from_hash

TXS_TO_INCLUDE = 4


def get_txs() -> Tuple[list[Transaction], list[str]]:
    """ 
    Fetch transactions to insert into block 
    Returns list of hashes
    """
    _, txs, code = flask_call('GET', REQUEST_TXS)
    if code != 200:
        raise ConnectionError

    # TODO: Only pick verified transactions!

    # Could find the transactions with maximum fee here
    selected = txs[:TXS_TO_INCLUDE]
    tx_objs = []
    hashes = []
    for t in selected:
        t_ = Transaction.load_json(json.dumps(t))
        tx_objs.append(t_)
        hashes.append(t_.hash)

    return tx_objs, hashes


def select_ancestor(chain: Blockchain) -> Tuple[str, int]:
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


def solve_pow(prev_hash: str, merkle_root: str, difficulty: int) -> Tuple[str, int, float]:
    """
    Solve the pow given previous block hash and merkle root hash
    """
    solved = False
    nonce = 0
    while True:
        ts = datetime.now().timestamp()
        hash_ = double_hash(prev_hash + str(ts) +
                            merkle_root + str(nonce))

        for c in hash_[:difficulty]:
            if c != '0':
                solved = False
                nonce += 1
                break
            else:
                solved = True

        if solved:
            return hash_, nonce, ts


def create_block(prev_hash: str, height: int) -> Block:
    """
    Create a block
    """
    # Time block creation
    start_ts = datetime.now().timestamp()

    # Get difficulty
    print(prev_hash)    # difficulty = get_difficulty_from_hash(prev_hash)
    difficulty = 6

    txs, tx_hashes = get_txs()

    # Get merkle root
    tree = MerkleTree(tx_hashes)
    root = tree.get_root()['hash']

    # Get priv key
    priv_key = ""
    with open(f"../vis/users/{SELF}_pvk.pem", "r") as file:
        priv_key = load_private(file.read())

    # Solve PoW
    new_hash, nonce, ts = solve_pow(prev_hash, root, difficulty)
    print(new_hash[:difficulty])

    # Sign block header
    b_hash = bytes(new_hash, 'utf-8')
    sig = rsa.sign(b_hash, priv_key, 'SHA-1')

    # Time block creation
    time_spent = datetime.now().timestamp() - start_ts

    new_block = Block(new_hash, nonce, ts, time_spent, height,
                      prev_hash, txs, mined_by=SELF, signature=save_signature(bytes(sig)))

    print(new_block)
    return new_block


def mine_block() -> Block:
    """
    Mine a block and propose it to the network
    """
    _, blockchain, code = flask_call('GET', GET_BLOCKCHAIN)
    if code != 200:
        print("Unable to fetch blockchain")
        raise ConnectionError

    parsed_chain = Blockchain.load_json(json.dumps(blockchain))
    ancestor_hash, new_height = select_ancestor(parsed_chain)

    return create_block(ancestor_hash, new_height)
