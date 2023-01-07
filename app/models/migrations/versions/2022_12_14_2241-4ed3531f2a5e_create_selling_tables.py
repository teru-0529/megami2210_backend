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
        sa.Column("coustomer_id", sa.String(4), primary_key=True, comment="得意先ID"),
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
        ["coustomer_id"],
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
        sa.Column("coustomer_id", sa.String(4), nullable=False, comment="得意先ID"),
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
        sa.Column("billing_no", sa.String(10), nullable=False, comment="請求NO"),
        *timestamps(),
        schema="selling",
    )

    op.create_foreign_key(
        "fk_costomer_id",
        "accounts_receivable_histories",
        "costomers",
        ["coustomer_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="selling",
        referent_schema="mst",
    )
    op.create_index(
        "ix_accounts_receivable_histories_supplier",
        "accounts_receivable_histories",
        ["coustomer_id", "transaction_date"],
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
            WHERE coustomer_id = NEW.coustomer_id AND year_month = yyyymm
            FOR UPDATE;

            IF recent_rec IS NULL THEN
                SELECT * INTO last_rec
                FROM selling.accounts_receivables
                WHERE coustomer_id = NEW.coustomer_id
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
                    NEW.coustomer_id,
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
                WHERE coustomer_id = NEW.coustomer_id AND year_month = yyyymm;
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
        sa.Column("coustomer_id", sa.String(4), nullable=False, comment="得意先ID"),
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
        ["coustomer_id"],
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
        ["coustomer_id", "closing_date", "deposit_deadline"],
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
        sa.Column("coustomer_id", sa.String(4), nullable=False, comment="得意先ID"),
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
        ["coustomer_id"],
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
            rec:=mst.calc_deposit_deadline(New.shipping_date, New.coustomer_id);
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
            coustomer_id_from_receiving character(4);
            coustomer_id_from_shipping character(4);
        BEGIN
            SELECT R.coustomer_id INTO coustomer_id_from_receiving
            FROM selling.receiving_details RD
            LEFT OUTER JOIN selling.receivings R ON RD.receiving_no = R.receiving_no
            WHERE RD.detail_no = t_receive_detail_no;

            SELECT coustomer_id INTO coustomer_id_from_shipping
            FROM selling.shippings
            WHERE shipping_no = t_shipping_no;

        RETURN coustomer_id_from_receiving = coustomer_id_from_shipping;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.create_check_constraint(
        "ck_coustomer_id",
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
            WHERE coustomer_id = shipping_rec.coustomer_id
            AND closing_date = shipping_rec.closing_date
            AND deposit_deadline = shipping_rec.deposit_deadline
            FOR UPDATE;

            IF t_billing_price IS NOT NULL THEN
                UPDATE selling.billings
                SET billing_price = t_billing_price + NEW.shipping_quantity * NEW.selling_unit_price
                WHERE coustomer_id = shipping_rec.coustomer_id
                AND closing_date = shipping_rec.closing_date
                AND deposit_deadline = shipping_rec.deposit_deadline;

            ELSE
                INSERT INTO selling.billings
                VALUES (
                    default,
                    shipping_rec.coustomer_id,
                    shipping_rec.closing_date,
                    shipping_rec.deposit_deadline,
                    NEW.shipping_quantity * NEW.selling_unit_price
                );
            END IF;

            -- 売掛変動履歴の登録
            SELECT billing_no INTO t_billing_no
            FROM selling.billings
            WHERE coustomer_id = shipping_rec.coustomer_id
            AND closing_date = shipping_rec.closing_date
            AND deposit_deadline = shipping_rec.deposit_deadline;

            INSERT INTO selling.accounts_receivable_histories
            VALUES (
                default,
                shipping_rec.shipping_date,
                shipping_rec.coustomer_id,
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

            tttt RECORD;
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
    op.execute("CREATE SEQUENCE selling.billing_no_seed START 1;")
    create_accounts_receivables_table()
    create_accounts_receivable_histories_table()
    create_billings_table()
    create_receivings_table()
    create_receiving_details_table()
    create_shippings_table()
    create_shipping_details_table()
    create_shipping_plan_products_table()
    create_view()


def downgrade() -> None:
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
