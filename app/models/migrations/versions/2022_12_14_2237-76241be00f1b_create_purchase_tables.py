"""create purchase tables

Revision ID: 76241be00f1b
Revises: f3ef6aa8d42a
Create Date: 2022-12-14 22:37:45.628970

"""
import sqlalchemy as sa
from alembic import op

from app.models.migrations.util import timestamps
from app.models.segment_values import paymentSituation, PayableTransitionType

# revision identifiers, used by Alembic.
revision = "76241be00f1b"
down_revision = "f3ef6aa8d42a"
branch_labels = None
depends_on = None

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_accounts_payables_table() -> None:
    op.create_table(
        "accounts_payables",
        sa.Column("supplier_id", sa.String(4), primary_key=True, comment="仕入先ID"),
        sa.Column("year_month", sa.String(6), primary_key=True, comment="取引年月"),
        sa.Column(
            "init_balance",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="月初残高",
        ),
        sa.Column(
            "purchase_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="購入額",
        ),
        sa.Column(
            "payment_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="支払額",
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
        schema="purchase",
    )

    op.create_foreign_key(
        "fk_supplier_id",
        "accounts_payables",
        "suppliers",
        ["supplier_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER accounts_payables_modified
            BEFORE UPDATE
            ON purchase.accounts_payables
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_accounts_payables() RETURNS TRIGGER AS $$
        BEGIN
            NEW.balance:=NEW.init_balance + NEW.purchase_amount - NEW.payment_amount;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER upsert_accounts_payables
            BEFORE INSERT OR UPDATE
            ON purchase.accounts_payables
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.calc_accounts_payables();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_accounts_payable_histories_table() -> None:
    op.create_table(
        "accounts_payable_histories",
        sa.Column("no", sa.Integer, primary_key=True, comment="買掛履歴NO"),
        sa.Column(
            "transaction_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="取引日",
        ),
        sa.Column("supplier_id", sa.String(4), nullable=False, comment="仕入先ID"),
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
                *PayableTransitionType.list(), name="transition_type", schema="purchase"
            ),
            nullable=False,
            comment="買掛変動区分",
        ),
        sa.Column("transition_reason", sa.Text, nullable=True, comment="買掛変動理由"),
        sa.Column(
            "transaction_no",
            sa.Integer,
            nullable=False,
            comment="取引管理NO",
        ),
        *timestamps(),
        schema="purchase",
    )

    # 「買掛変動区分」が「その他取引」の場合は、「買掛変動理由」が必須、「その他取引」以外の場合は「買掛変動理由」を指定してはいけない
    ck_transition_reason: str = """
    CASE
        WHEN transition_type='OTHER_TRANSITION' AND transition_reason IS NULL THEN FALSE
        WHEN transition_type!='OTHER_TRANSITION' AND transition_reason IS NOT NULL THEN FALSE
        ELSE TRUE
    END
    """
    op.create_check_constraint(
        "ck_transition_reason",
        "accounts_payable_histories",
        ck_transition_reason,
        schema="purchase",
    )
    op.create_foreign_key(
        "fk_supplier_id",
        "accounts_payable_histories",
        "suppliers",
        ["supplier_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="mst",
    )
    op.create_index(
        "ix_accounts_payable_histories_supplier",
        "accounts_payable_histories",
        ["supplier_id", "transaction_date"],
        schema="purchase",
    )

    op.execute(
        """
        CREATE TRIGGER accounts_payable_histories_modified
            BEFORE UPDATE
            ON purchase.accounts_payable_histories
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # # 導出項目計算
    # op.execute(
    #     """
    #     CREATE FUNCTION purchase.calc_accounts_payables() RETURNS TRIGGER AS $$
    #     BEGIN
    #         NEW.balance:=NEW.init_balance + NEW.purchase_amount - NEW.payment_amount;
    #         return NEW;
    #     END;
    #     $$ LANGUAGE plpgsql;
    #     """
    # )
    # 登録後、月次買掛金サマリーを自動作成TODO:
    op.execute(
        """
        CREATE FUNCTION purchase.set_summaries() RETURNS TRIGGER AS $$
        DECLARE
            yyyymm character(6);
            t_init_balance numeric;
            t_purchase_amount numeric;
            t_payment_amount numeric;
            t_other_amount numeric;

            recent_rec RECORD;
            last_rec RECORD;
        BEGIN
            yyyymm:=to_char(NEW.transaction_date, 'YYYYMM');

            SELECT * INTO recent_rec
                FROM purchase.accounts_payables
                WHERE supplier_id = NEW.supplier_id AND year_month = yyyymm
                FOR UPDATE;

            IF recent_rec IS NULL THEN
                SELECT * INTO last_rec
                    FROM purchase.accounts_payables
                    WHERE supplier_id = NEW.supplier_id
                    ORDER BY year_month DESC
                    LIMIT 1;

                IF last_rec IS NULL THEN
                    t_init_balance:=0.00;
                ELSE
                    t_init_balance:=last_rec.balance;
                END IF;

                t_purchase_amount:=0.00;
                t_payment_amount:=0.00;
                t_other_amount:=0.00;

            ELSE
                t_init_balance:=recent_rec.init_balance;
                t_purchase_amount:=recent_rec.purchase_amount;
                t_payment_amount:=recent_rec.payment_amount;
                t_other_amount:=recent_rec.other_amount;
            END IF;

            IF NEW.transition_type='PURCHASE' OR NEW.transition_type='ORDERING_RETURN' THEN
                t_purchase_amount:=t_purchase_amount + NEW.transaction_amount;
            ELSEIF NEW.transition_type='SELLING' THEN
                t_payment_amount:=t_payment_amount - NEW.transaction_amount;
            ELSEIF NEW.transition_type='BALANCE_OUT' OR NEW.transition_type='OTHER_TRANSITION' THEN
                t_other_amount:=t_other_amount + NEW.transaction_amount;
            END IF;

            IF recent_rec IS NULL THEN
                INSERT INTO purchase.accounts_payables
                VALUES (
                    NEW.supplier_id,
                    yyyymm,
                    t_init_balance,
                    t_purchase_amount,
                    t_payment_amount,
                    t_other_amount
                );
            ELSE
                UPDATE purchase.accounts_payables
                SET purchase_amount = t_purchase_amount,
                    payment_amount = t_payment_amount,
                    other_amount = t_other_amount
                WHERE supplier_id = NEW.supplier_id AND year_month = yyyymm;
            END IF;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_accounts_payable_histories
            AFTER INSERT
            ON purchase.accounts_payable_histories
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.set_summaries();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_payments_table() -> None:
    op.create_table(
        "payments",
        sa.Column(
            "payment_no",
            sa.String(10),
            primary_key=True,
            server_default="set_me",
            comment="支払NO",
        ),
        sa.Column("supplier_id", sa.String(4), nullable=False, comment="仕入先ID"),
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
        sa.Column(
            "payment_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="支払金額",
        ),
        sa.Column(
            "payment_check_datetime",
            sa.DateTime,
            nullable=True,
            comment="請求書確認日時",
        ),
        sa.Column("payment_check_pic", sa.String(5), nullable=True, comment="請求書確認者ID"),
        sa.Column(
            "payment_datetime",
            sa.DateTime,
            nullable=True,
            comment="支払実施日時",
        ),
        sa.Column("payment_pic", sa.String(5), nullable=True, comment="支払実施者ID"),
        sa.Column(
            "situation",
            sa.Enum(
                *paymentSituation.list(), name="payment_situation", schema="purchase"
            ),
            nullable=False,
            server_default=paymentSituation.before_closing,
            comment="支払状況",
        ),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        *timestamps(),
        schema="purchase",
    )

    op.create_foreign_key(
        "fk_supplier_id",
        "payments",
        "suppliers",
        ["supplier_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_payment_check_pic",
        "payments",
        "profiles",
        ["payment_check_pic"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="purchase",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_payment_pic",
        "payments",
        "profiles",
        ["payment_pic"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="purchase",
        referent_schema="account",
    )
    op.create_unique_constraint(
        "uk_payment_deadline",
        "payments",
        ["supplier_id", "closing_date", "payment_deadline"],
        schema="purchase",
    )

    op.execute(
        """
        CREATE TRIGGER payments_modified
            BEFORE UPDATE
            ON purchase.payments
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_payments() RETURNS TRIGGER AS $$
        BEGIN
            NEW.payment_no:='PM-'||to_char(nextval('purchase.payment_no_seed'),'FM0000000');
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_payments
            BEFORE INSERT
            ON purchase.payments
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.calc_payments();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
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

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_orderings() RETURNS TRIGGER AS $$
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
        EXECUTE PROCEDURE purchase.calc_orderings();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
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

    # 発注仕入先の商品であること(相関チェック)
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

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_ordering_details() RETURNS TRIGGER AS $$
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
        CREATE TRIGGER insert_ordering_details
            BEFORE INSERT
            ON purchase.ordering_details
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.calc_ordering_details();
        """
    )

    # 在庫変動予定の登録TODO:
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

                -- 受払予定を登録
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
                ); --FIXME:区分値の整備
            END IF;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_upsert_ordering_details
            AFTER INSERT OR UPDATE
            ON purchase.ordering_details
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.set_transition_estimates();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
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

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_wearhousings() RETURNS TRIGGER AS $$
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
        EXECUTE PROCEDURE purchase.calc_wearhousings();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
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

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_wearhousing_details() RETURNS TRIGGER AS $$
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
        CREATE TRIGGER insert_wearhousing_details
            BEFORE INSERT
            ON purchase.wearhousing_details
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.calc_wearhousing_details();
        """
    )

    # 在庫変動履歴/支払/買掛金の登録TODO:
    op.execute(
        """
        CREATE FUNCTION purchase.set_transition_histories_and_payments() RETURNS TRIGGER AS $$
        DECLARE
            t_wearhousing_quantity integer;
            t_wearhousing_date date;
            t_payment_price numeric;

            wearhousing_rec record;
        BEGIN
            -- 発注残数の更新
            SELECT wearhousing_quantity INTO t_wearhousing_quantity
            FROM purchase.ordering_details
            WHERE detail_no = NEW.order_detail_no
            FOR UPDATE;

            UPDATE purchase.ordering_details
            SET wearhousing_quantity = t_wearhousing_quantity + NEW.wearhousing_quantity
            WHERE detail_no = NEW.order_detail_no;

            -- 在庫変動履歴の登録
            SELECT * INTO wearhousing_rec
            FROM purchase.wearhousings
            WHERE wearhousing_no = NEW.wearhousing_no;

            INSERT INTO inventory.transition_histories
            VALUES (
                default,
                wearhousing_rec.wearhousing_date,
                NEW.site_id,
                NEW.product_id,
                NEW.wearhousing_quantity,
                NEW.wearhousing_quantity * NEW.wearhousing_unit_price,
                'PURCHASE',
                null,
                NEW.detail_no
            );

            -- 支払の登録、更新
            SELECT payment_price INTO t_payment_price
            FROM purchase.payments
            WHERE supplier_id = wearhousing_rec.supplier_id
            AND closing_date = wearhousing_rec.closing_date
            AND payment_deadline = wearhousing_rec.payment_deadline
            FOR UPDATE;

            IF t_payment_price IS NOT NULL THEN
                UPDATE purchase.payments
                SET payment_price = t_payment_price + NEW.wearhousing_quantity * NEW.wearhousing_unit_price
                WHERE supplier_id = wearhousing_rec.supplier_id
                AND closing_date = wearhousing_rec.closing_date
                AND payment_deadline = wearhousing_rec.payment_deadline;

            ELSE
                INSERT INTO purchase.payments
                VALUES (
                    default,
                    wearhousing_rec.supplier_id,
                    wearhousing_rec.closing_date,
                    wearhousing_rec.payment_deadline,
                    NEW.wearhousing_quantity * NEW.wearhousing_unit_price
                );
            END IF;

            -- 買掛変動履歴の登録
            INSERT INTO purchase.accounts_payable_histories
            VALUES (
                default,
                wearhousing_rec.wearhousing_date,
                wearhousing_rec.supplier_id,
                NEW.wearhousing_quantity * NEW.wearhousing_unit_price,
                'PURCHASE',
                null,
                NEW.detail_no
            );

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_wearhousing_details
            AFTER INSERT
            ON purchase.wearhousing_details
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.set_transition_histories_and_payments();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
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


# INFO:
def upgrade() -> None:
    op.execute("CREATE SEQUENCE purchase.ordering_no_seed START 1;")
    op.execute("CREATE SEQUENCE purchase.warehousing_no_seed START 1;")
    op.execute("CREATE SEQUENCE purchase.payment_no_seed START 1;")
    create_accounts_payables_table()
    create_accounts_payable_histories_table()
    create_payments_table()
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
    op.execute("DROP TABLE IF EXISTS purchase.payments CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase.accounts_payable_histories CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase.accounts_payables CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS purchase.ordering_no_seed CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS purchase.warehousing_no_seed CASCADE;")
    op.execute("DROP SEQUENCE IF EXISTS purchase.payment_no_seed CASCADE;")
