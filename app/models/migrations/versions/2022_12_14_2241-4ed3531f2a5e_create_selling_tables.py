"""create selling tables

Revision ID: 4ed3531f2a5e
Revises: 76241be00f1b
Create Date: 2022-12-14 22:41:16.215287

"""
import sqlalchemy as sa
from alembic import op

from app.models.segment_values import ShippingProductSituation
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
            t_site_type mst.site_type;
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
            --    SELECT site_type INTO t_site_type
            --    FROM purchase.orderings
            --    WHERE ordering_no = NEW.ordering_no;

            --    INSERT INTO inventory.transition_estimates
            --    VALUES (
            --        default,
            --        NEW.estimate_arrival_date,
            --        t_site_type,
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
def create_shipping_plan_products_table() -> None:
    op.create_table(
        "shipping_plan_products",
        sa.Column("product_id", sa.String(10), primary_key=True, comment="当社商品ID"),
        sa.Column("priority_no", sa.Integer, primary_key=True, comment="優先順位"),
        sa.Column(
            "situation",
            sa.Enum(
                *ShippingProductSituation.list(),
                name="shipping_situation",
                schema="selling",
            ),
            nullable=False,
            comment="出荷予定商品状況",
        ),
        sa.Column(
            "quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="出荷可能数",
        ),
        sa.Column(
            "available_shipment_date",
            sa.Date,
            server_default="2000-01-01",
            nullable=False,
            comment="出荷可能日",
        ),
        sa.Column(
            "fastest_ordering_date",
            sa.Date,
            nullable=True,
            comment="最速発注日",
        ),
        *timestamps(),
        schema="selling",
    )

    op.create_check_constraint(
        "ck_quantity",
        "shipping_plan_products",
        "quantity > 0",
        schema="selling",
    )
    op.create_foreign_key(
        "fk_product_id",
        "shipping_plan_products",
        "products",
        ["product_id"],
        ["product_id"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="mst",
    )

    # 出荷計画の作成
    op.execute(
        """
        CREATE FUNCTION selling.reset_shipping_plan() RETURNS TRIGGER AS $$
        DECLARE
            i_product_id text;
            t_plan_quantity integer;
            t_priority integer;
            t_quantity integer;

            t_today date;

            --検品日数(1日)
            instpect_interval interval:=CAST('+1 Day' AS interval);

            tttt RECORD;
            ordered_cursor refcursor;
            rec RECORD;

            ordering_dates RECORD;
            --FIXME:

        BEGIN
            i_product_id:=NEW.product_id;
            t_priority:=0;

            SELECT date INTO t_today
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';
            --FIXME:

            -- 指定商品の出荷計画を削除
            DELETE
            FROM selling.shipping_plan_products
            WHERE product_id = i_product_id;

            -- 受注残数の計算
            SELECT SUM(receive_quantity - shipping_quantity - cancel_quantity) INTO t_plan_quantity
            FROM selling.receiving_details
            WHERE product_id = i_product_id;

            IF t_plan_quantity IS NULL OR t_plan_quantity = 0 THEN
                return NEW;
            END iF;

            -- フリー在庫数の計算TODO:
            SELECT quantity INTO t_quantity
            FROM inventory.current_summaries_every_site
            WHERE product_id = i_product_id
            AND   site_type = 'MAIN';

            IF t_quantity IS NOT NULL AND t_quantity > 0 THEN
                IF t_quantity < t_plan_quantity THEN
                    t_plan_quantity:=t_plan_quantity-t_quantity;
                ELSE
                    t_quantity:=t_plan_quantity;
                    t_plan_quantity:=0;
                END IF;

                t_priority:=t_priority + 1;
                INSERT INTO selling.shipping_plan_products
                VALUES (
                    i_product_id,
                    t_priority,
                    'IN_STOCK',
                    t_quantity,
                    t_today
                );
            END IF;

            IF t_plan_quantity = 0 THEN
                return NEW;
            END iF;

            -- 検品中在庫数の計算TODO:
            SELECT quantity INTO t_quantity
            FROM inventory.current_summaries_every_site
            WHERE product_id = i_product_id
            AND   site_type = 'INSPECT_PRODUCT';

            IF t_quantity IS NOT NULL AND t_quantity > 0 THEN
                IF t_quantity < t_plan_quantity THEN
                    t_plan_quantity:=t_plan_quantity-t_quantity;
                ELSE
                    t_quantity:=t_plan_quantity;
                    t_plan_quantity:=0;
                END IF;

                t_priority:=t_priority + 1;
                INSERT INTO selling.shipping_plan_products
                VALUES (
                    i_product_id,
                    t_priority,
                    'ON_INSPECT',
                    t_quantity,
                    t_today + instpect_interval
                );
            END IF;

            IF t_plan_quantity = 0 THEN
                return NEW;
            END iF;

            -- 既発注数の計算TODO:
            OPEN ordered_cursor FOR
            SELECT *
            FROM purchase.view_remaining_order
            WHERE product_id = i_product_id
            ORDER BY estimate_arrival_date ASC;

            LOOP
                FETCH ordered_cursor INTO rec;
                IF NOT FOUND THEN
                    EXIT;
                END IF;
                IF t_plan_quantity=0 THEN
                    EXIT;
                END IF;

                IF rec.remaining_quantity < t_plan_quantity THEN
                    t_quantity:=rec.remaining_quantity;
                    t_plan_quantity:=t_plan_quantity-t_quantity;
                ELSE
                    t_quantity:=t_plan_quantity;
                    t_plan_quantity:=0;
                END IF;

                t_priority:=t_priority + 1;
                INSERT INTO selling.shipping_plan_products
                VALUES (
                    i_product_id,
                    t_priority,
                    'ARLEADY_ORDERED',
                    t_quantity,
                    rec.estimate_arrival_date + instpect_interval
                );

            END LOOP;
            CLOSE ordered_cursor;

            IF t_plan_quantity = 0 THEN
                return NEW;
            END iF;

            -- 未発注数の計算TODO:
            ordering_dates:=mst.calc_ordering_date(t_today, i_product_id);

            t_priority:=t_priority + 1;
            INSERT INTO selling.shipping_plan_products
            VALUES (
                i_product_id,
                t_priority,
                'NOT_YET_ORDERED',
                t_plan_quantity,
                ordering_dates.estimate_weahousing + instpect_interval,
                ordering_dates.estimate_ordering
            );
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER ship_plan_of_receiving_details
            AFTER INSERT OR UPDATE
            ON selling.receiving_details
            FOR EACH ROW
        EXECUTE PROCEDURE selling.reset_shipping_plan();
        """
    )
    op.execute(
        """
        CREATE TRIGGER ship_plan_of_ordering_details
            AFTER INSERT OR UPDATE
            ON purchase.ordering_details
            FOR EACH ROW
        EXECUTE PROCEDURE selling.reset_shipping_plan();
        """
    )
    op.execute(
        """
        CREATE TRIGGER ship_plan_of_inventory_summaries
            AFTER INSERT OR UPDATE
            ON inventory.current_summaries_every_site
            FOR EACH ROW
        EXECUTE PROCEDURE selling.reset_shipping_plan();
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
    op.execute(
        """
        CREATE VIEW inventory.view_current_summaries AS
            SELECT
                CS.product_id,
                CS.quantity AS assets_quantity,
                COALESCE(CE.quantity, 0) AS prepared_quantity,
                COALESCE(SP.quantity, 0) AS ordered_quantity,
                COALESCE(CE.quantity, 0) - COALESCE(SP.quantity, 0) AS free_quantity,
                CS.amount,
                CS.cost_price
            FROM inventory.current_summaries CS
            LEFT JOIN inventory.current_summaries_every_site CE
                ON CE.product_id = CS.product_id
                AND CE.site_type = 'MAIN'
            LEFT JOIN selling.shipping_plan_products SP
                ON SP.product_id = CS.product_id
                AND SP.situation = 'IN_STOCK';
            ;
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def upgrade() -> None:
    op.execute("CREATE SEQUENCE selling.receiving_no_seed START 1;")
    op.execute("CREATE SEQUENCE selling.shipping_no_seed START 1;")
    create_receivings_table()
    create_receiving_details_table()
    create_shipping_plan_products_table()
    create_view()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS selling.shipping_plan_products CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.receiving_details CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.receivings CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS selling.receiving_no_seed CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS selling.shipping_no_seed CASCADE;")
