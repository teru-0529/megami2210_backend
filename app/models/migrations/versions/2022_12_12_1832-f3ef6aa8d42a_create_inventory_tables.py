"""create inventory tables

Revision ID: f3ef6aa8d42a
Revises: 139619b8894b
Create Date: 2022-12-12 18:32:51.092614

"""
from datetime import date

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Table

from app.models.migrations.util import timestamps
from app.models.segment_values import StockTransitionType

# revision identifiers, used by Alembic.
revision = "f3ef6aa8d42a"
down_revision = "139619b8894b"
branch_labels = None
depends_on = None

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_transition_histories_table() -> Table:
    transition_histories_table = op.create_table(
        "transition_histories",
        sa.Column("no", sa.Integer, primary_key=True, comment="受払履歴NO"),
        sa.Column("transaction_date", sa.Date, nullable=False, comment="取引日"),
        sa.Column("site_id", sa.String(2), nullable=False, comment="倉庫ID"),
        sa.Column("product_id", sa.String(10), nullable=False, comment="当社商品ID"),
        sa.Column("transaction_quantity", sa.Integer, nullable=False, comment="取引数"),
        sa.Column("transaction_amount", sa.Numeric, nullable=False, comment="取引金額"),
        sa.Column(
            "transition_type",
            sa.Enum(
                *StockTransitionType.list(), name="transition_type", schema="inventory"
            ),
            nullable=False,
            index=True,
            comment="在庫変動区分",
        ),
        sa.Column("transition_reason", sa.Text, nullable=True, comment="在庫変動理由"),
        sa.Column(
            "transaction_no",
            sa.Integer,
            nullable=False,
            comment="取引管理NO",
        ),
        *timestamps(),
        schema="inventory",
    )
    # 「在庫変動区分」が「その他取引」の場合は、「在庫変動理由」が必須、「その他取引」以外の場合は「在庫変動理由」を指定してはいけない
    ck_transition_reason: str = """
    CASE
        WHEN transition_type='OTHER_TRANSITION' AND transition_reason IS NULL THEN FALSE
        WHEN transition_type!='OTHER_TRANSITION' AND transition_reason IS NOT NULL THEN FALSE
        ELSE TRUE
    END
    """
    op.create_check_constraint(
        "ck_transition_reason",
        "transition_histories",
        ck_transition_reason,
        schema="inventory",
    )
    op.create_foreign_key(
        "fk_product_id",
        "transition_histories",
        "products",
        ["product_id"],
        ["product_id"],
        ondelete="RESTRICT",
        source_schema="inventory",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_site_id",
        "transition_histories",
        "sites",
        ["site_id"],
        ["site_id"],
        ondelete="RESTRICT",
        source_schema="inventory",
        referent_schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER transition_histories_modified
            BEFORE UPDATE
            ON inventory.transition_histories
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    return transition_histories_table


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_transition_estimates_table() -> None:
    transition_estimates_table = op.create_table(
        "transition_estimates",
        sa.Column("no", sa.Integer, primary_key=True, comment="受払予定NO"),
        sa.Column("transaction_date", sa.Date, nullable=False, comment="取引予定日"),
        sa.Column("site_id", sa.String(2), nullable=False, comment="倉庫ID"),
        sa.Column("product_id", sa.String(10), nullable=False, comment="当社商品ID"),
        sa.Column("transaction_quantity", sa.Integer, nullable=False, comment="取引予定数"),
        sa.Column("transaction_amount", sa.Numeric, nullable=False, comment="取引予定金額"),
        sa.Column(
            "transition_type",
            sa.Enum(
                *StockTransitionType.list(), name="transition_type", schema="inventory"
            ),
            nullable=False,
            index=True,
            comment="在庫変動区分",
        ),
        sa.Column(
            "transaction_no",
            sa.Integer,
            nullable=False,
            comment="取引管理NO",
        ),
        *timestamps(),
        schema="inventory",
    )

    op.create_foreign_key(
        "fk_product_id",
        "transition_estimates",
        "products",
        ["product_id"],
        ["product_id"],
        ondelete="RESTRICT",
        source_schema="inventory",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_site_id",
        "transition_estimates",
        "sites",
        ["site_id"],
        ["site_id"],
        ondelete="RESTRICT",
        source_schema="inventory",
        referent_schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER transition_estimates_modified
            BEFORE UPDATE
            ON inventory.transition_estimates
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    op.bulk_insert(
        transition_estimates_table,
        [
            {
                "transaction_date": date(2023, 8, 10),
                "site_id": "N2",
                "product_id": "S001-00003",
                "transaction_quantity": 5,
                "transaction_amount": 5000.0,
                "transition_type": StockTransitionType.purchase,
                "transaction_no": 801,
            },
            {
                "transaction_date": date(2023, 8, 11),
                "site_id": "N2",
                "product_id": "S001-00003",
                "transaction_quantity": -5,
                "transaction_amount": 0.0,
                "transition_type": StockTransitionType.selling,
                "transaction_no": 802,
            },
        ],
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_moving_histories_table() -> Table:
    moving_histories_table = op.create_table(
        "moving_histories",
        sa.Column("no", sa.Integer, primary_key=True, comment="在庫移動NO"),
        sa.Column("transaction_date", sa.Date, nullable=False, comment="取引日"),
        sa.Column("site_id_from", sa.String(2), nullable=False, comment="移動元倉庫ID"),
        sa.Column("site_id_to", sa.String(2), nullable=False, comment="移動先倉庫ID"),
        sa.Column("product_id", sa.String(10), nullable=False, comment="当社商品ID"),
        sa.Column("moving_quantity", sa.Integer, nullable=False, comment="移動数"),
        *timestamps(),
        schema="inventory",
    )

    op.create_check_constraint(
        "ck_site_id",
        "moving_histories",
        "site_id_from != site_id_to",
        schema="inventory",
    )
    op.create_foreign_key(
        "fk_product_id",
        "moving_histories",
        "products",
        ["product_id"],
        ["product_id"],
        ondelete="RESTRICT",
        source_schema="inventory",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_site_id_from",
        "moving_histories",
        "sites",
        ["site_id_from"],
        ["site_id"],
        ondelete="RESTRICT",
        source_schema="inventory",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_site_id_to",
        "moving_histories",
        "sites",
        ["site_id_to"],
        ["site_id"],
        ondelete="RESTRICT",
        source_schema="inventory",
        referent_schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER moving_histories_modified
            BEFORE UPDATE
            ON inventory.moving_histories
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 在庫変動履歴の自動作成
    op.execute(
        """
        CREATE FUNCTION inventory.set_transition_histories_1st() RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO inventory.transition_histories
            VALUES (default, NEW.transaction_date, NEW.site_id_from, NEW.product_id, - NEW.moving_quantity , 0.0, 'MOVEMENT_SHIPPING', null, NEW.no);

            INSERT INTO inventory.transition_histories
            VALUES (default, NEW.transaction_date, NEW.site_id_to, NEW.product_id, NEW.moving_quantity , 0.0, 'MOVEMENT_WAREHOUSING', null, NEW.no);
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_moving_history
            BEFORE INSERT
            ON inventory.moving_histories
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.set_transition_histories_1st();
        """
    )

    return moving_histories_table


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_monthry_summaries_every_site_table() -> Table:
    op.create_table(
        "monthry_summaries_every_site",
        sa.Column("year_month", sa.String(6), primary_key=True, comment="取引年月"),
        sa.Column("site_id", sa.String(2), primary_key=True, comment="倉庫ID"),
        sa.Column("product_id", sa.String(10), primary_key=True, comment="当社商品ID"),
        sa.Column("init_quantity", sa.Integer, nullable=False, comment="月初在庫数"),
        sa.Column("warehousing_quantity", sa.Integer, nullable=False, comment="入庫数"),
        sa.Column("shipping_quantity", sa.Integer, nullable=False, comment="出庫数"),
        *timestamps(),
        schema="inventory",
    )

    op.create_check_constraint(
        "ck_quantity",
        "monthry_summaries_every_site",
        "init_quantity + warehousing_quantity - shipping_quantity >= 0",
        schema="inventory",
    )
    op.execute(
        """
        CREATE TRIGGER monthry_summaries_every_site_modified
            BEFORE UPDATE
            ON inventory.monthry_summaries_every_site
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 月次在庫サマリーテーブルの自動作成
    op.execute(
        """
        CREATE FUNCTION inventory.set_monthry_summaries_every_site() RETURNS TRIGGER AS $$
        DECLARE
            yyyymm character(6);
            t_site_id character(2);
            t_product_id character(10);
            t_init_quantity integer;
            t_warehousing_quantity integer;
            t_shipping_quantity integer;

            t_quantity integer;
            t_amount numeric;
            t_shipping numeric;

            recent_rec RECORD;
            last_rec RECORD;
        BEGIN
            yyyymm:=to_char(NEW.transaction_date, 'YYYYMM');
            t_site_id:=NEW.site_id;
            t_product_id:=NEW.product_id;

            SELECT * INTO recent_rec
                FROM inventory.monthry_summaries_every_site
                WHERE year_month = yyyymm AND site_id = t_site_id AND product_id = t_product_id
                FOR UPDATE;

            IF recent_rec IS NULL THEN
                SELECT * INTO last_rec
                    FROM inventory.monthry_summaries_every_site
                    WHERE site_id = t_site_id AND product_id = t_product_id
                    ORDER BY year_month DESC
                    LIMIT 1;

                IF last_rec IS NULL THEN
                    t_init_quantity:=0;
                ELSE
                    t_init_quantity:=last_rec.init_quantity + last_rec.warehousing_quantity - last_rec.shipping_quantity;
                END IF;

                t_warehousing_quantity:=0;
                t_shipping_quantity:=0;
            ELSE
                t_init_quantity:=recent_rec.init_quantity;
                t_warehousing_quantity:=recent_rec.warehousing_quantity;
                t_shipping_quantity:=recent_rec.shipping_quantity;
            END IF;

            IF NEW.transition_type='MOVEMENT_SHIPPING' OR NEW.transition_type='SELLING' OR NEW.transition_type='ORDERING_RETURN' THEN
                t_shipping_quantity:=t_shipping_quantity - NEW.transaction_quantity;
            ELSE
                t_warehousing_quantity:=t_warehousing_quantity + NEW.transaction_quantity;
            END IF;

            IF recent_rec IS NULL THEN
                INSERT INTO inventory.monthry_summaries_every_site
                VALUES (
                    yyyymm, t_site_id, t_product_id, t_init_quantity, t_warehousing_quantity,
                    t_shipping_quantity
                );
            ELSE
                UPDATE inventory.monthry_summaries_every_site
                SET warehousing_quantity = t_warehousing_quantity,
                    shipping_quantity = t_shipping_quantity
                WHERE year_month = yyyymm AND site_id = t_site_id AND product_id = t_product_id;

            END IF;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_transition_history_1st
            BEFORE INSERT
            ON inventory.transition_histories
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.set_monthry_summaries_every_site();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_monthry_summaries_table() -> Table:
    op.create_table(
        "monthry_summaries",
        sa.Column("year_month", sa.String(6), primary_key=True, comment="取引年月"),
        sa.Column("product_id", sa.String(10), primary_key=True, comment="当社商品ID"),
        sa.Column("init_quantity", sa.Integer, nullable=False, comment="月初在庫数"),
        sa.Column("warehousing_quantity", sa.Integer, nullable=False, comment="入庫数"),
        sa.Column("shipping_quantity", sa.Integer, nullable=False, comment="出庫数"),
        sa.Column("init_amount", sa.Numeric, nullable=False, comment="月初在庫額"),
        sa.Column("warehousing_amount", sa.Numeric, nullable=False, comment="入庫金額"),
        sa.Column("shipping_amount", sa.Numeric, nullable=False, comment="出庫金額"),
        sa.Column("cost_price", sa.Numeric, nullable=False, comment="原価"),
        *timestamps(),
        schema="inventory",
    )

    op.create_check_constraint(
        "ck_quantity",
        "monthry_summaries",
        "init_quantity + warehousing_quantity - shipping_quantity >= 0",
        schema="inventory",
    )
    op.execute(
        """
        CREATE TRIGGER monthry_summaries_modified
            BEFORE UPDATE
            ON inventory.monthry_summaries
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 月次在庫サマリーテーブルの自動作成
    op.execute(
        """
        CREATE FUNCTION inventory.set_monthry_summaries() RETURNS TRIGGER AS $$
        DECLARE
            yyyymm character(6);
            t_product_id character(10);
            t_init_quantity integer;
            t_warehousing_quantity integer;
            t_shipping_quantity integer;
            t_init_amount numeric;
            t_warehousing_amount numeric;
            t_shipping_amount numeric;
            t_cost_price numeric;

            t_quantity integer;
            t_amount numeric;
            t_shipping numeric;

            recent_rec RECORD;
            last_rec RECORD;
        BEGIN
            yyyymm:=to_char(NEW.transaction_date, 'YYYYMM');
            t_product_id:=NEW.product_id;

            SELECT * INTO recent_rec
                FROM inventory.monthry_summaries
                WHERE year_month = yyyymm AND product_id = t_product_id
                FOR UPDATE;

            IF recent_rec IS NULL THEN
                SELECT * INTO last_rec
                    FROM inventory.monthry_summaries
                    WHERE product_id = t_product_id
                    ORDER BY year_month DESC
                    LIMIT 1;

                IF last_rec IS NULL THEN
                    t_init_quantity:=0;
                    t_init_amount:=0.00;
                    t_cost_price:=0.00;
                ELSE
                    t_init_quantity:=last_rec.init_quantity + last_rec.warehousing_quantity - last_rec.shipping_quantity;
                    t_init_amount:=last_rec.init_amount + last_rec.warehousing_amount - last_rec.shipping_amount;
                    IF t_init_quantity = 0 THEN
                        t_cost_price:=0.00;
                    ELSE
                        t_cost_price:=ROUND(t_init_amount / t_init_quantity, 2);

                    END IF;
                END IF;

                t_warehousing_quantity:=0;
                t_shipping_quantity:=0;
                t_warehousing_amount:=0.00;
                t_shipping_amount:=0.00;
            ELSE
                t_init_quantity:=recent_rec.init_quantity;
                t_warehousing_quantity:=recent_rec.warehousing_quantity;
                t_shipping_quantity:=recent_rec.shipping_quantity;
                t_init_amount:=recent_rec.init_amount;
                t_warehousing_amount:=recent_rec.warehousing_amount;
                t_shipping_amount:=recent_rec.shipping_amount;
                t_cost_price:=recent_rec.cost_price;
            END IF;

            IF NEW.transition_type='SELLING' OR NEW.transition_type='ORDERING_RETURN' THEN
                t_shipping_quantity:=t_shipping_quantity - NEW.transaction_quantity;
                t_shipping:=NEW.transaction_quantity * t_cost_price;
                IF t_shipping_amount - t_shipping < 0 THEN
                    t_shipping_amount:=0.0;
                ELSE
                    t_shipping_amount:=t_shipping_amount - t_shipping;
                END IF;
                NEW.transaction_amount:=t_shipping;

            ELSEIF NEW.transition_type='PURCHASE' OR NEW.transition_type='SALES_RETURN' OR NEW.transition_type='OTHER_TRANSITION' THEN
                t_warehousing_quantity:=t_warehousing_quantity + NEW.transaction_quantity;
                t_warehousing_amount:=t_warehousing_amount + NEW.transaction_amount;
                t_quantity:=t_init_quantity + t_warehousing_quantity - t_shipping_quantity;
                t_amount:=t_init_amount + t_warehousing_amount - t_shipping_amount;
                t_cost_price:=ROUND(t_amount / t_quantity, 2);
            END IF;

            IF recent_rec IS NULL THEN
                INSERT INTO inventory.monthry_summaries
                VALUES (
                    yyyymm, t_product_id, t_init_quantity, t_warehousing_quantity,
                    t_shipping_quantity, t_init_amount, t_warehousing_amount, t_shipping_amount, t_cost_price
                );
            ELSE
                UPDATE inventory.monthry_summaries
                SET warehousing_quantity = t_warehousing_quantity,
                    shipping_quantity = t_shipping_quantity,
                    warehousing_amount = t_warehousing_amount,
                    shipping_amount = t_shipping_amount,
                    cost_price = t_cost_price
                WHERE year_month = yyyymm AND product_id = t_product_id;

            END IF;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_transition_history_3rd
            BEFORE INSERT
            ON inventory.transition_histories
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.set_monthry_summaries();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_current_summaries_every_site_table() -> Table:
    op.create_table(
        "current_summaries_every_site",
        sa.Column("site_id", sa.String(2), primary_key=True, comment="倉庫ID"),
        sa.Column("product_id", sa.String(10), primary_key=True, comment="当社商品ID"),
        sa.Column("quantity", sa.Integer, nullable=False, comment="在庫数"),
        *timestamps(),
        schema="inventory",
    )

    op.create_check_constraint(
        "ck_quantity",
        "current_summaries_every_site",
        "quantity >= 0",
        schema="inventory",
    )
    op.execute(
        """
        CREATE TRIGGER current_summaries_every_site_modified
            BEFORE UPDATE
            ON inventory.current_summaries_every_site
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 在庫サマリーテーブルの自動作成
    op.execute(
        """
        CREATE FUNCTION inventory.set_current_summaries_every_site() RETURNS TRIGGER AS $$
        DECLARE
            t_site_id character(2);
            t_product_id character(10);
            t_quantity integer;

            recent_rec RECORD;
        BEGIN
            t_site_id:=NEW.site_id;
            t_product_id:=NEW.product_id;

            SELECT * INTO recent_rec
                FROM inventory.current_summaries_every_site
                WHERE site_id = t_site_id AND product_id = t_product_id
                FOR UPDATE;

            IF recent_rec IS NULL THEN
                t_quantity:= NEW.transaction_quantity;
            ELSE
                t_quantity:=recent_rec.quantity + NEW.transaction_quantity;
            END IF;

            IF recent_rec IS NULL THEN
                INSERT INTO inventory.current_summaries_every_site
                VALUES (
                    t_site_id, t_product_id, t_quantity
                );
            ELSE
                UPDATE inventory.current_summaries_every_site
                SET quantity = t_quantity
                WHERE site_id = t_site_id AND product_id = t_product_id;
            END IF;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_transition_history_2nd
            BEFORE INSERT
            ON inventory.transition_histories
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.set_current_summaries_every_site();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_current_summaries_table() -> Table:
    op.create_table(
        "current_summaries",
        sa.Column("product_id", sa.String(10), primary_key=True, comment="当社商品ID"),
        sa.Column("quantity", sa.Integer, nullable=False, comment="在庫数"),
        sa.Column("amount", sa.Numeric, nullable=False, comment="在庫額"),
        sa.Column("cost_price", sa.Numeric, nullable=False, comment="原価"),
        *timestamps(),
        schema="inventory",
    )

    op.create_check_constraint(
        "ck_quantity",
        "current_summaries",
        "quantity >= 0",
        schema="inventory",
    )
    op.create_check_constraint(
        "ck_amount",
        "current_summaries",
        "amount >= 0",
        schema="inventory",
    )
    op.execute(
        """
        CREATE TRIGGER current_summaries_modified
            BEFORE UPDATE
            ON inventory.current_summaries
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 在庫サマリーテーブルの自動作成
    op.execute(
        """
        CREATE FUNCTION inventory.set_current_summaries() RETURNS TRIGGER AS $$
        DECLARE
            t_product_id character(10);
            t_quantity integer;
            t_amount numeric;
            t_cost_price numeric;

            t_shipping numeric;

            recent_rec RECORD;
        BEGIN
            t_product_id:=NEW.product_id;

            SELECT * INTO recent_rec
                FROM inventory.current_summaries
                WHERE product_id = t_product_id
                FOR UPDATE;

            IF recent_rec IS NULL THEN
                t_quantity:= 0;
                t_amount:=0.00;
                t_cost_price:=0.0;
            ELSE
                t_quantity:=recent_rec.quantity;
                t_amount:=recent_rec.amount;
                t_cost_price:=recent_rec.cost_price;
            END IF;

            IF NEW.transition_type='SELLING' OR NEW.transition_type='ORDERING_RETURN' THEN
                t_quantity:=t_quantity + NEW.transaction_quantity;
                t_amount:=t_amount + NEW.transaction_quantity * t_cost_price;

            ELSEIF NEW.transition_type='PURCHASE' OR NEW.transition_type='SALES_RETURN' OR NEW.transition_type='OTHER_TRANSITION' THEN
                t_quantity:=t_quantity + NEW.transaction_quantity;
                t_amount:=t_amount + NEW.transaction_amount;
                IF t_quantity = 0 THEN
                    t_cost_price:=0.00;
                ELSE
                    t_cost_price:=ROUND(t_amount / t_quantity, 2);
                END IF;

            END IF;

            IF recent_rec IS NULL THEN
                INSERT INTO inventory.current_summaries
                VALUES (t_product_id, t_quantity, t_amount, t_cost_price);
            ELSE
                UPDATE inventory.current_summaries
                SET quantity = t_quantity,
                    amount = t_amount,
                    cost_price = t_cost_price
                WHERE product_id = t_product_id;
            END IF;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_transition_history_4th
            BEFORE INSERT
            ON inventory.transition_histories
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.set_current_summaries();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_view() -> None:
    op.execute(
        """
        CREATE VIEW inventory.view_current_summaries AS
            SELECT
                CS.product_id,
                CS.quantity AS assets_quantity,
                (SELECT SUM(CE.quantity)
                    FROM inventory.current_summaries_every_site CE
                    LEFT JOIN mst.sites SI ON CE.site_id = SI.site_id
                    WHERE CE.product_id = CS.product_id
                    AND SI.is_free = true
                ) AS free_quantity,
                CS.amount,
                CS.cost_price
            FROM inventory.current_summaries CS;
        """
    )
    op.execute(
        """
        CREATE VIEW inventory.view_monthry_summaries AS
            SELECT
                MS.year_month,
                MS.product_id,
                (MS.init_quantity + MS.warehousing_quantity - MS.shipping_quantity) AS assets_quantity,
                (SELECT SUM(ME.init_quantity + ME.warehousing_quantity - ME.shipping_quantity)
                    FROM inventory.monthry_summaries_every_site ME
                    LEFT JOIN mst.sites SI ON ME.site_id = SI.site_id
                    WHERE ME.year_month = MS.year_month
                    AND ME.product_id = MS.product_id
                    AND SI.is_free = true
                ) AS free_quantity,
                (MS.init_amount + warehousing_amount - shipping_amount) AS amount,
                MS.cost_price
            FROM inventory.monthry_summaries MS;
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def insert_transition_histories(stock_transision: Table, stock_moving: Table) -> None:
    op.bulk_insert(
        stock_transision,
        [
            {
                "transaction_date": date(2022, 10, 20),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": 1,
                "transaction_amount": 18000.0,
                "transition_type": StockTransitionType.purchase,
                "transition_reason": None,
                "transaction_no": 501,
            },
            {
                "transaction_date": date(2022, 12, 10),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": 2,
                "transaction_amount": 48000.0,
                "transition_type": StockTransitionType.purchase,
                "transition_reason": None,
                "transaction_no": 502,
            },
            {
                "transaction_date": date(2022, 12, 12),
                "site_id": "E3",
                "product_id": "S001-00001",
                "transaction_quantity": 5,
                "transaction_amount": 100000.0,
                "transition_type": StockTransitionType.purchase,
                "transition_reason": None,
                "transaction_no": 503,
            },
        ],
    )
    op.bulk_insert(
        stock_moving,
        [
            {
                "transaction_date": date(2022, 12, 12),
                "site_id_from": "E3",
                "site_id_to": "E4",
                "product_id": "S001-00001",
                "moving_quantity": 2,
            },
            {
                "transaction_date": date(2022, 12, 12),
                "site_id_from": "E3",
                "site_id_to": "N1",
                "product_id": "S001-00001",
                "moving_quantity": 3,
            },
        ],
    )
    op.bulk_insert(
        stock_transision,
        [
            {
                "transaction_date": date(2022, 12, 14),
                "site_id": "E4",
                "product_id": "S001-00001",
                "transaction_quantity": -1,
                "transaction_amount": -20000.0,
                "transition_type": StockTransitionType.ordering_return,
                "transition_reason": None,
                "transaction_no": 504,
            },
            {
                "transaction_date": date(2023, 1, 5),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": -2,
                "transaction_amount": -40000.0,
                "transition_type": StockTransitionType.selling,
                "transition_reason": None,
                "transaction_no": 505,
            },
            {
                "transaction_date": date(2023, 1, 10),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": 3,
                "transaction_amount": 65000.0,
                "transition_type": StockTransitionType.purchase,
                "transition_reason": None,
                "transaction_no": 506,
            },
            {
                "transaction_date": date(2023, 1, 18),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": 1,
                "transaction_amount": 0.0,
                "transition_type": StockTransitionType.other_transition,
                "transition_reason": "棚卸の結果、帳簿在庫増",
                "transaction_no": 507,
            },
            {
                "transaction_date": date(2023, 1, 20),
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
        stock_moving,
        [
            {
                "transaction_date": date(2023, 1, 22),
                "site_id_from": "N1",
                "site_id_to": "E2",
                "product_id": "S001-00001",
                "moving_quantity": 2,
            },
        ],
    )
    op.bulk_insert(
        stock_transision,
        [
            {
                "transaction_date": date(2023, 1, 25),
                "site_id": "N1",
                "product_id": "S001-00002",
                "transaction_quantity": 1,
                "transaction_amount": 20000.0,
                "transition_type": StockTransitionType.sales_return,
                "transition_reason": None,
                "transaction_no": 509,
            },
            {
                "transaction_date": date(2023, 1, 30),
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


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def upgrade() -> None:
    stock_transision: Table = create_transition_histories_table()
    stock_moving: Table = create_moving_histories_table()
    create_current_summaries_table()
    create_current_summaries_every_site_table()
    create_monthry_summaries_table()
    create_monthry_summaries_every_site_table()
    create_transition_estimates_table()
    create_view()
    insert_transition_histories(stock_transision, stock_moving)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS inventory.current_summaries_every_site CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.current_summaries CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.monthry_summaries_every_site CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.monthry_summaries CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.moving_histories CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.transition_estimates CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.transition_histories CASCADE;")
    op.execute("DROP TYPE IF EXISTS inventory.transition_type;")
