import Rx from 'rxjs/Rx'
import config from './env'
import { connectDb, getXlmIdrTicker, Ticker } from './commons'


const loop = Rx.Observable.of(config.tickerInterval)
  .do(() => {
    console.log(`Starting ticker collector with ${config.tickerInterval / 1000} seconds interval`)
  })
  .switchMap((interval) => {
    return Rx.Observable.interval(interval)
  })
  .switchMap(() => {
    return connectDb()
      .switchMap(() => getXlmIdrTicker())
      .switchMap((it) => {
        const ticker = new Ticker({
          high: parseInt(it.high, 10),
          low: parseInt(it.low, 10),
          last: parseInt(it.last, 10),
          buy: parseInt(it.buy, 10),
          sell: parseInt(it.sell, 10),
          volumeInCrypto: parseFloat(it.volStr),
          volumeInIdr: parseInt(it.volIdr, 10),
          serverTime: new Date(it.serverTime * 1000),
          pair: 'xlm_idr',
        })

        return Rx.Observable.fromPromise(ticker.save())
          .observeOn(Rx.Scheduler.asap)
          .map(() => `Last: ${ticker.last} - High: ${ticker.high} - Low: ${ticker.low}`)
      })
  })

loop.subscribe((x) => {
  return x instanceof Error ? console.log('Continuing to next tick..') :
    console.log(x)
})
