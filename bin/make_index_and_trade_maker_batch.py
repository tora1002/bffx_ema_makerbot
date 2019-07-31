# -*- coding: utf-8 -*-
import sys
import os
from backports import configparser
import json
from time import sleep
from datetime import datetime
from pathlib import Path
import talib
import numpy as np
import pymysql.cursors
from sqlalchemy import desc

# 親ディレクトリの設定
app_home = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".." ))

# パスの読み込み
sys.path.append(os.path.join(app_home, "models"))
sys.path.append(os.path.join(app_home, "setting"))

# モジュール、設定系の読み込み
from bitflyer_ticker import BitflyerTicker
from bitflyer_macd import BitflyerMacd
from bitflyer_ema_trade_history import BitflyerEmaTradeHistory
from db_setting import session
from logger import logger
from bitflyer_ccxt import bitflyer


def get_tciker_info(bitflyer):
    ticker = bitflyer.fetch_ticker("FX_BTC_JPY")
    return ticker["info"]

def get_signal(session):
    signal = {}
    index_desc = Bitflyer6tema16dema.get_limit_record_order_desc(session, 1)
        
    for index in index_desc:
        signal["gcross"] = index.gcross
        signal["dcross"] = index.dcross

    return signal

def get_position(session, position_status):
    position = BitflyerEmaTradeHistory.get_record_filter_status(session, position_status)

    ### ポジションが1つ以上存在する
    if len(position) > 1:
        raise Exception("Hold multiple position")

    return position

def get_tciker_info(bitflyer):
    ticker = bitflyer.fetch_ticker("FX_BTC_JPY")
    return ticker["info"]

def create_buy_order(bitflyer, amount, price):
    res = bitflyer.create_order(symbol = "FX_BTC_JPY", type = "limit", side = "buy", amount = amount, price = price)
    
    if res["id"] is None:
        raise Exception("Can not order")

    return res

def create_sell_order(bitflyer, amount, price):
    res = bitflyer.create_order(symbol = "FX_BTC_JPY", type = "market", side = "sell", amount = amount, price)
    
    if res["id"] is None:
        raise Exception("Can not order")

    return res

def get_open_orders(bitflyer):
    open_orders = bitflyer.fetch_open_orders(symbol = "FX_BTC_JPY")

    if len(open_orders) > 1:
        raise Exception("Hold multiple position")

    return open_orders

def cancel_order(bitflyer, order_id):
    bitflyer.cancel_order(order_id, symbol = "FX_BTC_JPY")
    #TODO cancel エラーになった場合はどするか？

def insert_trade_history(session, request_nonce, amount, order_id):
    session.add(
        BitflyerEmaTradeHistory(
            order_request_nonce = request_nonce,
            amount = amount,
            status = "request",
            open_order_id = order_id,
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )
    session.commit()

def update_status_close(session, trade_history, order_id):
    trade_history.status = "close"
    trade_history.close_order_id = order_id
    trade_history.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.commit()

def update_status(session, trade_history, position_status):
    trade_history.status = position_status
    trade_history.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.commit()


if __name__ == "__main__" :
   
    logger.info("=== make_index_and_trade_batch start ===")
    logger.info("=== make_index start ===")

    try:
        request_nonce = datetime.now().strftime("%Y%m%d%H%M%S")

        ### tickerを取得 & index価格を作成
        ticker_info = get_tciker_info(bitflyer)
        index_price = (ticker_info["best_ask"] +ticker_info["best_bid"])/2

        ### tickerデータを保存
        BitflyerTicker.insert(session, request_nonce, ticker_info, index_price)

        ### emaデータを取得
        indexs_desc = BitflyerMacd.get_limit_record_order_desc(session, 19)
        
        ### 取得したデータを元に、emaデータを加工
        index_list = []
        prev_macd = 0
        prev_macdsignal = 0

        for index in indexs_desc:
            if prev_macd == 0:
                prev_macd = float(index.macd)
                prev_macdsignal = float(index.macdsignal)

            index_list.append(float(index.index_price))

        index_list.reverse()
        index_list.append(index_price)

        macd_list, macdsignal_list, macdhist_list = talib.MACD(np.array(index_list), fastperiod=6, slowperiod=12, signalperiod=9)

        macd = macd_list[-1]
        macdsignal = macdsignal_list[-1]
        macdhist = macdhist_list[-1]

        if (np.isnan(macd)):
            macd = 0
        if (np.isnan(macdsignal)):
            macdsignal = 0
        if (np.isnan(macdhist)):
            macdhist = 0

        ### emaデータからGクロス、Dクロスを判定
        gcross = bool((macd > macdsignal) & (prev_macd < prev_macdsignal))
        dcross = bool((macd < macdsignal) & (prev_macd > prev_macdsignal))

        ### emaデータを取得
        BitflyerMacd.insert(session, ticker_info["timestamp"], index_price, float(macd), float(macdsignal), float(macdhist), gcross, dcross)

    # キャッチして例外をログに記録
    except Exception as e:
        logger.exception(e)
        sys.exit(1)
    
    logger.info("=== make_index finish ===")
    logger.info("=== trade start ===")

    #TODO 変数化する
    # 最低購入金額0.01BTC（いずれレバレッジにした方が良い？）
    trade_amount = 0.01

    try:
        ### ポジションを持っているか？
        position = get_position(session, "open")

        ### ポジションを持っていない & Gクロスしていた場合
        if (len(position) == 0) & gcross:

            logger.info("Gcross & buy order")

            # bidの値を取得
            ticker_info = get_tciker_info(bitflyer)
            ticker_bid = ticker_info["best_bid"]

            # 注文
            request_nonce = datetime.now().strftime("%Y%m%d%H%M%S")
            res = create_buy_order(bitflyer, amount = trade_amount, price = ticker_bid + 1)

            order_id = res["id"]
            insert_trade_history(session, request_nonce, trade_amount, order_id)

            sleep(1)

            # 未決済のポジションを全て取得
            open_orders = get_open_orders(bitflyer)
            trade_history_list = get_position(session, "request")

            for obj in trade_history_list:
                trade_history = obj

            # takeされなかったのでキャンセル & data更新
            if len(open_orders) == 1:
                cancel_order(bitflyer, order_id)
                update_status(session, trade_history, "not_position")
                logger.info("Not Position")

            # takeされた場合
            else:
                update_status(session, trade_history, "open")
                logger.info("Open Position")


        ### ポジションを持っている & Dクロスしていた場合
        if (len(position) == 1) & dcross:

            logger.info("Dcross & sell order")

            # 変数をセット
            for p in position:
                trade_history = p

            # ポジションを解消したいので、orderを出し続けるためのflg
            order_flg = True

            while(order_flg):
                # askの値を取得
                ticker_info = get_tciker_info(bitflyer)
                ticker_ask = ticker_info["best_ask"]

                res = create_sell_order(bitflyer, amount = trade_amount, ticker_ask - 1)
                order_id = res["id"]

                sleep(1)

                # 未決済のポジションを全て取得
                open_orders = get_open_orders(bitflyer)

                # takeされなかったのでキャンセル
                if len(open_orders) == 1:
                    cancel_order(bitflyer, order_id)
                    logger.info("Can not sell order")

                # takeされた場合
                else:
                    update_status_close(session, trade_history, order_id)
                    order_flg = False
                    logger.info("Close position")

    # キャッチして例外をログに記録
    except Exception as e:
        logger.exception(e)
        sys.exit(1)

    logger.info("=== trade finish ===")
    logger.info("=== make_index_and_trade_batch finish ===")

