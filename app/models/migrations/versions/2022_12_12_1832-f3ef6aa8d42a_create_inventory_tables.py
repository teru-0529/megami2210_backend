"""create inventory tables

Revision ID: f3ef6aa8d42a
Revises: 139619b8894b
Create Date: 2022-12-12 18:32:51.092614

"""

import sqlalchemy as sa
from alembic import op

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
        sa.Column("init_quantity", sa.Integer, nullable=False, comment="月初在庫数"),
        sa.Column("warehousing_quantity", sa.Integer, nullable=False, comment="入庫数"),
        sa.Column("shipping_quantity", sa.Integer, nullable=False, comment="出庫数"),
        sa.Column("quantity", sa.Integer, nullable=False, comment="在庫数"),
        schema="inventory",
    )

    op.create_check_constraint(
        "ck_quantity",
        "monthry_summaries_every_site",
        "quantity >= 0",
        schema="inventory",
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION inventory.calc_monthry_summaries_every_site() RETURNS TRIGGER AS $$
        BEGIN
            --在庫数
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
        sa.Column("init_quantity", sa.Integer, nullable=False, comment="月初在庫数"),
        sa.Column("warehousing_quantity", sa.Integer, nullable=False, comment="入庫数"),
        sa.Column("shipping_quantity", sa.Integer, nullable=False, comment="出庫数"),
        sa.Column("quantity", sa.Integer, nullable=False, comment="在庫数"),
        sa.Column("init_amount", sa.Numeric, nullable=False, comment="月初在庫額"),
        sa.Column("warehousing_amount", sa.Numeric, nullable=False, comment="入庫額"),
        sa.Column("shipping_amount", sa.Numeric, nullable=False, comment="出庫額"),
        sa.Column("amount", sa.Numeric, nullable=False, comment="在庫額"),
        sa.Column("cost_price", sa.Numeric, nullable=False, comment="在庫原価"),
        sa.Column("profit_rate", sa.Numeric, nullable=False, comment="想定利益率"),
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
        "amount >= 0.00",
        schema="inventory",
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION inventory.calc_monthry_summaries() RETURNS TRIGGER AS $$
        BEGIN
            --在庫数,在庫額
            NEW.quantity:=NEW.init_quantity + NEW.warehousing_quantity - NEW.shipping_quantity;
            NEW.amount:=NEW.init_amount + NEW.warehousing_amount - NEW.shipping_amount;

            --在庫原価,予想利益率
            IF NEW.quantity = 0 THEN
                NEW.cost_price:=0.00;
                NEW.profit_rate:=0.0;
            ELSE
                NEW.cost_price:=calc_unit_price(NEW.amount, NEW.quantity);
                NEW.profit_rate:=mst.calc_profit_rate_for_cost(NEW.product_id, NEW.cost_price);
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
        sa.Column("quantity", sa.Integer, nullable=False, comment="在庫数"),
        schema="inventory",
    )

    op.create_check_constraint(
        "ck_quantity",
        "current_summaries_every_site",
        "quantity >= 0",
        schema="inventory",
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_current_summaries_table() -> None:
    op.create_table(
        "current_summaries",
        sa.Column("product_id", sa.String(10), primary_key=True, comment="当社商品ID"),
        sa.Column("quantity", sa.Integer, nullable=False, comment="在庫数"),
        sa.Column("amount", sa.Numeric, nullable=False, comment="在庫額"),
        sa.Column("cost_price", sa.Numeric, nullable=False, comment="在庫原価"),
        sa.Column("profit_rate", sa.Numeric, nullable=False, comment="想定利益率"),
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
        "amount >= 0.00",
        schema="inventory",
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION inventory.calc_current_summaries() RETURNS TRIGGER AS $$
        BEGIN
            --在庫原価,予想利益率
            IF NEW.quantity = 0 THEN
                NEW.cost_price:=0.00;
                NEW.profit_rate:=0.0;
            ELSE
                NEW.cost_price:=calc_unit_price(NEW.amount, NEW.quantity);
                NEW.profit_rate:=mst.calc_profit_rate_for_cost(NEW.product_id, NEW.cost_price);
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

    # 原価取得(在庫なしの場合は商品マスタの標準原価を返す)TODO:
    op.execute(
        """
        CREATE FUNCTION inventory.get_cost_price(
            i_product_id text,
            OUT o_cost_price numeric
        ) AS $$
        DECLARE
            t_cost_price numeric;
        BEGIN
            -- 在庫サマリの検索
            SELECT cost_price INTO o_cost_price
            FROM inventory.current_summaries
            WHERE product_id = i_product_id;

            --利益率計算
            IF t_cost_price IS NULL THEN
                --商品マスタの検索
                SELECT cost_price INTO o_cost_price
                FROM mst.products
                WHERE product_id = i_product_id;
            END IF;

        END;
        $$ LANGUAGE plpgsql;
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_transition_histories_table() -> None:
    op.create_table(
        "transition_histories",
        sa.Column("no", sa.Integer, primary_key=True, comment="在庫変動NO"),
        sa.Column("transaction_date", sa.Date, nullable=False, comment="取引日"),
        sa.Column(
            "site_type",
            sa.Enum(*SiteType.list(), name="site_type", schema="mst"),
            nullable=False,
            comment="倉庫種別 ",
        ),
        sa.Column("product_id", sa.String(10), nullable=False, comment="当社商品ID"),
        sa.Column("quantity", sa.Integer, nullable=False, comment="取引数"),
        sa.Column("amount", sa.Numeric, nullable=False, comment="取引額"),
        sa.Column(
            "transition_type",
            sa.Enum(
                *StockTransitionType.list(), name="transition_type", schema="inventory"
            ),
            nullable=False,
            comment="在庫変動区分",
        ),
        sa.Column("transaction_no", sa.Integer, nullable=False, comment="取引管理NO"),
        schema="inventory",
    )

    op.create_index(
        "ix_transition_histories_product",
        "transition_histories",
        ["product_id", "no"],
        schema="inventory",
    )

    # 登録後処理：月次在庫サマリーを自動作成
    op.execute(
        """
        CREATE FUNCTION inventory.set_summaries() RETURNS TRIGGER AS $$
        DECLARE
            yyyymm text:=to_char(NEW.transaction_date, 'YYYYMM');

            t_init_quantity integer;
            t_warehousing_quantity integer;
            t_shipping_quantity integer;
            t_init_amount numeric;
            t_warehousing_amount numeric;
            t_shipping_amount numeric;
            t_cost_price numeric;

            t_quantity integer;
            t_amount numeric;

            recent_rec record;
            last_rec record;
        BEGIN
            ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
            --1.月次在庫サマリー(倉庫別)TODO:
            --月次在庫サマリー(当月,倉庫別)検索
            SELECT * INTO recent_rec
            FROM inventory.monthry_summaries_every_site
            WHERE product_id = NEW.product_id AND year_month = yyyymm AND site_type = NEW.site_type
            FOR UPDATE;

            --月初在庫数,入庫数,出庫数判定
            IF recent_rec IS NULL THEN
                --月次在庫サマリー(過去,倉庫別)検索
                SELECT * INTO last_rec
                FROM inventory.monthry_summaries_every_site
                WHERE product_id = NEW.product_id AND site_type = NEW.site_type
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

            --取引数計上
            IF NEW.quantity > 0 THEN
                t_warehousing_quantity:=t_warehousing_quantity + NEW.quantity;
            ELSE
                t_shipping_quantity:=t_shipping_quantity - NEW.quantity;
            END IF;

            --登録
            IF recent_rec IS NULL THEN
                INSERT INTO inventory.monthry_summaries_every_site
                VALUES (
                    NEW.product_id,
                    yyyymm,
                    NEW.site_type,
                    t_init_quantity,
                    t_warehousing_quantity,
                    t_shipping_quantity
                );
            ELSE
                UPDATE inventory.monthry_summaries_every_site
                SET warehousing_quantity = t_warehousing_quantity,
                    shipping_quantity = t_shipping_quantity
                WHERE product_id = NEW.product_id AND year_month = yyyymm AND site_type = NEW.site_type;
            END IF;

            ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
            --2.月次在庫サマリーTODO:
            --月次在庫サマリー(当月)検索
            SELECT * INTO recent_rec
            FROM inventory.monthry_summaries
            WHERE product_id = NEW.product_id AND year_month = yyyymm
            FOR UPDATE;

            --月初在庫数,入庫数,出庫数,月初在庫額,入庫額,出庫額,在庫原価判定
            IF recent_rec IS NULL THEN
                --月次在庫サマリー(過去)検索
                SELECT * INTO last_rec
                FROM inventory.monthry_summaries
                WHERE product_id = NEW.product_id
                ORDER BY year_month DESC
                LIMIT 1;

                IF last_rec IS NULL THEN
                    t_init_quantity:=0;
                    t_init_amount:=0.00;
                    t_cost_price:=0.00;
                ELSE
                    t_init_quantity:=last_rec.quantity;
                    t_init_amount:=last_rec.amount;
                    t_cost_price:=last_rec.cost_price;
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

            --販売出庫時のみ取引額を在庫原価をもとに計算
            IF NEW.transition_type='SELLING' THEN
                NEW.amount:=NEW.quantity * t_cost_price;
            END IF;

            --取引数,取引額計上
            IF NEW.quantity > 0 THEN
                t_warehousing_quantity:=t_warehousing_quantity + NEW.quantity;
            ELSE
                t_shipping_quantity:=t_shipping_quantity - NEW.quantity;
            END IF;
            IF NEW.amount > 0.00 THEN
                t_warehousing_amount:=t_warehousing_amount + NEW.amount;
            ELSE
                t_shipping_amount:=t_shipping_amount - NEW.amount;
            END IF;

            --登録
            IF recent_rec IS NULL THEN
                INSERT INTO inventory.monthry_summaries
                VALUES (
                    NEW.product_id,
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
                WHERE product_id = NEW.product_id AND year_month = yyyymm;
            END IF;

            ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
            --3.最新在庫サマリー(倉庫別)TODO:
            --最新在庫サマリー(倉庫別)検索
            SELECT * INTO recent_rec
            FROM inventory.current_summaries_every_site
            WHERE product_id = NEW.product_id AND site_type = NEW.site_type
            FOR UPDATE;

            --登録
            IF recent_rec IS NULL THEN
                INSERT INTO inventory.current_summaries_every_site
                VALUES (
                    NEW.product_id,
                    NEW.site_type,
                    NEW.quantity
                );
            ELSE
                UPDATE inventory.current_summaries_every_site
                SET quantity = recent_rec.quantity + NEW.quantity
                WHERE product_id = NEW.product_id AND site_type = NEW.site_type;
            END IF;

            ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
            --4.最新在庫サマリーTODO:
            --最新在庫サマリー検索
            SELECT * INTO recent_rec
            FROM inventory.current_summaries
            WHERE product_id = NEW.product_id
            FOR UPDATE;

            --在庫数,在庫額,在庫原価判定
            IF recent_rec IS NULL THEN
                t_quantity:= 0;
                t_amount:=0.00;
                t_cost_price:=0.00;
            ELSE
                t_quantity:=recent_rec.quantity;
                t_amount:=recent_rec.amount;
                t_cost_price:=recent_rec.cost_price;
            END IF;

            --取引数,取引額(販売出庫時のみ在庫原価をもとに計算)計上
            t_quantity:=t_quantity + NEW.quantity;
            IF NEW.transition_type='SELLING' THEN
                t_amount:=t_amount + NEW.quantity * t_cost_price;
            ELSE
                t_amount:=t_amount + NEW.amount;
            END IF;

            --登録
            IF recent_rec IS NULL THEN
                INSERT INTO inventory.current_summaries
                VALUES (
                    NEW.product_id,
                    t_quantity,
                    t_amount
                );
            ELSE
                UPDATE inventory.current_summaries
                SET quantity = t_quantity,
                    amount = t_amount
                WHERE product_id = NEW.product_id;
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
def create_moving_instructions_table() -> None:
    op.create_table(
        "moving_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="倉庫移動指示NO"),
        sa.Column("operation_date", sa.Date, nullable=False, comment="移動日"),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="指示者ID"),
        sa.Column("instruction_cause", sa.Text, nullable=False, comment="倉庫移動理由"),
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
            "quantity", sa.Integer, nullable=False, server_default="0", comment="移動数"
        ),
        schema="inventory",
    )

    op.create_check_constraint(
        "ck_site_type",
        "moving_instructions",
        "site_type_from != site_type_to",
        schema="inventory",
    )
    op.create_check_constraint(
        "ck_quantity",
        "moving_instructions",
        "quantity > 0",
        schema="inventory",
    )
    op.create_foreign_key(
        "fk_operator_id",
        "moving_instructions",
        "profiles",
        ["operator_id"],
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
        ["product_id", "no"],
        schema="inventory",
    )

    # 導出項目計算(処理日付)
    op.execute(
        """
        CREATE TRIGGER insert_moving_instructions
            BEFORE INSERT
            ON inventory.moving_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_operation_date();
        """
    )

    # 登録後処理：在庫変動履歴を自動作成
    op.execute(
        """
        CREATE FUNCTION inventory.create_transition_histories_by_moving() RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO inventory.transition_histories
            VALUES (
                default,
                NEW.operation_date,
                NEW.site_type_from,
                NEW.product_id,
                - NEW.quantity ,
                0.00,
                'MOVEMENT_SHIPPING',
                NEW.no
            );

            INSERT INTO inventory.transition_histories
            VALUES (
                default,
                NEW.operation_date,
                NEW.site_type_to,
                NEW.product_id,
                NEW.quantity ,
                0.00,
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
        sa.Column("operation_date", sa.Date, nullable=False, comment="指示日"),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="指示者ID"),
        sa.Column("instruction_cause", sa.Text, nullable=False, comment="入出庫理由"),
        sa.Column(
            "site_type",
            sa.Enum(*SiteType.list(), name="site_type", schema="mst"),
            nullable=False,
            comment="倉庫種別 ",
        ),
        sa.Column("product_id", sa.String(10), nullable=False, comment="当社商品ID"),
        sa.Column(
            "quantity", sa.Integer, nullable=False, server_default="0", comment="入出庫数"
        ),
        sa.Column(
            "amount", sa.Numeric, nullable=False, server_default="0.00", comment="入出庫額"
        ),
        schema="inventory",
    )

    op.create_foreign_key(
        "fk_operator_id",
        "other_inventory_instructions",
        "profiles",
        ["operator_id"],
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

    # 導出項目計算(処理日付)
    op.execute(
        """
        CREATE TRIGGER insert_other_inventory_instructions
            BEFORE INSERT
            ON inventory.other_inventory_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_operation_date();
        """
    )

    # 登録後処理：在庫変動履歴を自動作成
    op.execute(
        """
        CREATE FUNCTION inventory.create_transition_histories_by_other() RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO inventory.transition_histories
            VALUES (
                default,
                NEW.operation_date,
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


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS inventory.current_summaries_every_site CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.current_summaries CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.monthry_summaries_every_site CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.monthry_summaries CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.moving_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.other_inventory_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory.transition_histories CASCADE;")
    op.execute("DROP TYPE IF EXISTS inventory.transition_type;")
