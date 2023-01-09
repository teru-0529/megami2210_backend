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


class SiteType(Base):
    main = "MAIN"
    keep_product = "KEEP_PRODUCT"
    inspect_product = "INSPECT_PRODUCT"
    damaged_product = "DAMAGED_PRODUCT"
    private_order = "PRIVATE_ORDER"

    def description() -> str:
        return """
倉庫種別:
  * `MAIN` - メイン倉庫
  * `KEEP_PRODUCT` - 確保商品倉庫
  * `INSPECT_PRODUCT` - 検品商品倉庫
  * `DAMAGED_PRODUCT` - 破損商品倉庫
  * `PRIVATE_ORDER` - 専用倉庫
    """


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class ShippingProductSituation(Base):
    in_stock = "IN_STOCK"
    on_inspect = "ON_INSPECT"
    arleady_ordered = "ARLEADY_ORDERED"
    not_yet_ordered = "NOT_YET_ORDERED"

    def description() -> str:
        return """
出荷商品状況:
  * `IN_STOCK` - 在庫商品
  * `ON_INSPECT` - 検品中商品
  * `ARLEADY_ORDERED` - 既発注商品
  * `NOT_YET_ORDERED` - 未発注商品
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


class ReceivableTransitionType(Base):
    selling = "SELLING"
    sales_return = "SALES_RETURN"
    deposit = "DEPOSIT"
    balance_out = "BALANCE_OUT"
    other_transition = "OTHER_TRANSITION"

    def description() -> str:
        return """
売掛変動区分:
  * `SELLING` - 販売売上
  * `SALES_RETURN` - 売上返品
  * `DEPOSIT` - 入金
  * `BALANCE_OUT` - 相殺
  * `OTHER_TRANSITION` - その他取引
    """


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class PaymentStatus(Base):
    before_payment = "BEFORE_PAYMENT"
    invoice_confirmed = "INVOICE_CONFIRMED"
    payment_processed = "PAYMENT_PROCESSED"

    def description() -> str:
        return """
支払状況:
  * `BEFORE_PAYMENT` -未払
  * `INVOICE_CONFIRMED` - 請求書受領
  * `PAYMENT_PROCESSED` - 支払完了
    """


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class DepositStatus(Base):
    before_deposit = "BEFORE_DEPOSIT"
    invoice_sended = "INVOICE_SENDED"
    deposit_confirmed = "DEPOSIT_CONFIRMED"

    def description() -> str:
        return """
支払状況:
  * `BEFORE_DEPOSIT` -未入金
  * `INVOICE_SENDED` -請求書送付
  * `DEPOSIT_CONFIRMED` - 入金確認完了
    """


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class Weeks(Base):
    sun = "SUN"
    mon = "MON"
    tue = "TUE"
    wed = "WED"
    thu = "THU"
    fri = "FRI"
    sat = "SAT"

    def description() -> str:
        return """
曜日:
  * `SUN` - 日曜日
  * `MON` - 月曜日
  * `TUE` - 火曜日
  * `WED` - 水曜日
  * `THU` - 木曜日
  * `FRI` - 金曜日
  * `SAT` - 土曜日
    """

    def week_num(self) -> int:
        list = [*Weeks.__members__.values()]
        return list.index(self)


def new_week_num(num: int) -> Weeks:
    return Weeks[num]
