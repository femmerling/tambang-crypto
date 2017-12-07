import requests
import psycopg2
import json
import random

import time

url_string = "https://vip.bitcoin.co.id/tradingview/history?symbol=%s&resolution=%s&from=%s&to=%s"
pair_symbol = 'BTCIDR'

# 1-jan to now
unix_timestamp_from = 1503187200     
unix_timestamp_to = 1511614800

candle_resolution = 1
MAX_TICKER = 10000

# response_data = '{"s":"ok","t":[1510311600,1510311660,1510311720,1510311780,1510311840,1510311900],"c":[4485900,4485900,4479900,4479900,4489100,4490000],"o":[4470700,4485900,4485900,4479900,4479900,4489100],"h":[4485900,4487600,4487100,4486900,4489100,4490000],"l":[4470700,4485900,4479900,4479900,4479900,4489100],"v":[16.54629806,15.63602211,7.60391211,0.505,1.04875302,5.56542519]}'
# candle_data = json.loads(response_data)

while unix_timestamp_from < unix_timestamp_to:
    
    tmp_to = unix_timestamp_from + (MAX_TICKER * 60)
    formatted_url = url_string % (pair_symbol, candle_resolution, unix_timestamp_from, tmp_to)
    print('GET %s to %s' % (unix_timestamp_from, unix_timestamp_to))
    print(formatted_url)
    # print(time.time())
    unix_timestamp_from = tmp_to + 60

    r = requests.get(formatted_url)
    candle_data = r.json()

    sql = 'INSERT INTO bitcoincoid_candles_idr_btc(start, open, high, low, close, vwp, volume, trades) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING'

    conn = psycopg2.connect(host="localhost",database="tambangkoin", user="postgres", password="postgres")
    cur = conn.cursor()
    for i in range(len(candle_data['t'])):
        vwp = (float(candle_data['h'][i]) + float(candle_data['l'][i]) + float(candle_data['c'][i])) / 3
        num_trades = random.randrange(7)
        cur.execute(sql, (candle_data['t'][i], candle_data['o'][i], candle_data['h'][i], candle_data['l'][i], candle_data['c'][i], vwp, candle_data['v'][i], num_trades ))

    conn.commit()
    # print(time.time())
    # print('sleep')
    time.sleep(5)
    