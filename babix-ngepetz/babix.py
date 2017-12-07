import vipbtc
import time
import json
import random

import requests
from requests_futures.sessions import FuturesSession

import logging
from logging.handlers import RotatingFileHandler

# INIT VALUE
API_KEY = 'YOUR-API-KEY'
API_SECRET = 'YOUR-API-SECRET'

# wait second until transaction filled
SLEEP_SECONDS = 5 
# wait second before we correct the transaction price
MAX_WAIT_TIME_SECONDS = 30
# wait second at last step (waiting for sell to IDR)
LAST_STEP_WAIT_TIME_SECONDS = 30

bitcoincoid_account = vipbtc.TradeAPI(API_KEY, API_SECRET)

base_url = 'https://vip.bitcoin.co.id/api/'
private_url = 'https://vip.bitcoin.co.id/tapi/'
pairs = {
    'BTC/IDR': 'btc_idr',
    'ETH/IDR': 'eth_idr',
    'LTC/IDR': 'ltc_idr',
    'XLM/IDR': 'str_idr',
    'XRP/IDR': 'xrp_idr',
    'NXT/IDR': 'nxt_idr',
    'ETH/BTC': 'eth_btc',
    'LTC/BTC': 'ltc_btc',
    'XLM/BTC': 'str_btc',
    'XRP/BTC': 'xrp_btc',
    'NXT/BTC': 'nxt_btc',
}

pip = {
    'str_idr': 1,
    'xrp_idr': 1,
    'nxt_idr': 1,
    'ltc_idr': 100,
    'eth_idr': 100,
    'btc_idr': 100
}

modal_duid = 15000000
fee_portion = 0.003
threshold = 0.003 #0.3pct profit threshold
net_portion = (1 - fee_portion)
market_depths = {}
final_idr = {}
config_path = {}
MAX_PARTITION = 20 # brute force partition to find best matchsess


#PROXY SAMPLE for luminati.io
# proxy_username = 'LUMINATI-USERNAME'
# proxy_password = 'LUMINATI-PASSWORD'
# proxy_port = 22225
# proxy_sesion_id = random.random()
# proxy_url = 'http://%s-country-sg-session-%s:%s@zproxy.luminati.io:%d' % (proxy_username, proxy_sesion_id, proxy_password, proxy_port)
# proxies = {'http': proxy_url, 'https': proxy_url}

# PROXY SAMPLE FOR PROXYMESH
# proxy_username = 'PROXYMESH-USERNAME'
# proxy_password = 'PROXYMESH-PASSWORD'
# proxy_host = 'jp.proxymesh.com'
# proxy_port = '31280'
# proxy_url = 'http://%s:%s@%s:%s' % (proxy_username, proxy_password, proxy_host, proxy_port)
# proxies = {'http': proxy_url, 'https': proxy_url}

# dont forget to change proxy setting on fetch_market_data

session = FuturesSession(max_workers=9)
logger = logging.getLogger("babix.ngepetz")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logfile_handler = RotatingFileHandler(filename='ngepetz.log', 
                              maxBytes=10485760,
                              backupCount=10)
