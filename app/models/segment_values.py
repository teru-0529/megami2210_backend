#!/usr/bin/python3
# config.py

from enum import Enum

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class Base(str, Enum):
    pass

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class DateType(Base):
    business_date = "BUSINESS_DATE"

    def description() -> str:
        return """
日付種類:
  * `BUSINESS_DATE` - 業務日付
    """


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskStatus(Base):
    todo = "TODO"
    doing = "DOING"
    done = "DONE"

    def description() -> str:
        return """
タスク状況:
  * `TODO` - 未対応
  * `DOING` - 対応中
  * `DONE` - 完了
    """


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class AccountTypes(Base):
    administrator = "ADMINISTRATOR"
    general = "GENERAL"
    provisional = "PROVISIONAL"

    def description() -> str:
        return """
アカウント種類:
  * `ADMINISTRATOR` - 管理ユーザー
  * `GENERAL` - 一般ユーザー
  * `PROVISIONAL` - 仮発行ユーザー
    """


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class MasterStatus(Base):
    ready = "READY"
    active = "ACTIVE"
    stop_dealing = "STOP_DEALING"

    def description() -> str:
        return """
マスターステータス:
  * `READY` - 準備中
  * `ACTIVE` - 取引中
  * `STOP_DEALING` - 取引停止
    """


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class OrderPolicy(Base):
    periodically = "PERIODICALLY"
    as_needed = "AS_NEEDED"

    def description() -> str:
        return """
発注方針:
  * `PERIODICALLY` - 定期発注
  * `AS_NEEDED` - 随時発注
    """


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class StockTransitionType(Base):
    movement_warehousing = "MOVEMENT_WAREHOUSING"
    purchase = "PURCHASE"
    sales_return = "SALES_RETURN"
    movement_shipping = "MOVEMENT_SHIPPING"
    selling = "SELLING"
    ordering_return = "ORDERING_RETURN"
    other_transition = "OTHER_TRANSITION"

    def description() -> str:
        return """
在庫変動区分:
  * `MOVEMENT_WAREHOUSING` - 移動入庫
  * `PURCHASE` - 仕入入庫
  * `SALES_RETURN` - 売上返品入庫
  * `MOVEMENT_SHIPPING` - 移動出庫
  * `SELLING` - 販売出庫
  * `ORDERING_RETURN` - 仕入返品出庫
  * `OTHER_TRANSITION` - その他取引
    """


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class PayableTransitionType(Base):
    purchase = "PURCHASE"
    ordering_return = "ORDERING_RETURN"
    payment = "PAYMENT"
    balance_out = "BALANCE_OUT"
    other_transition = "OTHER_TRANSITION"

    def description() -> str:
        return """
買掛変動区分:
  * `PURCHASE` - 購入仕入
  * `ORDERING_RETURN` - 仕入返品
  * `PAYMENT` - 支払
  * `BALANCE_OUT` - 相殺
  * `OTHER_TRANSITION` - その他取引
    """


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class Weeks(Base):
    mon = "MON"
    tue = "TUE"
    wed = "WED"
    thu = "THU"
    fri = "FRI"
    sat = "SAT"
    sun = "SUN"

    def description() -> str:
        return """
曜日:
  * `MON` - 月曜日
  * `TUE` - 火曜日
  * `WED` - 水曜日
  * `THU` - 木曜日
  * `FRI` - 金曜日
  * `SAT` - 土曜日
  * `SUN` - 日曜日
    """

    def week_num(self) -> int:
        list = [*Weeks.__members__.values()]
        return list.index(self)
