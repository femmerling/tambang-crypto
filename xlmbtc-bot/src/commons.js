import request from 'request-promise-native'
import Rx from 'rxjs/Rx'
import config from './env'
import mongoose from 'mongoose'

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

const getXlmIdrTrades = () => {
  const url = `${config.vipUrl}/api/str_idr/trades`
  return Rx.Observable.fromPromise(request.get(url).promise())
    .observeOn(Rx.Scheduler.asap)
    .map(x => JSON.parse(x))
}

const Ticker = mongoose.model('Ticker', {
  high: Number,
  low: Number,
  last: Number,
  buy: Number,
  sell: Number,
  volumeInCrypto: Number,
  volumeInIdr: Number,
  serverTime: Date,
  pair: String,
})

const connectDb = () => {
  mongoose.Promise = global.Promise

  const connConfig = {
    connString: `mongodb://${config.mongoHost}:${config.mongoPort}/${config.mongoDb}`,
    connOpts: {
      useMongoClient: true,
    },
  }

  return Rx.Observable.fromPromise(mongoose.connect(connConfig.connString, connConfig.connOpts))
    .retryWhen((err) => {
      // Retry not more than 3 times
      return err
        .scan((count, currentErr) => {
          if (count > 3) {
            throw new Error('Giving up trying to reconnect to database')
          }

          return count + 1
        }, 1)
        .do(() => {
          console.log('Retrying connection to database')
        })
    })
}

export { getXlmIdrTicker, getXlmIdrTrades, connectDb, Ticker }
