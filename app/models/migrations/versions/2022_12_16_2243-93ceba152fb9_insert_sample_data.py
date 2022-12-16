"""insert sample data

Revision ID: 93ceba152fb9
Revises: 4ed3531f2a5e
Create Date: 2022-12-16 22:43:54.629985

"""
from datetime import date

from alembic import op
from sqlalchemy import MetaData, Table

from app.models.segment_values import StockTransitionType

# revision identifiers, used by Alembic.
revision = "93ceba152fb9"
down_revision = "4ed3531f2a5e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    DUMMY_ORDER_NO = "dummy"
    DUMMY_DATE = date(2000, 1, 1)

    meta = MetaData(bind=op.get_bind())
    # 受注登録FIXME:在庫変動予定
    meta.reflect(schema="inventory")
    t_transition_estimates = Table("inventory.transition_estimates", meta)
    op.bulk_insert(
        t_transition_estimates,
        [
            {
                "transaction_date": date(2023, 1, 11),
                "site_id": "N2",
                "product_id": "S001-00003",
                "transaction_quantity": -5,
                "transaction_amount": 0.0,
                "transition_type": StockTransitionType.selling,
                "transaction_no": 801,
            },
            {
                "transaction_date": date(2023, 1, 11),
                "site_id": "N2",
                "product_id": "S001-00002",
                "transaction_quantity": -2,
                "transaction_amount": 0.0,
                "transition_type": StockTransitionType.selling,
                "transaction_no": 802,
            },
        ],
    )

    # 発注登録
    meta = MetaData(bind=op.get_bind())
    meta.reflect(schema="purchase")
    t_orderings = Table("purchase.orderings", meta)
    t_ordering_details = Table("purchase.ordering_details", meta)
    op.bulk_insert(
        t_orderings,
        [
            {
                "ordering_no": DUMMY_ORDER_NO,
                "order_date": date(2023, 1, 20),
                "supplier_id": "S001",
                "site_id": "E3",
                "purchase_pic": "T-901",
            },
            {
                "ordering_no": DUMMY_ORDER_NO,
                "order_date": date(2023, 1, 22),
                "supplier_id": "S002",
                "site_id": "E3",
                "purchase_pic": "T-902",
            },
        ],
    )
    op.bulk_insert(
        t_ordering_details,
        [
            {
                "ordering_no": "PO-0000001",
                "product_id": "S001-00002",
                "purchase_quantity": 3,
                "unit_purchase_price": 12000.0,
                "estimate_arrival_date": DUMMY_DATE,
            },
            {
                "ordering_no": "PO-0000001",
                "product_id": "S001-00003",
                "purchase_quantity": 2,
                "unit_purchase_price": 8000.0,
                "estimate_arrival_date": DUMMY_DATE,
            },
            {
                "ordering_no": "PO-0000002",
                "product_id": "S002-00001",
                "purchase_quantity": 5,
                "unit_purchase_price": 20000.0,
                "estimate_arrival_date": DUMMY_DATE,
            },
        ],
    )

    # 入庫・在庫移動・出庫
    meta.reflect(schema="inventory")
    t_transition_histories = Table("inventory.transition_histories", meta)
    # FIXME:在庫変動履歴
    t_moving_histories = Table("inventory.moving_histories", meta)
    # FIXME:在庫移動履歴
    op.bulk_insert(
        t_transition_histories,
        [
            {
                "transaction_date": date(2023, 10, 20),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": 1,
                "transaction_amount": 18000.0,
                "transition_type": StockTransitionType.purchase,
                "transition_reason": None,
                "transaction_no": 501,
            },
            {
                "transaction_date": date(2023, 12, 10),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": 2,
                "transaction_amount": 48000.0,
                "transition_type": StockTransitionType.purchase,
                "transition_reason": None,
                "transaction_no": 502,
            },
            {
                "transaction_date": date(2023, 12, 12),
                "site_id": "E3",
                "product_id": "S001-00001",
                "transaction_quantity": 5,
                "transaction_amount": 100000.0,
                "transition_type": StockTransitionType.purchase,
                "transition_reason": None,
                "transaction_no": 503,
            },
        ],  # FIXME:入庫
    )
    op.bulk_insert(
        t_moving_histories,
        [
            {
                "transaction_date": date(2023, 12, 12),
                "site_id_from": "E3",
                "site_id_to": "E4",
                "product_id": "S001-00001",
                "moving_quantity": 2,
            },
            {
                "transaction_date": date(2023, 12, 12),
                "site_id_from": "E3",
                "site_id_to": "N1",
                "product_id": "S001-00001",
                "moving_quantity": 3,
            },
        ],  # FIXME:在庫移動
    )
    op.bulk_insert(
        t_transition_histories,
        [
            {
                "transaction_date": date(2023, 12, 14),
                "site_id": "E4",
                "product_id": "S001-00001",
                "transaction_quantity": -1,
                "transaction_amount": -20000.0,
                "transition_type": StockTransitionType.ordering_return,
                "transition_reason": None,
                "transaction_no": 504,
            },
            {
                "transaction_date": date(2024, 1, 5),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": -2,
                "transaction_amount": -40000.0,
                "transition_type": StockTransitionType.selling,
                "transition_reason": None,
                "transaction_no": 505,
            },
            {
                "transaction_date": date(2024, 1, 10),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": 3,
                "transaction_amount": 65000.0,
                "transition_type": StockTransitionType.purchase,
                "transition_reason": None,
                "transaction_no": 506,
            },
            {
                "transaction_date": date(2024, 1, 18),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": 1,
                "transaction_amount": 0.0,
                "transition_type": StockTransitionType.other_transition,
                "transition_reason": "棚卸の結果、帳簿在庫増",
                "transaction_no": 507,
            },
            {
                "transaction_date": date(2024, 1, 20),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": -1,
                "transaction_amount": -20000.0,
                "transition_type": StockTransitionType.selling,
                "transition_reason": None,
                "transaction_no": 508,
            },
        ],
    )
    op.bulk_insert(
        t_moving_histories,
        [
            {
                "transaction_date": date(2024, 1, 22),
                "site_id_from": "N1",
                "site_id_to": "E2",
                "product_id": "S001-00001",
                "moving_quantity": 2,
            },
        ],  # FIXME:販売待ち
    )
    op.bulk_insert(
        t_transition_histories,
        [
            {
                "transaction_date": date(2024, 1, 25),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": 1,
                "transaction_amount": 20000.0,
                "transition_type": StockTransitionType.sales_return,
                "transition_reason": None,
                "transaction_no": 509,
            },
            {
                "transaction_date": date(2024, 1, 30),
                "site_id": "E2",
                "product_id": "S001-00001",
                "transaction_quantity": -1,
                "transaction_amount": -20000.0,
                "transition_type": StockTransitionType.selling,
                "transition_reason": None,
                "transaction_no": 510,
            },
        ],
    )
    pass


def downgrade() -> None:
    pass
