"""insert sample data

Revision ID: 93ceba152fb9
Revises: 4ed3531f2a5e
Create Date: 2022-12-16 22:43:54.629985

"""
from datetime import date

from alembic import op
from sqlalchemy import MetaData, Table

from app.models.segment_values import SiteType

# revision identifiers, used by Alembic.
revision = "93ceba152fb9"
down_revision = "4ed3531f2a5e"
branch_labels = None
depends_on = None


def upgrade() -> None:

    meta = MetaData(bind=op.get_bind())
    meta.reflect(schema="inventory")
    inv_moving_instructions = Table("inventory.moving_instructions", meta)
    inv_other_inventory_instructions = Table(
        "inventory.other_inventory_instructions", meta
    )

    meta = MetaData(bind=op.get_bind())
    meta.reflect(schema="purchase")
    pch_orderings = Table("purchase.orderings", meta)
    pch_ordering_details = Table("purchase.ordering_details", meta)
    pch_wearhousings = Table("purchase.wearhousings", meta)
    pch_wearhousing_details = Table("purchase.wearhousing_details", meta)
    pch_order_cancel_instructions = Table("purchase.order_cancel_instructions", meta)
    pch_arrival_date_instructions = Table("purchase.arrival_date_instructions", meta)
    pch_payment_instructions = Table("purchase.payment_instructions", meta)
    pch_payment_check_instructions = Table("purchase.payment_check_instructions", meta)
    pch_purchase_return_instructions = Table(
        "purchase.purchase_return_instructions", meta
    )
    pch_other_purchase_instructions = Table(
        "purchase.other_purchase_instructions", meta
    )

    meta = MetaData(bind=op.get_bind())
    meta.reflect(schema="selling")
    sel_receivings = Table("selling.receivings", meta)
    sel_receiving_details = Table("selling.receiving_details", meta)
    sel_shippings = Table("selling.shippings", meta)
    sel_shipping_details = Table("selling.shipping_details", meta)
    sel_receive_cancel_instructions = Table("selling.receive_cancel_instructions", meta)
    sel_sending_bill_instructions = Table("selling.sending_bill_instructions", meta)
    sel_deposit_instructions = Table("selling.deposit_instructions", meta)
    sel_selling_return_instructions = Table("selling.selling_return_instructions", meta)
    sel_other_selling_instructions = Table("selling.other_selling_instructions", meta)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-01-20 発注 INFO:
    op.execute(
        """
        update business_date SET date = '2023-01-20';
        """
    )
    op.bulk_insert(
        pch_orderings,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S001",
            },
        ],
    )
    op.bulk_insert(
        pch_ordering_details,
        [
            {
                "ordering_no": "PO-0000001",
                "product_id": "S001-00002",
                "purchase_quantity": 3,
                "purchase_unit_price": 11000.0,
            },
            {
                "ordering_no": "PO-0000001",
                "product_id": "S001-00003",
                "purchase_quantity": 2,
                "purchase_unit_price": 8000.0,
            },
            {
                "ordering_no": "PO-0000001",
                "product_id": "S001-00001",
                "purchase_quantity": 4,
                "purchase_unit_price": 10000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-01-22 発注 INFO:
    op.execute(
        """
        update business_date SET date = '2023-01-22';
        """
    )
    op.bulk_insert(
        pch_orderings,
        [
            {
                "operator_id": "T-902",
                "supplier_id": "S002",
            },
        ],
    )
    op.bulk_insert(
        pch_ordering_details,
        [
            {
                "ordering_no": "PO-0000002",
                "product_id": "S002-00001",
                "purchase_quantity": 8,
                "purchase_unit_price": 19000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-01-23 発注 INFO:
    op.execute(
        """
        update business_date SET date = '2023-01-23';
        """
    )
    op.bulk_insert(
        pch_orderings,
        [
            {
                "operator_id": "T-902",
                "supplier_id": "S002",
            },
        ],
    )
    op.bulk_insert(
        pch_ordering_details,
        [
            {
                "ordering_no": "PO-0000003",
                "product_id": "S002-00001",
                "purchase_quantity": 2,
                "purchase_unit_price": 22000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-01-24 発注納期変更 INFO:
    op.execute(
        """
        update business_date SET date = '2023-01-24';
        """
    )
    op.bulk_insert(
        pch_arrival_date_instructions,
        [
            {
                "operator_id": "T-902",
                "change_reason": "メーカー在庫なし",
                "order_detail_no": 1,
                "arrival_date": date(2023, 2, 5),
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-01-25 発注キャンセル INFO:
    op.execute(
        """
        update business_date SET date = '2023-01-25';
        """
    )
    op.bulk_insert(
        pch_order_cancel_instructions,
        [
            {
                "operator_id": "T-902",
                "cancel_reason": "護発注",
                "order_detail_no": 2,
                "calcel_quantity": 2,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-01-28 発注キャンセル INFO:
    op.execute(
        """
        update business_date SET date = '2023-01-28';
        """
    )
    op.bulk_insert(
        pch_order_cancel_instructions,
        [
            {
                "operator_id": "T-902",
                "cancel_reason": "受注キャンセルの対応",
                "order_detail_no": 3,
                "calcel_quantity": 1,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-01-30 入荷 INFO:
    op.execute(
        """
        update business_date SET date = '2023-01-30';
        """
    )
    op.bulk_insert(
        pch_wearhousings,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S001",
            },
        ],
    )
    op.bulk_insert(
        pch_wearhousing_details,
        [
            {
                "wearhousing_no": "WH-0000001",
                "order_detail_no": 3,
                "wearhousing_quantity": 3,
                "wearhousing_unit_price": 10000.0,
                "site_type": SiteType.inspect_product,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-01-31 検品 INFO:
    op.execute(
        """
        update business_date SET date = '2023-01-31';
        """
    )
    op.bulk_insert(
        inv_moving_instructions,
        [
            {
                "operator_id": "T-901",
                "instruction_cause": "検品（異常なし）",
                "site_type_from": SiteType.inspect_product,
                "site_type_to": SiteType.main,
                "product_id": "S001-00001",
                "quantity": 1,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-02-06 入荷(mainに直接入荷:検品を省略) INFO:
    op.execute(
        """
        update business_date SET date = '2023-02-06';
        """
    )
    op.bulk_insert(
        pch_wearhousings,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S001",
            },
            {
                "operator_id": "T-901",
                "supplier_id": "S002",
            },
        ],
    )
    op.bulk_insert(
        pch_wearhousing_details,
        [
            {
                "wearhousing_no": "WH-0000002",
                "order_detail_no": 1,
                "wearhousing_quantity": 3,
                "wearhousing_unit_price": 10500.0,
                "site_type": SiteType.main,
            },
            {
                "wearhousing_no": "WH-0000003",
                "order_detail_no": 4,
                "wearhousing_quantity": 3,
                "wearhousing_unit_price": 19000.0,
                "site_type": SiteType.main,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-02-07 入荷(mainに直接入荷:検品を省略) INFO:
    op.execute(
        """
        update business_date SET date = '2023-02-07';
        """
    )
    op.bulk_insert(
        pch_wearhousings,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S002",
                "note": "代理入荷(T-902)",
            },
        ],
    )
    op.bulk_insert(
        pch_wearhousing_details,
        [
            {
                "wearhousing_no": "WH-0000004",
                "order_detail_no": 4,
                "wearhousing_quantity": 5,
                "wearhousing_unit_price": 17000.0,
                "site_type": SiteType.main,
            },
            {
                "wearhousing_no": "WH-0000004",
                "order_detail_no": 5,
                "wearhousing_quantity": 1,
                "wearhousing_unit_price": 22000.0,
                "site_type": SiteType.main,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-02-08 仕入返品/その他買掛金取引/ 請求書確認INFO:
    op.execute(
        """
        update business_date SET date = '2023-02-08';
        """
    )
    # 仕入返品
    op.bulk_insert(
        pch_purchase_return_instructions,
        [
            {
                "operator_id": "T-902",
                "return_reason": "お客様受注のキャンセル対応",
                "supplier_id": "S002",
                "product_id": "S002-00001",
                "return_quantity": 2,
                "return_unit_price": 18500.0,
                "site_type": SiteType.main,
            }
        ],
    )
    # その他買掛金取引
    op.bulk_insert(
        pch_other_purchase_instructions,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S001",
                "instruction_cause": "輸送費追加計上",
                "transition_amount": 2800.0,
            },
        ],
    )
    # 請求書確認
    op.bulk_insert(
        pch_payment_check_instructions,
        [
            {
                "operator_id": "T-901",
                "payment_no": "PM-0000001",
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-02-09 その他買掛金取引INFO:
    op.execute(
        """
        update business_date SET date = '2023-02-09';
        """
    )
    op.bulk_insert(
        pch_other_purchase_instructions,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S002",
                "instruction_cause": "誤請求返金(2022年10月分)",
                "transition_amount": -10000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-02-15 即時受注/出荷 INFO:
    op.execute(
        """
        update business_date SET date = '2023-02-15';
        """
    )
    op.bulk_insert(
        sel_receivings,
        [
            {
                "operator_id": "T-901",
                "costomer_id": "S001",
            },
        ],
    )
    op.bulk_insert(
        sel_receiving_details,
        [
            {
                "receiving_no": "RO-0000001",
                "product_id": "S002-00001",
                "receive_quantity": 1,
                "selling_unit_price": 43000.0,
            },
        ],
    )
    op.bulk_insert(
        sel_shippings,
        [
            {
                "operator_id": "T-901",
                "costomer_id": "S001",
            },
        ],
    )
    op.bulk_insert(
        sel_shipping_details,
        [
            {
                "shipping_no": "SP-0000001",
                "receive_detail_no": 1,
                "shipping_quantity": 1,
                "selling_unit_price": 43000.0,
            },
        ],
    )
    op.bulk_insert(
        sel_receivings,
        [
            {
                "operator_id": "T-902",
                "costomer_id": "C001",
            },
        ],
    )
    op.bulk_insert(
        sel_receiving_details,
        [
            {
                "receiving_no": "RO-0000002",
                "product_id": "S002-00001",
                "receive_quantity": 2,
                "selling_unit_price": 45000.0,
            },
        ],
    )
    op.bulk_insert(
        sel_shippings,
        [
            {
                "operator_id": "T-901",
                "costomer_id": "C001",
            },
        ],
    )
    op.bulk_insert(
        sel_shipping_details,
        [
            {
                "shipping_no": "SP-0000002",
                "receive_detail_no": 2,
                "shipping_quantity": 2,
                "selling_unit_price": 44000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-02-16 請求書送付INFO:
    op.execute(
        """
        update business_date SET date = '2023-02-16';
        """
    )
    op.bulk_insert(
        sel_sending_bill_instructions,
        [
            {
                "operator_id": "T-901",
                "billing_no": "BL-0000001",
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-03-01 請求書確認INFO:
    op.execute(
        """
        update business_date SET date = '2023-03-01';
        """
    )
    op.bulk_insert(
        pch_payment_check_instructions,
        [
            {
                "operator_id": "T-902",
                "payment_no": "PM-0000003",
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-03-10 請求書確認INFO:
    op.execute(
        """
        update business_date SET date = '2023-03-10';
        """
    )
    op.bulk_insert(
        pch_payment_check_instructions,
        [
            {
                "operator_id": "T-901",
                "payment_no": "PM-0000002",
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-03-11 請求書送付INFO:
    op.execute(
        """
        update business_date SET date = '2023-03-11';
        """
    )
    op.bulk_insert(
        sel_sending_bill_instructions,
        [
            {
                "operator_id": "T-901",
                "billing_no": "BL-0000002",
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-03-20 支払INFO:
    op.execute(
        """
        update business_date SET date = '2023-03-20';
        """
    )
    op.bulk_insert(
        pch_payment_instructions,
        [
            {
                "operator_id": "T-901",
                "payment_no": "PM-0000001",
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-03-21 入金INFO:
    op.execute(
        """
        update business_date SET date = '2023-03-21';
        """
    )
    op.bulk_insert(
        sel_deposit_instructions,
        [
            {
                "operator_id": "T-901",
                "costomer_id": "S001",
                "deposit_amount": 43000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-04-10 支払INFO:
    op.execute(
        """
        update business_date SET date = '2023-04-10';
        """
    )
    op.bulk_insert(
        pch_payment_instructions,
        [
            {
                "operator_id": "T-902",
                "payment_no": "PM-0000003",
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-04-15 入金INFO:
    op.execute(
        """
        update business_date SET date = '2023-04-15';
        """
    )
    op.bulk_insert(
        sel_deposit_instructions,
        [
            {
                "operator_id": "T-901",
                "costomer_id": "C001",
                "deposit_amount": 30000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-04-19 入金INFO:
    op.execute(
        """
        update business_date SET date = '2023-04-19';
        """
    )
    op.bulk_insert(
        sel_deposit_instructions,
        [
            {
                "operator_id": "T-901",
                "costomer_id": "C001",
                "deposit_amount": 48000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-05-13 支払INFO:
    op.execute(
        """
        update business_date SET date = '2023-05-13';
        """
    )
    op.bulk_insert(
        pch_payment_instructions,
        [
            {
                "operator_id": "T-901",
                "payment_no": "PM-0000002",
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-10-10 発注 INFO:
    op.execute(
        """
        update business_date SET date = '2023-10-10';
        """
    )
    op.bulk_insert(
        pch_orderings,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S001",
            },
        ],
    )
    op.bulk_insert(
        pch_ordering_details,
        [
            {
                "ordering_no": "PO-0000004",
                "product_id": "S001-00002",
                "purchase_quantity": 1,
                "purchase_unit_price": 12000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-10-20 入荷(mainに直接入荷:検品を省略) INFO:
    op.execute(
        """
        update business_date SET date = '2023-10-20';
        """
    )
    op.bulk_insert(
        pch_wearhousings,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S001",
            },
        ],
    )
    op.bulk_insert(
        pch_wearhousing_details,
        [
            {
                "wearhousing_no": "WH-0000005",
                "order_detail_no": 6,
                "wearhousing_quantity": 1,
                "wearhousing_unit_price": 12000.0,
                "site_type": SiteType.main,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-11-06 請求書確認INFO:
    op.execute(
        """
        update business_date SET date = '2023-11-06';
        """
    )
    op.bulk_insert(
        pch_payment_check_instructions,
        [
            {
                "operator_id": "T-901",
                "payment_no": "PM-0000004",
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-11-21 予約受注 INFO:
    op.execute(
        """
        update business_date SET date = '2023-11-21';
        """
    )
    op.bulk_insert(
        sel_receivings,
        [
            {
                "operator_id": "T-901",
                "costomer_id": "C001",
            },
        ],
    )
    op.bulk_insert(
        sel_receiving_details,
        [
            {
                "receiving_no": "RO-0000003",
                "product_id": "S001-00002",
                "receive_quantity": 3,
                "selling_unit_price": 30000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-11-23 受注キャンセル INFO:
    op.execute(
        """
        update business_date SET date = '2023-11-23';
        """
    )
    op.bulk_insert(
        sel_receive_cancel_instructions,
        [
            {
                "operator_id": "T-901",
                "cancel_reason": "顧客要望",
                "receive_detail_no": 3,
                "calcel_quantity": 1,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-11-25 発注 INFO:
    op.execute(
        """
        update business_date SET date = '2023-11-25';
        """
    )
    op.bulk_insert(
        pch_orderings,
        [
            {
                "operator_id": "T-902",
                "supplier_id": "S001",
                "note": "代理発注(T-901)",
            },
        ],
    )
    op.bulk_insert(
        pch_ordering_details,
        [
            {
                "ordering_no": "PO-0000005",
                "product_id": "S001-00001",
                "purchase_quantity": 5,
                "purchase_unit_price": 10000.0,
            },
            {
                "ordering_no": "PO-0000005",
                "product_id": "S001-00002",
                "purchase_quantity": 2,
                "purchase_unit_price": 11000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-11-27 発注納期変更 INFO:
    op.execute(
        """
        update business_date SET date = '2023-11-27';
        """
    )
    op.bulk_insert(
        pch_arrival_date_instructions,
        [
            {
                "operator_id": "T-901",
                "change_reason": "輸送業者都合",
                "order_detail_no": 7,
                "arrival_date": date(2023, 12, 12),
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-12-05 入荷 INFO:
    op.execute(
        """
        update business_date SET date = '2023-12-05';
        """
    )
    op.bulk_insert(
        pch_wearhousings,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S001",
            },
        ],
    )
    op.bulk_insert(
        pch_wearhousing_details,
        [
            {
                "wearhousing_no": "WH-0000006",
                "order_detail_no": 8,
                "wearhousing_quantity": 2,
                "wearhousing_unit_price": 10000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-12-06 検品 INFO:
    op.execute(
        """
        update business_date SET date = '2023-12-06';
        """
    )
    op.bulk_insert(
        inv_moving_instructions,
        [
            {
                "operator_id": "T-902",
                "instruction_cause": "検品（異常なし）",
                "site_type_from": SiteType.inspect_product,
                "site_type_to": SiteType.main,
                "product_id": "S001-00002",
                "quantity": 2,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-12-12 入荷/検品 INFO:
    op.execute(
        """
        update business_date SET date = '2023-12-12';
        """
    )
    # 入荷
    op.bulk_insert(
        pch_wearhousings,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S001",
            },
        ],
    )
    op.bulk_insert(
        pch_wearhousing_details,
        [
            {
                "wearhousing_no": "WH-0000007",
                "order_detail_no": 7,
                "wearhousing_quantity": 5,
                "wearhousing_unit_price": 11000.0,
            },
        ],
    )
    # 検品
    op.bulk_insert(
        inv_moving_instructions,
        [
            {
                "operator_id": "T-901",
                "instruction_cause": "検品（異常なし）",
                "site_type_from": SiteType.inspect_product,
                "site_type_to": SiteType.main,
                "product_id": "S001-00001",
                "quantity": 3,
            },
            {
                "operator_id": "T-901",
                "instruction_cause": "検品（不良品）",
                "site_type_from": SiteType.inspect_product,
                "site_type_to": SiteType.damaged_product,
                "product_id": "S001-00001",
                "quantity": 2,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-12-14 仕入返品/その他入出庫 INFO:
    op.execute(
        """
        update business_date SET date = '2023-12-14';
        """
    )
    # 仕入返品
    op.bulk_insert(
        pch_purchase_return_instructions,
        [
            {
                "operator_id": "T-901",
                "return_reason": "検品不良の対応",
                "wearhousing_detail_no": 8,
                "return_quantity": 1,
                "site_type": SiteType.damaged_product,
            }
        ],
    )
    # その他入出庫（廃棄）
    op.bulk_insert(
        inv_other_inventory_instructions,
        [
            {
                "operator_id": "T-901",
                "instruction_cause": "検品不良により廃棄、費用は雑費用として処理",
                "site_type": SiteType.damaged_product,
                "product_id": "S001-00001",
                "quantity": -1,
                "amount": -11000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 23-12-15 請求書確認INFO:
    op.execute(
        """
        update business_date SET date = '2023-12-15';
        """
    )
    op.bulk_insert(
        pch_payment_check_instructions,
        [
            {
                "operator_id": "T-901",
                "payment_no": "PM-0000005",
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-01-03 出荷 INFO:
    op.execute(
        """
        update business_date SET date = '2024-01-03';
        """
    )
    op.bulk_insert(
        sel_shippings,
        [
            {
                "operator_id": "T-901",
                "costomer_id": "C001",
            },
        ],
    )
    op.bulk_insert(
        sel_shipping_details,
        [
            {
                "shipping_no": "SP-0000003",
                "receive_detail_no": 3,
                "shipping_quantity": 2,
                "selling_unit_price": 30000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-01-05 発注 INFO:
    op.execute(
        """
        update business_date SET date = '2024-01-05';
        """
    )
    op.bulk_insert(
        pch_orderings,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S001",
            },
        ],
    )
    op.bulk_insert(
        pch_ordering_details,
        [
            {
                "ordering_no": "PO-0000006",
                "product_id": "S001-00002",
                "purchase_quantity": 3,
                "purchase_unit_price": 12000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-01-09 売上返品INFO:
    op.execute(
        """
        update business_date SET date = '2024-01-09';
        """
    )
    op.bulk_insert(
        sel_selling_return_instructions,
        [
            {
                "operator_id": "T-901",
                "return_reason": "クレーム返品",
                "costomer_id": "C001",
                "product_id": "S001-00002",
                "return_quantity": 1,
                "selling_unit_price": 27000.0,
                "cost_price": 10000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-01-11 請求書送付INFO:
    op.execute(
        """
        update business_date SET date = '2024-01-11';
        """
    )
    op.bulk_insert(
        sel_sending_bill_instructions,
        [
            {
                "operator_id": "T-901",
                "billing_no": "BL-0000003",
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-01-15 入荷(mainに直接入荷:検品を省略) INFO:
    op.execute(
        """
        update business_date SET date = '2024-01-15';
        """
    )
    op.bulk_insert(
        pch_wearhousings,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S001",
            },
        ],
    )
    op.bulk_insert(
        pch_wearhousing_details,
        [
            {
                "wearhousing_no": "WH-0000008",
                "order_detail_no": 9,
                "wearhousing_quantity": 3,
                "wearhousing_unit_price": 11500.0,
                "site_type": SiteType.main,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-01-18 その他入出庫 INFO:
    op.execute(
        """
        update business_date SET date = '2024-01-18';
        """
    )
    # その他入出庫（棚卸）
    op.bulk_insert(
        inv_other_inventory_instructions,
        [
            {
                "operator_id": "T-901",
                "instruction_cause": "棚卸結果反映、帳簿在庫増",
                "site_type": SiteType.main,
                "product_id": "S001-00002",
                "quantity": 1,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-01-20 即時受注/出荷 INFO:
    op.execute(
        """
        update business_date SET date = '2024-01-20';
        """
    )
    op.bulk_insert(
        sel_receivings,
        [
            {
                "operator_id": "T-902",
                "costomer_id": "C002",
                "note": "初回取引",
            },
        ],
    )
    op.bulk_insert(
        sel_receiving_details,
        [
            {
                "receiving_no": "RO-0000004",
                "product_id": "S001-00002",
                "receive_quantity": 1,
                "selling_unit_price": 32000.0,
            },
            {
                "receiving_no": "RO-0000004",
                "product_id": "S001-00001",
                "receive_quantity": 3,
                "selling_unit_price": 26000.0,
            },
        ],
    )
    op.bulk_insert(
        sel_shippings,
        [
            {
                "operator_id": "T-902",
                "costomer_id": "C002",
                "note": "初回取引",
            },
        ],
    )
    op.bulk_insert(
        sel_shipping_details,
        [
            {
                "shipping_no": "SP-0000004",
                "receive_detail_no": 4,
                "shipping_quantity": 1,
                "selling_unit_price": 32000.0,
            },
            {
                "shipping_no": "SP-0000004",
                "receive_detail_no": 5,
                "shipping_quantity": 3,
                "selling_unit_price": 26000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-01-25 売上返品INFO:
    op.execute(
        """
        update business_date SET date = '2024-01-25';
        """
    )
    op.bulk_insert(
        sel_selling_return_instructions,
        [
            {
                "operator_id": "T-902",
                "return_reason": "破損による返品",
                "shipping_detail_no": 4,
                "return_quantity": 1,
                "site_type": SiteType.damaged_product,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-02-01 請求書送付INFO:
    op.execute(
        """
        update business_date SET date = '2024-02-01';
        """
    )
    op.bulk_insert(
        sel_sending_bill_instructions,
        [
            {
                "operator_id": "T-902",
                "billing_no": "BL-0000004",
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-02-10 発注 INFO:
    op.execute(
        """
        update business_date SET date = '2024-02-10';
        """
    )
    op.bulk_insert(
        pch_orderings,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S001",
            },
        ],
    )
    op.bulk_insert(
        pch_ordering_details,
        [
            {
                "ordering_no": "PO-0000007",
                "product_id": "S001-00001",
                "purchase_quantity": 1,
                "purchase_unit_price": 11000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-02-11 その他売掛金取引INFO:
    op.execute(
        """
        update business_date SET date = '2024-02-11';
        """
    )
    op.bulk_insert(
        sel_other_selling_instructions,
        [
            {
                "operator_id": "T-901",
                "costomer_id": "C001",
                "instruction_cause": "延滞金請求(BL-0000003)",
                "transition_amount": 10000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-02-13 発注 INFO:
    op.execute(
        """
        update business_date SET date = '2024-02-13';
        """
    )
    op.bulk_insert(
        pch_orderings,
        [
            {
                "operator_id": "T-901",
                "supplier_id": "S001",
            },
        ],
    )
    op.bulk_insert(
        pch_ordering_details,
        [
            {
                "ordering_no": "PO-0000008",
                "product_id": "S001-00001",
                "purchase_quantity": 2,
                "purchase_unit_price": 9500.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-02-15 入金INFO:
    op.execute(
        """
        update business_date SET date = '2024-02-15';
        """
    )
    op.bulk_insert(
        sel_deposit_instructions,
        [
            {
                "operator_id": "T-901",
                "costomer_id": "C001",
                "deposit_amount": 30000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-02-16 受注 INFO:
    op.execute(
        """
        update business_date SET date = '2024-02-16';
        """
    )
    op.bulk_insert(
        sel_receivings,
        [
            {
                "operator_id": "T-902",
                "costomer_id": "C002",
            },
        ],
    )
    op.bulk_insert(
        sel_receiving_details,
        [
            {
                "receiving_no": "RO-0000005",
                "product_id": "S001-00001",
                "receive_quantity": 5,
                "selling_unit_price": 25000.0,
            },
            {
                "receiving_no": "RO-0000005",
                "product_id": "S001-00002",
                "receive_quantity": 3,
                "selling_unit_price": 30000.0,
            },
        ],
    )
    op.bulk_insert(
        sel_receivings,
        [
            {
                "operator_id": "T-901",
                "costomer_id": "C001",
                "shipping_priority": 1,
            },
        ],
    )
    op.bulk_insert(
        sel_receiving_details,
        [
            {
                "receiving_no": "RO-0000006",
                "product_id": "S001-00001",
                "receive_quantity": 8,
                "selling_unit_price": 28000.0,
            },
            {
                "receiving_no": "RO-0000006",
                "product_id": "S002-00001",
                "receive_quantity": 6,
                "selling_unit_price": 33000.0,
            },
            {
                "receiving_no": "RO-0000006",
                "product_id": "S001-00003",
                "receive_quantity": 1,
                "selling_unit_price": 33000.0,
            },
            {
                "receiving_no": "RO-0000006",
                "product_id": "S005-00001",
                "receive_quantity": 3,
                "selling_unit_price": 5000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-02-18 出荷 INFO:
    op.execute(
        """
        update business_date SET date = '2024-02-18';
        """
    )
    op.bulk_insert(
        sel_shippings,
        [
            {
                "operator_id": "T-901",
                "costomer_id": "C001",
            },
        ],
    )
    op.bulk_insert(
        sel_shipping_details,
        [
            {
                "shipping_no": "SP-0000005",
                "receive_detail_no": 9,
                "shipping_quantity": 2,
                "selling_unit_price": 35000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    # 24-03-01 入金INFO:
    op.execute(
        """
        update business_date SET date = '2024-03-01';
        """
    )
    op.bulk_insert(
        sel_deposit_instructions,
        [
            {
                "operator_id": "T-902",
                "costomer_id": "C002",
                "deposit_amount": 90000.0,
            },
        ],
    )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    pass


def downgrade() -> None:
    pass
