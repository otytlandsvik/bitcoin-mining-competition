"""
Enrico Tedeschi @ UiT - Norges Arktiske Universitet, Faculty of Computer Science.
enrico.tedeschi@uit.no

INF 3203 - Advanced Distributed Systems

Assignment 1 - Blockchain Mining Competition

Usage:
        -h                  : display usage information
        -i [b, u]           : display information for blocks or users
        -t                  : request N transactions                    #TODO
        -m                  : mine a block                              #TODO
        -v b                : visualize blockchain, saved to vis/blockchain/blockchain.pdf
        -d                  : request DIFFICULTY level
"""
__author__ = "Enrico Tedeschi"
__copyright__ = "Copyright (C) 2023 Enrico Tedeschi"
__license__ = "GNU General Public License."
__version__ = "v1.0"

import sys
import getopt
import random
import requests
import json
from datetime import datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from abstractions.transaction import Transaction
from backbone.consensus import mine_block

from utils.flask_utils import flask_call
from abstractions.block import Blockchain
from server import BLOCK_PROPOSAL, REQUEST_DIFFICULTY, REQUEST_TXS, GET_BLOCKCHAIN, ADDRESS, PORT, GET_USERS
from utils.view import visualize_blockchain, visualize_blockchain_terminal


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hi:tmdv:")
        # print(f'opts : {opts}\nargs : {args}')
        valid_args = False
        for opt, arg in opts:
            if opt == "-h":  # usage
                print(__doc__)
                valid_args = True
                break
            if opt == "-m":  # mine block
                new_block = mine_block()
                response, _, _ = flask_call(
                    'POST', BLOCK_PROPOSAL, data=new_block.to_dict())
                print(response)
                valid_args = True
            if opt == "-i":
                # INFO
                if arg == "b":
                    _, blockchain, _ = flask_call('GET', GET_BLOCKCHAIN)
                    if blockchain:
                        b = Blockchain.load_json(json.dumps(blockchain))
                        visualize_blockchain_terminal(
                            b.block_list, n_blocks=40)
                        print(b.block_list[0].merkle_tree)
                    else:
                        print("Failed to fetch blockchain info...")
                    valid_args = True
                elif arg == "u":
                    users_data, users, code = flask_call('GET', GET_USERS)
                    if users:
                        print(users_data)
                    else:
                        print("Could not parse users...")
                    valid_args = True
                else:
                    valid_args = False
            if opt == "-t":
                _, txs, _ = flask_call('GET', REQUEST_TXS)
                if txs:
                    for t in txs:
                        x = Transaction.load_json(json.dumps(t))
                        print("TRANSACTION: ----------------------------")
                        print(f"Fee: {x.fee}")
                        print(f"Amount: {x.amount}\n")
                valid_args = True
            if opt == "-v":
                if arg == "b":
                    # fetch blockchain from server
                    # get blockchain info
                    _, blockchain, code = flask_call('GET', GET_BLOCKCHAIN)
                    if blockchain:
                        b_chain = Blockchain.load_json(json.dumps(blockchain))
                        # saves the blockchain as pdf in "vis/blockchain/blockchain.pdf"
                        visualize_blockchain(b_chain.block_list, n_blocks=40)
                        visualize_blockchain_terminal(
                            b_chain.block_list, n_blocks=40)
                    valid_args = True
            if opt == "-d":
                response, table, code = flask_call('GET', REQUEST_DIFFICULTY)
                print(response)
                print(table)
                valid_args = True
        if valid_args is False:
            print(__doc__)
    except getopt.GetoptError:
        print(__doc__)
        sys.exit(2)
    except ValueError as e:
        print(e)
        print(__doc__)
        sys.exit(2)  # exit due to misuse of shell/bash --> check documentation
    except KeyboardInterrupt as e:
        print(e)


def connect_to_server():
    """

    :return:
    """
    url = 'https://' + ADDRESS + ':' + PORT + '/'
    response = requests.get(url, verify=False)
    return response


if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    main(sys.argv[1:])
