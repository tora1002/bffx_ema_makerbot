# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
from time import sleep
from datetime import datetime
from pathlib import Path
import pymysql.cursors
from sqlalchemy import desc

# 親ディレクトリの設定、パスの読み込み
app_home = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".." ))
sys.path.append(os.path.join(app_home, "models"))
sys.path.append(os.path.join(app_home, "setting"))

# モジュール、設定系の読み込み
from bitflyer_6tema_16dema import Bitflyer6tema16dema
from bitflyer_ema_trade_history import BitflyerEmaTradeHistory
from db_setting import session
from logger import logger
from bitflyer_ccxt import bitflyer

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

def create_order(bitflyer, side, amount, price):
    res = bitflyer.create_order(symbol = "FX_BTC_JPY", type = "limit", side = side, amount = amount, price = price)
    
    if res["id"] is None:
        raise Exception("Can not order")

    return res

def get_open_orders(bitflyer):
    open_orders = bitflyer.fetch_open_orders()

    if len(open_orders) > 1:
        raise Exception("Hold multiple position")

    return open_orders

def cancel_order(bitflyer, order_id):
    bitflyer.cancel_order(order_id)
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

    #TODO 変数化する
    # 最低購入金額0.005BTC（いずれレバレッジにした方が良い？）
    trade_amount = 0.005

    logger.info("=== trade_batch start ===")
    
    ### プロセスがないか確認する
    if (os.path.exists("process.txt")):
        logger.info("Exist process")
        logger.info("=== trade_batch finish ===")
        sys.exit(1)

    ### プロセス起動中ファイルを作成
    Path("process.txt").touch()

    try:
        ### 最新のシグナルを取得
        signal = get_signal(session)
    
        ### ポジションを持っているか？
        position = get_position(session, "open")
        
        ### ポジションを持っていない & Gクロスしていた場合
        if (len(position) == 0) & signal["gcross"]:
        
            logger.info("Gcross & buy order")
            
            # bidの値を取得
            ticker_info = get_tciker_info(bitflyer)
            ticker_bid = ticker_info["bid"]

            # 注文
            request_nonce = datetime.now().strftime("%Y%m%d%H%M%S")
            res = create_order(bitflyer, side = "buy", amount = trade_amount, price = ticker_bid)

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
        if (len(position) == 1) & signal["dcross"]:

            logger.info("Dcross & sell order")
            
            # 変数をセット
            for p in position:
                trade_history = p
            
            # ポジションを解消したいので、orderを出し続けるためのflg
            order_flg = True
            
            while(order_flg):
                # askの値を取得
                ticker_info = get_tciker_info(bitflyer)
                ticker_ask = ticker_info["ask"]

                res = create_order(bitflyer, side = "sell", amount = trade_amount, price = ticker_ask)
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

    ### プロセス終了のため、ファイルを削除
    os.remove("process.txt")
    logger.info("=== trade_batch finish ===")

