from requests.auth import AuthBase
from urllib.parse import urlencode
import hashlib
import hmac
import time

from . import common

class vipAuth(AuthBase):
    def __init__(self, key, sign):
        # setup any auth-related data here
        self.key = key
        self.sign = sign
    def __call__(self, r):
        # modify and return the request
        r.headers['Key'] = self.key
        r.headers['Sign'] = self.sign
        return r

def nonce():
    # time.sleep(1)
    return str(round(time.time() * 1000))

def signature(secret, params):
    sig = hmac.new(secret.encode(), params.encode(), hashlib.sha512)
    return sig.hexdigest()


class TradeAPI:  
    def __init__(self, key, secret, requests_session=None):
        self.__key = key
        self.__secret = secret

        if requests_session is not None:
            self.__requests_session = requests_session
        else:
            self.__requests_session = common.Session()

    def __post(self, method, params):        
        url = 'https://vip.bitcoin.co.id/tapi'
        params['method'] = method
        params['nonce'] = nonce()
        auth = vipAuth(self.__key, signature(self.__secret, urlencode(params))) 
        response = self.__requests_session.api_request(url, params, auth, 'post')
        
        return response.json()

    def getInfo(self):
        return self.__post('getInfo', {})

    def transHistory(self):
        return self.__post('transHistory', {})

    def trade(self, pair, ttype, amount, price, base):
        params = {
            "pair" : pair, #btc_idr, stc_idr
            "type" : ttype, #buy / sell
            "price" : price #price
        } 
        params[base] = amount #idr, btc, etch etc
        return self.__post('trade', params)

    def tradeHistory(self, **kwargs):
        '''Arguments : count, from_id, end_id, order, since, end'''
        params = {"pair" : 'btc_idr'}
        if kwargs:
            for key, value in kwargs.items():
                params[key] = value
        return self.__post('tradeHistory', params)

    def openOrders(self):
        # params = { "pair" : 'btc_idr' }
        params = {}
        return self.__post('openOrders', params)
        # return self.__post('openOrders')

    def cancelOrder(self, order_id, pair, ttype):
        params = {
            'pair' : pair,
            'order_id' : order_id,
            'type' : ttype}
        return self.__post('cancelOrder', params)
    
    def getOrder(self, order_id, pair):
        params = {
            'pair': pair,
            'order_id': order_id
        }
        return self.__post('getOrder', params)

    def withdrawCoin(self, currency, withdraw_address, withdraw_amount, request_id, withdraw_memo):
        params = {
            'currency': currency,
            'withdraw_address': withdraw_address,
            'withdraw_amount': withdraw_amount,
            'withdraw_memo': withdraw_memo,
            'request_id': request_id
        }
        return self.__post('withdrawCoin', params)