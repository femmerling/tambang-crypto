# Bitcoin.co.id Ticker

This is an electron app to tick Bitcoin.co.id public data to the menubar.

## Installing & Running

```
$ npm i
$ npm i -g electron electron-packager # if you haven't already
$ electron .
```

## Packaging

```
$ electron-packager . "Bitcoin.co.id Ticker" --electron-version 1.7.9 --platform=darwin --arch=x64 --overwrite --prune=true
```
