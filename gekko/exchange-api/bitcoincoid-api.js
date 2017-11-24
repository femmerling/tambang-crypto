var querystring = require('querystring'),
VError = require('verror'),
crypto = require('crypto'),
url = require('url'),
request = require('request-promise');

var self;

var bitcoinCoId = function bitcoinCoId(settings)
{
    self = this;
    this.key = settings.key; 
    this.secret = settings.secret;
    this.url =  settings.url || "https://vip.bitcoin.co.id/api";
    this.tradeUrl = settings.tradeUrl || "https://vip.bitcoin.co.id/tapi/";
};


function makePublicRequest( path, args, callback)
{
    var functionName = 'bitcoinCoIdbitcoinCoId.makePublicRequest()';
    var options = {}
    options.url = url.parse(self.url+path);
    options.method = "GET";
    executeRequest(options, {}, callback);
};


function makePrivateRequest(method, args, callback)
{
    var functionName = 'bitcoinCoIdbitcoinCoId.makePrivateRequest()';
    var uri = self.tradeUrl;
    var nonce = (new Date()).getTime();

    args.nonce = nonce;

    if (!self.key || !self.secret)
    {
        return callback(new VError("%s must provide key and secret to make a private API request.", functionName));
    }

    postData = JSON.stringify(args);
    var content_data = querystring.stringify(args);

    var signature = crypto
    .createHmac('sha512', new Buffer(self.secret, 'utf8'))
    .update(new Buffer(content_data, 'utf8'))
    .digest('hex');

    var options = {}
    options.url = url.parse(self.tradeUrl);
    options.method = 'POST'
    options.headers = {
        'Key': self.key,
        'Sign': signature,
        'content-type': 'application/x-www-form-urlencoded',
        'content-length': content_data.length,
    }
    executeRequest(options, args, callback);
};

function executeRequest(options, content, callback){
    var functionName = 'bitcoincoid.executeRequest()';
    if (options.method == 'POST') {
        request.post(options, function(err, resp, body)
        { 
            body = JSON.parse(body);
            callback(err,resp,body);
        }).form(content)
    } else {
        request.get(options, function(err, resp, body)
        { 
            body = JSON.parse(body);
            callback(err,resp,body);
        })
    }
}


bitcoinCoId.prototype.getTicker = function(tickerSymbol, callback)
{
    makePublicRequest( "/"+tickerSymbol+"/ticker", {}, callback);
};

bitcoinCoId.prototype.getTrades = function(tickerSymbol, callback)
{
    makePublicRequest( "/"+tickerSymbol+"/trades", {}, callback);
};

bitcoinCoId.prototype.getDepth = function(tickerSymbol, callback)
{
    makePublicRequest( "/"+tickerSymbol+"/depth", {}, callback);
};


bitcoinCoId.prototype.getInfo = function(callback)
{
    makePrivateRequest("POST", {"method":"getInfo"}, callback);
};

bitcoinCoId.prototype.transHistory = function(callback)
{
    makePrivateRequest("POST", {"method":"transHistory"}, callback);
};

bitcoinCoId.prototype.tradeHistory = function(params, callback)
{
    params.method = "tradeHistory";
    makePrivateRequest("POST", params, callback);
};

bitcoinCoId.prototype.openOrders = function(params, callback)
{
    params.method = "openOrders";
    makePrivateRequest("POST", params, callback);
};

bitcoinCoId.prototype.trade = function(params, callback)
{
    params.method = "trade";
    makePrivateRequest("POST", params, callback);
};

bitcoinCoId.prototype.cancelOrder = function(params, callback)
{
    params.method = "cancelOrder";
    makePrivateRequest("POST", params, callback);
};

bitcoinCoId.prototype.getOrder = function(params, callback)
{
    params.method = "getOrder";
    makePrivateRequest("POST", params, callback);
};


module.exports = bitcoinCoId;