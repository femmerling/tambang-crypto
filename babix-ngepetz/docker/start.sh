#!/bin/bash

case $1 in
  "run")
    while true; do SECONDS=0; python babix.py; sleep $((RANDOM%10+20-$SECONDS)); done
    ;;
  *)
    echo "usage: $0 [run]"
    exit 1
    ;;
esac
