import asyncio
import json
from style import style
import sys
import time

from web3 import Web3
from web3.exceptions import TransactionNotFound

from decimal import *

# More than 8 Decimals are not supportet in the input from the token buy amount! No impact to Token Decimals!
getcontext().prec = 8


class TXN:
    def __init__(self, token_address, quantity):
        self.w3 = self.connect()
        self.address, self.private_key = self.setup_address()
        self.token_address = Web3.toChecksumAddress(token_address)
        self.token_contract = self.setup_token()
        self.targeted_function = self.setupTargetedFunction()
        self.swapper_address = self.set_swap1()
        self.contract_swap = self.set_swap2()
        self.MaxGasInBNB, self.gas_price = self.setupGas()
        self.slippage = self.setupSlippage()
        self.quantity = quantity
        self.nonce = self.w3.eth.getTransactionCount(self.address)

    def connect(self):
        with open("./Settings.json") as f:
            keys = json.load(f)

        if keys["RPC"][:2].lower() == "ws":
            w3 = Web3(Web3.WebsocketProvider(keys["RPC"]))
        else:
            w3 = Web3(Web3.HTTPProvider(keys["RPC"]))
        return w3

    def is_connect(self):
        print(self.connect().isConnected())

    def setupGas(self):
        with open("./Settings.json") as f:
            keys = json.load(f)
        return keys["MaxTXFeeBNB"], int(keys["GWEI_GAS"] * (10 ** 9))

    def setup_address(self):
        with open("./Settings.json") as f:
            keys = json.load(f)
        if len(keys["metamask_address"]) <= 41:
            print(style.RED + "Set your Address in the keys.json file!" + style.RESET)
            sys.exit()
        if len(keys["metamask_private_key"]) <= 42:
            print(
                style.RED + "Set your PrivateKey in the keys.json file!" + style.RESET
            )
            sys.exit()
        return keys["metamask_address"], keys["metamask_private_key"]

    def setupSlippage(self):
        with open("./Settings.json") as f:
            keys = json.load(f)
        return keys["Slippage"]

    def get_token_decimals(self):
        return self.token_contract.functions.decimals().call()

    def getBlockHigh(self):
        return self.w3.eth.block_number

    def set_swap1(self):  # DIFFERENCE ICI ***
        swapper_address = Web3.toChecksumAddress(
            "0xa0C267F8753dF1E1b8b279D396BF3A61FeD62328"
        )
        return swapper_address

    def set_swap2(self):  # DIFFERENCE ICI ***
        swapper_addressx = Web3.toChecksumAddress(
            "0xa0C267F8753dF1E1b8b279D396BF3A61FeD62328"
        )
        with open("./ABI/SWAPRICE.json") as f2:
            contract_abiX = json.load(f2)
        abix = contract_abiX["abi"]
        contract_swap = self.w3.eth.contract(address=swapper_addressx, abi=abix)
        return contract_swap

    def setup_token(self):
        with open("./ABI/bep20_abi_token.json") as f:
            contract_abi = json.load(f)
        token_contract = self.w3.eth.contract(
            address=self.token_address, abi=contract_abi
        )
        return token_contract

    def get_token_balance(self):
        return self.token_contract.functions.balanceOf(self.address).call() / (
            10 ** self.token_contract.functions.decimals().call()
        )

    # DEV: ici, trouver un moyen de check si c'est un honey ***
    def checkToken(
        self,
    ):  # ATTENTION, deuxième fonction "check_token" active plus bas !
        pass  # getTokenInfos

    # DEV : Check si le token peut être acheté ou pas ***
    def checkifTokenBuyDisabled(self):
        pass  # getTokenInfos
        # Il faut réussir à choper l'info suivante : ??

    def estimateGas(self, txn):
        gas = self.w3.eth.estimateGas(
            {
                "from": txn["from"],
                "to": txn["to"],
                "value": txn["value"],
                "data": txn["data"],
            }
        )
        gas = gas + (gas / 10)  # Adding 1/10 from gas to gas!
        maxGasBNB = Web3.fromWei(gas * self.gas_price, "ether")
        print(
            style.GREEN
            + "\nMax Transaction cost "
            + str(maxGasBNB)
            + " BNB"
            + style.RESET
        )
        if maxGasBNB > self.MaxGasInBNB:
            print(style.RED + "\nTx cost exceeds your settings, exiting!")
            sys.exit()
        return gas

    # DEV : Calculer Output pour un trade BNB => TOKEN *** CHECK IF LIQUIDITY IS ADDED
    def getOutputfromBNBtoToken(self):
        call = self.contract_swap.functions.getOutputfromBNBtoToken(
            self.token_address,
        ).call()
        Amount = call[2]
        return Amount

    # DEV : Calculer Output pour un trade TOKEN => BNB *** CHECK THE PRICE
    def getOutputfromTokentoBNB(self):
        call = self.contract_swap.functions.getOutputfromTokentoBNB(
            self.token_address,
            # int(self.token_contract.functions.balanceOf(self.address).call()),
        ).call()
        Amount = call[3]
        return Amount

    # DEV : Calculer Output pour un trade TOKEN => TOKEN ***
    # def getOutputfromTokentoToken(self):
    #     pass
    # Il faut réussir à choper l'info suivante : SAME SHIT HERE (pas prioritaire)

    def check_token(self):
        txn = self.contract_swap.functions.checkHoney(
            self.token_address,
            self.slippage * 10 ** 18,
            int(float(0.001) * 10 ** 18),
            (int(time.time()) + 10000),
        ).buildTransaction(
            {
                "from": self.address,
                "gas": 480000,
                "gasPrice": self.gas_price,
                "nonce": self.nonce,
                "value": int(float(0.001) * 10 ** 18),
            }
        )
        txn.update({"gas": int(self.estimateGas(txn))})
        signed_txn = self.w3.eth.account.sign_transaction(txn, self.private_key)
        txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        print(style.GREEN + "\nCHECK Hash:", txn.hex() + style.RESET)
        txn_receipt = self.w3.eth.waitForTransactionReceipt(txn)
        if txn_receipt["status"] == 1:
            return True, style.GREEN + "\nCHECK Transaction Successfull!" + style.RESET
        else:
            return False, style.RED + "\nCHECK Transaction Failed!" + style.RESET

    # DEV : Creer notre propre SC afin de remplir les fonctions de SWAP + INFO;
    def buy_token(self):
        self.quantity = float(self.quantity) * (10 ** 18)
        txn = self.contract_swap.functions.fromBNBtoToken(
            self.token_address,
            self.slippage * 10 ** 18,
            int(self.quantity),
            (int(time.time()) + 10000),
        ).buildTransaction(
            {
                "from": self.address,
                "gas": 480000,
                "gasPrice": self.gas_price,
                "nonce": (
                    self.nonce + 1
                ),  # +1 sur le nonce du checkHoney, car pas le temps de call le nonce
                "value": int(self.quantity),
            }
        )
        txn.update({"gas": int(self.estimateGas(txn))})
        signed_txn = self.w3.eth.account.sign_transaction(txn, self.private_key)
        txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        print(style.GREEN + "\nBUY Hash:", txn.hex() + style.RESET)
        txn_receipt = self.w3.eth.waitForTransactionReceipt(txn)
        if txn_receipt["status"] == 1:
            return True, style.GREEN + "\nBUY Transaction Successfull!" + style.RESET
        else:
            return False, style.RED + "\nBUY Transaction Failed!" + style.RESET

    def is_approve(self):
        Approve = self.token_contract.functions.allowance(
            self.address, self.swapper_address
        ).call()
        Aproved_quantity = self.token_contract.functions.balanceOf(self.address).call()
        if int(Approve) <= int(Aproved_quantity):
            return False
        else:
            return True

    def approve(self):
        if self.is_approve() == False:
            txn = self.token_contract.functions.approve(
                self.swapper_address,
                115792089237316195423570985008687907853269984665640564039457584007913129639935,  # Max Approve
            ).buildTransaction(
                {
                    "from": self.address,
                    "gas": 100000,
                    "gasPrice": self.gas_price,
                    "nonce": self.w3.eth.getTransactionCount(self.address),
                    "value": 0,
                }
            )
            txn.update({"gas": int(self.estimateGas(txn))})
            signed_txn = self.w3.eth.account.sign_transaction(txn, self.private_key)
            txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
            print(style.GREEN + "\nApprove Hash:", txn.hex() + style.RESET)
            txn_receipt = self.w3.eth.waitForTransactionReceipt(txn)
            if txn_receipt["status"] == 1:
                return True, style.GREEN + "\nApprove Successfull!" + style.RESET
            else:
                return False, style.RED + "\nApprove Transaction Failed!" + style.RESET
        else:
            return True, style.GREEN + "\nAllready approved!" + style.RESET

    def sell_tokens(self):
        self.approve()
        txn = self.contract_swap.functions.fromTokentoBNBFee(
            self.token_address,
            self.slippage * 10 ** 18,
            int(self.token_contract.functions.balanceOf(self.address).call() - 1),
            (int(time.time()) + 10000),
        ).buildTransaction(
            {
                "from": self.address,
                "gas": 550000,
                "gasPrice": self.gas_price,
                "nonce": self.w3.eth.getTransactionCount(self.address),
                "value": 0,
            }
        )
        txn.update({"gas": int(self.estimateGas(txn))})
        signed_txn = self.w3.eth.account.sign_transaction(txn, self.private_key)
        txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        print(style.GREEN + "\nSELL Hash :", txn.hex() + style.RESET)
        txn_receipt = self.w3.eth.waitForTransactionReceipt(txn)
        if txn_receipt["status"] == 1:
            return True, style.GREEN + "\nSELL Transaction Successfull!" + style.RESET
        else:
            return False, style.RED + "\nSELL Transaction Faild!" + style.RESET

    # --------------- ANTIBOT MEASURES ---------------

    # The following methods are used to check if a specific function has been called by contract owner.
    # It checks in the mempool for token contract's transactions, if the specified function is called, then we buy.
    # Ultra useful to bypass antibots measures. You just have to specify the targeted function in settings.json
    # (exemple: stopSniperPrevention or something like that). You have to know and study the contract prior to launch.
    def setupTargetedFunction(self) -> str:
        """
        Load the targeted function in contract address.
        :return: formatted function
        """
        with open("./Settings.json") as f:
            keys = json.load(f)
        if ' ' in keys['function']:
            return self.format_function(keys['function'])
        else:
            return keys['function']

    @staticmethod
    def format_function(function: str) -> str:
        """
        Format the function to be able to convert it's signature to hash.
        :param function: string specified in settings.json
        :return: formatted function. Delete parameters name, spaces, and keep parameters types.
        """
        splitted = function.split(' ')[:-1]
        return ','.join([e for e in splitted if ',' not in e]) + ')'

    def check_for_function_in_event(self, event) -> bool:
        """
        Will return True if a tx has been sent implying the targeted function.
        :param event: Web3 event
        :return: bool
        """
        tx = Web3.toJSON(event).replace('"', '')
        tx_details = self.w3.eth.getTransaction(tx)
        if tx_details['to'] == self.token_address:
            if str(self.w3.keccak(text=self.targeted_function)[0:4].hex()) in tx_details['input']:
                return True

    async def wait_for_function(self, event_filter, poll_interval: float) -> bool:
        """
        Get events in the mempool then send them to check_for_function_in_event.
        :param event_filter: web3 filtering pending blocks
        :param poll_interval: time in seconds
        :return: bool if targeted function has been caught
        """
        while True:
            try:
                for event in event_filter.get_new_entries():
                    check = self.check_for_function_in_event(event)
                    if check:
                        return True
                await asyncio.sleep(poll_interval)
            except TransactionNotFound:
                continue

    def checkFunctionCall(self) -> bool:
        """
        Run the event loop to filter txs in mempool. If we exit loop (wen targeted function has been caught),
        we return True.
        :return: bool if targeted function has been caught.
        """
        tx_filter = self.w3.eth.filter('pending')
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(
                asyncio.gather(
                    self.wait_for_function(tx_filter, 0.07)))
        finally:
            # Function called by token owner, return True
            return True