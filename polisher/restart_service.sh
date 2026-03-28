#!/bin/bash

# Kill all existing processes
killall -9 python3 python 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null

sleep 3

# Start service
cd /Users/marquiserosier/Documents/instaforlazypeople/polisher
python main.py
