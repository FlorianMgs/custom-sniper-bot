from web3 import Web3
import argparse, math, sys, json, requests
import sys
from txns import TXN
from time import sleep
from style import style
from halo import Halo

# DEV : Add spinner features ! ***

ascii = """
  ______   __    __  ________  ________  ________   ______   __    __         ______   __       __   ______   _______  
 /      \ |  \  |  \|        \|        \|        \ /      \ |  \  |  \       /      \ |  \  _  |  \ /      \ |       \ 
|  $$$$$$\| $$  | $$| $$$$$$$$| $$$$$$$$| $$$$$$$$|  $$$$$$\| $$  | $$      |  $$$$$$\| $$ / \ | $$|  $$$$$$\| $$$$$$$
| $$___\$$| $$__| $$| $$__    | $$__    | $$__    | $$___\$$| $$__| $$      | $$___\$$| $$/  $\| $$| $$__| $$| $$__/ $$
 \$$    \ | $$    $$| $$  \   | $$  \   | $$  \    \$$    \ | $$    $$       \$$    \ | $$  $$$\ $$| $$    $$| $$    $$
 _\$$$$$$\| $$$$$$$$| $$$$$   | $$$$$   | $$$$$    _\$$$$$$\| $$$$$$$$       _\$$$$$$\| $$ $$\$$\$$| $$$$$$$$| $$$$$$$ 
|  \__| $$| $$  | $$| $$_____ | $$_____ | $$_____ |  \__| $$| $$  | $$      |  \__| $$| $$$$  \$$$$| $$  | $$| $$      
 \$$    $$| $$  | $$| $$     \| $$     \| $$     \ \$$    $$| $$  | $$       \$$    $$| $$$    \$$$| $$  | $$| $$      
  \$$$$$$  \$$   \$$ \$$$$$$$$ \$$$$$$$$ \$$$$$$$$  \$$$$$$  \$$   \$$        \$$$$$$  \$$      \$$ \$$   \$$ \$$      
                                                                                                                                 
"""


# spinneroptions = {"interval": 250, "frames": ["🚀 ", "🌙 ", "🚀 ", "🌕 ", "💸 "]}

parser = argparse.ArgumentParser(
    description='Set your Token and Amount example: "sniper.py -t 0x34faa80fec0233e045ed4737cc152a71e490e2e3 -a 0.2 -sl 15"'
)
parser.add_argument(
    "-t",
    "--token",
    help='str, Token for snipe e.g. "-t 0x34faa80fec0233e045ed4737cc152a71e490e2e3"',
)
parser.add_argument(
    "-a", "--amount", default=0, help='float, Amount in Bnb to snipe e.g. "-a 0.1"'
)
parser.add_argument(
    "-tx",
    "--txamount",
    default=1,
    nargs="?",
    const=1,
    type=int,
    help='int, how mutch tx you want to send? It Split your BNB Amount in e.g. "-tx 5"',
)
parser.add_argument(
    "-hp",
    "--honeypot",
    action="store_true",
    help='Check if your token to buy is a Honeypot, e.g. "-hp" or "--honeypot"',
)
parser.add_argument(
    "-nb",
    "--nobuy",
    action="store_true",
    help="No Buy, Skipp buy, if you want to use only TakeProfit/StopLoss/TrailingStopLoss",
)
parser.add_argument(
    "-tp",
    "--takeprofit",
    default=0,
    nargs="?",
    const=True,
    type=int,
    help='int, Percentage TakeProfit from your input BNB amount "-tp 50" ',
)
parser.add_argument(
    "-sl",
    "--stoploss",
    default=0,
    nargs="?",
    const=True,
    type=int,
    help='int, Percentage Stop loss from your input BNB amount "-sl 50" ',
)
parser.add_argument(
    "-tsl",
    "--trailingstoploss",
    default=0,
    nargs="?",
    const=True,
    type=int,
    help='int, Percentage Trailing-Stop-loss from your first Quote "-tsl 50" ',
)
parser.add_argument(
    "-wb",
    "--awaitBlocks",
    default=0,
    nargs="?",
    const=True,
    type=int,
    help='int, Await Blocks before sending BUY Transaction "-ab 50" ',
)
parser.add_argument(
    "-so",
    "--sellonly",
    action="store_true",
    help="Sell all your Tokens from given address",
)
parser.add_argument(
    "-bo",
    "--buyonly",
    action="store_true",
    help="Buy Tokens with from your given amount",
)
parser.add_argument(
    "-dsec",
    "--DisabledSwapEnabledCheck",
    action="store_true",
    help="this argument disabled the SwapEnabled Check!",
)
parser.add_argument(
    "-wf",
    "--awaitFunctionCall",
    action="store_true",
    help="Await for a specific function to be called before buy, allowing antibot measures bypass",
)

