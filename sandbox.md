### FastAPIサンプル
https://nmomos.com/tips/2021/01/23/fastapi-docker-1/
https://zenn.dev/sh0nk/books/537bb028709ab9/viewer/f1b6fc

### SQLAlchemyの使い方（マッピングの自動生成）
https://zenn.dev/myuki/books/02fe236c7bc377/viewer/ceb112


#### postgresへのenum登録内容確認
https://mebee.info/2022/07/23/post-45272/#outline__3
```
select pn.nspname,
       pt.typname,
       pe.enumlabel
from pg_type pt
   join pg_enum pe on pt.oid = pe.enumtypid
   join pg_catalog.pg_namespace pn ON pn.oid = pt.typnamespace
```

#### バージョン 0.19 から asyncio_mode のデフォルトが auto から strict に変わっていました。
https://www.beex-inc.com/blog/rejoin-nasu

#### asyncioとpytestでテスト用fixtureを作るときにgot Future <Future pending> attached to a different loopが出る話
https://blog.hirokiky.org/entry/2019/01/04/183048
https://github.com/pytest-dev/pytest-asyncio/issues/38

#### pytestのmark.parametrizeでサブテストに簡単に名前をつける方法
https://dev.classmethod.jp/articles/pytest-mark-parametrize-name/

#### pytestのtest IDに日本語を使う方法
https://qiita.com/gimKondo/items/d7a874a97af1ad93052a

#### Location Header に登録後のURLを入れる（request.url_for()）
https://stackoverflow.com/questions/63682956/fastapi-retrieve-url-from-view-name-route-name

#### sql文
https://www.m3tech.blog/entry/sqlalchemy-tutorial
https://docs.sqlalchemy.org/en/20/core/expression_api.html
https://docs.sqlalchemy.org/en/20/core/selectable.html

#### pydantic
https://qiita.com/uenosy/items/2f6b1aa258018d3db76c
https://qiita.com/0622okakyo/items/d1dcb896621907f9002b#validate-always

#### OpenAPI
https://future-architect.github.io/articles/20200409/

#### FastAPI + SQLAlchemy でpytestのcoverageが100%いかない件
https://zenn.dev/rhosoi/scraps/7225a0e89cdb57

#### 【pydantic】未定義フィールドの動作
https://www.mathkuro.com/python/%E3%80%90pydantic%E3%80%91%E6%9C%AA%E5%AE%9A%E7%BE%A9%E3%83%95%E3%82%A3%E3%83%BC%E3%83%AB%E3%83%89%E3%81%AE%E5%8B%95%E4%BD%9C/

#### WEBAPIのベストプラクティス
https://qiita.com/mserizawa/items/b833e407d89abd21ee72

#### joinサンプル
```
   query = (
      select(ac_Profile, ac_Auth)
      .join(ac_Auth, ac_Profile.account_id == ac_Auth.account_id)
      .filter(ac_Profile.account_id == id)
   )
```
#### ランダム文字列生成
https://qiita.com/Scstechr/items/c3b2eb291f7c5b81902a

#### パスワードのHash化
https://qiita.com/dumbbell/items/62735f30d8cb33dd2773
https://qiita.com/matsulib/items/2bcf59c2b2cb5eb5c5c4

#### テスト時のengineの作り方
https://qiita.com/takkeybook/items/bc8c1b6712362db53267

#### sqlalchemyのfilterいろいろ
https://mycodingjp.blogspot.com/2019/07/flask-sqlalchemy.html
