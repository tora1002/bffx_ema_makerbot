# 考え方

10秒ごとにtikcerを取得して、それを元にMACDを計算。

ポジションがなく、Gクロスした場合はLポジションを取得→Dクロスでポジション清算。

ポジションがなく、Dクロスした場合はSポジションを取得→Gクロスでポジション清算。

なお、ポジションを取得する場合、1秒待ってもポジションを持っていない場合は解して、次を待つ。

クローズする場合は、ひたすら刺し続ける。

# 動かし方

* cloneする
* logディレクトリ作る
* デーブル作る
* DBアクセス情報を、setting/db_setting.py に書き込む
* bin/make_index_and_trade_batch.py を10秒に1回動くようにcron設定する
* bin/aggregate_batch.py を3分に1回くらい動くようにcron設定する


# 構造

* bin/make_index_and_trade_batch.py
    * ticker取得
    * MACD作成
    * トレード判定
    * トレード
* bin/aggregate_batch.py
    * 取引IDを元に取引データを取得して、bitflyer_ema_trade_historyの必要カラムを埋める

* models/bitflyer_ticker.py
       * Ticker情報を格納するテーブル
* models/bitflyer_macd.py
    * Tickerから計算したMACD情報を格納するテーブル
    * 結論、Ticker情報テーブルと分けた意味はあまりなかった...
* models/bitflyer_ema_trade_history.py
    * Trade履歴を格納するテーブル

* setting/bitflyer_ccxt.py
* setting/db_setting.py
* setting/logger.py

※ cloneしたら、logディレクトリを作らないと動かなくてエラーはきますw

# 使っているテーブル

```
CREATE TABLE bitflyer_ticker (
 id BIGINT AUTO_INCREMENT NOT NULL PRIMARY KEY,
 request_nonce BIGINT NOT NULL,
 bid DECIMAL(10,1) NOT NULL,
 ask DECIMAL(10,1) NOT NULL,
 volume DECIMAL(18,10) NOT NULL,
 timestamp BIGINT NOT NULL,
 server_nonce BIGINT NOT NULL,
 index_price DECIMAL(12,2) NOT NULL,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```
```
CREATE TABLE bitflyer_ema_trade_history (
 id BIGINT AUTO_INCREMENT NOT NULL PRIMARY KEY,
 order_request_nonce BIGINT NOT NULL,
 amount DECIMAL(10,7) NOT NULL,
 status VARCHAR(20) NOT NULL,
 open_order_id VARCHAR(30) NOT NULL,
 open_time DATETIME,
 open_rate DECIMAL(10,1),
 close_order_id VARCHAR(30),
 close_time DATETIME,
 close_rate DECIMAL(10,1),
 profit BIGINT,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
 updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```
```
CREATE TABLE bitflyer_macd (
 id BIGINT AUTO_INCREMENT NOT NULL PRIMARY KEY,
 server_nonce BIGINT NOT NULL,
 index_price DECIMAL(12,2) NOT NULL,
 macd DECIMAL(15,5) DEFAULT NULL,
 macdsignal DECIMAL(15,5) DEFAULT NULL,
 macdhist DECIMAL(15,5) DEFAULT NULL,
 gcross BOOLEAN NOT NULL,
 dcross BOOLEAN NOT NULL,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

# 困りごと / 手抜きどころ

* ポジションをオープンする際、1秒待ってオープンしなかったのでキャンセルオーダーしたら、実はその間にポジションを持っていた場合の処理が皆無
* ポジションをクローズする際、best価格で指値をし続けてもなかなか約定しない場合があり、その際過大に損失を出す
* ポジションをオープン・クローズする場合、0.01BTC以下だけ約定した場合の処理が皆無
* その他なんか微妙なバグありそう


