#!/bin/bash

case $1 in
  "run")
    while true; do SECONDS=0; python babix.py; sleep 10; done
    ;;
  *)
    echo "usage: $0 [run]"
    exit 1
    ;;
esac
