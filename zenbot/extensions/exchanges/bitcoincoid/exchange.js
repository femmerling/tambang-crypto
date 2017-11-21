//
// Warning - Some of the functions need testing
// by someone in posession of a BTCe account
// In particular this is the case for
// the buy, sell, cancelOrderand getOrderfunctions
//
var BitcoinCoId = require('./bitcoincoid.js')
  , path = require('path')
  , colors = require('colors')
  , numbro = require('numbro')

module.exports = function container (get, set, clear) {
  var c = get('conf')

  var public_client, authed_client

  function publicClient () {
    if (!public_client) {
      // public_client = new BitcoinCoId({})
      public_client = new BitcoinCoId({key: c.bitcoincoid.key, secret: c.bitcoincoid.secret})
    }
    return public_client
  }

  function authedClient () {
    if (!authed_client) {
      if (!c.bitcoincoid || !c.bitcoincoid.key || c.bitcoincoid.key === 'YOUR-API-KEY') {
        throw new Error('please configure your BTCe credentials in conf.js')
      }
      authed_client = new BitcoinCoId({key: c.bitcoincoid.key, secret: c.bitcoincoid.secret})
    }
    return authed_client
  }

  function joinProduct (product_id) {
    return product_id.split('-')[0] + '_' + product_id.split('-')[1]
  }

  function statusErr (err, body) {
    if (body === null) {
      return new Error(err)
    } else if (!body.success) {
      if (body.error === 'invalid api key' || body.error === 'invalid sign') {
        console.log(err)
        throw new Error('please correct your BitcoinCoId credentials in conf.js')
      } else if (err) {
        return new Error('\nError: ' + err)
      }
    } else {
      return body
    }
  }


  function retry (method, args, err) {
    if (method !== 'getTrades') {
      console.error(('\nBitcoinCoId API is down! unable to call ' + method + ', retrying in 10s').red)
      if (err) console.error(err)
      console.error(args.slice(0, -1))
    }
    setTimeout(function () {
      exchange[method].apply(exchange, args)
    }, 10000)
  }

  var orders = {}

  var exchange = {
    name: 'bitcoincoid',
    historyScan: 'false',
    makerFee: 0,
    takerFee: 0.3,

    getProducts: function () {
      return require('./products.json')
    },

    getTrades: function (opts, cb) {
      var func_args = [].slice.call(arguments)
      var client = publicClient()
      var pair = joinProduct(opts.product_id).toLowerCase()
      var args = {}
      if (opts.from) {
        // move cursor into the future
        args.before = opts.from
      }
      else if (opts.to) {
        // move cursor into the past
        args.after = opts.to
      }
      client.getTrades(pair, function (err, body) {
        if (err) return retry('getTrades', func_args, err)
        var trades = body.map(function (trade) {
          return {
            trade_id: trade.tid,
            time: trade.date * 1000,
            //time: new Date(trade.date).getTime(),
            size: trade.amount,
            price: trade.price,
            side: trade.type
          }
        })
        cb(null, trades)
      })
    },

    getBalance: function (opts, cb) {
      var args = {
        currency: opts.currency.toLowerCase(),
        asset: opts.asset.toLowerCase(),
        wait: 10
      }
      var func_args = [].slice.call(arguments)
      var client = authedClient()
      client.getInfo(function (err, body) {
        // console.log("error:")
        // console.log(err)
        // console.log("body:")
        // console.log(body)
        body = statusErr(err, body)
        if (err) {
          return retry('getBalance', func_args, err)
        }
        if (body.success) {
          var balance = {asset: 0, currency: 0}
          var funds = body.return.balance
          balance.currency = funds[args.currency]
          balance.asset = funds[args.asset]
          balance.currency_hold = 0
          balance.asset_hold = 0
          cb(null, balance)
        } else {
        }
      })
    },

    getQuote: function (opts, cb) {
      var func_args = [].slice.call(arguments)
      var client = publicClient()
      var pair = joinProduct(opts.product_id).toLowerCase()
      client.getTicker(pair, function (err, body) {
        if (err) return retry('getQuote', func_args, err)
        cb(null, { bid: body.ticker.buy, ask: body.ticker.sell })
      })
    },

    cancelOrder: function (opts, cb) {
      var func_args = [].slice.call(arguments)
      var client = authedClient()
      var params = {
        order_id: opts.order_id,
        type: opts.type,
        pair: joinProduct(opts.product_id).toLowerCase()
      }

      client.cancelOrder(params, function (err, resp, body) {
        body = statusErr(err, body)
        // Fix me - Check return codes
        if (body && (body.message === 'invalid order.' || body.message === 'order not found')) return cb()
        if (err) return retry('cancelOrder', func_args, err)
        cb()
      })
    },

    trade: function (type, opts, cb) {
      var func_args = [].slice.call(arguments)
      var client = authed_client()
      var pair = joinProduct(opts.product_id).toLowerCase()
      /* BTCe has no order type?
      if (typeof opts.post_only === 'undefined') {
        opts.post_only = true
      }
      if (opts.order_type === 'taker') {
        delete opts.price
        delete opts.post_only
        opts.type = 'market'
      }
      */
      delete opts.order_type
      delete opts.cancel_after

      var params = {
        pair: pair,
        type: type,
        price: opts.price
      }

      if (opts.type === 'buy') {
        params[opts.product_id.split('-')[1].toLowerCase()] = opts.size
      } else {
        params[opts.product_id.split('-')[0].toLowerCase()] = opts.size
      }
      
      
      client.trade(params, function(err, body) {
        body = statusErr(err, body)
        // Fix me - Check return codes from API
        if (body && body.message === 'Insufficient balance.') {
          var order = {
            status: 'rejected',
            reject_reason: 'balance'
          }
          return cb(null, order)
        }
        if (err) return retry(type, func_args, err)
        orders['~' + body.return.order.order_id] = body
        cb(null,body)
        //else console.log(err)
      })
    },

    buy: function (opts, cb) {
      exchange.trade('buy', opts, cb)
    },

    sell: function (opts, cb) {
      exchange.trade('sell', opts, cb)
    },

    getOrder: function (opts, cb) {
      var func_args = [].slice.call(arguments)
      var client = authedClient()
      // Fix me - Check return result
      var params = {
        order_id: opts.order_id,
        pair: joinProduct(opts.product_id).toLowerCase()
      }
      client.getOrder(params, function (err, resp, body){
        body = statusErr(err, body)
        if (err) return retry('getOrder', func_args, err)
        
        var keys = Object.keys(body.return.order)
        keys.forEach(function(key) {
          if (key.substring(0, 6) === 'remain') {
            body.remaining_size = body.return.order[key]
          }
        })

        if (body.return.order.status === 'filled') {
          // order was cancelled. recall from cache
          body = orders['~' + opts.order_id]
          body.status = 'done'
          body.done_reason = 'filled'
        } else {
          body.filled_size = 0
        }
        cb(null, body)
      })
    },

    // return the property used for range querying.
    getCursor: function (trade) {
      return trade.trade_id
    }
  }
  return exchange
}
