from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 固定変数
dialect = "mysql"
driver = "pymysql"
username = "root"
password = "Yuu-1984-0608"
#password = "rootroot"
host = "localhost"
database = "crypto_databases"
charset_type = "utf8"
db_url = f"{dialect}+{driver}://{username}:{password}@{host}/{database}?charset={charset_type}"

#ENGINE = create_engine(db_url, echo=True)
ENGINE = create_engine(db_url, echo=False)

# session作成
Session = sessionmaker(bind = ENGINE)
session = Session()

# Baseモデルの作成
Base = declarative_base()

