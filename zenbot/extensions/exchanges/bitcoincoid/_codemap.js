module.exports = {
  _ns: 'zenbot',

  'exchanges.bitcoincoid': require('./exchange'),
  'exchanges.list[]': '#exchanges.bitcoincoid'
}