logfile_handler.setFormatter(formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(logfile_handler)



def fetch_market_data():
    req_result = {}
    fetch_depths = {}
    # logger.info('Started loading market pair data')
    for pair in pairs:
        
        url = base_url + pairs[pair] + '/depth'
        # req_result[pair] = session.get(url, proxies=proxies)
        req_result[pair] = session.get(url)

    for pair in pairs:
        market_state = {}
        response = req_result[pair].result()
        if response.status_code == 200:
            trade_list = response.json()
            highest_buy = trade_list['buy'][0][0]
            highest_sell = trade_list['sell'][0][0]
            market_state['highest_buy'] = highest_buy
            market_state['highest_sell'] = highest_sell
            market_state['buy'] = trade_list['buy']
            market_state['sell'] = trade_list['sell']
        fetch_depths[pair] = market_state
    # logger.info('Finished loading market pair data')
    return fetch_depths

def calculate_idr_btc_alt_path(initial_amount):
    fee_1 = initial_amount * 0.003
    btc_aqcuired = (initial_amount / float(market_depths['BTC/IDR']['highest_sell']))
    btc_buy_price = float(market_depths['BTC/IDR']['highest_sell'])
    if btc_aqcuired > float(market_depths['BTC/IDR']['sell'][0][1]):
        for btc_sell in market_depths['BTC/IDR']['sell']:
            if float(btc_sell[1]) > btc_aqcuired:
                btc_buy_price = float(btc_sell[0])
                break
    
    for alt_symbol in ['ETH', 'LTC', 'XLM', 'XRP', 'NXT']:
        
        config_key = 'IDR_BTC_' + alt_symbol
        config_path[config_key] = {}

        market_btc_symbol = alt_symbol + '/BTC'
        market_idr_symbol = alt_symbol + '/IDR'
        alt_buy_price = float(market_depths[market_btc_symbol]['highest_sell'])
        altcoin_acquired = (btc_aqcuired / float(market_depths[market_btc_symbol]['highest_sell']))
        if altcoin_acquired > float(market_depths[market_btc_symbol]['sell'][0][1]):
            for alt_sell in market_depths[market_btc_symbol]['sell']:
                if float(alt_sell[1]) > altcoin_acquired:
                    alt_buy_price = float(alt_sell[0])
                    altcoin_acquired = (btc_aqcuired / alt_buy_price)
                    break
        
        idr_acquired = altcoin_acquired * float(market_depths[market_idr_symbol]['highest_buy'])
        alt_sell_price = float(market_depths[market_idr_symbol]['highest_buy'])
        if altcoin_acquired > float(market_depths[market_idr_symbol]['buy'][0][1]):
            for alt_buy in market_depths[market_idr_symbol]['buy']:
                if float(alt_buy[1]) > altcoin_acquired:
                    alt_sell_price = float(alt_buy[0])
                    idr_acquired = altcoin_acquired * alt_sell_price
                    break

        idr_acquired = (idr_acquired * 0.997) - fee_1
        config_path[config_key]['step1_btc_buy_price'] = btc_buy_price
        config_path[config_key]['step2_alt_buy_price'] = alt_buy_price
        config_path[config_key]['step3_alt_sell_price'] = alt_sell_price
        config_path[config_key]['final_idr'] = idr_acquired

def calculate_idr_alt_btc_path(initial_amount):
    fee_1 = initial_amount * 0.003
    for alt_symbol in ['ETH', 'LTC', 'XLM', 'XRP', 'NXT']:
        
        config_key = 'IDR_' + alt_symbol + '_BTC'
        config_path[config_key] = {}

        market_btc_symbol = alt_symbol + '/BTC'
        market_idr_symbol = alt_symbol + '/IDR'
        
        alt_buy_price = float(market_depths[market_idr_symbol]['highest_sell'])
        altcoin_acquired = (initial_amount / float(market_depths[market_idr_symbol]['highest_sell']))
        
        if altcoin_acquired > float(market_depths[market_idr_symbol]['sell'][0][1]):
            for alt_sell in market_depths[market_idr_symbol]['sell']:
                if float(alt_sell[1]) > altcoin_acquired:
                    alt_buy_price = float(alt_sell[0])
                    altcoin_acquired = (initial_amount / float(alt_sell[0]))
                    break
        
        btc_acquired = altcoin_acquired * float(market_depths[market_btc_symbol]['highest_buy'])
        alt_sell_price = float(market_depths[market_btc_symbol]['highest_buy'])
        
        if altcoin_acquired > float(market_depths[market_btc_symbol]['buy'][0][1]):
            for alt_buy in market_depths[market_btc_symbol]['buy']:
                if float(alt_buy[1]) > altcoin_acquired:
                    alt_sell_price = float(alt_buy[0])
                    btc_acquired = altcoin_acquired * alt_sell_price
                    break

        idr_acquired = (btc_acquired * float(market_depths['BTC/IDR']['highest_buy']))
        btc_sell_price = float(market_depths['BTC/IDR']['highest_buy'])
        if btc_acquired > float(market_depths['BTC/IDR']['buy'][0][1]):
            for btc_buy in market_depths['BTC/IDR']['buy']:
                if float(btc_buy[1]) > btc_acquired:
                    btc_sell_price = float(btc_buy[0])
                    idr_acquired = btc_acquired * btc_sell_price
                    break

        idr_acquired = (idr_acquired * 0.997) - fee_1
        config_path[config_key]['step1_alt_buy_price'] = alt_buy_price
        config_path[config_key]['step2_alt_sell_price'] = alt_sell_price
        config_path[config_key]['step3_btc_sell_price'] = btc_sell_price
        config_path[config_key]['final_idr'] = idr_acquired

def path_idr_btc_alt(market_pair_btc, market_pair_idr, alt_btc_pair, alt_idr_pair, alt_symbol, path_name, amount_idr):
    corrective_action_triggered = False
    wait_time_seconds = 0
    #execute trading path
    # buy BTC:
    logger.info('Following profit PATH IDR to BTC to %s to IDR' % alt_symbol)
    # logger.debug('Initial state: %s ' % bitcoincoid_account.getInfo())

    price_to_buy = config_path[path_name]['step1_btc_buy_price']
    amount_to_buy = amount_idr
    
    logger.info('Put order to buy BTC at price %.10f, amount %.10f' % (price_to_buy, amount_to_buy))
    trade_result = bitcoincoid_account.trade('btc_idr', 'buy', amount_to_buy, price_to_buy, 'idr')
    logger.debug(json.dumps(trade_result))

    while trade_result['success'] != 1:
        logger.info('Error putting order, retrying')
        time.sleep(1)
        trade_result = bitcoincoid_account.trade('btc_idr', 'buy', amount_to_buy, price_to_buy, 'idr')
        logger.debug(json.dumps(trade_result))

    order_id = trade_result['return']['order_id']
    spent_rp = float(trade_result['return']['remain_rp']) + float(trade_result['return']['spend_rp'])
    amount_btc_received = float(spent_rp / price_to_buy)

    logger.info('Successfully put buy BTC on %.10f amount %.10f, got %.10f' % (price_to_buy, amount_to_buy, amount_btc_received))
    order_info = bitcoincoid_account.getOrder(order_id, 'btc_idr')

    logger.debug(json.dumps(order_info))
    while order_info['return']['order']['status'] != 'filled':
        logger.info('Waiting for orders to be finalized, sleep %s seconds' % SLEEP_SECONDS)
        time.sleep(SLEEP_SECONDS)
        wait_time_seconds += SLEEP_SECONDS
        order_info = bitcoincoid_account.getOrder(order_id, 'btc_idr')
        logger.debug(json.dumps(order_info))
        
        # corrective action while nyangkuts
        if wait_time_seconds >= MAX_WAIT_TIME_SECONDS:
            order_info = corrective_action(pair='btc_idr', order_info=order_info)
            order_id = order_info['return']['order']['order_id']
            corrective_action_triggered = True
            wait_time_seconds = 0
    
    # buy altcoin using BTC
    price_to_buy = config_path[path_name]['step2_alt_buy_price']
    amount_to_buy = amount_btc_received

    if corrective_action_triggered:
        current_coins = get_current_coin_amount('btc')
        amount_to_buy = amount_btc_received if amount_btc_received < current_coins else current_coins
        price_to_buy = get_latest_price(alt_btc_pair, 'buy')

    logger.info('Put order to buy %s at price %.10f,amount %.10f BTC' % (alt_symbol, price_to_buy, amount_to_buy))
    trade_result = bitcoincoid_account.trade(alt_btc_pair, 'buy', amount_to_buy, price_to_buy, 'btc')
    logger.debug(json.dumps(trade_result))

    while trade_result['success'] != 1:
        logger.info('Error putting order, retrying')
        time.sleep(1)
        trade_result = bitcoincoid_account.trade(alt_btc_pair, 'buy', amount_to_buy, price_to_buy, 'btc')
        logger.debug(json.dumps(trade_result))

    order_id = trade_result['return']['order_id']

    spent_btc = float(trade_result['return']['remain_btc']) + float(trade_result['return']['spend_btc'])
    amount_alt_received = float(spent_btc / price_to_buy)

    logger.info('Successfully put buy %s on %.10f amount %.10f' % (alt_symbol,  price_to_buy, amount_to_buy))
    
    order_info = bitcoincoid_account.getOrder(order_id, alt_btc_pair)
    logger.debug(json.dumps(order_info))
    while order_info['return']['order']['status'] != 'filled':
        logger.info('Waiting for orders to be finalized, sleep %s seconds' % SLEEP_SECONDS)
        time.sleep(SLEEP_SECONDS)
        wait_time_seconds += SLEEP_SECONDS
        order_info = bitcoincoid_account.getOrder(order_id, alt_btc_pair)
        logger.debug(json.dumps(order_info))

        # corrective action while nyangkuts
        if wait_time_seconds >= MAX_WAIT_TIME_SECONDS:
            order_info = corrective_action(pair=alt_btc_pair, order_info=order_info)
            order_id = order_info['return']['order']['order_id']
            corrective_action_triggered = True
            wait_time_seconds = 0
    
    # sell altcoin to IDR
    price_to_sell = config_path[path_name]['step3_alt_sell_price']
    amount_to_sell = amount_alt_received

    if corrective_action_triggered:
        current_coins = get_current_coin_amount(alt_symbol)
        amount_to_sell = amount_alt_received if amount_alt_received < current_coins else current_coins
        price_to_sell = get_latest_price(alt_idr_pair, 'sell')

    logger.info('Put order to sell %s at price %.10f IDR, amount %.10f' % (alt_symbol, price_to_sell, amount_to_sell))
    trade_result = bitcoincoid_account.trade(alt_idr_pair, 'sell', amount_to_sell, price_to_sell, alt_symbol)
    logger.debug(json.dumps(trade_result))

    while trade_result['success'] != 1:
        logger.info('Error putting order, retrying')
        time.sleep(1)
        trade_result = bitcoincoid_account.trade(alt_idr_pair, 'sell', amount_to_sell, price_to_sell, alt_symbol)
        logger.debug(json.dumps(trade_result))

    order_id = trade_result['return']['order_id']
    order_info = bitcoincoid_account.getOrder(order_id, alt_idr_pair)
    logger.debug(json.dumps(order_info))
    while order_info['return']['order']['status'] != 'filled':
        logger.info('Waiting for orders to be finalized, sleep %s seconds' % SLEEP_SECONDS)
        time.sleep(SLEEP_SECONDS) # sleep for 5 secs, wait for orders to finalize
        wait_time_seconds += SLEEP_SECONDS
        logger.debug(json.dumps(order_info))

        # corrective action while nyangkuts
        if wait_time_seconds >= LAST_STEP_WAIT_TIME_SECONDS:
            order_info = corrective_action(pair=alt_idr_pair, order_info=order_info)
            order_id = order_info['return']['order']['order_id']
            corrective_action_triggered = True
            wait_time_seconds = 0
    
    # logger.debug('Last state: %s ' % bitcoincoid_account.getInfo())

def path_idr_alt_btc(market_pair_btc, market_pair_idr, alt_btc_pair, alt_idr_pair, alt_symbol, path_name, amount_idr):
    corrective_action_triggered = False
    wait_time_seconds = 0
    #execute trading path
    #buy alt from IDR:
    logger.info('Following profit PATH IDR to %s to BTC to IDR' % alt_symbol)
    # logger.debug('Initial state: %s ' % bitcoincoid_account.getInfo())

    price_to_buy = config_path[path_name]['step1_alt_buy_price']
    amount_to_buy = amount_idr

    logger.info('Put order to buy %s at price %.10f, amount %.10f' % (alt_symbol, price_to_buy, amount_to_buy))
    trade_result = bitcoincoid_account.trade(alt_idr_pair, 'buy', amount_to_buy, price_to_buy, 'idr')
    logger.debug(json.dumps(trade_result))

    while trade_result['success'] != 1:
        logger.info('Error putting order, retrying')
        time.sleep(1)
        trade_result = bitcoincoid_account.trade(alt_idr_pair, 'buy', amount_to_buy, price_to_buy, 'idr')
        logger.debug(json.dumps(trade_result))

    
    order_id = trade_result['return']['order_id']

    spent_rp = float(trade_result['return']['remain_rp']) + float(trade_result['return']['spend_rp'])
    amount_alt_received = float(spent_rp / price_to_buy)

    logger.info('Successfully put buy %s on %.10f amount %.10f' % (alt_symbol, price_to_buy, amount_to_buy))
    order_info = bitcoincoid_account.getOrder(order_id, alt_idr_pair)
    logger.debug(json.dumps(order_info))
    while order_info['return']['order']['status'] != 'filled':
        logger.info('Waiting for orders to be finalized, sleep %s seconds' % SLEEP_SECONDS)
        time.sleep(SLEEP_SECONDS)
        wait_time_seconds += SLEEP_SECONDS
        order_info = bitcoincoid_account.getOrder(order_id, alt_idr_pair)
        logger.debug(json.dumps(order_info))
        
        # corrective action while nyangkuts
        if wait_time_seconds >= MAX_WAIT_TIME_SECONDS:
            order_info = corrective_action(pair=alt_idr_pair, order_info=order_info)
            order_id = order_info['return']['order']['order_id']
            corrective_action_triggered = True
            wait_time_seconds = 0
    
    
    # buy BTC using alt
    price_to_buy = config_path[path_name]['step2_alt_sell_price']
    amount_to_buy = amount_alt_received

    if corrective_action_triggered:
        current_coins = get_current_coin_amount(alt_symbol)
        amount_to_buy = amount_alt_received if amount_alt_received < current_coins else current_coins
        price_to_buy = get_latest_price(alt_btc_pair, 'sell')
    
    logger.info('Put order to buy BTC from %s at price %.10f, amount %.10f' % (alt_symbol, price_to_buy, amount_to_buy))
    trade_result = bitcoincoid_account.trade(alt_btc_pair, 'sell', amount_to_buy, price_to_buy, alt_symbol)
    logger.debug(json.dumps(trade_result))


    while trade_result['success'] != 1:
        logger.info('Error putting order, retrying')
        time.sleep(1)
        trade_result = bitcoincoid_account.trade(alt_btc_pair, 'sell', amount_to_buy, price_to_buy, alt_symbol)
        logger.debug(json.dumps(trade_result))

    
    order_id = trade_result['return']['order_id']
    amount_btc_received = amount_alt_received * price_to_buy

    logger.info('Successfully put buy BTC on %s amount %.10f' % (price_to_buy, amount_to_buy))
    order_info = bitcoincoid_account.getOrder(order_id, alt_btc_pair)
    logger.debug(json.dumps(order_info))
    while order_info['return']['order']['status'] != 'filled':
        logger.info('Waiting for orders to be finalized, sleep %s seconds' % SLEEP_SECONDS)
        time.sleep(SLEEP_SECONDS)
        wait_time_seconds += SLEEP_SECONDS
        order_info = bitcoincoid_account.getOrder(order_id, alt_btc_pair)
        logger.debug(json.dumps(order_info))

        # corrective action while nyangkuts
        if wait_time_seconds >= MAX_WAIT_TIME_SECONDS:
            order_info = corrective_action(pair=alt_btc_pair, order_info=order_info)
            order_id = order_info['return']['order']['order_id']
            corrective_action_triggered = True
            wait_time_seconds = 0
    
    
    # sell BTC to IDR
    price_to_sell = config_path[path_name]['step3_btc_sell_price']
    amount_to_sell = amount_btc_received

    if corrective_action_triggered:
        current_coins = get_current_coin_amount('btc')
        amount_to_sell = amount_btc_received if amount_btc_received < current_coins else current_coins
        price_to_sell = get_latest_price('btc_idr', 'sell')
    
    logger.info('Put order to sell BTC to IDR at price %.10f' % (price_to_sell))
    trade_result = bitcoincoid_account.trade('btc_idr', 'sell', amount_to_sell, price_to_sell, 'btc')
    logger.debug(json.dumps(trade_result))

    while trade_result['success'] != 1:
        logger.info('Error putting order, retrying')
        time.sleep(1)
        trade_result = bitcoincoid_account.trade('btc_idr', 'sell', amount_to_sell, price_to_sell, 'btc')
        logger.debug(json.dumps(trade_result))

    order_id = trade_result['return']['order_id']
    order_info = bitcoincoid_account.getOrder(order_id, 'btc_idr')
    logger.debug(json.dumps(order_info))
    while order_info['return']['order']['status'] != 'filled':
        logger.info('Waiting for orders to be finalized, sleep %s seconds' % SLEEP_SECONDS)
        time.sleep(SLEEP_SECONDS) 
        wait_time_seconds += SLEEP_SECONDS
        order_info = bitcoincoid_account.getOrder(order_id, 'btc_idr')
        logger.debug(json.dumps(order_info))

        # its the latest step anyway, give it one minutes before correction to avoid taker
        if wait_time_seconds >= LAST_STEP_WAIT_TIME_SECONDS:
            order_info = corrective_action(pair='btc_idr', order_info=order_info)
            order_id = order_info['return']['order']['order_id']
            corrective_action_triggered = True
            wait_time_seconds = 0
    
    # logger.debug(bitcoincoid_account.getInfo())

# sometimes, order is not fulfilled due to market changes. If in (x) time it's not filled, do corrective action
# 1. cancel order
# 2. put new order with latest price
def corrective_action(pair, order_info):
    logger.info('Correcting %s ' % pair)
    order_id = order_info['return']['order']['order_id']
    transaction_type = order_info['return']['order']['type']

    # if the latest price same as our placed order, do nothing
    price = get_latest_price(pair, transaction_type)
    if price == float(order_info['return']['order']['price']):
        return order_info

    cancel_order = bitcoincoid_account.cancelOrder(order_id, pair, transaction_type)
    logger.debug(json.dumps(cancel_order))
    while cancel_order['success'] != 1:
        cancel_order = bitcoincoid_account.cancelOrder(order_id, pair, transaction_type)
        logger.debug(json.dumps(cancel_order))
        # assume it's already filled
        if cancel_order['success'] != 1:
            if 'invalid order' in cancel_order['error']:
                break
        time.sleep(1)
    
    # if somehow order is filled before its cancelled
    order_info = bitcoincoid_account.getOrder(order_id, pair)
    logger.debug(json.dumps(order_info))
    if order_info['return']['order']['status'] == 'filled':
        return order_info
    
    amount = float([value for key, value in order_info['return']['order'].items() if 'remain_' in key.lower()][0])
    
    curr_symbol = pair[-3:] if transaction_type == 'buy' else pair[:3]
    
    logger.info('Put order to %s %s at price %.10f, amount %.10f' % (transaction_type, curr_symbol, price, amount))

    trade_result = bitcoincoid_account.trade(pair, transaction_type, amount, price, curr_symbol)
    logger.debug(json.dumps(trade_result))
    while trade_result['success'] != 1:
        trade_result = bitcoincoid_account.trade(pair, transaction_type, amount, price, curr_symbol)
        logger.debug(json.dumps(trade_result))
        time.sleep(1)

    order_id = trade_result['return']['order_id']
    order_info = bitcoincoid_account.getOrder(order_id, pair)
    logger.debug(json.dumps(order_info))
    while order_info['success'] != 1:
        order_info = bitcoincoid_account.getOrder(order_id, pair)
        logger.debug(json.dumps(order_info))
        time.sleep(1)
    
    return order_info

def get_current_coin_amount(coin_symbol):
    account_info = bitcoincoid_account.getInfo()
    while account_info['success'] != 1:
        account_info = bitcoincoid_account.getInfo()
    return float(account_info['return']['balance'][coin_symbol])

def get_latest_price(pair, transaction_type):
    url = base_url + pair + '/depth'
    response = requests.get(url)
    while response.status_code != 200:
        response = requests.get(url)
        time.sleep(SLEEP_SECONDS)
    
    trade_list = response.json()
    highest_buy = float(trade_list['buy'][0][0])
    highest_sell = float(trade_list['sell'][0][0])
    
    if transaction_type == 'buy':
        return highest_sell
    elif transaction_type == 'sell' and pair[-3:] != 'btc' :
        # assume price in IDR
        highest_buy = float(trade_list['buy'][0][0]) + float(pip[pair])
        #if we avoid taker, keep it, if not, bye
        if float(trade_list['sell'][0][0]) == highest_buy:
            return float(trade_list['buy'][0][0])
        else:
            return highest_buy
    else:
        return highest_buy

market_depths = fetch_market_data()
max_profit = 0
max_profit_path = ''
highest_profit_percentage = -9999
highest_idr = 0
highest_path = ''
highest_target = 0
highest_partition = 0
profit_path = {}

for portion in range(MAX_PARTITION, 1, -1):
    amount_idr = (portion / MAX_PARTITION) * modal_duid
    calculate_idr_btc_alt_path(amount_idr)
    calculate_idr_alt_btc_path(amount_idr)
    # print(config_path)

    for path_name in config_path:
        if ((config_path[path_name]['final_idr']-amount_idr)/(amount_idr) > threshold):
            if max_profit < config_path[path_name]['final_idr']:
                max_profit = config_path[path_name]['final_idr']
                max_profit_path = path_name
            logger.info('Profit PATH %s : %s' % (path_name, config_path[path_name]['final_idr']))
            # profit_path.append(path_name)

    if max_profit_path == '':
        # calculate for debugging
        for path_name in config_path:
            if highest_profit_percentage < (float(config_path[path_name]['final_idr']/amount_idr) * 100):
                highest_profit_percentage = float(config_path[path_name]['final_idr']/amount_idr) * 100
                highest_idr = config_path[path_name]['final_idr']
                highest_path = path_name
                highest_partition = portion
                highest_target = amount_idr + (amount_idr * threshold)
    else:
        logger.info(config_path)
        if max_profit_path == 'IDR_BTC_ETH':
            path_idr_btc_alt('ETH/BTC', 'ETH/IDR', 'eth_btc', 'eth_idr', 'eth', 'IDR_BTC_ETH', amount_idr)
        elif max_profit_path == 'IDR_BTC_LTC':
            path_idr_btc_alt('LTC/BTC', 'LTC/IDR', 'ltc_btc', 'ltc_idr', 'ltc', 'IDR_BTC_LTC', amount_idr)
        elif max_profit_path == 'IDR_BTC_XLM':
            path_idr_btc_alt('XLM/BTC', 'XLM/IDR', 'str_btc', 'str_idr', 'str', 'IDR_BTC_XLM', amount_idr)
        elif max_profit_path == 'IDR_BTC_XRP':
            path_idr_btc_alt('XRP/BTC', 'XRP/IDR', 'xrp_btc', 'xrp_idr', 'xrp', 'IDR_BTC_XRP', amount_idr)
        elif max_profit_path == 'IDR_BTC_NXT':
            path_idr_btc_alt('NXT/BTC', 'NXT/IDR', 'nxt_btc', 'nxt_idr', 'nxt', 'IDR_BTC_NXT', amount_idr)
        elif max_profit_path == 'IDR_ETH_BTC':
            path_idr_alt_btc('ETH/BTC', 'ETH/IDR', 'eth_btc', 'eth_idr', 'eth', 'IDR_ETH_BTC', amount_idr)
        elif max_profit_path == 'IDR_LTC_BTC':
            path_idr_alt_btc('LTC/BTC', 'LTC/IDR', 'ltc_btc', 'ltc_idr', 'ltc', 'IDR_LTC_BTC', amount_idr)
        elif max_profit_path == 'IDR_XLM_BTC':
            path_idr_alt_btc('XLM/BTC', 'XLM/IDR', 'str_btc', 'str_idr', 'str', 'IDR_XLM_BTC', amount_idr)
        elif max_profit_path == 'IDR_XRP_BTC':
            path_idr_alt_btc('XRP/BTC', 'XRP/IDR', 'xrp_btc', 'xrp_idr', 'xrp', 'IDR_XRP_BTC', amount_idr)
        elif max_profit_path == 'IDR_NXT_BTC':
            path_idr_alt_btc('NXT/BTC', 'NXT/IDR', 'nxt_btc', 'nxt_idr', 'nxt', 'IDR_NXT_BTC', amount_idr)
        break

if max_profit_path == '':
    logger.info('Nothing to take profit')
    logger.info('Max path %s at partition %s percentage %s value %s target %s' % (highest_path, highest_partition, highest_profit_percentage, highest_idr, highest_target))

# TEST AREAS
# config_path['IDR_XLM_BTC']['step1_alt_buy_price'] = 900
# config_path['IDR_XLM_BTC']['step2_alt_sell_price'] = 0.00001
# config_path['IDR_XLM_BTC']['step3_btc_sell_price'] = 200000000
# path_idr_alt_btc('XLM/BTC', 'XLM/IDR', 'str_btc', 'str_idr', 'str', 'IDR_XLM_BTC')