args = parser.parse_args()


class SniperBot:
    def __init__(self):
        self.parseArgs()
        self.settings = self.loadSettings()
        self.SayWelcome()

    def loadSettings(self):
        with open("Settings.json", "r") as settings:
            settings = json.load(settings)
        return settings

    def SayWelcome(self):
        print(style().YELLOW + ascii + style().RESET)
        print(
            style().GREEN
            + "Start Sniper Tool with following arguments:"
            + style().RESET
        )
        print(style().BLUE + "---------------------------------" + style().RESET)
        print(
            style().YELLOW + "Amount for Buy:",
            style().GREEN + str(self.amount) + " BNB" + style().RESET,
        )
        print(
            style().YELLOW + "Token to Interact :",
            style().GREEN + str(self.token) + style().RESET,
        )
        print(
            style().YELLOW + "Transaction to send:",
            style().GREEN + str(self.tx) + style().RESET,
        )
        print(
            style().YELLOW + "Amount per transaction :",
            style().GREEN + str("{0:.8f}".format(self.amountForSnipe)) + style().RESET,
        )
        print(
            style().YELLOW + "Await Blocks before buy :",
            style().GREEN + str(self.wb) + style().RESET,
        )
        if self.tsl != 0:
            print(
                style().YELLOW + "Trailing Stop loss Percent :",
                style().GREEN + str(self.tsl) + style().RESET,
            )
        if self.tp != 0:
            print(
                style().YELLOW + "Take Profit Percent :",
                style().GREEN + str(self.tp) + style().RESET,
            )
            print(
                style().YELLOW + "Target Output for Take Profit:",
                style().GREEN
                + str("{0:.8f}".format(self.takeProfitOutput))
                + style().RESET,
            )
        if self.sl != 0:
            print(
                style().YELLOW + "Stop loss Percent :",
                style().GREEN + str(self.sl) + style().RESET,
            )
            print(
                style().YELLOW + "Sell if Output is smaller as:",
                style().GREEN + str("{0:.8f}".format(self.stoploss)) + style().RESET,
            )
        print(style().BLUE + "---------------------------------" + style().RESET)

    def parseArgs(self):
        self.token = args.token
        if self.token == None:
            print(
                style.RED
                + "Please Check your Token argument e.g. -t 0x34faa80fec0233e045ed4737cc152a71e490e2e3"
            )
            print("exit!")
            sys.exit()
        self.amount = args.amount
        if args.nobuy != True:
            if not args.sellonly:
                if self.amount == 0:
                    print(style.RED + "Please Check your Amount argument e.g. -a 0.01")
                    print("exit!")
                    sys.exit()
        self.tx = args.txamount
        self.amountForSnipe = float(self.amount) / float(self.tx)
        self.hp = args.honeypot
        self.wb = args.awaitBlocks
        self.wf = args.awaitFunctionCall
        self.tp = args.takeprofit
        self.sl = args.stoploss
        self.tsl = args.trailingstoploss
        self.stoploss = 0
        self.takeProfitOutput = 0
        if self.tp != 0:
            self.takeProfitOutput = self.calcProfit()
        if self.sl != 0:
            self.stoploss = self.calcloss()

    def calcProfit(self):  # Return Amount of BNB you want to receive at end's snip
        a = ((self.amountForSnipe * self.tx) * self.tp) / 100
        b = a + (self.amountForSnipe * self.tx)
        return b

    def calcloss(self):
        a = ((self.amountForSnipe * self.tx) * self.sl) / 100
        b = (self.amountForSnipe * self.tx) - a
        return b

    def calcNewTrailingStop(self, currentPrice):
        a = (currentPrice * self.tsl) / 100
        b = currentPrice - a
        return b

    def awaitBuy(self):
        # spinner = Halo(text="await Buy", spinner=spinneroptions)
        # spinner.start()
        for i in range(self.tx):
            # spinner.start()
            self.TXN = TXN(self.token, self.amountForSnipe)
            # tx_check = self.TXN.check_token()
            tx = self.TXN.buy_token()
            # spinner.stop()
            # print(tx_check[1])
            print(tx[1])
            if tx[0] != True:
                sys.exit()

    def awaitSell(self):
        # spinner = Halo(text="await Sell", spinner=spinneroptions)
        # spinner.start()
        self.TXN = TXN(self.token, self.amountForSnipe)
        tx = self.TXN.sell_tokens()
        # spinner.stop()
        print(tx[1])
        if tx[0] != True:
            sys.exit()

    def awaitApprove(self):
        # spinner = Halo(text="await Approve", spinner=spinneroptions)
        # spinner.start()
        self.TXN = TXN(self.token, self.amountForSnipe)
        tx = self.TXN.approve()
        # spinner.stop()
        print(tx[1])
        if tx[0] != True:
            sys.exit()

    def awaitBlocks(self):
        # spinner = Halo(text="await Blocks", spinner=spinneroptions)
        # spinner.start()
        waitForBlock = self.TXN.getBlockHigh() + self.wb
        while True:
            sleep(0.13)
            if self.TXN.getBlockHigh() > waitForBlock:
                # spinner.stop()
                break
        print(style().GREEN + "[DONE] Wait Blocks finish!")

    # DEV : A adapter avec le smart contract ***
    def awaitLiquidity(self):
        # spinner = Halo(text="await Liquidity", spinner=spinneroptions)
        # spinner.start()
        while True:
            sleep(0.07)
            try:
                self.TXN.getOutputfromBNBtoToken()
                # spinner.stop()
                break
            except Exception as e:
                if "UPDATE" in str(e):
                    print(e)
                    sys.exit()
                continue
        print(style().GREEN + "[DONE] Liquidity is Added!" + style().RESET)

    # DEV : A adapter avec le smart contract ***
    def awaitEnabledBuy(self):
        # spinner = Halo(text="await Dev Enables Swapping", spinner=spinneroptions)
        # spinner.start()
        while True:
            sleep(0.07)
            try:
                if self.TXN.checkifTokenBuyDisabled() == True:
                    # spinner.stop()
                    break
            except Exception as e:
                if "UPDATE" in str(e):
                    print(e)
                    sys.exit()
                continue
        print(style().GREEN + "[DONE] Swapping is Enabled!" + style().RESET)

    # DEV : A adapter avec le smart contract / TRAILING STOP / TP / SL*** (TP ok, manque le reste)
    def awaitManagePosition(self):
        highestLastPrice = 0
        TokenBalance = round(self.TXN.get_token_balance(), 5)
        while True:
            sleep(0.3)
            LastPrice = float(self.TXN.getOutputfromTokentoBNB() / (10 ** 18))
            if self.tsl != 0:
                if LastPrice > highestLastPrice:
                    highestLastPrice = LastPrice
                    TrailingStopLoss = self.calcNewTrailingStop(LastPrice)
                if LastPrice < TrailingStopLoss:
                    print(
                        style().GREEN + "[TRAILING STOP LOSS] Triggert!" + style().RESET
                    )
                    self.awaitSell()
                    break
            if self.takeProfitOutput != 0:  # en cours de TEST ! (Done)
                if LastPrice * TokenBalance >= self.takeProfitOutput:
                    print()
                    print(style().GREEN + "[TAKE PROFIT] Triggert!" + style().RESET)
                    self.awaitSell()
                    break
            if self.stoploss != 0:
                if LastPrice <= self.stoploss:
                    print()
                    print(style().GREEN + "[STOP LOSS] Triggert!" + style().RESET)
                    self.awaitSell()
                    break
            # bosser sur les outputs pour avoir le suivi du trade (en % ou juste comparer prix entrée + prix sortie)
            msg = str(
                "Token Balance: "
                + str("{0:.5f}".format(TokenBalance))
                + "| CurrentOutput: "
                + str("{0:.7f}".format(LastPrice))
                + " BNB"
            )
            if self.stoploss != 0:
                msg = (
                    msg
                    + "| Stop loss below: "
                    + str("{0:.7f}".format(self.stoploss))
                    + "BNB"
                )
            if self.takeProfitOutput != 0:
                priceOver = self.takeProfitOutput / TokenBalance
                msg = (
                    msg
                    + "| Take Profit Over: "
                    + str("{0:.7f}".format(self.takeProfitOutput))
                    + " BNB"
                    + "| Price Profit Over: "
                    + str("{0:.10f}".format(priceOver))
                    + " BNB"
                )
            if self.tsl != 0:
                msg = (
                    msg
                    + "| Trailing Stop loss below: "
                    + str("{0:.7f}".format(TrailingStopLoss))
                    + " BNB"
                )
            print(msg, end="\r")

        print(style().GREEN + "[DONE] Position Manager Finished!" + style().RESET)

    # DEV: sell_tokens
    def StartUP(self):
        self.TXN = TXN(self.token, self.amountForSnipe)

        if args.sellonly:
            print("Start SellOnly, Selling Now all tokens!")
            inp = input("please confirm y/n\n")
            if inp.lower() == "y":
                print(self.TXN.sell_tokens()[1])
                sys.exit()
            else:
                sys.exit()

        if args.buyonly:
            print(f"Start BuyOnly, buy now with {self.amountForSnipe}BNB tokens!")
            print(self.TXN.buy_token()[1])
            sys.exit()

        if args.nobuy != True:
            self.awaitLiquidity()
            if args.DisabledSwapEnabledCheck != True:
                self.awaitEnabledBuy()

        honeyTax = self.TXN.checkToken()
        if self.hp == True:
            print(style().YELLOW + "Checking Token is Honeypot..." + style().RESET)
            if honeyTax[2] == True:
                print(style.RED + "Token is Honeypot, exiting")
                sys.exit()
            elif honeyTax[2] == False:
                print(style().GREEN + "[DONE] Token is NOT a Honeypot!" + style().RESET)
        if honeyTax[1] > self.settings["MaxSellTax"]:
            print(style().RED + "Token SellTax exceeds Settings.json, exiting!")
            sys.exit()
        if honeyTax[0] > self.settings["MaxBuyTax"]:
            print(style().RED + "Token BuyTax exceeds Settings.json, exiting!")
            sys.exit()

        if self.wb != 0:
            self.awaitBlocks()

        if args.nobuy != True:
            if self.wf:
                function_called = self.TXN.checkFunctionCall()
                if function_called:
                    print(
                        style().GREEN
                        + "[DONE] Function called, now we buy!"
                        + style().RESET
                    )
                    self.awaitBuy()
            else:
                self.awaitBuy()

        sleep(
            7
        )  # Give the RPC/WS some time to Index your address nonce, make it higher if " ValueError: {'code': -32000, 'message': 'nonce too low'} "
        self.awaitApprove()

        if self.tsl != 0 or self.stoploss != 0 or self.takeProfitOutput != 0:
            self.awaitManagePosition()

        print(style().GREEN + "[DONE] Sheeeeesh Sniper Bot finish!" + style().RESET)


SniperBot().StartUP()
