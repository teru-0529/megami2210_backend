"""create selling tables

Revision ID: 4ed3531f2a5e
Revises: 76241be00f1b
Create Date: 2022-12-14 22:41:16.215287

"""
import sqlalchemy as sa
from alembic import op

from app.models.segment_values import (
    ShippingProductSituation,
    SiteType,
    ReceivableTransitionType,
)
from app.models.migrations.util import timestamps

# revision identifiers, used by Alembic.
revision = "4ed3531f2a5e"
down_revision = "76241be00f1b"
branch_labels = None
depends_on = None

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_accounts_receivables_table() -> None:
    op.create_table(
        "accounts_receivables",
        sa.Column("costomer_id", sa.String(4), primary_key=True, comment="得意先ID"),
        sa.Column("year_month", sa.String(6), primary_key=True, comment="取引年月"),
        sa.Column(
            "init_balance",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="月初残高",
        ),
        sa.Column(
            "selling_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="販売額",
        ),
        sa.Column(
            "deposit_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="入金額",
        ),
        sa.Column(
            "other_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="その他変動額",
        ),
        sa.Column(
            "balance", sa.Numeric, nullable=False, server_default="0.0", comment="残高"
        ),
        *timestamps(),
        schema="selling",
    )

    op.create_foreign_key(
        "fk_costomer_id",
        "accounts_receivables",
        "costomers",
        ["costomer_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER accounts_receivable_modified
            BEFORE UPDATE
            ON selling.accounts_receivables
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION selling.calc_accounts_receivables() RETURNS TRIGGER AS $$
        BEGIN
            NEW.balance:=NEW.init_balance + NEW.selling_amount - NEW.deposit_amount + NEW.other_amount;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER upsert_accounts_receivable
            BEFORE INSERT OR UPDATE
            ON selling.accounts_receivables
            FOR EACH ROW
        EXECUTE PROCEDURE selling.calc_accounts_receivables();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_accounts_receivable_histories_table() -> None:
    op.create_table(
        "accounts_receivable_histories",
        sa.Column("no", sa.Integer, primary_key=True, comment="売掛履歴NO"),
        sa.Column(
            "transaction_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="取引日",
        ),
        sa.Column("costomer_id", sa.String(4), nullable=False, comment="得意先ID"),
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
                *ReceivableTransitionType.list(),
                name="transition_type",
                schema="selling",
            ),
            nullable=False,
            comment="売掛変動区分",
        ),
        sa.Column("transaction_no", sa.Integer, nullable=True, comment="取引管理NO"),
        sa.Column("billing_no", sa.String(10), nullable=True, comment="請求NO"),
        *timestamps(),
        schema="selling",
    )

    op.create_foreign_key(
        "fk_costomer_id",
        "accounts_receivable_histories",
        "costomers",
        ["costomer_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="mst",
    )
    op.create_index(
        "ix_accounts_receivable_histories_supplier",
        "accounts_receivable_histories",
        ["costomer_id", "transaction_date"],
        schema="selling",
    )

    op.execute(
        """
        CREATE TRIGGER accounts_receivable_histories_modified
            BEFORE UPDATE
            ON selling.accounts_receivable_histories
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 登録後、月次売掛金サマリーを自動作成TODO:
    op.execute(
        """
        CREATE FUNCTION selling.set_summaries() RETURNS TRIGGER AS $$
        DECLARE
            yyyymm character(6);
            t_init_balance numeric;
            t_selling_amount numeric;
            t_deposit_amount numeric;
            t_other_amount numeric;

            recent_rec RECORD;
            last_rec RECORD;
        BEGIN
            yyyymm:=to_char(NEW.transaction_date, 'YYYYMM');

            SELECT * INTO recent_rec
            FROM selling.accounts_receivables
            WHERE costomer_id = NEW.costomer_id AND year_month = yyyymm
            FOR UPDATE;

            IF recent_rec IS NULL THEN
                SELECT * INTO last_rec
                FROM selling.accounts_receivables
                WHERE costomer_id = NEW.costomer_id
                ORDER BY year_month DESC
                LIMIT 1;

                IF last_rec IS NULL THEN
                    t_init_balance:=0.00;
                ELSE
                    t_init_balance:=last_rec.balance;
                END IF;

                t_selling_amount:=0.00;
                t_deposit_amount:=0.00;
                t_other_amount:=0.00;

            ELSE
                t_init_balance:=recent_rec.init_balance;
                t_selling_amount:=recent_rec.selling_amount;
                t_deposit_amount:=recent_rec.deposit_amount;
                t_other_amount:=recent_rec.other_amount;
            END IF;

            IF NEW.transition_type='SELLING' OR NEW.transition_type='SALES_RETURN' THEN
                t_selling_amount:=t_selling_amount + NEW.transaction_amount;
            ELSEIF NEW.transition_type='DEPOSIT' THEN
                t_deposit_amount:=t_deposit_amount - NEW.transaction_amount;
            ELSEIF NEW.transition_type='BALANCE_OUT' OR NEW.transition_type='OTHER_TRANSITION' THEN
                t_other_amount:=t_other_amount + NEW.transaction_amount;
            END IF;

            IF recent_rec IS NULL THEN
                INSERT INTO selling.accounts_receivables
                VALUES (
                    NEW.costomer_id,
                    yyyymm,
                    t_init_balance,
                    t_selling_amount,
                    t_deposit_amount,
                    t_other_amount
                );
            ELSE
                UPDATE selling.accounts_receivables
                SET selling_amount = t_selling_amount,
                    deposit_amount = t_deposit_amount,
                    other_amount = t_other_amount
                WHERE costomer_id = NEW.costomer_id AND year_month = yyyymm;
            END IF;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_accounts_receivable_histories
            AFTER INSERT
            ON selling.accounts_receivable_histories
            FOR EACH ROW
        EXECUTE PROCEDURE selling.set_summaries();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_billings_table() -> None:
    op.create_table(
        "billings",
        sa.Column(
            "billing_no",
            sa.String(10),
            primary_key=True,
            server_default="set_me",
            comment="請求NO",
        ),
        sa.Column("costomer_id", sa.String(4), nullable=False, comment="得意先ID"),
        sa.Column(
            "closing_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="請求締日",
        ),
        sa.Column(
            "deposit_deadline",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="入金期限日",
        ),
        sa.Column(
            "billing_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="請求金額",
        ),
        sa.Column(
            "deposited_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="入金済金額",
        ),
        sa.Column(
            "fully_paid",
            sa.Boolean,
            nullable=False,
            server_default="false",
            comment="入金済",
        ),
        sa.Column(
            "billing_send_date",
            sa.Date,
            nullable=True,
            comment="請求書送付日",
        ),
        sa.Column(
            "billing_send_pic", sa.String(5), nullable=True, comment="請求書送付担当者ID"
        ),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        *timestamps(),
        schema="selling",
    )

    op.create_foreign_key(
        "fk_costomer_id",
        "billings",
        "costomers",
        ["costomer_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_billing_send_pic",
        "billings",
        "profiles",
        ["billing_send_pic"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="selling",
        referent_schema="account",
    )
    op.create_unique_constraint(
        "uk_deposit_deadline",
        "billings",
        ["costomer_id", "closing_date", "deposit_deadline"],
        schema="selling",
    )

    op.execute(
        """
        CREATE TRIGGER billings_modified
            BEFORE UPDATE
            ON selling.billings
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION selling.calc_billings() RETURNS TRIGGER AS $$
        BEGIN
            NEW.billing_no:='BL-'||to_char(nextval('selling.billing_no_seed'),'FM0000000');
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_billings
            BEFORE INSERT
            ON selling.billings
            FOR EACH ROW
        EXECUTE PROCEDURE selling.calc_billings();
        """
    )


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
        sa.Column("costomer_id", sa.String(4), nullable=False, comment="得意先ID"),
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
        ["costomer_id"],
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

            -- 処理日付を取得
            SELECT date INTO NEW.receive_date
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';

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
            "selling_unit_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="販売単価",
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
        "ck_selling_unit_price",
        "receiving_details",
        "selling_unit_price > 0",
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

            NEW.assumption_profit_rate:=ROUND((NEW.selling_unit_price - t_cost_price) / NEW.selling_unit_price, 2);

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


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_shippings_table() -> None:
    op.create_table(
        "shippings",
        sa.Column(
            "shipping_no",
            sa.String(10),
            primary_key=True,
            server_default="set_me",
            comment="出荷NO",
        ),
        sa.Column(
            "shipping_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="出荷日",
        ),
        sa.Column("costomer_id", sa.String(4), nullable=False, comment="得意先ID"),
        sa.Column("shipping_pic", sa.String(5), nullable=True, comment="出荷担当者ID"),
        sa.Column(
            "closing_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="請求締日",
        ),
        sa.Column(
            "deposit_deadline",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="入金期限日",
        ),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        *timestamps(),
        schema="selling",
    )

    op.create_foreign_key(
        "fk_costomer_id",
        "shippings",
        "costomers",
        ["costomer_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_shipping_pic",
        "shippings",
        "profiles",
        ["shipping_pic"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="selling",
        referent_schema="account",
    )

    op.execute(
        """
        CREATE TRIGGER shippings_modified
            BEFORE UPDATE
            ON selling.shippings
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION selling.calc_shippings() RETURNS TRIGGER AS $$
        DECLARE
            rec record;

        BEGIN
            NEW.shipping_no:='SP-'||to_char(nextval('selling.shipping_no_seed'),'FM0000000');

            -- 処理日付を取得
            SELECT date INTO NEW.shipping_date
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';

            -- 締日・入金期限の計算
            rec:=mst.calc_deposit_deadline(New.shipping_date, New.costomer_id);
            New.closing_date:=rec.closing_date;
            New.deposit_deadline:=rec.deposit_deadline;
            New.note:=rec.dummy;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_shippings
            BEFORE INSERT
            ON selling.shippings
            FOR EACH ROW
        EXECUTE PROCEDURE selling.calc_shippings();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_shipping_details_table() -> None:
    op.create_table(
        "shipping_details",
        sa.Column("detail_no", sa.Integer, primary_key=True, comment="出荷明細NO"),
        sa.Column("shipping_no", sa.String(10), nullable=False, comment="出荷NO"),
        sa.Column("receive_detail_no", sa.Integer, nullable=False, comment="受注明細NO"),
        sa.Column(
            "product_id",
            sa.String(10),
            nullable=False,
            server_default="set_me",
            comment="当社商品ID",
        ),
        sa.Column(
            "shipping_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="出荷数",
        ),
        sa.Column(
            "return_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="返品数",
        ),
        sa.Column(
            "selling_unit_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="販売単価",
        ),
        sa.Column(
            "cost_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="原価",
        ),
        sa.Column(
            "real_profit_rate",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="実利益率",
        ),
        sa.Column(
            "site_type",
            sa.Enum(*SiteType.list(), name="site_type", schema="mst"),
            nullable=False,
            server_default=SiteType.main,
            comment="出荷倉庫種別 ",
        ),
        *timestamps(),
        schema="selling",
    )

    # 受注時の得意先と等しいこと(相関チェック)
    op.execute(
        """
        CREATE FUNCTION selling.ck_coustomer_with_receiving(
            t_shipping_no character(10),
            t_receive_detail_no integer
        ) RETURNS boolean AS $$
        DECLARE
            costomer_id_from_receiving character(4);
            costomer_id_from_shipping character(4);
        BEGIN
            SELECT R.costomer_id INTO costomer_id_from_receiving
            FROM selling.receiving_details RD
            LEFT OUTER JOIN selling.receivings R ON RD.receiving_no = R.receiving_no
            WHERE RD.detail_no = t_receive_detail_no;

            SELECT costomer_id INTO costomer_id_from_shipping
            FROM selling.shippings
            WHERE shipping_no = t_shipping_no;

        RETURN costomer_id_from_receiving = costomer_id_from_shipping;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.create_check_constraint(
        "ck_costomer_id",
        "shipping_details",
        "selling.ck_coustomer_with_receiving(shipping_no, receive_detail_no)",
        schema="selling",
    )
    op.create_check_constraint(
        "ck_shipping_quantity",
        "shipping_details",
        "shipping_quantity > 0",
        schema="selling",
    )
    op.create_check_constraint(
        "ck_return_quantity",
        "shipping_details",
        "return_quantity >= 0",
        schema="selling",
    )
    op.create_check_constraint(
        "ck_quantity",
        "shipping_details",
        "return_quantity <= shipping_quantity",
        schema="selling",
    )
    op.create_check_constraint(
        "ck_selling_unit_price",
        "shipping_details",
        "selling_unit_price > 0",
        schema="selling",
    )
    op.create_check_constraint(
        "ck_cost_price",
        "shipping_details",
        "cost_price > 0",
        schema="selling",
    )
    op.create_foreign_key(
        "fk_shipping_no",
        "shipping_details",
        "shippings",
        ["shipping_no"],
        ["shipping_no"],
        ondelete="CASCADE",
        source_schema="selling",
        referent_schema="selling",
    )
    op.create_foreign_key(
        "fk_receive_detail_no",
        "shipping_details",
        "receiving_details",
        ["receive_detail_no"],
        ["detail_no"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="selling",
    )
    op.create_index(
        "ix_shipping_details_shipping",
        "shipping_details",
        ["shipping_no", "detail_no"],
        schema="selling",
    )

    op.execute(
        """
        CREATE TRIGGER shipping_details_modified
            BEFORE UPDATE
            ON selling.shipping_details
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION selling.calc_shipping_details() RETURNS TRIGGER AS $$
        BEGIN
            -- 受注明細から商品番号を取得
            SELECT product_id INTO NEW.product_id
            FROM selling.receiving_details
            WHERE detail_no = NEW.receive_detail_no;

            -- 在庫サマリから原価を取得
            SELECT cost_price INTO NEW.cost_price
            FROM inventory.current_summaries
            WHERE product_id = NEW.product_id;

            -- 実利益率を計算
            NEW.real_profit_rate:=ROUND((NEW.selling_unit_price - NEW.cost_price) / NEW.selling_unit_price, 2);
            NEW.return_quantity:=0;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_shipping_details
            BEFORE INSERT
            ON selling.shipping_details
            FOR EACH ROW
        EXECUTE PROCEDURE selling.calc_shipping_details();
        """
    )

    # 在庫変動履歴/入金/売掛金変動履歴の登録TODO:
    op.execute(
        """
        CREATE FUNCTION selling.set_inventories_and_deposits() RETURNS TRIGGER AS $$
        DECLARE
            t_shipping_quantity integer;
            t_billing_price numeric;
            t_billing_no text;

            shipping_rec record;
        BEGIN
            -- 受注残数の更新
            SELECT shipping_quantity INTO t_shipping_quantity
            FROM selling.receiving_details
            WHERE detail_no = NEW.receive_detail_no
            FOR UPDATE;

            UPDATE selling.receiving_details
            SET shipping_quantity = t_shipping_quantity + NEW.shipping_quantity
            WHERE detail_no = NEW.receive_detail_no;

            -- 在庫変動履歴の登録
            SELECT * INTO shipping_rec
            FROM selling.shippings
            WHERE shipping_no = NEW.shipping_no;

            INSERT INTO inventory.transition_histories
            VALUES (
                default,
                shipping_rec.shipping_date,
                NEW.site_type,
                NEW.product_id,
                - NEW.shipping_quantity,
                - NEW.shipping_quantity * NEW.cost_price,
                'SELLING',
                NEW.detail_no
            );

            -- 請求の登録、更新
            SELECT billing_price INTO t_billing_price
            FROM selling.billings
            WHERE costomer_id = shipping_rec.costomer_id
            AND closing_date = shipping_rec.closing_date
            AND deposit_deadline = shipping_rec.deposit_deadline
            FOR UPDATE;

            IF t_billing_price IS NOT NULL THEN
                UPDATE selling.billings
                SET billing_price = t_billing_price + NEW.shipping_quantity * NEW.selling_unit_price
                WHERE costomer_id = shipping_rec.costomer_id
                AND closing_date = shipping_rec.closing_date
                AND deposit_deadline = shipping_rec.deposit_deadline;

            ELSE
                INSERT INTO selling.billings
                VALUES (
                    default,
                    shipping_rec.costomer_id,
                    shipping_rec.closing_date,
                    shipping_rec.deposit_deadline,
                    NEW.shipping_quantity * NEW.selling_unit_price
                );
            END IF;

            -- 売掛変動履歴の登録
            SELECT billing_no INTO t_billing_no
            FROM selling.billings
            WHERE costomer_id = shipping_rec.costomer_id
            AND closing_date = shipping_rec.closing_date
            AND deposit_deadline = shipping_rec.deposit_deadline;

            INSERT INTO selling.accounts_receivable_histories
            VALUES (
                default,
                shipping_rec.shipping_date,
                shipping_rec.costomer_id,
                NEW.shipping_quantity * NEW.selling_unit_price,
                'SELLING',
                NEW.detail_no,
                t_billing_no
            );

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_shipping_details
            AFTER INSERT
            ON selling.shipping_details
            FOR EACH ROW
        EXECUTE PROCEDURE selling.set_inventories_and_deposits();
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

            ordered_cursor refcursor;
            rec RECORD;

            ordering_dates RECORD;

        BEGIN
            i_product_id:=NEW.product_id;
            t_priority:=0;

            SELECT date INTO t_today
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';

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
            SELECT
                detail_no,
                (purchase_quantity - wearhousing_quantity - cancel_quantity) AS remaining_quantity,
                estimate_arrival_date
            FROM purchase.ordering_details
            WHERE product_id = i_product_id
            AND   (purchase_quantity - wearhousing_quantity - cancel_quantity) > 0
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
                    t_plan_quantity:=t_plan_quantity - t_quantity;
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
def create_receive_cancel_instructions_table() -> None:
    op.create_table(
        "receive_cancel_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="キャンセル指示NO"),
        sa.Column(
            "instruction_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="指示日",
        ),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="指示者ID"),
        sa.Column("cancel_reason", sa.Text, nullable=False, comment="キャンセル理由"),
        sa.Column("receive_detail_no", sa.Integer, nullable=False, comment="受注明細NO"),
        sa.Column(
            "calcel_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="キャンセル数",
        ),
        *timestamps(),
        schema="selling",
    )

    op.create_check_constraint(
        "ck_calcel_quantity",
        "receive_cancel_instructions",
        "calcel_quantity > 0",
        schema="selling",
    )
    op.create_foreign_key(
        "fk_operator_id",
        "receive_cancel_instructions",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="selling",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_receive_detail_no",
        "receive_cancel_instructions",
        "receiving_details",
        ["receive_detail_no"],
        ["detail_no"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="selling",
    )

    op.execute(
        """
        CREATE TRIGGER receive_cancel_instructions_modified
            BEFORE UPDATE
            ON selling.receive_cancel_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION selling.calc_receive_cancel_instructions() RETURNS TRIGGER AS $$
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
        CREATE TRIGGER insert_receive_cancel_instructions
            BEFORE INSERT
            ON selling.receive_cancel_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE selling.calc_receive_cancel_instructions();
        """
    )

    # 発注明細の変更TODO:
    op.execute(
        """
        CREATE FUNCTION selling.update_receive_quantity() RETURNS TRIGGER AS $$
        DECLARE
            t_cancel_quantity integer;
        BEGIN
            -- キャンセル数の更新
            SELECT cancel_quantity INTO t_cancel_quantity
            FROM selling.receiving_details
            WHERE detail_no = NEW.receive_detail_no
            FOR UPDATE;

            UPDATE selling.receiving_details
            SET cancel_quantity = t_cancel_quantity + NEW.calcel_quantity
            WHERE detail_no = NEW.receive_detail_no;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_receive_cancel_instructions
            AFTER INSERT
            ON selling.receive_cancel_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE selling.update_receive_quantity();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_sending_bill_instructions_table() -> None:
    op.create_table(
        "sending_bill_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="請求書送付NO"),
        sa.Column(
            "instruction_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="送付日",
        ),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="送付担当者ID"),
        sa.Column(
            "billing_no",
            sa.String(10),
            nullable=False,
            server_default="set_me",
            comment="請求NO",
        ),
        *timestamps(),
        schema="selling",
    )

    op.create_foreign_key(
        "fk_operator_id",
        "sending_bill_instructions",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="selling",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_payment_no",
        "sending_bill_instructions",
        "billings",
        ["billing_no"],
        ["billing_no"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="selling",
    )
    op.create_index(
        "ix_sending_bill_instructions_billing_no",
        "sending_bill_instructions",
        ["billing_no"],
        unique=True,
        schema="selling",
    )

    op.execute(
        """
        CREATE TRIGGER sending_bill_instructions_modified
            BEFORE UPDATE
            ON selling.sending_bill_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION selling.calc_sending_bill_instructions() RETURNS TRIGGER AS $$
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
        CREATE TRIGGER insert_sending_bill_instructions
            BEFORE INSERT
            ON selling.sending_bill_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE selling.calc_sending_bill_instructions();
        """
    )

    # 請求書送付後処理TODO:
    op.execute(
        """
        CREATE FUNCTION selling.set_send_bill() RETURNS TRIGGER AS $$
        DECLARE
            rec RECORD;
        BEGIN

            -- 請求へ、送付日、送付担当者の登録
            UPDATE selling.billings
            SET billing_send_date = NEW.instruction_date, billing_send_pic = NEW.operator_id
            WHERE billing_no = NEW.billing_no;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_sending_bill_instructions
            AFTER INSERT
            ON selling.sending_bill_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE selling.set_send_bill();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_deposit_instructions_table() -> None:
    op.create_table(
        "deposit_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="入金NO"),
        sa.Column(
            "instruction_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="入金日",
        ),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="入金確認者ID"),
        sa.Column("costomer_id", sa.String(4), nullable=False, comment="得意先ID"),
        sa.Column(
            "deposit_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="入金額",
        ),
        *timestamps(),
        schema="selling",
    )

    op.create_foreign_key(
        "fk_operator_id",
        "deposit_instructions",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="selling",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_costomer_id",
        "deposit_instructions",
        "costomers",
        ["costomer_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER deposit_instructions_modified
            BEFORE UPDATE
            ON selling.deposit_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION selling.calc_deposit_instructions() RETURNS TRIGGER AS $$
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
        CREATE TRIGGER insert_deposit_instructions
            BEFORE INSERT
            ON selling.deposit_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE selling.calc_deposit_instructions();
        """
    )

    # 入金指示後、入金日時更新、売掛変動履歴を自動作成TODO:
    op.execute(
        """
        CREATE FUNCTION selling.set_deposit() RETURNS TRIGGER AS $$
        DECLARE
            billing_cursor refcursor;
            rec record;

            t_deposit numeric;

            t_closing_date date;
            t_deposit_deadline date;
            t_deposited_price numeric;
            --t_billing_no text;

            --rec record;
        BEGIN

            -- 売掛変動履歴の登録
            INSERT INTO selling.accounts_receivable_histories
            VALUES (
                default,
                NEW.instruction_date,
                NEW.costomer_id,
                - NEW.deposit_amount,
                'DEPOSIT',
                NEW.no
            );

            -- 請求へ、金額の充当
            OPEN billing_cursor FOR
            SELECT *
            FROM selling.billings
            WHERE costomer_id = NEW.costomer_id
            AND fully_paid = false
            ORDER BY closing_date ASC;

            t_deposit:=NEW.deposit_amount;
            LOOP
                FETCH billing_cursor INTO rec;
                IF NOT FOUND THEN
                    EXIT;
                END IF;
                IF t_deposit = 0.0 THEN
                    EXIT;
                END IF;

                IF rec.billing_price - rec.deposited_price > t_deposit THEN
                    UPDATE selling.billings
                    SET deposited_price = rec.deposited_price + t_deposit
                    WHERE billing_no = rec.billing_no;

                    t_deposit:=0.0;

                ELSE
                    UPDATE selling.billings
                    SET deposited_price = rec.billing_price,
                        fully_paid = true
                    WHERE billing_no = rec.billing_no;

                    t_deposit:=t_deposit - (rec.billing_price - rec.deposited_price);

                END IF;

            END LOOP;
            CLOSE billing_cursor;

            --残額がある場合は、新規の請求に計上
            IF t_deposit = 0.0 THEN
                return NEW;
            END IF;

            -- 締日、入金期限の算出
            rec:=mst.calc_deposit_deadline(New.instruction_date, New.costomer_id);
            t_closing_date:=rec.closing_date;
            t_deposit_deadline:=rec.deposit_deadline;

            -- 請求の登録、更新
            SELECT deposited_price INTO t_deposited_price
            FROM selling.billings
            WHERE costomer_id = NEW.costomer_id
            AND closing_date = t_closing_date
            AND deposit_deadline = t_deposit_deadline
            FOR UPDATE;

            IF t_deposited_price IS NOT NULL THEN
                UPDATE selling.billings
                SET deposited_price = t_deposited_price + t_deposit
                WHERE costomer_id = NEW.costomer_id
                AND closing_date = t_closing_date
                AND deposit_deadline = t_deposit_deadline;

            ELSE
                INSERT INTO selling.billings
                VALUES (
                    default,
                    NEW.costomer_id,
                    t_closing_date,
                    t_deposit_deadline,
                    0.0,
                    t_deposit
                );
            END IF;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_deposit_instructions
            AFTER INSERT
            ON selling.deposit_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE selling.set_deposit();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_selling_return_instructions_table() -> None:
    op.create_table(
        "selling_return_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="返品指示NO"),
        sa.Column(
            "instruction_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="指示日",
        ),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="指示者ID"),
        sa.Column("return_reason", sa.Text, nullable=False, comment="返品理由"),
        sa.Column("shipping_detail_no", sa.Integer, nullable=True, comment="出荷明細NO"),
        sa.Column("costomer_id", sa.String(4), nullable=False, comment="得意先ID"),
        sa.Column(
            "product_id",
            sa.String(10),
            nullable=False,
            server_default="set_me",
            comment="当社商品ID",
        ),
        sa.Column(
            "return_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="返品数",
        ),
        sa.Column(
            "selling_unit_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="返品単価",
        ),
        sa.Column(
            "cost_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="返品原価",
        ),
        sa.Column(
            "site_type",
            sa.Enum(*SiteType.list(), name="site_type", schema="mst"),
            nullable=False,
            server_default=SiteType.main,
            comment="返品先倉庫種別 ",
        ),
        *timestamps(),
        schema="selling",
    )

    op.create_check_constraint(
        "ck_return_quantity",
        "selling_return_instructions",
        "return_quantity > 0",
        schema="selling",
    )
    op.create_check_constraint(
        "ck_selling_unit_price",
        "selling_return_instructions",
        "selling_unit_price > 0",
        schema="selling",
    )
    op.create_check_constraint(
        "ck_cost_price",
        "selling_return_instructions",
        "cost_price > 0",
        schema="selling",
    )
    op.create_foreign_key(
        "fk_operator_id",
        "selling_return_instructions",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="selling",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_shipping_detail_no",
        "selling_return_instructions",
        "shipping_details",
        ["shipping_detail_no"],
        ["detail_no"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="selling",
    )
    op.create_foreign_key(
        "fk_costomer_id",
        "selling_return_instructions",
        "costomers",
        ["costomer_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER selling_return_instructions_modified
            BEFORE UPDATE
            ON selling.selling_return_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION selling.calc_selling_return_instructions() RETURNS TRIGGER AS $$
        DECLARE
            rec record;
        BEGIN
            -- 処理日付を取得
            SELECT date INTO NEW.instruction_date
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';

            IF NEW.shipping_detail_no IS NOT NULL THEN
                -- 出荷明細から当社商品ID、得意先ID、返品単価、返品原価を取得
                SELECT * INTO rec
                FROM selling.shipping_details
                WHERE detail_no = NEW.shipping_detail_no
                FOR UPDATE;

                SELECT costomer_id INTO NEW.costomer_id
                FROM selling.shippings
                WHERE shipping_no = rec.shipping_no;

                -- 入荷明細に返品数を登録
                UPDATE selling.shipping_details
                SET return_quantity = rec.return_quantity + NEW.return_quantity
                WHERE detail_no = NEW.shipping_detail_no;

                NEW.product_id:= rec.product_id;
                NEW.selling_unit_price:= rec.selling_unit_price;
                NEW.cost_price:= rec.cost_price;

            END iF;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_selling_return_instructions
            BEFORE INSERT
            ON selling.selling_return_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE selling.calc_selling_return_instructions();
        """
    )

    # 在庫変動履歴/請求/売掛金変動履歴の登録TODO:
    op.execute(
        """
        CREATE FUNCTION selling.set_inventories_and_billings_by_return() RETURNS TRIGGER AS $$
        DECLARE
            t_closing_date date;
            t_deposit_deadline date;
            t_billing_price numeric;
            t_billing_no text;

            rec record;
        BEGIN
            -- 締日、入金期限の算出
            rec:=mst.calc_deposit_deadline(New.instruction_date, New.costomer_id);
            t_closing_date:=rec.closing_date;
            t_deposit_deadline:=rec.deposit_deadline;

            -- 在庫変動履歴の登録
            INSERT INTO inventory.transition_histories
            VALUES (
                default,
                NEW.instruction_date,
                NEW.site_type,
                NEW.product_id,
                NEW.return_quantity,
                NEW.return_quantity * NEW.cost_price,
                'SALES_RETURN',
                NEW.no
            );

            -- 請求の登録、更新
            SELECT billing_price INTO t_billing_price
            FROM selling.billings
            WHERE costomer_id = NEW.costomer_id
            AND closing_date = t_closing_date
            AND deposit_deadline = t_deposit_deadline
            FOR UPDATE;

            IF t_billing_price IS NOT NULL THEN
                UPDATE selling.billings
                SET billing_price = t_billing_price - NEW.return_quantity * NEW.selling_unit_price
                WHERE costomer_id = NEW.costomer_id
                AND closing_date = t_closing_date
                AND deposit_deadline = t_deposit_deadline;

            ELSE
                INSERT INTO selling.billings
                VALUES (
                    default,
                    NEW.costomer_id,
                    t_closing_date,
                    t_deposit_deadline,
                    - NEW.return_quantity * NEW.selling_unit_price
                );
            END IF;

            -- 売掛変動履歴の登録
            SELECT billing_no INTO t_billing_no
            FROM selling.billings
            WHERE costomer_id = NEW.costomer_id
            AND closing_date = t_closing_date
            AND deposit_deadline = t_deposit_deadline;

            INSERT INTO selling.accounts_receivable_histories
            VALUES (
                default,
                NEW.instruction_date,
                NEW.costomer_id,
                - NEW.return_quantity * NEW.selling_unit_price,
                'SALES_RETURN',
                NEW.no,
                t_billing_no
            );

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_selling_return_instructions
            AFTER INSERT
            ON selling.selling_return_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE selling.set_inventories_and_billings_by_return();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_other_selling_instructions_table() -> None:
    op.create_table(
        "other_selling_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="雑売上指示NO"),
        sa.Column(
            "instruction_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="指示日",
        ),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="指示者ID"),
        sa.Column("instruction_cause", sa.Text, nullable=False, comment="変動理由"),
        sa.Column("costomer_id", sa.String(4), nullable=False, comment="得意先ID"),
        sa.Column(
            "transition_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="変動金額",
        ),
        *timestamps(),
        schema="selling",
    )

    op.create_foreign_key(
        "fk_operator_id",
        "other_selling_instructions",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="selling",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_costomer_id",
        "other_selling_instructions",
        "costomers",
        ["costomer_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER other_selling_instructions_modified
            BEFORE UPDATE
            ON selling.other_selling_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION selling.calc_other_selling_instructions() RETURNS TRIGGER AS $$
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
        CREATE TRIGGER insert_other_selling_instructions
            BEFORE INSERT
            ON selling.other_selling_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE selling.calc_other_selling_instructions();
        """
    )

    # 請求/売掛金変動履歴の登録TODO:
    op.execute(
        """
        CREATE FUNCTION selling.set_billings_by_other_instruction() RETURNS TRIGGER AS $$
        DECLARE
            t_closing_date date;
            t_deposit_deadline date;
            t_billing_price numeric;
            t_billing_no text;

            rec record;
        BEGIN
            -- 締日、入金期限の算出
            rec:=mst.calc_deposit_deadline(New.instruction_date, New.costomer_id);
            t_closing_date:=rec.closing_date;
            t_deposit_deadline:=rec.deposit_deadline;

            -- 請求の登録、更新
            SELECT billing_price INTO t_billing_price
            FROM selling.billings
            WHERE costomer_id = NEW.costomer_id
            AND closing_date = t_closing_date
            AND deposit_deadline = t_deposit_deadline
            FOR UPDATE;

            IF t_billing_price IS NOT NULL THEN
                UPDATE selling.billings
                SET billing_price = t_billing_price + NEW.transition_amount
                WHERE costomer_id = NEW.costomer_id
                AND closing_date = t_closing_date
                AND deposit_deadline = t_deposit_deadline;

            ELSE
                INSERT INTO selling.billings
                VALUES (
                    default,
                    NEW.costomer_id,
                    t_closing_date,
                    t_deposit_deadline,
                    NEW.transition_amount
                );
            END IF;

            -- 売掛変動履歴の登録
            SELECT billing_no INTO t_billing_no
            FROM selling.billings
            WHERE costomer_id = NEW.costomer_id
            AND closing_date = t_closing_date
            AND deposit_deadline = t_deposit_deadline;

            INSERT INTO selling.accounts_receivable_histories
            VALUES (
                default,
                NEW.instruction_date,
                NEW.costomer_id,
                NEW.transition_amount,
                'OTHER_TRANSITION',
                NEW.no,
                t_billing_no
            );

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_other_selling_instructions
            AFTER INSERT
            ON selling.other_selling_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE selling.set_billings_by_other_instruction();
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
                R.costomer_id,
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
    op.execute("CREATE SEQUENCE selling.billing_no_seed START 1;")
    create_accounts_receivables_table()
    create_accounts_receivable_histories_table()
    create_billings_table()
    create_receivings_table()
    create_receiving_details_table()
    create_shippings_table()
    create_shipping_details_table()
    create_shipping_plan_products_table()
    create_receive_cancel_instructions_table()
    create_sending_bill_instructions_table()
    create_deposit_instructions_table()
    create_selling_return_instructions_table()
    create_other_selling_instructions_table()
    create_view()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS selling.other_selling_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.selling_return_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.deposit_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.sending_bill_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.receive_cancel_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.shipping_plan_products CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.shipping_details CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.shippings CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.receiving_details CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.receivings CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.billings CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.accounts_receivable_histories CASCADE;")
    op.execute("DROP TABLE IF EXISTS selling.accounts_receivables CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS selling.billing_no_seed CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS selling.receiving_no_seed CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS selling.shipping_no_seed CASCADE;")
