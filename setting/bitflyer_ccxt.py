# -*- coding: utf-8 -*-
import sys
import os
import random
import ccxt

#### api keys #####
api_keys = [
    {"api_key": "XLh5nLnMk9SArPwV9oEiRn", "api_secret": "SpPGllAzy1DiR3cuy1zrDlhRKRkpSfeMVtx0kY+mmCk="},
    {"api_key": "XLh5nLnMk9SArPwV9oEiRn", "api_secret": "SpPGllAzy1DiR3cuy1zrDlhRKRkpSfeMVtx0kY+mmCk="},
    {"api_key": "XLh5nLnMk9SArPwV9oEiRn", "api_secret": "SpPGllAzy1DiR3cuy1zrDlhRKRkpSfeMVtx0kY+mmCk="},
    {"api_key": "XLh5nLnMk9SArPwV9oEiRn", "api_secret": "SpPGllAzy1DiR3cuy1zrDlhRKRkpSfeMVtx0kY+mmCk="},
    {"api_key": "XLh5nLnMk9SArPwV9oEiRn", "api_secret": "SpPGllAzy1DiR3cuy1zrDlhRKRkpSfeMVtx0kY+mmCk="}
]

num = random.randint(0,4)
using_key = api_keys[num]

API_KEY = using_key["api_key"]
API_SECRET = using_key["api_secret"]

##### set ccxt #####
bitflyer = ccxt.bitflyer({
    "apiKey" : API_KEY,
    "secret" : API_SECRET
})


