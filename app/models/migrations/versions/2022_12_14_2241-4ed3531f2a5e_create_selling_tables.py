"""create selling tables

Revision ID: 4ed3531f2a5e
Revises: 76241be00f1b
Create Date: 2022-12-14 22:41:16.215287

"""
import sqlalchemy as sa
from alembic import op

from app.models.migrations.util import timestamps

# revision identifiers, used by Alembic.
revision = "4ed3531f2a5e"
down_revision = "76241be00f1b"
branch_labels = None
depends_on = None

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_receivings_table() -> None:
    op.create_table(
        "receivings",
        sa.Column(
            "receiving_no",
            sa.String(10),
            primary_key=True,
            server_default="set_me",
            comment="受注NO",
        ),
        sa.Column(
            "receive_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="受注日",
        ),
        sa.Column("coustomer_id", sa.String(4), nullable=False, comment="得意先ID"),
        sa.Column("receiving_pic", sa.String(5), nullable=True, comment="受注担当者ID"),
        sa.Column(
            "shipping_priority",
            sa.Integer,
            nullable=False,
            server_default="50",
            comment="優先出荷度数",
        ),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        *timestamps(),
        schema="selling",
    )

    op.create_check_constraint(
        "ck_shipping_priority",
        "receivings",
        "shipping_priority > 0 and shipping_priority < 100",
        schema="selling",
    )
    op.create_foreign_key(
        "fk_costomer_id",
        "receivings",
        "costomers",
        ["coustomer_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_receiving_pic",
        "receivings",
        "profiles",
        ["receiving_pic"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="selling",
        referent_schema="account",
    )

    op.execute(
        """
        CREATE TRIGGER receivings_modified
            BEFORE UPDATE
            ON selling.receivings
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION selling.create_receivings() RETURNS TRIGGER AS $$
        BEGIN
            NEW.receiving_no:='RO-'||to_char(nextval('selling.receiving_no_seed'),'FM0000000');
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_receivings
            BEFORE INSERT
            ON selling.receivings
            FOR EACH ROW
        EXECUTE PROCEDURE selling.create_receivings();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_receiving_details_table() -> None:
    op.create_table(
        "receiving_details",
        sa.Column("detail_no", sa.Integer, primary_key=True, comment="受注明細NO"),
        sa.Column("receiving_no", sa.String(10), nullable=False, comment="受注NO"),
        sa.Column("product_id", sa.String(10), nullable=False, comment="当社商品ID"),
        sa.Column(
            "receive_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="受注数",
        ),
        sa.Column(
            "shipping_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="出荷済数",
        ),
        sa.Column(
            "cancel_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="キャンセル済数",
        ),
        sa.Column(
            "receiving_unit_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="受注単価",
        ),
        sa.Column(
            "assumption_profit_rate",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="想定利益率",
        ),
        *timestamps(),
        schema="selling",
    )

    op.create_check_constraint(
        "ck_receive_quantity",
        "receiving_details",
        "receive_quantity > 0",
        schema="selling",
    )
    op.create_check_constraint(
        "ck_shipping_quantity",
        "receiving_details",
        "shipping_quantity >= 0",
        schema="selling",
    )
    op.create_check_constraint(
        "ck_cancel_quantity",
        "receiving_details",
        "cancel_quantity >= 0",
        schema="selling",
    )
    op.create_check_constraint(
        "ck_quantity",
        "receiving_details",
        "receive_quantity >= shipping_quantity + cancel_quantity",
        schema="selling",
    )
    op.create_check_constraint(
        "ck_receiving_unit_price",
        "receiving_details",
        "receiving_unit_price > 0",
        schema="selling",
    )
    op.create_foreign_key(
        "fk_receiving_no",
        "receiving_details",
        "receivings",
        ["receiving_no"],
        ["receiving_no"],
        ondelete="CASCADE",
        source_schema="selling",
        referent_schema="selling",
    )
    op.create_foreign_key(
        "fk_product_id",
        "receiving_details",
        "products",
        ["product_id"],
        ["product_id"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="mst",
    )
    op.create_index(
        "ix_selling_details_receiving",
        "receiving_details",
        ["receiving_no", "detail_no"],
        schema="selling",
    )

    op.execute(
        """
        CREATE TRIGGER receiving_details_modified
            BEFORE UPDATE
            ON selling.receiving_details
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION selling.calc_receiving_details() RETURNS TRIGGER AS $$
        DECLARE
            t_cost_price numeric;
        BEGIN
            -- 商品の標準原価取得
            SELECT cost_price INTO t_cost_price
            FROM mst.products
            WHERE product_id = NEW.product_id;

            NEW.assumption_profit_rate:=ROUND((NEW.receiving_unit_price - t_cost_price) / NEW.receiving_unit_price, 2);

            -- 発注済数、キャンセル済数の設定
            NEW.shipping_quantity:=0;
            NEW.cancel_quantity:=0;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_receiving_details
            BEFORE INSERT
            ON selling.receiving_details
            FOR EACH ROW
        EXECUTE PROCEDURE selling.calc_receiving_details();
        """
    )

    # 在庫変動予定の登録TODO:
    op.execute(
        """
        CREATE FUNCTION selling.set_transition_estimates() RETURNS TRIGGER AS $$
        DECLARE
            t_site_id character(2);
            t_remaining_quantity integer;
        BEGIN
            --t_remaining_quantity:=NEW.purchase_quantity - NEW.wearhousing_quantity - NEW.cancel_quantity;

            --IF TG_OP = 'UPDATE' THEN
            --    IF t_remaining_quantity = 0 THEN
            --        -- 発注残数が0になった場合は受払予定を削除
            --        DELETE FROM inventory.transition_estimates
            --        WHERE transaction_no = NEW.detail_no;

            --    ELSE
            --        -- 受払予定を更新
            --        UPDATE inventory.transition_estimates
            --        SET transaction_date = NEW.estimate_arrival_date,
            --            transaction_quantity = t_remaining_quantity,
            --            transaction_amount = t_remaining_quantity * NEW.purchase_unit_price
            --        WHERE transaction_no = NEW.detail_no;
            --    END IF;

            --ELSEIF TG_OP = 'INSERT' THEN

            --    -- 受払予定を登録
            --    SELECT site_id INTO t_site_id
            --    FROM purchase.orderings
            --    WHERE ordering_no = NEW.ordering_no;

            --    INSERT INTO inventory.transition_estimates
            --    VALUES (
            --        default,
            --        NEW.estimate_arrival_date,
            --        t_site_id,
            --       NEW.product_id,
            --        t_remaining_quantity,
            --        t_remaining_quantity * NEW.purchase_unit_price,
            --        'PURCHASE',
            --        NEW.detail_no
            --    );
            --END IF;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_upsert_receiving_details
            AFTER INSERT OR UPDATE
            ON selling.receiving_details
            FOR EACH ROW
        EXECUTE PROCEDURE selling.set_transition_estimates();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_view() -> None:
    op.execute(
        """
        CREATE VIEW selling.view_remaining_receive AS
            SELECT
                RD.detail_no,
                RD.product_id,
                RD.receive_quantity,
                (RD.receive_quantity - RD.shipping_quantity - RD.cancel_quantity) AS remaining_quantity,
                R.coustomer_id,
                R.shipping_priority
            FROM selling.receiving_details RD
            LEFT OUTER JOIN selling.receivings R ON RD.receiving_no = R.receiving_no
            WHERE (RD.receive_quantity - RD.shipping_quantity - RD.cancel_quantity) > 0
            ORDER BY RD.product_id, R.shipping_priority ASC, RD.detail_no;
        """
    )
    op.execute(
        """
        CREATE VIEW selling.view_remaining_receive_products AS
            SELECT
                RD.product_id,
                SUM(RD.receive_quantity - RD.shipping_quantity - RD.cancel_quantity) AS remaining_quantity
            FROM selling.receiving_details RD
            WHERE (RD.receive_quantity - RD.shipping_quantity - RD.cancel_quantity) > 0
            GROUP BY RD.product_id
            ORDER BY RD.product_id;
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def upgrade() -> None:
    op.execute("CREATE SEQUENCE selling.receiving_no_seed START 1;")
    op.execute("CREATE SEQUENCE selling.shipping_no_seed START 1;")
    create_receivings_table()
    create_receiving_details_table()
    create_view()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS selling.receiving_details CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.receivings CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS selling.receiving_no_seed CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS selling.shipping_no_seed CASCADE;")
