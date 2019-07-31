import os
import sys
from datetime import datetime
import time
from sqlalchemy import Column, BIGINT, DECIMAL, DATETIME 

# 親ディレクトリの設定
app_home = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".." ))

# パス / 設定系の読み込み
sys.path.append(os.path.join(app_home, "setting"))
from db_setting import ENGINE, Base

class BitflyerTicker(Base):
    
    """
    BitflyerTickerModel
    """
    __tablename__ = "bitflyer_ticker"
 
    id = Column(BIGINT, primary_key = True, nullable = True)
    request_nonce = Column(BIGINT, nullable = True)
    bid = Column(DECIMAL, nullable = True)
    ask = Column(DECIMAL, nullable = True)
    volume = Column(DECIMAL, nullable = True)
    timestamp = Column(BIGINT, nullable = True)
    server_nonce = Column(BIGINT, nullable = True)
    index_price = Column(DECIMAL, nullable = True)
    created_at = Column(DATETIME, nullable = True)

    ##### insert
    def insert(session, request_nonce, ticker_info, index_price):
        sharping_time = ticker_info["timestamp"].split(".")[0].replace("T", " ")
        session.add(
            BitflyerTicker(
                request_nonce = request_nonce,
                bid = ticker_info["best_bid"],
                ask = ticker_info["best_ask"],
                volume = ticker_info["volume"],
                timestamp = datetime.strptime(sharping_time, "%Y-%m-%d %H:%M:%S").timestamp(),
                server_nonce = int(sharping_time.replace(" ", "").replace("-", "").replace(":", "")),
                index_price = index_price,
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        session.commit()

def main(args):
    Base.metadata.create_all(bind = ENGINE)

if __name__ == "__main__":
    main(sys.argv)

