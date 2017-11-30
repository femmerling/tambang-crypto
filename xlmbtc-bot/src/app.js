import request from 'request-promise-native'
import qs from 'querystring'
import crypto from 'crypto'
import Rx from 'rxjs/Rx'
import config from './env'

const vipTapiMethods = {
  GET_INFO: 'getInfo',
  OPEN_ORDERS: 'openOrders',
}

const pairs = {
  XLM_IDR: 'str_idr',
  XLM_BTC: 'str_btc',
}

const vipSignRequest = (postBody) => {
  return crypto.createHmac('sha512', config.vipApiSecret).update(qs.stringify(postBody)).digest('hex')
}

const sendVipTapiCommand = (method, params) => {
  const url = `${config.vipUrl}/tapi`
  const postBody = params === undefined ? {
    method,
    nonce: new Date().getTime(),
  } : {
    method,
    ...params,
    nonce: new Date().getTime(),
  }
  const headers = {
    Key: config.vipApiKey,
    Sign: vipSignRequest(postBody),
  }
  const reqOpts = {
    url,
    headers,
  }

  return Rx.Observable.fromPromise(request.post(reqOpts).form(postBody).promise())
    .observeOn(Rx.Scheduler.asap)
    .map(x => JSON.parse(x))
    .switchMap((response) => {
      return response.success === 1 ?
        Rx.Observable.of(response.return) : Rx.Observable.empty()
    })
}

const getXlmIdrTicker = () => {
  const url = `${config.vipUrl}/api/str_idr/ticker`
  return Rx.Observable.fromPromise(request.get(url).promise())
    .observeOn(Rx.Scheduler.asap)
    .map(x => JSON.parse(x))
    .map(x => x.ticker)
    .map((x) => {
      return {
        high: parseInt(x.high, 10),
        low: parseInt(x.low, 10),
        volStr: parseFloat(x.vol_str),
        volIdr: parseFloat(x.vol_idr),
        last: parseInt(x.last, 10),
        buy: parseInt(x.buy, 10),
        sell: parseInt(x.sell, 10),
        serverTime: parseInt(x.server_time, 10),
      }
    })
}

const loop = Rx.Observable.interval(config.interval)
  // Get XLM/IDR Price
  .switchMap(() => {
    return getXlmIdrTicker()
  })
  .switchMap((ticker) => {
    const xlmIdrOrders = sendVipTapiCommand(vipTapiMethods.OPEN_ORDERS, { pair: pairs.XLM_IDR })
    const xlmBtcOrders = sendVipTapiCommand(vipTapiMethods.OPEN_ORDERS, { pair: pairs.XLM_BTC })
    return Rx.Observable.zip(Rx.Observable.of(ticker), xlmIdrOrders, xlmBtcOrders)
  })
  .catch(err => console.log(err))

loop.subscribe(x => console.log(x))
