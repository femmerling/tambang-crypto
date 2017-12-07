# babix-ngepetz

Stupid scalping bot. Use at your own risk.
Coded without clean-code in mind, many global vars and mutable. Not modularized. Be careful.

Help needed to make it modular and readable.

Bitcoin API Limitation:
- 20-30 req/minute for public API
- 180 req/minute for private API (trade API)

What it does:
- Find small profit chance (scalping) by exploiting bitcoin.co.id market fee
- Current market fee was 0.3% per IDR transaction, but 0.00% per ALT/BTC transaction
- There is two pathfinder, IDR to BTC to ALT to IDR (buy BTC, buy ALT using BTC, sell ALT to IDR) and IDR to ALT to BTC to IDR (buy ALTCOIN, buy BTC using ALT, sell BTC to IDR)
- Find best profit path using partition window (foreach 100% of predefined amount towards 1% of predefined amount )
- Do corrective action if transaction was not successfull (as market price might be changed in matter of seconds). If this case, it might generate losses, but hopefully not that bad.
- Write logs to `ngepetz.log`


What to setup:
Modify babix.py
- modal_duid : base IDR amount that you want to trade
- threshold : profit threshold before execute trade (default 0.005, which is 0.5 percent)
- API_KEY
- API_SECRET
- SLEEP_SECONDS
- MAX_WAIT_TIME_SECONDS
- LAST_STEP_WAIT_TIME_SECONDS
- proxy (if used)
- MAX_PARTITION
- and other parts (you can limit the number of monitored pairs, but dont forget to change in `calculate_idr_btc_alt_path` and `calculate_idr_alt_btc_path`)

How to run:
- Download python3
- pip3 install -r requirements.txt
- python3 babix.py

You can run it on the background, using something like `run.sh`
```
#!/bin/bash
while true; do SECONDS=0; python3.6 babix.py; sleep $((RANDOM%10+20-$SECONDS)); done
```


# DOCKERIZE

ENV_VAR:
    API_KEY : API_KEY
    API_SECRET : API_SECRET
    SLEEP_SECONDS : 5
    MAX_WAIT_TIME_SECONDS : 30
    LAST_STEP_WAIT_TIME_SECONDS : 30
    BASE_URL : https://vip.bitcoin.co.id/api/
    PRIVATE_URL : https://vip.bitcoin.co.id/tapi/
    MODAL_DUID : 15000000
    FEE_PORTION : 0.003
    THRESHOLD : 0.003
    MAX_PARTITION : 20

## **How to build service**
```bash
$ docker build -f docker/Dockerfile -t coralteam/babix-ngepetz:latest .
```

## **How to run service**
**Docker image assumed have been created**
```bash
$ docker run -d --name babix-ngepetz \
      -e API_KEY="API_KEY" \
      -e API_SECRET="API_SECRET" \
      -e SLEEP_SECONDS="5" \
      -e MAX_WAIT_TIME_SECONDS="30" \
      -e LAST_STEP_WAIT_TIME_SECONDS="30" \
      -e BASE_URL="https://vip.bitcoin.co.id/api/" \
      -e PRIVATE_URL="https://vip.bitcoin.co.id/tapi/" \
      -e MODAL_DUID="15000000" \
      -e FEE_PORTION="0.003" \
      -e THRESHOLD="0.003" \
      -e MAX_PARTITION="20" \
      coralteam/babix-ngepetz:latest
```
