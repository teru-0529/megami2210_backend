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
