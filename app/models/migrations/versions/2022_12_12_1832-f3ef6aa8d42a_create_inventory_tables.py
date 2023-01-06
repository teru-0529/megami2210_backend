"""create inventory tables

Revision ID: f3ef6aa8d42a
Revises: 139619b8894b
Create Date: 2022-12-12 18:32:51.092614

"""

import sqlalchemy as sa
from alembic import op

from app.models.migrations.util import timestamps
from app.models.segment_values import StockTransitionType, SiteType

# revision identifiers, used by Alembic.
revision = "f3ef6aa8d42a"
down_revision = "139619b8894b"
branch_labels = None
depends_on = None

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_monthry_summaries_every_site_table() -> None:
    op.create_table(
        "monthry_summaries_every_site",
        sa.Column("product_id", sa.String(10), primary_key=True, comment="当社商品ID"),
        sa.Column("year_month", sa.String(6), primary_key=True, comment="取引年月"),
        sa.Column(
            "site_type",
            sa.Enum(*SiteType.list(), name="site_type", schema="mst"),
            primary_key=True,
            comment="倉庫種別 ",
        ),
        sa.Column(
            "init_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="月初在庫数",
        ),
        sa.Column(
            "warehousing_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="入庫数",
        ),
        sa.Column(
            "shipping_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="出庫数",
        ),
        sa.Column(
            "quantity", sa.Integer, nullable=False, server_default="0", comment="在庫数"
        ),
        *timestamps(),
        schema="inventory",
    )

    op.create_check_constraint(
        "ck_quantity",
        "monthry_summaries_every_site",
        "quantity >= 0",
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

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION inventory.calc_monthry_summaries_every_site() RETURNS TRIGGER AS $$
        BEGIN
            NEW.quantity:=NEW.init_quantity + NEW.warehousing_quantity - NEW.shipping_quantity;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER upsert_monthry_summaries_every_site
            BEFORE INSERT OR UPDATE
            ON inventory.monthry_summaries_every_site
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.calc_monthry_summaries_every_site();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+

# INFO:
def create_monthry_summaries_table() -> None:
    op.create_table(
        "monthry_summaries",
        sa.Column("product_id", sa.String(10), primary_key=True, comment="当社商品ID"),
        sa.Column("year_month", sa.String(6), primary_key=True, comment="取引年月"),
        sa.Column(
            "init_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="月初在庫数",
        ),
        sa.Column(
            "warehousing_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="入庫数",
        ),
        sa.Column(
            "shipping_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="出庫数",
        ),
        sa.Column(
            "quantity", sa.Integer, nullable=False, server_default="0", comment="在庫数"
        ),
        sa.Column(
            "init_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="月初在庫額",
        ),
        sa.Column(
            "warehousing_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="入庫金額",
        ),
        sa.Column(
            "shipping_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="出庫金額",
        ),
        sa.Column(
            "amount", sa.Numeric, nullable=False, server_default="0.0", comment="在庫額"
        ),
        sa.Column(
            "cost_price", sa.Numeric, nullable=False, server_default="0.0", comment="原価"
        ),
        *timestamps(),
        schema="inventory",
    )

    op.create_check_constraint(
        "ck_quantity",
        "monthry_summaries",
        "quantity >= 0",
        schema="inventory",
    )
    op.create_check_constraint(
        "ck_amount",
        "monthry_summaries",
        "amount >= 0.0",
        schema="inventory",
    )
    op.create_index(
        "ix_monthry_summaries_product",
        "monthry_summaries",
        ["product_id", "year_month"],
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

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION inventory.calc_monthry_summaries() RETURNS TRIGGER AS $$
        BEGIN
            NEW.quantity:=NEW.init_quantity + NEW.warehousing_quantity - NEW.shipping_quantity;
            NEW.amount:=NEW.init_amount + NEW.warehousing_amount - NEW.shipping_amount;
            IF NEW.quantity = 0 THEN
                NEW.cost_price:=0.0;
            ELSE
                NEW.cost_price:=ROUND(NEW.amount / NEW.quantity, 2);
            END IF;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER upsert_monthry_summaries
            BEFORE INSERT OR UPDATE
            ON inventory.monthry_summaries
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.calc_monthry_summaries();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_current_summaries_every_site_table() -> None:
    op.create_table(
        "current_summaries_every_site",
        sa.Column("product_id", sa.String(10), primary_key=True, comment="当社商品ID"),
        sa.Column(
            "site_type",
            sa.Enum(*SiteType.list(), name="site_type", schema="mst"),
            primary_key=True,
            comment="倉庫種別 ",
        ),
        sa.Column(
            "quantity", sa.Integer, nullable=False, server_default="0", comment="在庫数"
        ),
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


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_current_summaries_table() -> None:
    op.create_table(
        "current_summaries",
        sa.Column("product_id", sa.String(10), primary_key=True, comment="当社商品ID"),
        sa.Column(
            "quantity", sa.Integer, nullable=False, server_default="0", comment="在庫数"
        ),
        sa.Column(
            "amount", sa.Numeric, nullable=False, server_default="0.0", comment="在庫額"
        ),
        sa.Column(
            "cost_price", sa.Numeric, nullable=False, server_default="0.0", comment="原価"
        ),
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
        "amount >= 0.0",
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

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION inventory.calc_current_summaries() RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.quantity = 0 THEN
                NEW.cost_price:=0.0;
            ELSE
                NEW.cost_price:=ROUND(NEW.amount / NEW.quantity, 2);
            END IF;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER upsert_current_summaries
            BEFORE INSERT OR UPDATE
            ON inventory.current_summaries
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.calc_current_summaries();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_transition_histories_table() -> None:
    op.create_table(
        "transition_histories",
        sa.Column("no", sa.Integer, primary_key=True, comment="受払履歴NO"),
        sa.Column(
            "transaction_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="取引日",
        ),
        sa.Column(
            "site_type",
            sa.Enum(*SiteType.list(), name="site_type", schema="mst"),
            nullable=False,
            comment="倉庫種別 ",
        ),
        sa.Column("product_id", sa.String(10), nullable=False, comment="当社商品ID"),
        sa.Column(
            "transaction_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="取引数",
        ),
        sa.Column(
            "transaction_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="取引金額",
        ),
        sa.Column(
            "transition_type",
            sa.Enum(
                *StockTransitionType.list(), name="transition_type", schema="inventory"
            ),
            nullable=False,
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
        "transition_histories",
        "products",
        ["product_id"],
        ["product_id"],
        ondelete="RESTRICT",
        source_schema="inventory",
        referent_schema="mst",
    )
    op.create_index(
        "ix_transition_histories_product",
        "transition_histories",
        ["product_id", "transaction_date"],
        schema="inventory",
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

    # 登録後、月次在庫サマリーを自動作成
    op.execute(
        """
        CREATE FUNCTION inventory.set_summaries() RETURNS TRIGGER AS $$
        DECLARE
            yyyymm character(6);
            t_product_id character(10);
            t_site_type mst.site_type;
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
            t_site_type:=NEW.site_type;
            t_product_id:=NEW.product_id;

            ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
            -- 月次サマリー（倉庫別）TODO:
            SELECT * INTO recent_rec
                FROM inventory.monthry_summaries_every_site
                WHERE product_id = t_product_id AND year_month = yyyymm AND site_type = t_site_type
                FOR UPDATE;

            IF recent_rec IS NULL THEN
                SELECT * INTO last_rec
                    FROM inventory.monthry_summaries_every_site
                    WHERE product_id = t_product_id AND site_type = t_site_type
                    ORDER BY year_month DESC
                    LIMIT 1;

                IF last_rec IS NULL THEN
                    t_init_quantity:=0;
                ELSE
                    t_init_quantity:=last_rec.quantity;
                END IF;

                t_warehousing_quantity:=0;
                t_shipping_quantity:=0;
            ELSE
                t_init_quantity:=recent_rec.init_quantity;
                t_warehousing_quantity:=recent_rec.warehousing_quantity;
                t_shipping_quantity:=recent_rec.shipping_quantity;
            END IF;

            IF NEW.transaction_quantity > 0 THEN
                t_warehousing_quantity:=t_warehousing_quantity + NEW.transaction_quantity;
            ELSE
                t_shipping_quantity:=t_shipping_quantity - NEW.transaction_quantity;
            END IF;

            IF recent_rec IS NULL THEN
                INSERT INTO inventory.monthry_summaries_every_site
                VALUES (
                    t_product_id,
                    yyyymm,
                    t_site_type,
                    t_init_quantity,
                    t_warehousing_quantity,
                    t_shipping_quantity
                );
            ELSE
                UPDATE inventory.monthry_summaries_every_site
                SET warehousing_quantity = t_warehousing_quantity,
                    shipping_quantity = t_shipping_quantity
                WHERE product_id = t_product_id AND year_month = yyyymm AND site_type = t_site_type;
            END IF;

            ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
            -- 月次サマリーTODO:
            SELECT * INTO recent_rec
                FROM inventory.monthry_summaries
                WHERE product_id = t_product_id AND year_month = yyyymm
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
                    t_init_quantity:=last_rec.quantity;
                    t_init_amount:=last_rec.amount;
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

            IF NEW.transition_type='SELLING' THEN
                NEW.transaction_amount:=NEW.transaction_quantity * t_cost_price;
            END IF;

            IF NEW.transaction_quantity > 0 THEN
                t_warehousing_quantity:=t_warehousing_quantity + NEW.transaction_quantity;
            ELSE
                t_shipping_quantity:=t_shipping_quantity - NEW.transaction_quantity;
            END IF;
            IF NEW.transaction_amount > 0.0 THEN
                t_warehousing_amount:=t_warehousing_amount + NEW.transaction_amount;
            ELSE
                t_shipping_amount:=t_shipping_amount - NEW.transaction_amount;
            END IF;

            IF recent_rec IS NULL THEN
                INSERT INTO inventory.monthry_summaries
                VALUES (
                    t_product_id,
                    yyyymm,
                    t_init_quantity,
                    t_warehousing_quantity,
                    t_shipping_quantity,
                    0,
                    t_init_amount,
                    t_warehousing_amount,
                    t_shipping_amount
                );
            ELSE
                UPDATE inventory.monthry_summaries
                SET warehousing_quantity = t_warehousing_quantity,
                    shipping_quantity = t_shipping_quantity,
                    warehousing_amount = t_warehousing_amount,
                    shipping_amount = t_shipping_amount
                WHERE product_id = t_product_id AND year_month = yyyymm;
            END IF;

            ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
            -- 在庫サマリー（倉庫別）TODO:

            SELECT * INTO recent_rec
                FROM inventory.current_summaries_every_site
                WHERE product_id = t_product_id AND site_type = t_site_type
                FOR UPDATE;

            IF recent_rec IS NULL THEN
                t_quantity:= NEW.transaction_quantity;
            ELSE
                t_quantity:=recent_rec.quantity + NEW.transaction_quantity;
            END IF;

            IF recent_rec IS NULL THEN
                INSERT INTO inventory.current_summaries_every_site
                VALUES (
                    t_product_id,
                    t_site_type,
                    t_quantity
                );
            ELSE
                UPDATE inventory.current_summaries_every_site
                SET quantity = t_quantity
                WHERE product_id = t_product_id AND site_type = t_site_type;
            END IF;

            ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
            -- 在庫サマリーTODO:

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

            t_quantity:=t_quantity + NEW.transaction_quantity;
            IF NEW.transition_type='SELLING' THEN
                t_amount:=t_amount + NEW.transaction_quantity * t_cost_price;
            ELSE
                t_amount:=t_amount + NEW.transaction_amount;
            END IF;

            IF recent_rec IS NULL THEN
                INSERT INTO inventory.current_summaries
                VALUES (
                    t_product_id,
                    t_quantity,
                    t_amount
                );
            ELSE
                UPDATE inventory.current_summaries
                SET quantity = t_quantity,
                    amount = t_amount
                WHERE product_id = t_product_id;
            END IF;

            ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_transition_histories
            AFTER INSERT
            ON inventory.transition_histories
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.set_summaries();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_transition_estimates_table() -> None:
    op.create_table(
        "transition_estimates",
        sa.Column("no", sa.Integer, primary_key=True, comment="受払予定NO"),
        sa.Column(
            "transaction_date",
            sa.Date,
            nullable=False,
            server_default=sa.func.now(),
            comment="取引予定日",
        ),
        sa.Column("product_id", sa.String(10), nullable=False, comment="当社商品ID"),
        sa.Column(
            "transaction_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="取引予定数",
        ),
        sa.Column(
            "transaction_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="取引予定金額",
        ),
        sa.Column(
            "transition_type",
            sa.Enum(
                *StockTransitionType.list(), name="transition_type", schema="inventory"
            ),
            nullable=False,
            comment="在庫変動区分",
        ),  # FIXME:変動区分整理
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
    op.create_index(
        "ix_transition_estimates_product",
        "transition_estimates",
        ["product_id", "transaction_date"],
        schema="inventory",
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


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_moving_instructions_table() -> None:
    op.create_table(
        "moving_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="移動指示NO"),
        sa.Column(
            "instruction_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="移動日",
        ),
        sa.Column("instruction_pic", sa.String(5), nullable=True, comment="指示者ID"),
        sa.Column("moving_reason", sa.Text, nullable=False, comment="移動理由"),
        sa.Column(
            "site_type_from",
            sa.Enum(*SiteType.list(), name="site_type", schema="mst"),
            nullable=False,
            comment="移動元倉庫種別 ",
        ),
        sa.Column(
            "site_type_to",
            sa.Enum(*SiteType.list(), name="site_type", schema="mst"),
            nullable=False,
            comment="移動先倉庫種別 ",
        ),
        sa.Column("product_id", sa.String(10), nullable=False, comment="当社商品ID"),
        sa.Column(
            "moving_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="移動数",
        ),
        *timestamps(),
        schema="inventory",
    )

    op.create_check_constraint(
        "ck_site_type",
        "moving_instructions",
        "site_type_from != site_type_to",
        schema="inventory",
    )
    op.create_check_constraint(
        "ck_moving_quantity",
        "moving_instructions",
        "moving_quantity > 0",
        schema="inventory",
    )
    op.create_foreign_key(
        "fk_instruction_pic",
        "moving_instructions",
        "profiles",
        ["instruction_pic"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="inventory",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_product_id",
        "moving_instructions",
        "products",
        ["product_id"],
        ["product_id"],
        ondelete="RESTRICT",
        source_schema="inventory",
        referent_schema="mst",
    )
    op.create_index(
        "ix_moving_instructions_product",
        "moving_instructions",
        ["product_id", "instruction_date"],
        schema="inventory",
    )

    op.execute(
        """
        CREATE TRIGGER moving_instructions_modified
            BEFORE UPDATE
            ON inventory.moving_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION inventory.calc_moving_instructions() RETURNS TRIGGER AS $$
        BEGIN
            -- 処理日付を取得
            SELECT date INTO NEW.instruction_date
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_moving_instructions
            BEFORE INSERT
            ON inventory.moving_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.calc_moving_instructions();
        """
    )

    # 登録後、在庫変動履歴を自動作成
    op.execute(
        """
        CREATE FUNCTION inventory.create_transition_histories_by_moving() RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO inventory.transition_histories
            VALUES (
                default,
                NEW.instruction_date,
                NEW.site_type_from,
                NEW.product_id,
                - NEW.moving_quantity ,
                0.0,
                'MOVEMENT_SHIPPING',
                NEW.no
            );

            INSERT INTO inventory.transition_histories
            VALUES (
                default,
                NEW.instruction_date,
                NEW.site_type_to,
                NEW.product_id,
                NEW.moving_quantity ,
                0.0,
                'MOVEMENT_WAREHOUSING',
                NEW.no
            );
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_moving_instructions
            AFTER INSERT
            ON inventory.moving_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.create_transition_histories_by_moving();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_other_inventory_instructions_table() -> None:
    op.create_table(
        "other_inventory_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="雑入出庫指示NO"),
        sa.Column(
            "instruction_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="指示日",
        ),
        sa.Column("instruction_pic", sa.String(5), nullable=True, comment="指示者ID"),
        sa.Column("transition_reason", sa.Text, nullable=False, comment="入出庫理由"),
        sa.Column(
            "site_type",
            sa.Enum(*SiteType.list(), name="site_type", schema="mst"),
            nullable=False,
            comment="倉庫種別 ",
        ),
        sa.Column("product_id", sa.String(10), nullable=False, comment="当社商品ID"),
        sa.Column(
            "quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="入出庫数",
        ),
        sa.Column(
            "amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="入出庫額",
        ),
        *timestamps(),
        schema="inventory",
    )

    op.create_foreign_key(
        "fk_instruction_pic",
        "other_inventory_instructions",
        "profiles",
        ["instruction_pic"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="inventory",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_product_id",
        "other_inventory_instructions",
        "products",
        ["product_id"],
        ["product_id"],
        ondelete="RESTRICT",
        source_schema="inventory",
        referent_schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER other_inventory_instructions_modified
            BEFORE UPDATE
            ON inventory.other_inventory_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION inventory.calc_other_inventory_instructions() RETURNS TRIGGER AS $$
        BEGIN
            -- 処理日付を取得
            SELECT date INTO NEW.instruction_date
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_other_inventory_instructions
            BEFORE INSERT
            ON inventory.other_inventory_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.calc_other_inventory_instructions();
        """
    )

    # 登録後、在庫変動履歴を自動作成
    op.execute(
        """
        CREATE FUNCTION inventory.create_transition_histories_by_other() RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO inventory.transition_histories
            VALUES (
                default,
                NEW.instruction_date,
                NEW.site_type,
                NEW.product_id,
                NEW.quantity ,
                NEW.amount,
                'OTHER_TRANSITION',
                NEW.no
            );
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_other_inventory_instructions
            AFTER INSERT
            ON inventory.other_inventory_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE inventory.create_transition_histories_by_other();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def upgrade() -> None:
    create_current_summaries_table()
    create_current_summaries_every_site_table()
    create_monthry_summaries_table()
    create_monthry_summaries_every_site_table()
    create_transition_histories_table()
    create_moving_instructions_table()
    create_other_inventory_instructions_table()
    create_transition_estimates_table()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS inventory.current_summaries_every_site CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.current_summaries CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.monthry_summaries_every_site CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.monthry_summaries CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.moving_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.other_inventory_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.transition_estimates CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.transition_histories CASCADE;")
    op.execute("DROP TYPE IF EXISTS inventory.transition_type;")
