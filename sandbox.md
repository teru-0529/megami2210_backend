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
