const {app, Tray, Menu, BrowserWindow, nativeImage} = require('electron')
const path = require('path')
const request = require('request')
const prettydate = require('pretty-date')

let window = undefined
let tray = undefined

const iconPath = path.join(__dirname, 'btcTemplate.png');
const icon = nativeImage.createFromPath(iconPath)
const appIconPath = path.join(__dirname, 'appIcon.png');

const ONE_MINUTE_IN_MILLIS = 60 * 1000
const FIVE_SECONDS_IN_MILLIS = 5 * 1000

app.dock.hide()

app.on('ready', () => {
  win = new BrowserWindow({
    show: false,
    icon: appIconPath
  })
  win.title = 'Bitcoin.co.id Ticker'

  tray = new Tray(icon)
  tray.setTitle('Bitcoin.co.id Ticker')

  tick()
  setInterval(tick, ONE_MINUTE_IN_MILLIS)
})

const toCurrency = (text) => {
  text = parseInt(text)
  text = text.toLocaleString('ID-id')

  return `Rp. ${text}`
}

const fillContextMenu = (high, low, last, btc_vol, idr_vol, buy, sell, timestamp) => {
  high = toCurrency(high)
  low = toCurrency(low)
  last = toCurrency(last)
  buy = toCurrency(buy)
  sell = toCurrency(sell)
  idr_vol = toCurrency(idr_vol)

  let date = new Date(timestamp * 1000)
  date = prettydate.format(date)

  const contextMenu = Menu.buildFromTemplate([
    {label: `High: ${high}`},
    {label: `Low: ${low}`},
    {label: `Last: ${last}`},
    {label: `Buy: ${buy}`},
    {label: `Sell: ${sell}`},
    {label: `Low: ${low}`},
    {label: `BTC Vol: ${btc_vol} BTC`},
    {label: `IDR Vol: Rp. ${idr_vol}`},
    {type: 'separator'},
    {role: 'quit'}
  ])

  tray.setContextMenu(contextMenu)
}

const tick = () => {
  const url = 'https://vip.bitcoin.co.id/api/btc_idr/ticker'

  console.log('Getting BTC_IDR last')

  request(url, {json: true}, (err, res, body) => {
    if(err) {
      console.log('Error requesting ticker')
      console.log(err)
    }

    console.log(body.ticker)

    const last = toCurrency(body.ticker.last)

    tray.setTitle(last)
    fillContextMenu(body.ticker.high, body.ticker.low, body.ticker.last, body.ticker.vol_btc, 
      body.ticker.vol_idr, body.ticker.buy, body.ticker.sell, body.ticker.server_time)
  })
}

