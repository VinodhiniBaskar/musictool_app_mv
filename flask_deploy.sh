#!/usr/bin/env bash
echo "Deploy development mode"
# source activate mv
export PYTHONPATH=.:$PYTHONPATH
python mv_nalign/app.py

