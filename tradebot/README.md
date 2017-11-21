# Tradebot

This bot leverages a buy-sell-buy approach.

Settings can be done in the stats.txt

`slot` is the amount of IDR you wish to use to buy BTC and will remain constant in each purchase
`initial_buy` should be set to 1 if you with start the trading with buy
`expected_margin_amt` set this with the percentage you wish to attain

Bear in mind that trading fee occurs at 0.3%

set your API-key and API-Secret in the app.py file

# Requirements

Python 3.5+

```
$ pip install virtualenv
$ virtualenv -p python3 env
$ source env/bin/activate
$ python app.py
```

Hold tight and see

