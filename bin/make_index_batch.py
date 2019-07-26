# -*- coding: utf-8 -*-
import sys
import os
from backports import configparser
import json
from datetime import datetime
import talib
import numpy as np
import pymysql.cursors

# 親ディレクトリの設定
app_home = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".." ))

# パスの読み込み
sys.path.append(os.path.join(app_home, "models"))
sys.path.append(os.path.join(app_home, "setting"))

# モジュール、設定系の読み込み
from bitflyer_ticker import BitflyerTicker
from bitflyer_6tema_16dema import Bitflyer6tema16dema
from db_setting import session
from logger import logger
from bitflyer_ccxt import bitflyer


def get_tciker_info(bitflyer):
    ticker = bitflyer.fetch_ticker("FX_BTC_JPY")
    return ticker["info"]


if __name__ == "__main__" :

    try:
        logger.info("=== make_index_batch start ===")

        request_nonce = datetime.now().strftime("%Y%m%d%H%M%S")

        ### tickerを取得 & index価格を作成
        ticker_info = get_tciker_info(bitflyer)
        index_price = (ticker_info["best_ask"] +ticker_info["best_bid"])/2

        ### tickerデータを保存
        BitflyerTicker.insert(session, request_nonce, ticker_info, index_price)

        ### emaデータを取得
        indexs_desc = Bitflyer6tema16dema.get_limit_record_order_desc(session, 30)
        
        ### 取得したデータを元に、emaデータを加工
        short_index_list = []
        long_index_list = []
        prev_short_ema = 0
        prev_long_ema = 0

        for index in indexs_desc:
            if prev_short_ema == 0:
                prev_short_ema = float(index.short_ema)
                prev_long_ema = float(index.long_ema)

            long_index_list.append(float(index.index_price))
            
            if (len(short_index_list) < 15):
                short_index_list.append(float(index.index_price))

        if len(long_index_list) != 0:
            long_index_list.reverse()
            short_index_list.reverse()

        long_index_list.append(index_price)
        short_index_list.append(index_price)

        short_ema = round(float(talib.TEMA(np.array(short_index_list), timeperiod = 6)[-1]), 4)
        long_ema = round(float(talib.DEMA(np.array(long_index_list), timeperiod = 16)[-1]), 4)

        if (np.isnan(short_ema)):
            short_ema = 0
        if (np.isnan(long_ema)):
            long_ema = 0

        ### emaデータからGクロス、Dクロスを判定
        gcross = bool((short_ema > long_ema) & (prev_short_ema < prev_long_ema))
        dcross = bool((short_ema < long_ema) & (prev_short_ema > prev_long_ema))

        ### emaデータを取得
        Bitflyer6tema16dema.insert(session, ticker_info["timestamp"], index_price, short_ema, long_ema, gcross, dcross)
        
        logger.info("=== make_index_batch finish ===")

    # キャッチして例外をログに記録
    except Exception as e:
        logger.exception(e)
        sys.exit(1)

