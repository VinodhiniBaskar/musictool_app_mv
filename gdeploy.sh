#!/usr/bin/env bash
source activate mv
export PYTHONPATH=.:$PYTHONPATH

gunicorn -b 0.0.0.0:6003 -w 5 --log-file nalign.log wsgi:app  >/dev/null 2>&1 &