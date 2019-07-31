# -*- coding: utf-8 -*-
import sys
import os
from time import sleep
from datetime import datetime
from pathlib import Path
import pymysql.cursors
from sqlalchemy import desc

# 親ディレクトリの設定
app_home = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".." ))

# パスの読み込み
sys.path.append(os.path.join(app_home, "models"))
sys.path.append(os.path.join(app_home, "setting"))

# モジュール、設定系の読み込み
from bitflyer_ema_trade_history import BitflyerEmaTradeHistory
from db_setting import session
from logger import logger
from bitflyer_ccxt import bitflyer

if __name__ == "__main__" :

    logger.info("=== aggregate_batch start ===")
    
    try:
        #statusがcloseのレコードを取得する
        gcross_close_positions = BitflyerEmaTradeHistory.get_record_filter_status(session, "gcross_close")

        if gcross_close_positions is not None:
        
            # 直近の取引履歴25件をcoincheckから取得する
            my_trades = bitflyer.fetch_my_trades(symbol = "FX_BTC_JPY")
            
            # 1件ずつ、order_idをキーに突合し、抜けているデータを保存する
            for trade_history in gcross_close_positions:
                # 変数初期化
                open_time = None
                open_rate = None
                close_time = None
                close_rate = None

                for my_trade in my_trades:
                    if str(my_trade["order"]) == str(trade_history.open_order_id):
                        open_time = my_trade["datetime"].split(".")[0].replace("T", " ")
                        open_rate = my_trade["price"]
                    if str(my_trade["order"]) == str(trade_history.close_order_id):
                        close_time = my_trade["datetime"].split(".")[0].replace("T", " ")
                        close_rate = my_trade["price"]
 
                if open_time is not None and close_time is not None: 
                    # update
                    trade_history.status = "gcross_agregated"
                    trade_history.open_time = datetime.strptime(open_time, "%Y-%m-%d %H:%M:%S")
                    trade_history.open_rate = open_rate
                    trade_history.close_time =datetime.strptime(close_time, "%Y-%m-%d %H:%M:%S")
                    trade_history.close_rate = close_rate
                    trade_history.profit = (float(close_rate) - float(open_rate)) * 0.01
                    trade_history.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    session.commit()

        #statusがcloseのレコードを取得する
        dcross_close_positions = BitflyerEmaTradeHistory.get_record_filter_status(session, "dcross_close")

        if dcross_close_positions is not None:
        
            # 直近の取引履歴25件をcoincheckから取得する
            my_trades = bitflyer.fetch_my_trades(symbol = "FX_BTC_JPY")
            
            # 1件ずつ、order_idをキーに突合し、抜けているデータを保存する
            for trade_history in dcross_close_positions:
                # 変数初期化
                open_time = None
                open_rate = None
                close_time = None
                close_rate = None

                for my_trade in my_trades:
                    if str(my_trade["order"]) == str(trade_history.open_order_id):
                        open_time = my_trade["datetime"].split(".")[0].replace("T", " ")
                        open_rate = my_trade["price"]
                    if str(my_trade["order"]) == str(trade_history.close_order_id):
                        close_time = my_trade["datetime"].split(".")[0].replace("T", " ")
                        close_rate = my_trade["price"]
 
                if open_time is not None and close_time is not None: 
                    # update
                    trade_history.status = "dcross_agregated"
                    trade_history.open_time = datetime.strptime(open_time, "%Y-%m-%d %H:%M:%S")
                    trade_history.open_rate = open_rate
                    trade_history.close_time =datetime.strptime(close_time, "%Y-%m-%d %H:%M:%S")
                    trade_history.close_rate = close_rate
                    trade_history.profit = (float(open_rate) - float(close_rate)) * 0.01
                    trade_history.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    session.commit()





    # キャッチして例外をログに記録
    except Exception as e:
        logger.exception(e)
        sys.exit(1)

    logger.info("=== aggregate_batch finish ===")


