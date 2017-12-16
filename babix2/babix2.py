import asyncio
import logging
import sys
import time
import json
from decimal import Decimal, getcontext as dec_context, ROUND_DOWN

from functional import seq, pseq

from vipio import VipIo, VipIoError

PAIRS = {
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
MODAL_DUID = Decimal('300000')
THRESHOLD = Decimal('0.001')
FEES = Decimal('0.003') * 3
# FEES = Decimal('0.0')
VIP_API_KEY = 'YFXLG0HC-ENZV1VGS-KV6RRQQZ-AEQJB9IU-HRJOKJQU'
VIP_API_SECRET = 'c680b1d3f6c6d8571bf682f7c9b21b250757034cf97bf0641719089737e046dd23c8f0c45d163ef0'
CHECK_ORDER_DURATION = 1.0
CHECK_ORDER_RETRIES = 30
PIP = Decimal('1000')

dec_context().prec = 8
dec_context().rounding = ROUND_DOWN

logger = logging.getLogger("babix.ngepetz")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logfile_handler = logging.StreamHandler(stream=sys.stdout)
logfile_handler.setFormatter(formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(logfile_handler)


def get_margins(market_data):
    idr_btc = market_data.get('btc_idr').get('highest_sell')
    btc_bought_from_idr = MODAL_DUID / idr_btc

    btc_alts = (seq(PAIRS.values())
        .filter(lambda x: x.endswith('_btc'))
        .map(lambda x: {x.split('_')[0]: btc_bought_from_idr / market_data.get(x).get('highest_buy')})
    )
    btc_alts = {k: v for d in btc_alts for k, v in d.items()}
    logger.debug('BTC to ALTS: %s' % btc_alts )

    alts_idr = (seq(PAIRS.values())
        .filter(lambda x: x.endswith('_idr'))
        .filter(lambda x: x != 'btc_idr')
        .map(lambda x: {x.split('_')[0]: btc_alts[x.split('_')[0]] * market_data.get(x).get('highest_sell')})
    )
    alts_idr = {k: v for d in alts_idr for k, v in d.items()}
    logger.debug('ALTS to IDR: %s' % alts_idr)

    margins = (seq(PAIRS.values())
        .filter(lambda x: x.endswith('_btc'))
        .map(lambda x: x.split('_')[0])
        .map(lambda x: {x: (alts_idr[x] / MODAL_DUID - 1)})
        .filter(lambda x: list(x.values())[0] >= (THRESHOLD + FEES))
    )
    margins = {k: v for d in margins for k, v in d.items()}
    logger.debug('Margins: %s' % margins)

    return margins


def log_config():
    logger.info('Modal Duid: IDR %d' % MODAL_DUID)
    logger.info('Fees: %.3f' % FEES)
    logger.info('Threshold: %.3f' % THRESHOLD)
    logger.info('Check order duration: %d second(s)' % CHECK_ORDER_DURATION)
    logger.info('Check order retries: %d' % CHECK_ORDER_RETRIES)


async def is_trade_executed(vip, order_id, pair):
    order = vip.get_order(order_id=order_id,
                          pair=pair)

    return order.get('order').get('status') == 'filled'


async def trade(market_data, margins):
    vip = VipIo(api_key=VIP_API_KEY,
                api_secret=VIP_API_SECRET)

    idr_btc = market_data.get('btc_idr').get('highest_sell')
    btc_bought_from_idr = MODAL_DUID / idr_btc

    logger.info('Buying BTC from IDR - Expecting to get %.8f BTC' % btc_bought_from_idr)

    btc = vip.trade(pair='btc_idr',
                    ttype='buy',
                    price=idr_btc,
                    amount=MODAL_DUID)

    logger.info('Order made for %.8f BTC with order id %s' % (btc_bought_from_idr, btc.get('order_id')))

    check_order_counter = 1
    while not await is_trade_executed(vip=vip,
                                      order_id=btc.get('order_id'),
                                      pair='btc_idr'):
        logger.info('Checking order id %s' % btc.get('order_id'))
        check_order_counter += 1

        if check_order_counter <= CHECK_ORDER_RETRIES:
            time.sleep(CHECK_ORDER_DURATION)
            continue

        logger.info('Check order retries expired, canceling buying BTC from IDR')
        vip.cancel_order(order_id=btc.get('order_id'),
                         pair='btc_idr',
                         ttype='buy')
        logger.info('Order id %s is canceled, bailing this tick' % btc.get('order_id'))
        return

    logger.info('Order id %s is filled' % btc.get('order_id'))

    for alt_path in margins.keys():
        pair = '%s_btc' % alt_path

        alt_bought_from_btc = btc_bought_from_idr / market_data.get(pair).get('highest_sell')

        logger.info('Walking path %s, making trade with %.8f %s' % (pair, alt_bought_from_btc, alt_path.upper()))
        alt_price = str(market_data.get(pair).get('highest_sell'))
        logger.info('%s price now at %s BTC' % (alt_path.upper(), alt_price))
        alt = vip.trade(pair=pair,
                        ttype='buy',
                        price=alt_price,
                        amount=btc_bought_from_idr)

        check_order_counter = 1
        while not await is_trade_executed(vip=vip,
                                          order_id=alt.get('order_id'),
                                          pair=pair):
            logger.info('Checking order id %s' % alt.get('order_id'))
            check_order_counter += 1

            if check_order_counter <= CHECK_ORDER_RETRIES:
                time.sleep(CHECK_ORDER_DURATION)
                continue

            logger.info('Check order retries expired, canceling buying %s from BTC' % alt_path.upper())
            vip.cancel_order(order_id=alt.get('order_id'),
                             pair=pair,
                             ttype='buy')
            logger.info('Order id %s is canceled, bailing this tick' % alt.get('order_id'))

        logger.info('Going to sell %s to IDR' % alt_path.upper())

        idr = vip.trade(pair='%s_idr' % alt_path,
                        ttype='sell',
                        price=market_data.get(pair).get('highest_sell'),
                        amount=alt_bought_from_btc)

        check_order_counter = 1
        while not await is_trade_executed(vip=vip,
                                          order_id=idr.get('order_id'),
                                          pair=pair):
            logger.info('Checking order id %s' % idr.get('order_id'))
            check_order_counter += 1

            if check_order_counter <= CHECK_ORDER_RETRIES:
                time.sleep(CHECK_ORDER_DURATION)
                continue

            logger.info('Check order retries expired, canceling buying IDR from %s' % alt_path.upper())
            vip.cancel_order(order_id=alt.get('order_id'),
                             pair='%s_idr' % alt_path,
                             ttype='sell')
            logger.info('Order id %s is canceled, bailing this tick' % idr.get('order_id'))

        break


async def main():
    log_config()

    market_data = await VipIo.get_depths(pairs=PAIRS.values(),
                                         max_workers=len(PAIRS.keys()),
                                         as_numpy_array=True)

    market_data = (seq(market_data)
        .map(lambda x: dict(pair=x.get('pair'),
                            highest_buy=Decimal(x.get('highest_buy')),
                            highest_sell=Decimal(x.get('highest_sell')),
                            highest_buy_volume=Decimal(x.get('buy')[0][1]),
                            highest_sell_volume=Decimal(x.get('sell')[0][1]),
                            buy_volume=seq(x.get('buy')).map(lambda y: Decimal(y[0])).sum(),
                            sell_volume=seq(x.get('sell')).map(lambda y: Decimal(y[0])).sum()
        ))
        .map(lambda x: {x.get('pair'): x})
    )
    market_data = {k: v for d in market_data for k, v in d.items()}

    margins = get_margins(market_data=market_data)
    if len(margins.keys()) == 0:
        logger.info('No margins to play with, bailing this tick')
        return

    try:
        await trade(market_data=market_data,
                    margins=margins)
    except VipIoError as e:
        logger.critical('Failed executing trade, bailing this tick')
        logger.critical(json.dumps(e.payload))


if __name__ == '__main__':
    logger.info('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    logger.info('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
