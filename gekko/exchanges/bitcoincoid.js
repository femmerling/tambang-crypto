var BitcoinCoId = require('../exchange-api/bitcoincoid-api.js');
var util = require('../core/util.js');
var _ = require('lodash');
var moment = require('moment');
var log = require('../core/log');

var Trader = function(config) {
    _.bindAll(this);
    if(_.isObject(config)) {
      this.key = config.key;
      this.secret = config.secret;
    }
    this.name = 'bitcoincoid';
    this.pair = [config.asset, config.currency].join('_').toLowerCase();
    this.bitcoincoid = new BitcoinCoId({key: this.key, secret: this.secret});
}

// if the exchange errors we try the same call again after
// waiting 10 seconds
Trader.prototype.retry = function(method, args) {
    var wait = +moment.duration(10, 'seconds');
    log.debug(this.name, 'returned an error, retrying..');

    var self = this;

    // make sure the callback (and any other fn)
    // is bound to Trader
    _.each(args, function(arg, i) {
        if(_.isFunction(arg))
            args[i] = _.bind(arg, self);
    });

    // run the failed method again with the same
    // arguments after wait
    setTimeout(
        function() { method.apply(self, args) },
        wait
    );
}

Trader.prototype.getPortfolio = function(callback) {
    var process = function(err, response, data) {

        if(_.has(data, 'error')) {
            if(data.error === 'Invalid credentials. API not found or session has expired.')
                util.die('Bitcoincoid said: ' + data.error);

            return callback(data.error, []);
        }

        var portofolio = []
        var balance_dict = data.return.balance
        for (var curr_symbol in balance_dict){
            var balance = {}
            balance.name = curr_symbol.toUpperCase();
            balance.amount = parseFloat(balance_dict[curr_symbol]);
            portfolio.push(balance)
        }

        callback(err, portfolio);
    };

    this.bitcoincoid.getInfo(process);
}


Trader.prototype.getTicker = function(callback) {
    var args = _.toArray(arguments);
    var process = function(err, response, data) {
        if(err) {
            log.error('Error getTicker()', err)
            return this.retry(this.getTicker, args);
        }
        callback(err, {bid: +data.ticker.buy, ask: +data.ticker.sell})
    };

    this.bitcoincoid.getTicker(this.pair, process);

}


Trader.prototype.getFee = function(callback) {
    const fee = 0.003;

    callback(false, fee);
}


Trader.prototype.buy = function(amount, price, callback) {

}

Trader.prototype.sell = function(amount, price, callback) {
    
}

Trader.prototype.getOrder = function(order, callback) {
    
}

Trader.prototype.checkOrder = function(order, callback) {
    
}

Trader.prototype.cancelOrder = function(order, callback) {
    
}


// bitcoin.co.id doesn't support historical data
Trader.prototype.getTrades = function(since, callback, descending) {
    log.debug('getTrades called!')

    var args = _.toArray(arguments);
    var process = function(err, response, data) {
        if(err) {
            log.error('Error getTrades()', err)
            return this.retry(this.getTrades, args);
        }
        var result = _.map(data, function(trade) {
            return {
                tid: trade.tid,
                amount: parseFloat(trade.amount),
                date: trade.date,
                price: parseFloat(trade.price),
                type: trade.type
            };
        });
        callback(null, result.reverse())
    }

    this.bitcoincoid.getTrades(this.pair, process);

}


Trader.getCapabilities = function () {
    return {
        name: 'BitcoinCoId',
        slug: 'bitcoincoid',
        currencies: ['IDR'],
        assets: ['BTC', 'BCH', 'ETH', 'BTG', 'ETC', 'LTC', 'WAVES', 'XLM', 'XRP', 'XZC'],
        tradable: true,
        forceReorderDelay: true,
        providesHistory: false,
        maxHistoryFetch: null,
        markets: [
            { pair: ['IDR', 'BTC'], minimalOrder: { amount: 10000, unit: 'currency' } },
            { pair: ['IDR', 'BCH'], minimalOrder: { amount: 10000, unit: 'currency' } },
            { pair: ['IDR', 'ETH'], minimalOrder: { amount: 10000, unit: 'currency' } },
            { pair: ['IDR', 'BTG'], minimalOrder: { amount: 10000, unit: 'currency' } },
            { pair: ['IDR', 'ETC'], minimalOrder: { amount: 10000, unit: 'currency' } },
            { pair: ['IDR', 'LTC'], minimalOrder: { amount: 10000, unit: 'currency' } },
            { pair: ['IDR', 'WAVES'], minimalOrder: { amount: 10000, unit: 'currency' } },
            { pair: ['IDR', 'XLM'], minimalOrder: { amount: 10000, unit: 'currency' } },
            { pair: ['IDR', 'XRP'], minimalOrder: { amount: 10000, unit: 'currency' } },
            { pair: ['IDR', 'XZC'], minimalOrder: { amount: 10000, unit: 'currency' } },
        ],
        requires: ['key', 'secret'],
        fetchTimespan: 2,
        tid: 'tid'
    };
}

  
module.exports = Trader;