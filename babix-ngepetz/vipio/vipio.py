from .cfsession import create_scraper, AuthBase
from urllib.parse import urlencode

import asyncio
import concurrent.futures
import hashlib
import hmac
import time

BASE_URL = 'https://vip.bitcoin.co.id'
PUBLIC_API_URL = '%s/api' % BASE_URL
PRIVATE_API_URL = '%s/tapi' % BASE_URL

requests = create_scraper()


async def _get_public_api(method, pairs=[], max_workers=20):
    def _build_url(pair):
        return '%s/%s/%s' % (PUBLIC_API_URL, pair, method)

    def _get(url):
        time.sleep(0.05)
        return requests.get(url)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop = asyncio.get_event_loop()
        futures = list(map(lambda x: loop.run_in_executor(executor,
                                                          _get,
                                                          _build_url(pair=x)), pairs))

        def _format_depth(depth_response):
            response = depth_response.json()

            buy = response.get('buy')
            sell = response.get('sell')

            return {
                'highest_buy': buy[0][0],
                'highest_sell': sell[0][0],
                'buy': buy,
                'sell': sell
            }

        responses = [_format_depth(response) for response in await asyncio.gather(*futures)]
        results = {}

        for index in range(0, len(pairs) - 1):
            results[pairs[index]] = responses[index]

        return results


def get_tickers(pairs, max_workers=20):
    if not isinstance(pairs, list) or len(pairs) == 0:
        return []
    if max_workers <= 0:
        return []

    loop = asyncio.get_event_loop()

    responses = loop.run_until_complete(_get_public_api('ticker', pairs, max_workers))

    return responses


def get_depths(pairs, max_workers=20):
    if not isinstance(pairs, list) or len(pairs) == 0:
        return []
    if max_workers <= 0:
        return []

    loop = asyncio.get_event_loop()

    responses = loop.run_until_complete(_get_public_api('depth', pairs, max_workers))

    return responses


def get_trades(pairs, max_workers=20):
    if not isinstance(pairs, list) or len(pairs) == 0:
        return []
    if max_workers <= 0:
        return []

    loop = asyncio.get_event_loop()

    responses = loop.run_until_complete(_get_public_api('trades', pairs, max_workers))

    return responses


class VipIoError(Exception):
    def __init__(self, message, status_code=500, payload=None):
        Exception.__init__(self)

        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message

        return rv


class VipIo(object):
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    @classmethod
    def get_trades(cls, pairs, max_workers=20):
        return get_trades(pairs, max_workers)

    @classmethod
    def get_tickers(cls, pairs, max_workers=20):
        return get_tickers(pairs, max_workers)

    @classmethod
    def get_depths(cls, pairs, max_workers=20):
        return get_depths(pairs, max_workers)

    def _sign(self, params):
        signature = hmac.new(self.api_secret.encode(),
                             params.encode(),
                             hashlib.sha512)
        return signature.hexdigest()

    def _send_command(self, command, params):
        params['method'] = command
        params['nonce'] = int(time.time()) * 1000

        headers = {
            'Key': self.api_key,
            'Sign': self._sign(urlencode(params))
        }

        response = requests.post(url=PRIVATE_API_URL,
                                 data=params,
                                 headers=headers)

        if 200 > response.status_code > 399:
            raise VipIoError('[%d] Got a non successful response from VIP Api' % response.status_code,
                             status_code=response.status_code,
                             payload=response.json())

        response_body = response.json()
        success = int(response_body.get('success'))
        if success == 0:
            raise VipIoError('[400] VIP Api says the request is not a success because of you',
                             status_code=400,
                             payload=response_body)

        result = response_body.get('return')
        if not result:
            raise VipIoError('[500] VIP Api returns an invalid response',
                             status_code=500,
                             payload=result)

        return result

    def get_info(self):
        return self._send_command('getInfo', dict())

    def get_transaction_history(self):
        return self._send_command('transHistory', dict())

    def trade(self, pair, ttype, price, idr, btc):
        if ttype == 'buy' and not idr:
            raise VipIoError('[400] The idr param is required when buying',
                             status_code=400)
        if ttype == 'sell' and not btc:
            raise VipIoError('[400] The btc param is required when selling',
                             status_code=400)

        params = {
            'pair': pair,
            'type': ttype,
            'price': price
        }

        if ttype == 'buy':
            params['idr'] = idr
        if ttype == 'sell':
            params['btc'] = btc

        return self._send_command('trade', params)

    def get_open_orders(self, pair):
        params = {
            'pair': pair
        }

        return self._send_command('openOrders', params)

    def get_order(self, order_id, pair):
        params = {
            'order_id': order_id,
            'pair': pair
        }

        return self._send_command('getOrder', params)

    def cancel_order(self, order_id, pair, ttype):
        params = {
            'order_id': order_id,
            'pair': pair,
            'type': ttype
        }

        return self._send_command('cancelOrder', params)


if __name__ == '__main__':
    tickers = VipIo.get_tickers(['str_idr', 'btc_idr'], 20)
    print(tickers)

    depths = VipIo.get_depths(['str_idr', 'btc_idr'], 20)
    print(depths)

    trades = VipIo.get_trades(['str_idr', 'btc_idr'], 20)
    print(trades)
