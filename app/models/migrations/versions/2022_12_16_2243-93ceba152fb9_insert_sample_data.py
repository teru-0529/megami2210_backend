"""insert sample data

Revision ID: 93ceba152fb9
Revises: 4ed3531f2a5e
Create Date: 2022-12-16 22:43:54.629985

"""
from datetime import date

from alembic import op
from sqlalchemy import MetaData, Table

from app.models.segment_values import StockTransitionType, SiteType

# revision identifiers, used by Alembic.
revision = "93ceba152fb9"
down_revision = "4ed3531f2a5e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    DUMMY_AMOUNT = 0.0

    meta = MetaData(bind=op.get_bind())
    meta.reflect(schema="inventory")
    # FIXME:在庫変動予定(受注-出荷予定)
    inv_transition_estimates = Table("inventory.transition_estimates", meta)
    # FIXME:在庫変動履歴(出荷、売上返品)
    inv_transition_histories = Table("inventory.transition_histories", meta)
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
    pch_purchase_return_instructions = Table(
        "purchase.purchase_return_instructions", meta
    )
    pch_other_purchase_instructions = Table(
        "purchase.other_purchase_instructions", meta
    )

    # 受注-出荷予定FIXME:在庫変動予定WARNING:
    op.bulk_insert(
        inv_transition_estimates,
        [
            {
                "transaction_date": date(2023, 1, 11),
                "site_type": SiteType.main,
                "product_id": "S001-00003",
                "transaction_quantity": -5,
                "transaction_amount": DUMMY_AMOUNT,
                "transition_type": StockTransitionType.selling,
                "transaction_no": 801,
            },
            {
                "transaction_date": date(2023, 1, 11),
                "site_type": SiteType.main,
                "product_id": "S001-00002",
                "transaction_quantity": -2,
                "transaction_amount": DUMMY_AMOUNT,
                "transition_type": StockTransitionType.selling,
                "transaction_no": 802,
            },
        ],
    )

    # 発注
    op.bulk_insert(
        pch_orderings,
        [
            {
                "order_date": date(2023, 1, 20),
                "supplier_id": "S001",
                "purchase_pic": "T-901",
            },
            {
                "order_date": date(2023, 1, 22),
                "supplier_id": "S002",
                "purchase_pic": "T-902",
            },
            {
                "order_date": date(2023, 1, 23),
                "supplier_id": "S002",
                "purchase_pic": "T-902",
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
            {
                "ordering_no": "PO-0000002",
                "product_id": "S002-00001",
                "purchase_quantity": 5,
                "purchase_unit_price": 19000.0,
            },
            {
                "ordering_no": "PO-0000003",
                "product_id": "S002-00001",
                "purchase_quantity": 2,
                "purchase_unit_price": 22000.0,
            },
        ],
    )

    # 発注納期変更
    op.bulk_insert(
        pch_arrival_date_instructions,
        [
            {
                "instruction_date": date(2023, 1, 24),
                "instruction_pic": "T-902",
                "change_reason": "メーカー在庫なし",
                "ordering_detail_no": 1,
                "arrival_date": date(2023, 2, 5),
            },
        ],
    )

    # 発注キャンセル
    op.bulk_insert(
        pch_order_cancel_instructions,
        [
            {
                "instruction_date": date(2023, 1, 25),
                "instruction_pic": "T-902",
                "cancel_reason": "護発注",
                "ordering_detail_no": 2,
                "calcel_quantity": 2,
            },
            {
                "instruction_date": date(2023, 1, 28),
                "instruction_pic": "T-902",
                "cancel_reason": "受注キャンセルの対応",
                "ordering_detail_no": 3,
                "calcel_quantity": 1,
            },
        ],
    )

    # 入荷(mainに直接入荷:検品を省略)
    op.bulk_insert(
        pch_wearhousings,
        [
            {
                "wearhousing_date": date(2023, 1, 30),
                "supplier_id": "S001",
                "wearhousing_pic": "T-901",
            },
            {
                "wearhousing_date": date(2023, 2, 6),
                "supplier_id": "S001",
                "wearhousing_pic": "T-901",
            },
            {
                "wearhousing_date": date(2023, 2, 6),
                "supplier_id": "S002",
                "wearhousing_pic": "T-902",
            },
            {
                "wearhousing_date": date(2023, 2, 7),
                "supplier_id": "S002",
                "wearhousing_pic": "T-902",
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
            {
                "wearhousing_no": "WH-0000004",
                "order_detail_no": 4,
                "wearhousing_quantity": 2,
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
    # 仕入返品
    op.bulk_insert(
        pch_purchase_return_instructions,
        [
            {
                "instruction_date": date(2023, 2, 8),
                "instruction_pic": "T-902",
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
                "instruction_date": date(2023, 2, 8),
                "instruction_pic": "T-901",
                "supplier_id": "S001",
                "transition_reason": "輸送費追加計上",
                "transition_amount": 2800.0,
            },
            {
                "instruction_date": date(2023, 2, 9),
                "instruction_pic": "T-901",
                "supplier_id": "S002",
                "transition_reason": "誤請求返金(2022年10月分)",
                "transition_amount": -10000.0,
            },
        ],
    )

    # 請求書の確認-支払
    op.execute(
        """
        UPDATE purchase.payments
        SET payment_check_datetime = '2023-2-8', payment_check_pic = 'T-901'
        WHERE payment_no = 'PM-0000001';

        UPDATE purchase.payments
        SET payment_check_datetime = '2023-3-1', payment_check_pic = 'T-902'
        WHERE payment_no = 'PM-0000003';

        UPDATE purchase.payments
        SET payment_check_datetime = '2023-3-10', payment_check_pic = 'T-901'
        WHERE payment_no = 'PM-0000002';
        """
    )
    op.bulk_insert(
        pch_payment_instructions,
        [
            {
                "instruction_date": date(2023, 3, 20),
                "instruction_pic": "T-901",
                "payment_no": "PM-0000001",
            },
            {
                "instruction_date": date(2023, 4, 10),
                "instruction_pic": "T-902",
                "payment_no": "PM-0000003",
            },
            {
                "instruction_date": date(2023, 5, 13),
                "instruction_pic": "T-901",
                "payment_no": "PM-0000002",
            },
        ],
    )

    # 発注-入荷(mainに直接入荷:検品を省略)
    op.bulk_insert(
        pch_orderings,
        [
            {
                "order_date": date(2023, 10, 10),
                "supplier_id": "S001",
                "purchase_pic": "T-901",
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
    op.bulk_insert(
        pch_wearhousings,
        [
            {
                "wearhousing_date": date(2023, 10, 20),
                "supplier_id": "S001",
                "wearhousing_pic": "T-901",
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

    # 請求書の確認
    op.execute(
        """
        UPDATE purchase.payments
        SET payment_check_datetime = '2023-11-6', payment_check_pic = 'T-901'
        WHERE payment_no = 'PM-0000004';
        """
    )

    # 発注
    op.bulk_insert(
        pch_orderings,
        [
            {
                "order_date": date(2023, 11, 25),
                "supplier_id": "S001",
                "purchase_pic": "T-901",
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

    # 予定納期日の変更
    op.execute(
        """
        UPDATE purchase.ordering_details SET estimate_arrival_date = '2023-12-12' WHERE detail_no = 7;
        """
    )

    # 入荷
    op.bulk_insert(
        pch_wearhousings,
        [
            {
                "wearhousing_date": date(2023, 12, 5),
                "supplier_id": "S001",
                "wearhousing_pic": "T-901",
            },
            {
                "wearhousing_date": date(2023, 12, 12),
                "supplier_id": "S001",
                "wearhousing_pic": "T-901",
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
            {
                "wearhousing_no": "WH-0000007",
                "order_detail_no": 7,
                "wearhousing_quantity": 5,
                "wearhousing_unit_price": 11000.0,
            },
        ],
    )

    # 在庫移動（検品）
    op.bulk_insert(
        inv_moving_instructions,
        [
            {
                "instruction_date": date(2023, 12, 6),
                "instruction_pic": "T-902",
                "moving_reason": "検品（異常なし）",
                "site_type_from": SiteType.inspect_product,
                "site_type_to": SiteType.main,
                "product_id": "S001-00002",
                "moving_quantity": 2,
            },
            {
                "instruction_date": date(2023, 12, 12),
                "instruction_pic": "T-901",
                "moving_reason": "検品（不良品）",
                "site_type_from": SiteType.inspect_product,
                "site_type_to": SiteType.damaged_product,
                "product_id": "S001-00001",
                "moving_quantity": 2,
            },
            {
                "instruction_date": date(2023, 12, 12),
                "instruction_pic": "T-901",
                "moving_reason": "検品（異常なし）",
                "site_type_from": SiteType.inspect_product,
                "site_type_to": SiteType.main,
                "product_id": "S001-00001",
                "moving_quantity": 3,
            },
        ],
    )

    # 仕入返品
    op.bulk_insert(
        pch_purchase_return_instructions,
        [
            {
                "instruction_date": date(2023, 12, 14),
                "instruction_pic": "T-901",
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
                "instruction_date": date(2023, 12, 14),
                "instruction_pic": "T-901",
                "transition_reason": "検品不良により廃棄、費用は雑費用として処理",
                "site_type": SiteType.damaged_product,
                "product_id": "S001-00001",
                "quantity": -1,
                "amount": -11000.0,
            },
        ],
    )

    # 請求書の確認
    op.execute(
        """
        UPDATE purchase.payments
        SET payment_check_datetime = '2023-12-14', payment_check_pic = 'T-901'
        WHERE payment_no = 'PM-0000005';
        """
    )

    # 販売FIXME:
    op.bulk_insert(
        inv_transition_histories,
        [
            {
                "transaction_date": date(2024, 1, 3),
                "site_type": SiteType.main,
                "product_id": "S001-00002",
                "transaction_quantity": -2,
                "transaction_amount": DUMMY_AMOUNT,
                "transition_type": StockTransitionType.selling,
                "transaction_no": 505,
            },
        ],
    )

    # 発注-入荷(mainに直接入荷:検品を省略)
    op.bulk_insert(
        pch_orderings,
        [
            {
                "order_date": date(2024, 1, 5),
                "supplier_id": "S001",
                "purchase_pic": "T-901",
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
    op.bulk_insert(
        pch_wearhousings,
        [
            {
                "wearhousing_date": date(2024, 1, 15),
                "supplier_id": "S001",
                "wearhousing_pic": "T-901",
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

    # その他入出庫（棚卸）
    op.bulk_insert(
        inv_other_inventory_instructions,
        [
            {
                "instruction_date": date(2024, 1, 18),
                "instruction_pic": "T-901",
                "transition_reason": "棚卸結果反映、帳簿在庫増",
                "site_type": SiteType.main,
                "product_id": "S001-00002",
                "quantity": 1,
            },
        ],
    )

    # 即時販売FIXME:
    op.bulk_insert(
        inv_transition_histories,
        [
            {
                "transaction_date": date(2024, 1, 20),
                "site_type": SiteType.main,
                "product_id": "S001-00002",
                "transaction_quantity": -1,
                "transaction_amount": DUMMY_AMOUNT,
                "transition_type": StockTransitionType.selling,
                "transaction_no": 508,
            },
        ],
    )

    # # 在庫移動（予約商品確保）
    # op.bulk_insert(
    #     inv_moving_instructions,
    #     [
    #         {
    #             "instruction_date": date(2024, 1, 22),
    #             "instruction_pic": "T-901",
    #             "moving_reason": "予約販売商品確保",
    #             "site_id_from": "N1",
    #             "site_id_to": "E2",
    #             "product_id": "S001-00001",
    #             "moving_quantity": 2,
    #         },
    #     ],
    # )

    # 売上返品FIXME:
    op.bulk_insert(
        inv_transition_histories,
        [
            {
                "transaction_date": date(2024, 1, 25),
                "site_type": SiteType.main,
                "product_id": "S001-00002",
                "transaction_quantity": 1,
                "transaction_amount": 20000.0,
                "transition_type": StockTransitionType.sales_return,
                "transaction_no": 509,
            },
        ],
    )

    # 予約販売FIXME:
    op.bulk_insert(
        inv_transition_histories,
        [
            {
                "transaction_date": date(2024, 1, 30),
                "site_type": SiteType.main,
                "product_id": "S001-00001",
                "transaction_quantity": -1,
                "transaction_amount": DUMMY_AMOUNT,
                "transition_type": StockTransitionType.selling,
                "transaction_no": 510,
            },
        ],
    )

    # 発注
    op.bulk_insert(
        pch_orderings,
        [
            {
                "order_date": date(2024, 2, 10),
                "supplier_id": "S001",
                "purchase_pic": "T-901",
            },
            {
                "order_date": date(2024, 2, 13),
                "supplier_id": "S001",
                "purchase_pic": "T-901",
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
            {
                "ordering_no": "PO-0000008",
                "product_id": "S001-00001",
                "purchase_quantity": 2,
                "purchase_unit_price": 9500.0,
            },
        ],
    )
    pass


def downgrade() -> None:
    pass
