from .cfsession import create_scraper
from urllib.parse import urlencode

import asyncio
import concurrent.futures
import hashlib
import hmac
import time
import numpy
from decimal import Decimal
from datetime import datetime

BASE_URL = 'https://vip.bitcoin.co.id'
PUBLIC_API_URL = '%s/api' % BASE_URL
PRIVATE_API_URL = '%s/tapi' % BASE_URL

requests = create_scraper()


async def _get_public_api(method, pairs, max_workers=20):
    def _build_url(pair):
        return '%s/%s/%s' % (PUBLIC_API_URL, pair, method)

    def _get(url, pair):
        resp = requests.get(url)

        if 399 < resp.status_code < 200:
            raise VipIoError('Error response from VIP',
                             status_code=resp.status_code,
                             payload=resp.text)

        body = resp.json()
        body['pair'] = pair

        return body

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop = asyncio.get_event_loop()
        futures = list(map(lambda x: loop.run_in_executor(executor,
                                                          _get,
                                                          _build_url(pair=x),
                                                          x), pairs))

        def _format_depth(depth_response):
            buy = depth_response.get('buy')
            sell = depth_response.get('sell')

            return {
                'highest_buy': buy[0][0],
                'highest_sell': sell[0][0],
                'buy': buy,
                'sell': sell,
                'pair': depth_response.get('pair')
            }

        if method == 'depth':
            responses = [_format_depth(response) for response in await asyncio.gather(*futures)]
        else:
            responses = []

        return responses


async def get_tickers(pairs, max_workers=20):
    if len(pairs) == 0:
        return []
    if max_workers <= 0:
        return []

    return await _get_public_api('ticker', pairs, max_workers)


async def get_depths(pairs, max_workers=20):
    if len(pairs) == 0:
        return []
    if max_workers <= 0:
        return []

    return await _get_public_api('depth', pairs, max_workers)


async def get_trades(pairs, max_workers=20):
    if len(pairs) == 0:
        return []
    if max_workers <= 0:
        return []

    return await _get_public_api('trades', pairs, max_workers)


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
    async def get_trades(cls, pairs, max_workers=20):
        return await get_trades(pairs, max_workers)

    @classmethod
    async def get_tickers(cls, pairs, max_workers=20):
        return await get_tickers(pairs, max_workers)

    @classmethod
    async def get_depths(cls, pairs, max_workers=20, as_numpy_array=False):
        result = await get_depths(pairs, max_workers)
        if as_numpy_array:
            result = numpy.array(result)

        return result

    def _sign(self, params):
        signature = hmac.new(self.api_secret.encode(),
                             params.encode(),
                             hashlib.sha512)
        return signature.hexdigest()

    def _send_command(self, command, params):
        params['method'] = command

        now = datetime.utcnow()
        params['nonce'] = int(time.mktime(now.timetuple()) * 1e3 + now.microsecond / 1e3) * 1000

        def _parse_value(val):
            if isinstance(val, Decimal):
                val = float(val)
                val = str(val) if val < 1 else '%d' % val

            return val

        params = {k: _parse_value(v) for (k, v) in params.items()}

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
                             payload={'params': params, 'response': response_body})

        result = response_body.get('return')
        if not result:
            raise VipIoError('[500] VIP Api returns an invalid response',
                             status_code=500,
                             payload={'params': params, 'response': response_body})

        return result

    def get_info(self):
        return self._send_command('getInfo', dict())

    def get_transaction_history(self):
        return self._send_command('transHistory', dict())

    def trade(self, pair, ttype, price, amount):
        params = {
            'pair': pair,
            'type': ttype,
            'price': price
        }
        pair = pair.split('_')

        if ttype == 'buy':
            params[pair[1]] = amount
        if ttype == 'sell':
            params[pair[0]] = amount

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
