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