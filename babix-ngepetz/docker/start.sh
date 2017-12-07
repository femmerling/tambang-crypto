#!/bin/bash

case $1 in
  "run")
    shift
    python3 babix.py
    ;;
  *)
    echo "usage: $0 [run]"
    exit 1
    ;;
esac
