import json
import vipbtc
import time

api_key = "some-api-key-from-bitcoin.co.id"
secret_key = "some-secret-key-from-bitcoin.co.id"

slot = 0
purchase_price=0
btc_bought=0.0
last_price=0
last_sell=0
expected_margin=0
expected_margin_amt=0.0
initial_buy = False

def update_stat_file():
    last_data = dict(
        slot=slot,
        purchase_price=purchase_price,
        btc_bought=float(btc_bought),
        last_price=last_price,
        last_sell=last_sell,
        initial_buy=1 if initial_buy else 0)
    stats = open('stats.txt','w')
    stats.write(json.dumps(last_data))
    stats.close()

def count_sell_margin():
    return (last_price*float(btc_bought)) - (purchase_price*float(btc_bought))

with open('stats.txt','r') as stats:
    stats=json.loads(stats.readline())
    slot=stats.get('slot')
    purchase_price=stats.get('purchase_price')
    btc_bought=stats.get('btc_bought')
    last_price=stats.get('last_price')
    last_low=stats.get('last_low')
    initial_buy= True if stats.get('initial_buy') == 1 else False
    expected_margin_amt=stats.get('expected_margin_amt')
    expected_margin=slot*expected_margin_amt

api = vipbtc.TradeAPI(api_key,secret_key)

def buy_it(amount,price):
    return api.trade(
        ttype="buy",
        amount=amount,
        price=price)

def sell_it(amount,price):
    return api.trade(
        ttype="sell",
        amount=amount,
        price=price)

while True:
    last_info = vipbtc.getTicker()
    sell = last_info.get("buy")
    print("last sell {}".format(sell))
    buy = last_info.get("sell")
    print("last buy {}".format(buy))
    if initial_buy:
        transaction = buy_it(slot,buy)
        initial_buy = False
        last_price=buy
        purchase_price=buy
        btc_bought=transaction.get("return").get("receive_btc")
        print("Bought {} BTC at {}".format(btc_bought, buy))
        print("------")
        update_stat_file()
    else:
        last_price = sell
        margin = count_sell_margin()
        if margin >= expected_margin:
            transaction = sell_it(float(btc_bought), sell)
            print("Sold {} BTC at {}".format(btc_bought, sell))
            last_sell=sell
            purchase_price=sell
            btc_bought=0.0
            initial_buy=True
            print("------")
            update_stat_file()
            transaction = buy_it(slot, buy)
            initial_buy = False
            last_price=buy
            purchase_price=buy
            btc_bought=transaction.get("return").get("receive_btc")
            print("Bought {} BTC at {}".format(btc_bought, buy))
            print("------")
            update_stat_file()
        else:
            print("not selling, margin is only {} of the expected {}".format(margin, expected_margin))
            print("------")
    time.sleep(2)

print("Thanks for trading!!!")
