import os
import sys
from datetime import datetime
from sqlalchemy import Column, BIGINT, DECIMAL, DATETIME, BOOLEAN, desc

# 親ディレクトリの設定
app_home = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".." ))

# パス / 設定系の読み込み
sys.path.append(os.path.join(app_home, "setting"))
from db_setting import ENGINE, Base

class BitflyerMacd(Base):
    
    """
    BitflyerMacdModel
    """
    __tablename__ = "bitflyer_macd"
 
    id = Column(BIGINT, primary_key = True, nullable = True)
    server_nonce = Column(BIGINT, nullable = True)
    index_price = Column(DECIMAL, nullable = True)
    macd = Column(DECIMAL)
    macdsignal = Column(DECIMAL)
    macdhist = Column(DECIMAL)
    gcross = Column(BOOLEAN, nullable = True)
    dcross = Column(BOOLEAN, nullable = True)
    created_at = Column(DATETIME, nullable = True)

    ##### select
    def get_limit_record_order_desc(session, limit_num):
        return session.query(BitflyerMacd).order_by(desc(BitflyerMacd.id)).limit(limit_num).all()

    ##### insert
    def insert(session, ticker_timestamp, index_price, macd, macdsignal, macdhist, gcross, dcross):
        sharping_time = ticker_timestamp.split(".")[0].replace("T", "")
        session.add(
            BitflyerMacd(
                server_nonce = int(sharping_time),
                index_price = index_price,
                macd = macd,
                macdsignal = macdsignal,
                macdhist = macdhist,
                gcross = gcross,
                dcross = dcross,
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        session.commit()


def main(args):
    Base.metadata.create_all(bind = ENGINE)

if __name__ == "__main__":
    main(sys.argv)

