"""create purchase tables

Revision ID: 76241be00f1b
Revises: f3ef6aa8d42a
Create Date: 2022-12-14 22:37:45.628970

"""
import sqlalchemy as sa
from alembic import op

from app.models.migrations.util import timestamps

# revision identifiers, used by Alembic.
revision = "76241be00f1b"
down_revision = "f3ef6aa8d42a"
branch_labels = None
depends_on = None

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_orderings_table() -> None:
    op.create_table(
        "orderings",
        sa.Column(
            "ordering_no",
            sa.String(10),
            primary_key=True,
            server_default="set_me",
            comment="発注NO",
        ),
        sa.Column(
            "order_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="発注日",
        ),
        sa.Column("supplier_id", sa.String(4), nullable=False, comment="仕入先ID"),
        sa.Column("site_id", sa.String(2), nullable=False, comment="入荷予定倉庫ID"),
        sa.Column("purchase_pic", sa.String(5), nullable=True, comment="発注担当者ID"),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        *timestamps(),
        schema="purchase",
    )

    op.create_foreign_key(
        "fk_supplier_id",
        "orderings",
        "suppliers",
        ["supplier_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_site_id",
        "orderings",
        "sites",
        ["site_id"],
        ["site_id"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_purchase_pic",
        "orderings",
        "profiles",
        ["purchase_pic"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="purchase",
        referent_schema="account",
    )

    op.execute(
        """
        CREATE TRIGGER orderings_modified
            BEFORE UPDATE
            ON purchase.orderings
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 発注番号の自動採番
    op.execute(
        """
        CREATE FUNCTION purchase.create_orderings() RETURNS TRIGGER AS $$
        BEGIN
            NEW.ordering_no:='PO-'||to_char(nextval('purchase.ordering_no_seed'),'FM0000000');
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_orderings
            BEFORE INSERT
            ON purchase.orderings
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.create_orderings();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_ordering_details_table() -> None:
    op.create_table(
        "ordering_details",
        sa.Column("detail_no", sa.Integer, primary_key=True, comment="発注明細NO"),
        sa.Column("ordering_no", sa.String(10), nullable=False, comment="発注NO"),
        sa.Column("product_id", sa.String(10), nullable=False, comment="当社商品ID"),
        sa.Column(
            "purchase_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="発注数",
        ),
        sa.Column(
            "wearhousing_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="入荷済数",
        ),
        sa.Column(
            "cancel_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="キャンセル済数",
        ),
        sa.Column(
            "purchase_unit_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="発注単価",
        ),
        sa.Column(
            "standard_arrival_date",
            sa.Date,
            nullable=False,
            server_default="2999-12-31",
            comment="標準納期日",
        ),
        sa.Column(
            "estimate_arrival_date",
            sa.Date,
            nullable=False,
            server_default="2999-12-31",
            comment="予定納期日",
        ),
        *timestamps(),
        schema="purchase",
    )

    # 発注仕入先の商品であること
    op.execute(
        """
        CREATE FUNCTION purchase.ck_product_with_supplier(
            t_ordering_no character(10),
            t_product_id character(10)
        ) RETURNS boolean AS $$
        DECLARE
            supplier_id_from_ordering character(4);
            supplier_id_from_product character(4);
        BEGIN
            SELECT supplier_id INTO supplier_id_from_ordering
            FROM purchase.orderings
            WHERE ordering_no = t_ordering_no;

            SELECT supplier_id INTO supplier_id_from_product
            FROM mst.products
            WHERE product_id = t_product_id;

        RETURN supplier_id_from_ordering=supplier_id_from_product;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.create_check_constraint(
        "ck_product_id",
        "ordering_details",
        "purchase.ck_product_with_supplier(ordering_no, product_id)",
        schema="purchase",
    )
    op.create_check_constraint(
        "ck_purchase_quantity",
        "ordering_details",
        "purchase_quantity > 0",
        schema="purchase",
    )
    op.create_check_constraint(
        "ck_wearhousing_quantity",
        "ordering_details",
        "wearhousing_quantity >= 0",
        schema="purchase",
    )
    op.create_check_constraint(
        "ck_cancel_quantity",
        "ordering_details",
        "cancel_quantity >= 0",
        schema="purchase",
    )
    op.create_check_constraint(
        "ck_quantity",
        "ordering_details",
        "purchase_quantity >= wearhousing_quantity + cancel_quantity",
        schema="purchase",
    )
    op.create_foreign_key(
        "fk_ordering_no",
        "ordering_details",
        "orderings",
        ["ordering_no"],
        ["ordering_no"],
        ondelete="CASCADE",
        source_schema="purchase",
        referent_schema="purchase",
    )
    op.create_foreign_key(
        "fk_product_id",
        "ordering_details",
        "products",
        ["product_id"],
        ["product_id"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="mst",
    )
    op.create_index(
        "ix_ordering_details_ordering",
        "ordering_details",
        ["ordering_no", "detail_no"],
        schema="purchase",
    )

    op.execute(
        """
        CREATE TRIGGER ordering_details_modified
            BEFORE UPDATE
            ON purchase.ordering_details
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 入荷予定日の計算
    op.execute(
        """
        CREATE FUNCTION purchase.culc_ordering_details() RETURNS TRIGGER AS $$
        DECLARE
            t_interval_days integer;
            t_order_date date;
            t_standard_arrival_date date;

            product_rec RECORD;
        BEGIN
            -- 商品単位の標準入荷日数取得
            SELECT supplier_id, days_to_arrive INTO product_rec
            FROM mst.products
            WHERE product_id = NEW.product_id;

            -- 商品単位の設定がない場合、仕入先単位の標準入荷日数取得
            IF product_rec.days_to_arrive IS NULL THEN
                SELECT days_to_arrive INTO t_interval_days
                FROM mst.suppliers
                WHERE company_id = product_rec.supplier_id;
            ELSE
                t_interval_days:=product_rec.days_to_arrive;
            END IF;

            -- 発注日取得
            SELECT order_date INTO t_order_date
            FROM purchase.orderings
            WHERE ordering_no = NEW.ordering_no;

            -- 標準入荷日の計算
            t_standard_arrival_date:= t_order_date + CAST(
                CAST(t_interval_days as character varying)|| 'days' AS INTERVAL
            );
            NEW.standard_arrival_date:=t_standard_arrival_date;
            NEW.estimate_arrival_date:=t_standard_arrival_date;

            -- 発注済数、キャンセル済数の設定
            NEW.wearhousing_quantity:=0;
            NEW.cancel_quantity:=0;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER before_set_ordering_details
            BEFORE INSERT
            ON purchase.ordering_details
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.culc_ordering_details();
        """
    )

    # 在庫変動予定の登録
    op.execute(
        """
        CREATE FUNCTION purchase.set_transition_estimates() RETURNS TRIGGER AS $$
        DECLARE
            t_site_id character(2);
            t_remaining_quantity integer;
        BEGIN
            t_remaining_quantity:=NEW.purchase_quantity - NEW.wearhousing_quantity - NEW.cancel_quantity;

            IF TG_OP = 'UPDATE' THEN
                IF t_remaining_quantity = 0 THEN
                    -- 発注残数が0になった場合は受払予定を削除
                    DELETE FROM inventory.transition_estimates
                    WHERE transaction_no = NEW.detail_no;

                ELSE
                    -- 受払予定を更新
                    UPDATE inventory.transition_estimates
                    SET transaction_date = NEW.estimate_arrival_date,
                        transaction_quantity = t_remaining_quantity,
                        transaction_amount = t_remaining_quantity * NEW.purchase_unit_price
                    WHERE transaction_no = NEW.detail_no;
                END IF;

            ELSEIF TG_OP = 'INSERT' THEN

                -- 受払予定を登録FIXME:区分値の整備
                SELECT site_id INTO t_site_id
                FROM purchase.orderings
                WHERE ordering_no = NEW.ordering_no;

                INSERT INTO inventory.transition_estimates
                VALUES (
                    default,
                    NEW.estimate_arrival_date,
                    t_site_id,
                    NEW.product_id,
                    t_remaining_quantity,
                    t_remaining_quantity * NEW.purchase_unit_price,
                    'PURCHASE',
                    NEW.detail_no
                );
            END IF;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER after_set_ordering_details
            AFTER INSERT OR UPDATE
            ON purchase.ordering_details
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.set_transition_estimates();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_wearhousings_table() -> None:
    op.create_table(
        "wearhousings",
        sa.Column(
            "wearhousing_no",
            sa.String(10),
            primary_key=True,
            server_default="set_me",
            comment="入荷NO",
        ),
        sa.Column(
            "wearhousing_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="入荷日",
        ),
        sa.Column("supplier_id", sa.String(4), nullable=False, comment="仕入先ID"),
        sa.Column("wearhousing_pic", sa.String(5), nullable=True, comment="入荷担当者ID"),
        sa.Column(
            "closing_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="支払締日",
        ),
        sa.Column(
            "payment_deadline",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="支払期限日",
        ),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        *timestamps(),
        schema="purchase",
    )

    op.create_foreign_key(
        "fk_supplier_id",
        "wearhousings",
        "suppliers",
        ["supplier_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_wearhousing_pic",
        "wearhousings",
        "profiles",
        ["wearhousing_pic"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="purchase",
        referent_schema="account",
    )

    op.execute(
        """
        CREATE TRIGGER wearhousings_modified
            BEFORE UPDATE
            ON purchase.wearhousings
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 入荷番号の自動採番、締日、支払期限の計算TODO:
    op.execute(
        """
        CREATE FUNCTION purchase.create_wearhousings() RETURNS TRIGGER AS $$
        DECLARE
            rec record;

        BEGIN
            NEW.wearhousing_no:='WH-'||to_char(nextval('purchase.warehousing_no_seed'),'FM0000000');
            rec:=mst.calc_payment_deadline(New.wearhousing_date, New.supplier_id);
            New.closing_date:=rec.closing_date;
            New.payment_deadline:=rec.payment_deadline;
            New.note:=rec.dummy;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_wearhousings
            BEFORE INSERT
            ON purchase.wearhousings
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.create_wearhousings();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_wearhousing_details_table() -> None:
    op.create_table(
        "wearhousing_details",
        sa.Column("detail_no", sa.Integer, primary_key=True, comment="入荷明細NO"),
        sa.Column("wearhousing_no", sa.String(10), nullable=False, comment="入荷NO"),
        sa.Column("order_detail_no", sa.Integer, nullable=False, comment="発注明細NO"),
        sa.Column(
            "product_id",
            sa.String(10),
            nullable=False,
            server_default="set_me",
            comment="当社商品ID",
        ),
        sa.Column(
            "wearhousing_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="入荷数",
        ),
        sa.Column(
            "wearhousing_unit_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="入荷単価",
        ),
        sa.Column("site_id", sa.String(2), nullable=False, comment="入荷倉庫ID"),
        *timestamps(),
        schema="purchase",
    )

    op.create_check_constraint(
        "ck_wearhousing_quantity",
        "wearhousing_details",
        "wearhousing_quantity > 0",
        schema="purchase",
    )
    op.create_check_constraint(
        "ck_wearhousing_unit_price",
        "wearhousing_details",
        "wearhousing_unit_price > 0",
        schema="purchase",
    )
    op.create_foreign_key(
        "fk_wearhousing_no",
        "wearhousing_details",
        "wearhousings",
        ["wearhousing_no"],
        ["wearhousing_no"],
        ondelete="CASCADE",
        source_schema="purchase",
        referent_schema="purchase",
    )
    op.create_foreign_key(
        "fk_order_detail_no",
        "wearhousing_details",
        "ordering_details",
        ["order_detail_no"],
        ["detail_no"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="purchase",
    )
    op.create_foreign_key(
        "fk_site_id",
        "wearhousing_details",
        "sites",
        ["site_id"],
        ["site_id"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="mst",
    )
    op.create_index(
        "ix_wearhousing_details_wearhousing",
        "wearhousing_details",
        ["wearhousing_no", "detail_no"],
        schema="purchase",
    )

    op.execute(
        """
        CREATE TRIGGER wearhousing_details_modified
            BEFORE UPDATE
            ON purchase.wearhousing_details
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 入荷予定日の計算
    op.execute(
        """
        CREATE FUNCTION purchase.culc_wearhousing_details() RETURNS TRIGGER AS $$
        BEGIN
            -- 発注明細から商品番号を取得
            SELECT product_id INTO NEW.product_id
            FROM purchase.ordering_details
            WHERE detail_no = NEW.order_detail_no;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER before_create_wearhousing_details
            BEFORE INSERT
            ON purchase.wearhousing_details
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.culc_wearhousing_details();
        """
    )

    # 在庫変動履歴の登録
    op.execute(
        """
        CREATE FUNCTION purchase.set_transition_histories_1st() RETURNS TRIGGER AS $$
        DECLARE
            t_wearhousing_quantity integer;
            t_wearhousing_date date;
        BEGIN
            -- 発注残数の更新
            SELECT wearhousing_quantity INTO t_wearhousing_quantity
            FROM purchase.ordering_details
            WHERE detail_no = NEW.order_detail_no
            FOR UPDATE;

            UPDATE purchase.ordering_details
            SET wearhousing_quantity = t_wearhousing_quantity + NEW.wearhousing_quantity
            WHERE detail_no = NEW.order_detail_no;

            -- 在庫変動履歴の登録FIXME:区分値の整備
            SELECT wearhousing_date INTO t_wearhousing_date
            FROM purchase.wearhousings
            WHERE wearhousing_no = NEW.wearhousing_no;

            INSERT INTO inventory.transition_histories
            VALUES (
                default,
                t_wearhousing_date,
                NEW.site_id,
                NEW.product_id,
                NEW.wearhousing_quantity,
                NEW.wearhousing_quantity * NEW.wearhousing_unit_price,
                'PURCHASE',
                null,
                NEW.detail_no
            );

            -- 買掛金変動履歴の登録FIXME:

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER after_create_wearhousing_details
            AFTER INSERT
            ON purchase.wearhousing_details
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.set_transition_histories_1st();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_view() -> None:
    op.execute(
        """
        CREATE VIEW purchase.view_remaining_ordering_details AS
            SELECT
                OD.detail_no,
                OD.product_id,
                OD.purchase_quantity,
                OD.wearhousing_quantity,
                OD.cancel_quantity,
                (OD.purchase_quantity - OD.wearhousing_quantity - OD.cancel_quantity) AS remaining_quantity,
                OD.purchase_unit_price,
                OD.estimate_arrival_date
            FROM purchase.ordering_details OD
            WHERE (OD.purchase_quantity - OD.wearhousing_quantity - OD.cancel_quantity) > 0
            ORDER BY OD.product_id, OD.estimate_arrival_date;
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def upgrade() -> None:
    op.execute("CREATE SEQUENCE purchase.ordering_no_seed START 1;")
    op.execute("CREATE SEQUENCE purchase.warehousing_no_seed START 1;")
    create_orderings_table()
    create_ordering_details_table()
    create_wearhousings_table()
    create_wearhousing_details_table()
    create_view()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS purchase.wearhousing_details CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase.wearhousings CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase.ordering_details CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase.orderings CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS purchase.ordering_no_seed CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS purchase.warehousing_no_seed CASCADE;")
