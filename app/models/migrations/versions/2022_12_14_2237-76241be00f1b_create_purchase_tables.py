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
        sa.Column("ordering_no", sa.String(10), primary_key=True, comment="発注NO"),
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

    op.execute(
        """
        CREATE TRIGGER orderings_modified
            BEFORE UPDATE
            ON purchase.orderings
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
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
        sa.Column("purchase_quantity", sa.Integer, nullable=False, comment="発注数"),
        sa.Column("unit_purchase_price", sa.Numeric, nullable=False, comment="発注単価"),
        sa.Column("estimate_arrival_date", sa.Date, nullable=False, comment="入荷予定日"),
        *timestamps(),
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

    # 在庫変動予定の登録
    op.execute(
        """
        CREATE FUNCTION purchase.set_transition_estimates() RETURNS TRIGGER AS $$
        DECLARE
            t_transaction_no integer;
            t_transaction_date date;
            t_product_id character(10);
            t_site_id character(2);
            t_quantity integer;
            t_amount numeric;
            t_interval_days integer;
            t_order_date date;

            product_rec RECORD;
            ordering_rec RECORD;
        BEGIN

            IF TG_OP = 'UPDATE' THEN
                UPDATE inventory.transition_estimates
                SET transaction_date = NEW.estimate_arrival_date
                WHERE transaction_no = NEW.detail_no;

            ELSEIF TG_OP = 'INSERT' THEN
                -- 商品単位の標準入荷日数取得
                SELECT supplier_id, days_to_arrive INTO product_rec
                FROM mst.products WHERE product_id = NEW.product_id;

                -- 商品単位の設定がない場合、仕入先単位の標準入荷日数取得
                IF product_rec.days_to_arrive IS NULL THEN
                    SELECT days_to_arrive INTO t_interval_days FROM mst.suppliers
                    WHERE company_id = product_rec.supplier_id;
                ELSE
                    t_interval_days:=product_rec.days_to_arrive;
                END IF;

                -- 入荷予定倉庫、発注日取得
                SELECT order_date, site_id INTO ordering_rec
                FROM purchase.orderings WHERE ordering_no = NEW.ordering_no;

                -- 入荷予定日の計算
                t_transaction_date:= ordering_rec.order_date + CAST(
                    CAST(t_interval_days as character varying)|| 'days' AS INTERVAL
                );
                NEW.estimate_arrival_date:=t_transaction_date;

                t_site_id:=ordering_rec.site_id;
                t_transaction_no:=NEW.detail_no;
                t_product_id:=NEW.product_id;
                t_quantity:=NEW.purchase_quantity;
                t_amount:=NEW.purchase_quantity * NEW.unit_purchase_price;

                -- FIXME:区分値の整備
                INSERT INTO inventory.transition_estimates
                VALUES (default, t_transaction_date, t_site_id, t_product_id, t_quantity, t_amount, 'PURCHASE', t_transaction_no);
            END IF;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_ordering_details
            BEFORE INSERT OR DELETE OR UPDATE
            ON purchase.ordering_details
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.set_transition_estimates();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def upgrade() -> None:
    op.execute("CREATE SEQUENCE purchase.ordering_no_seed START 1;")
    op.execute("CREATE SEQUENCE purchase.warehousing_no_seed START 1;")
    create_orderings_table()
    create_ordering_details_table()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS purchase.ordering_details CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase.orderings CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS purchase.ordering_no_seed CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS purchase.warehousing_no_seed CASCADE;")
