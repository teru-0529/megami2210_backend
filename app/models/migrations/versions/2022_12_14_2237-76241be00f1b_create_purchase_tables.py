"""create purchase tables

Revision ID: 76241be00f1b
Revises: f3ef6aa8d42a
Create Date: 2022-12-14 22:37:45.628970

"""
import sqlalchemy as sa
from alembic import op

from app.models.migrations.util import timestamps
from app.models.segment_values import PayableTransitionType, PaymentStatus, SiteType

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
        sa.Column("init_balance", sa.Numeric, nullable=False, comment="月初残高"),
        sa.Column("purchase_amount", sa.Numeric, nullable=False, comment="購入額"),
        sa.Column("payment_amount", sa.Numeric, nullable=False, comment="支払額"),
        sa.Column("other_amount", sa.Numeric, nullable=False, comment="その他変動額"),
        sa.Column("balance", sa.Numeric, nullable=False, comment="残高"),
        schema="purchase",
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_accounts_payables() RETURNS TRIGGER AS $$
        BEGIN
            --残高
            NEW.balance:=NEW.init_balance + NEW.purchase_amount - NEW.payment_amount + NEW.other_amount;

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
        sa.Column("no", sa.Integer, primary_key=True, comment="買掛変動NO"),
        sa.Column("transaction_date", sa.Date, nullable=False, comment="取引日"),
        sa.Column("supplier_id", sa.String(4), nullable=False, comment="仕入先ID"),
        sa.Column("amount", sa.Numeric, nullable=False, comment="取引額"),
        sa.Column(
            "transition_type",
            sa.Enum(
                *PayableTransitionType.list(), name="transition_type", schema="purchase"
            ),
            nullable=False,
            comment="買掛変動区分",
        ),
        sa.Column("transaction_no", sa.Integer, nullable=False, comment="取引管理NO"),
        sa.Column("payment_no", sa.String(10), nullable=False, comment="支払NO"),
        schema="purchase",
    )

    op.create_index(
        "ix_accounts_payable_histories_supplier",
        "accounts_payable_histories",
        ["supplier_id", "no"],
        schema="purchase",
    )

    # 登録後処理：月次買掛金サマリーを自動作成TODO:
    op.execute(
        """
        CREATE FUNCTION purchase.set_summaries() RETURNS TRIGGER AS $$
        DECLARE
            yyyymm text:=to_char(NEW.transaction_date, 'YYYYMM');

            t_init_balance numeric;
            t_purchase_amount numeric;
            t_payment_amount numeric;
            t_other_amount numeric;

            recent_rec record;
            last_rec record;
        BEGIN
            --月次買掛金サマリー(当月)検索
            SELECT * INTO recent_rec
            FROM purchase.accounts_payables
            WHERE supplier_id = NEW.supplier_id AND year_month = yyyymm
            FOR UPDATE;

            --月初残高,購入額,支払額,その他変動額判定
            IF recent_rec IS NULL THEN
                --月次買掛金サマリー(過去)検索
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

            --取引額計上
            IF NEW.transition_type='PURCHASE' OR NEW.transition_type='ORDERING_RETURN' THEN
                t_purchase_amount:=t_purchase_amount + NEW.amount;
            ELSEIF NEW.transition_type='PAYMENT' THEN
                t_payment_amount:=t_payment_amount - NEW.amount;
            ELSEIF NEW.transition_type='BALANCE_OUT' OR NEW.transition_type='OTHER_TRANSITION' THEN
                t_other_amount:=t_other_amount + NEW.amount;
            END IF;

            --登録
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
            server_default="auto",
            comment="支払NO",
        ),
        sa.Column("supplier_id", sa.String(4), nullable=False, comment="仕入先ID"),
        sa.Column("closing_date", sa.Date, nullable=False, comment="締日"),
        sa.Column("payment_deadline", sa.Date, nullable=False, comment="支払期限日"),
        sa.Column("amount", sa.Numeric, nullable=False, comment="支払額"),
        sa.Column(
            "status",
            sa.Enum(*PaymentStatus.list(), name="payment_status", schema="purchase"),
            nullable=False,
            server_default=PaymentStatus.before_payment,
            comment="ステータス",
        ),
        sa.Column(
            "payment_check_date",
            sa.Date,
            nullable=True,
            comment="（消す）請求書確認日",
        ),
        sa.Column(
            "payment_check_pic", sa.String(5), nullable=True, comment="（消す）請求書確認者ID"
        ),
        sa.Column(
            "payment_date",
            sa.Date,
            nullable=True,
            comment="（消す）支払実施日",
        ),
        sa.Column("payment_pic", sa.String(5), nullable=True, comment="（消す）支払実施者ID"),
        schema="purchase",
    )  # FIXME:項目消す

    op.create_unique_constraint(
        "uk_payment_deadline",
        "payments",
        ["supplier_id", "closing_date", "payment_deadline"],
        schema="purchase",
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_payments() RETURNS TRIGGER AS $$
        BEGIN
            --支払NO
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
            server_default="auto",
            comment="発注NO",
        ),
        sa.Column("operation_date", sa.Date, nullable=False, comment="発注日"),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="発注担当者ID"),
        sa.Column("supplier_id", sa.String(4), nullable=False, comment="仕入先ID"),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        schema="purchase",
    )

    op.create_foreign_key(
        "fk_operator_id",
        "orderings",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="purchase",
        referent_schema="account",
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
    op.create_index(
        "ix_orderings_supplier",
        "orderings",
        ["supplier_id", "ordering_no"],
        schema="purchase",
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_orderings() RETURNS TRIGGER AS $$
        BEGIN
            --発注NO
            NEW.ordering_no:='PO-'||to_char(nextval('purchase.ordering_no_seed'),'FM0000000');

            -- 処理日付
            NEW.operation_date:=get_operation_date();

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
            "quantity", sa.Integer, nullable=False, server_default="0", comment="発注数"
        ),
        sa.Column(
            "wearhousing_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="入荷数",
        ),
        sa.Column(
            "cancel_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="キャンセル数",
        ),
        sa.Column("remaining_quantity", sa.Integer, nullable=False, comment="発注残"),
        sa.Column(
            "cost_price",
            sa.Numeric,
            nullable=False,
            server_default="0.00",
            comment="発注単価",
        ),
        sa.Column("profit_rate", sa.Numeric, nullable=False, comment="想定利益率"),
        sa.Column("standard_arrival_date", sa.Date, nullable=False, comment="標準納期日"),
        sa.Column("estimate_arrival_date", sa.Date, nullable=False, comment="予定納期日"),
        schema="purchase",
    )

    # 発注仕入先の商品であること(相関チェック)
    op.execute(
        """
        CREATE FUNCTION purchase.ck_product_with_supplier(
            i_ordering_no text,
            i_product_id text
        ) RETURNS boolean AS $$
        DECLARE
            supplier_id_from_ordering text;
            supplier_id_from_product text;
        BEGIN
            --発注仕入先の検索
            SELECT supplier_id INTO supplier_id_from_ordering
            FROM purchase.orderings
            WHERE ordering_no = i_ordering_no;

            --商品仕入先の検索
            SELECT supplier_id INTO supplier_id_from_product
            FROM mst.products
            WHERE product_id = i_product_id;

        RETURN supplier_id_from_ordering = supplier_id_from_product;
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
        "ck_quantity",
        "ordering_details",
        "quantity > 0",
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
        "ck_remaining_quantity",
        "ordering_details",
        "remaining_quantity >= 0",
        schema="purchase",
    )
    op.create_check_constraint(
        "ck_cost_price",
        "ordering_details",
        "cost_price > 0.00",
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

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_ordering_details() RETURNS TRIGGER AS $$
        DECLARE
            t_interval_days integer;
            t_operation_date date;
            t_standard_arrival_date date;

            product_rec record;
        BEGIN
            --新規登録の場合のみ実施
            IF TG_OP = 'INSERT' THEN

                --商品単位の標準入荷日数取得
                SELECT * INTO product_rec
                FROM mst.products
                WHERE product_id = NEW.product_id;

                --仕入先単位の標準入荷日数取得(商品単位の設定がない場合)
                IF product_rec.days_to_arrive IS NULL THEN
                    SELECT days_to_arrive INTO t_interval_days
                    FROM mst.suppliers
                    WHERE company_id = product_rec.supplier_id;
                ELSE
                    t_interval_days:=product_rec.days_to_arrive;
                END IF;

                --発注日取得
                SELECT operation_date INTO t_operation_date
                FROM purchase.orderings
                WHERE ordering_no = NEW.ordering_no;

                --標準納期日,予定納期日
                t_standard_arrival_date:= t_operation_date + CAST(
                    CAST(t_interval_days as character varying)|| 'days' AS INTERVAL
                );
                NEW.standard_arrival_date:=t_standard_arrival_date;
                NEW.estimate_arrival_date:=t_standard_arrival_date;
            END IF;

            --発注残
            NEW.remaining_quantity:=NEW.quantity - NEW.wearhousing_quantity - NEW.cancel_quantity;
            --予定利益率
            NEW.profit_rate:=mst.calc_profit_rate_for_cost(NEW.product_id, NEW.cost_price);

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER upsert_ordering_details
            BEFORE INSERT OR UPDATE
            ON purchase.ordering_details
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.calc_ordering_details();
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
            server_default="auto",
            comment="入荷NO",
        ),
        sa.Column("operation_date", sa.Date, nullable=False, comment="入荷日"),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="入荷担当者ID"),
        sa.Column("supplier_id", sa.String(4), nullable=False, comment="仕入先ID"),
        sa.Column("closing_date", sa.Date, nullable=False, comment="締日"),
        sa.Column("payment_deadline", sa.Date, nullable=False, comment="支払期限日"),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        schema="purchase",
    )

    op.create_foreign_key(
        "fk_operator_id",
        "wearhousings",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="purchase",
        referent_schema="account",
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
    op.create_index(
        "ix_wearhousings_supplier",
        "wearhousings",
        ["supplier_id", "wearhousing_no"],
        schema="purchase",
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_wearhousings() RETURNS TRIGGER AS $$
        DECLARE
            rec record;

        BEGIN
            --入荷NO
            NEW.wearhousing_no:='WH-'||to_char(nextval('purchase.warehousing_no_seed'),'FM0000000');

            -- 処理日付
            NEW.operation_date:=get_operation_date();

            -- 締日,支払期限
            rec:=mst.calc_payment_deadline(NEW.operation_date, NEW.supplier_id);
            NEW.closing_date:=rec.closing_date;
            NEW.payment_deadline:=rec.payment_deadline;
            IF NEW.note IS NULL THEN
                NEW.note:=rec.note;
            ELSE
                NEW.note:=NEW.note||'、'||rec.note;
            END IF;

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
            server_default="auto",
            comment="当社商品ID",
        ),
        sa.Column(
            "quantity", sa.Integer, nullable=False, server_default="0", comment="入荷数"
        ),
        sa.Column(
            "return_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="返品数",
        ),
        sa.Column(
            "cost_price",
            sa.Numeric,
            nullable=False,
            server_default="0.00",
            comment="入荷単価",
        ),
        sa.Column("profit_rate", sa.Numeric, nullable=False, comment="想定利益率"),
        sa.Column(
            "site_type",
            sa.Enum(*SiteType.list(), name="site_type", schema="mst"),
            nullable=False,
            server_default=SiteType.inspect_product,
            comment="入荷倉庫種別 ",
        ),
        schema="purchase",
    )

    # 発注時の仕入先と等しいこと(相関チェック)
    op.execute(
        """
        CREATE FUNCTION purchase.ck_supplier_with_ordering(
            i_wearhousing_no text,
            i_order_detail_no integer
        ) RETURNS boolean AS $$
        DECLARE
            supplier_id_from_ordering text;
            supplier_id_from_wearhousing text;
        BEGIN
            --発注仕入先の検索
            SELECT O.supplier_id INTO supplier_id_from_ordering
            FROM purchase.ordering_details OD
            LEFT OUTER JOIN purchase.orderings O ON OD.ordering_no = O.ordering_no
            WHERE OD.detail_no = i_order_detail_no;

            --入荷仕入先の検索
            SELECT supplier_id INTO supplier_id_from_wearhousing
            FROM purchase.wearhousings
            WHERE wearhousing_no = i_wearhousing_no;

        RETURN supplier_id_from_ordering = supplier_id_from_wearhousing;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.create_check_constraint(
        "ck_supplier_id",
        "wearhousing_details",
        "purchase.ck_supplier_with_ordering(wearhousing_no, order_detail_no)",
        schema="purchase",
    )
    op.create_check_constraint(
        "ck_quantity",
        "wearhousing_details",
        "quantity > 0 AND return_quantity <= quantity",
        schema="purchase",
    )
    op.create_check_constraint(
        "ck_return_quantity",
        "wearhousing_details",
        "return_quantity >= 0",
        schema="purchase",
    )
    op.create_check_constraint(
        "ck_cost_price",
        "wearhousing_details",
        "cost_price > 0.00",
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
    op.create_index(
        "ix_wearhousing_details_wearhousing",
        "wearhousing_details",
        ["wearhousing_no", "detail_no"],
        schema="purchase",
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_wearhousing_details() RETURNS TRIGGER AS $$
        DECLARE
            t_selling_price numeric;

        BEGIN
            --新規登録の場合のみ実施
            IF TG_OP = 'INSERT' THEN

                --当社商品ID
                SELECT product_id INTO NEW.product_id
                FROM purchase.ordering_details
                WHERE detail_no = NEW.order_detail_no;
            END IF;

            --予定利益率
            NEW.profit_rate:=mst.calc_profit_rate_for_cost(NEW.product_id, NEW.cost_price);

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER upsert_wearhousing_details
            BEFORE INSERT OR UPDATE
            ON purchase.wearhousing_details
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.calc_wearhousing_details();
        """
    )

    # 登録後処理：在庫変動履歴/支払/買掛金変動履歴の登録TODO:
    op.execute(
        """
        CREATE FUNCTION purchase.set_inventories_and_payments() RETURNS TRIGGER AS $$
        DECLARE
            t_amount numeric:=NEW.quantity * NEW.cost_price;
            t_payment_no text;

            rec record;

            ck_dummy numeric;
        BEGIN
            -- 発注残数の更新
            UPDATE purchase.ordering_details
            SET wearhousing_quantity = wearhousing_quantity + NEW.quantity
            WHERE detail_no = NEW.order_detail_no;

            -- 在庫変動履歴の登録
            SELECT * INTO rec
            FROM purchase.wearhousings
            WHERE wearhousing_no = NEW.wearhousing_no;

            INSERT INTO inventory.transition_histories
            VALUES (
                default,
                rec.operation_date,
                NEW.site_type,
                NEW.product_id,
                NEW.quantity,
                t_amount,
                'PURCHASE',
                NEW.detail_no
            );

            -- 支払の登録、更新
            SELECT amount INTO ck_dummy
            FROM purchase.payments
            WHERE supplier_id = rec.supplier_id
            AND closing_date = rec.closing_date
            AND payment_deadline = rec.payment_deadline
            FOR UPDATE;

            IF ck_dummy IS NOT NULL THEN
                UPDATE purchase.payments
                SET amount = amount + t_amount
                WHERE supplier_id = rec.supplier_id
                AND closing_date = rec.closing_date
                AND payment_deadline = rec.payment_deadline;

            ELSE
                INSERT INTO purchase.payments
                VALUES (
                    default,
                    rec.supplier_id,
                    rec.closing_date,
                    rec.payment_deadline,
                    t_amount
                );
            END IF;

            -- 買掛変動履歴の登録
            SELECT payment_no INTO t_payment_no
            FROM purchase.payments
            WHERE supplier_id = rec.supplier_id
            AND closing_date = rec.closing_date
            AND payment_deadline = rec.payment_deadline;

            INSERT INTO purchase.accounts_payable_histories
            VALUES (
                default,
                rec.operation_date,
                rec.supplier_id,
                t_amount,
                'PURCHASE',
                NEW.detail_no,
                t_payment_no
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
        EXECUTE PROCEDURE purchase.set_inventories_and_payments();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_payment_instructions_table() -> None:
    op.create_table(
        "payment_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="支払指示NO"),
        sa.Column(
            "operation_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="指示日",
        ),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="指示者ID"),
        sa.Column(
            "payment_no",
            sa.String(10),
            nullable=False,
            server_default="set_me",
            comment="支払NO",
        ),
        *timestamps(),
        schema="purchase",
    )

    op.create_foreign_key(
        "fk_operator_id",
        "payment_instructions",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="purchase",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_payment_no",
        "payment_instructions",
        "payments",
        ["payment_no"],
        ["payment_no"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="purchase",
    )
    op.create_index(
        "ix_payment_instructions_payment_no",
        "payment_instructions",
        ["payment_no"],
        unique=True,
        schema="purchase",
    )

    op.execute(
        """
        CREATE TRIGGER payment_instructions_modified
            BEFORE UPDATE
            ON purchase.payment_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_payment_instructions() RETURNS TRIGGER AS $$
        BEGIN
            -- 処理日付を取得
            SELECT date INTO NEW.operation_date
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_payment_instructions
            BEFORE INSERT
            ON purchase.payment_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.calc_payment_instructions();
        """
    )

    # 入金指示後、入金日時更新、買掛変動履歴を自動作成TODO:
    op.execute(
        """
        CREATE FUNCTION purchase.set_payment() RETURNS TRIGGER AS $$
        DECLARE
            rec RECORD;
        BEGIN

            -- 支払へ、入金日、入金担当者の登録
            UPDATE purchase.payments
            SET payment_date = NEW.operation_date, payment_pic = NEW.operator_id
            WHERE payment_no = NEW.payment_no;

            -- 買掛変動履歴の登録
            SELECT * INTO rec
            FROM purchase.payments
            WHERE payment_no = NEW.payment_no;

            INSERT INTO purchase.accounts_payable_histories
            VALUES (
                default,
                NEW.operation_date,
                rec.supplier_id,
                - rec.amount,
                'PAYMENT',
                NEW.no,
                NEW.payment_no
            );

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_payment_instructions
            AFTER INSERT
            ON purchase.payment_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.set_payment();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_payment_check_instructions_table() -> None:
    op.create_table(
        "payment_check_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="支払確認NO"),
        sa.Column(
            "operation_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="確認日",
        ),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="確認者ID"),
        sa.Column(
            "payment_no",
            sa.String(10),
            nullable=False,
            server_default="set_me",
            comment="支払NO",
        ),
        *timestamps(),
        schema="purchase",
    )

    op.create_foreign_key(
        "fk_operator_id",
        "payment_check_instructions",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="purchase",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_payment_no",
        "payment_check_instructions",
        "payments",
        ["payment_no"],
        ["payment_no"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="purchase",
    )
    op.create_index(
        "ix_payment_check_instructions_payment_no",
        "payment_check_instructions",
        ["payment_no"],
        unique=True,
        schema="purchase",
    )

    op.execute(
        """
        CREATE TRIGGER payment_check_instructions_modified
            BEFORE UPDATE
            ON purchase.payment_check_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_payment_check_instructions() RETURNS TRIGGER AS $$
        BEGIN
            -- 処理日付を取得
            SELECT date INTO NEW.operation_date
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_payment_check_instructions
            BEFORE INSERT
            ON purchase.payment_check_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.calc_payment_check_instructions();
        """
    )

    # 請求書確認後処理TODO:
    op.execute(
        """
        CREATE FUNCTION purchase.set_check_payment() RETURNS TRIGGER AS $$
        DECLARE
            rec RECORD;
        BEGIN

            -- 支払へ、確認日、確認担当者の登録
            UPDATE purchase.payments
            SET payment_check_date = NEW.operation_date, payment_check_pic = NEW.operator_id
            WHERE payment_no = NEW.payment_no;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_payment_check_instructions
            AFTER INSERT
            ON purchase.payment_check_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.set_check_payment();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_order_cancel_instructions_table() -> None:
    op.create_table(
        "order_cancel_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="キャンセル指示NO"),
        sa.Column(
            "operation_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="指示日",
        ),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="指示者ID"),
        sa.Column("cancel_reason", sa.Text, nullable=False, comment="キャンセル理由"),
        sa.Column("order_detail_no", sa.Integer, nullable=True, comment="発注明細NO"),
        sa.Column(
            "calcel_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="キャンセル数",
        ),
        *timestamps(),
        schema="purchase",
    )

    op.create_check_constraint(
        "ck_calcel_quantity",
        "order_cancel_instructions",
        "calcel_quantity > 0",
        schema="purchase",
    )
    op.create_foreign_key(
        "fk_operator_id",
        "order_cancel_instructions",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="purchase",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_order_detail_no",
        "order_cancel_instructions",
        "ordering_details",
        ["order_detail_no"],
        ["detail_no"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="purchase",
    )

    op.execute(
        """
        CREATE TRIGGER order_cancel_instructions_modified
            BEFORE UPDATE
            ON purchase.order_cancel_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_order_cancel_instructions() RETURNS TRIGGER AS $$
        BEGIN
            -- 処理日付を取得
            SELECT date INTO NEW.operation_date
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_order_cancel_instructions
            BEFORE INSERT
            ON purchase.order_cancel_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.calc_order_cancel_instructions();
        """
    )

    # 発注明細の変更TODO:
    op.execute(
        """
        CREATE FUNCTION purchase.update_order_quantity() RETURNS TRIGGER AS $$
        DECLARE
            t_cancel_quantity integer;
        BEGIN
            -- キャンセル数の更新
            SELECT cancel_quantity INTO t_cancel_quantity
            FROM purchase.ordering_details
            WHERE detail_no = NEW.order_detail_no
            FOR UPDATE;

            UPDATE purchase.ordering_details
            SET cancel_quantity = t_cancel_quantity + NEW.calcel_quantity
            WHERE detail_no = NEW.order_detail_no;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_order_cancel_instructions
            AFTER INSERT
            ON purchase.order_cancel_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.update_order_quantity();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_arrival_date_instructions_table() -> None:
    op.create_table(
        "arrival_date_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="納期変更NO"),
        sa.Column(
            "operation_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="変更実施日",
        ),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="変更者ID"),
        sa.Column("change_reason", sa.Text, nullable=False, comment="変更理由"),
        sa.Column("order_detail_no", sa.Integer, nullable=True, comment="発注明細NO"),
        sa.Column(
            "arrival_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="予定納期日",
        ),
        *timestamps(),
        schema="purchase",
    )

    op.create_foreign_key(
        "fk_operator_id",
        "arrival_date_instructions",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="purchase",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_order_detail_no",
        "arrival_date_instructions",
        "ordering_details",
        ["order_detail_no"],
        ["detail_no"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="purchase",
    )

    op.execute(
        """
        CREATE TRIGGER arrival_date_instructions_modified
            BEFORE UPDATE
            ON purchase.arrival_date_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_arrival_date_instructions() RETURNS TRIGGER AS $$
        BEGIN
            -- 処理日付を取得
            SELECT date INTO NEW.operation_date
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_arrival_date_instructions
            BEFORE INSERT
            ON purchase.arrival_date_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.calc_arrival_date_instructions();
        """
    )

    # 発注明細の変更TODO:
    op.execute(
        """
        CREATE FUNCTION purchase.update_arrival_date() RETURNS TRIGGER AS $$
        BEGIN
            -- 入荷予定日の更新
            UPDATE purchase.ordering_details
            SET estimate_arrival_date = NEW.arrival_date
            WHERE detail_no = NEW.order_detail_no;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_purchase_cancel_instructions
            AFTER INSERT
            ON purchase.arrival_date_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.update_arrival_date();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_purchase_return_instructions_table() -> None:
    op.create_table(
        "purchase_return_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="返品指示NO"),
        sa.Column(
            "operation_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="指示日",
        ),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="指示者ID"),
        sa.Column("return_reason", sa.Text, nullable=False, comment="返品理由"),
        sa.Column("wearhousing_detail_no", sa.Integer, nullable=True, comment="入荷明細NO"),
        sa.Column("supplier_id", sa.String(4), nullable=False, comment="仕入先ID"),
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
            "return_unit_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="返品単価",
        ),
        sa.Column(
            "site_type",
            sa.Enum(*SiteType.list(), name="site_type", schema="mst"),
            nullable=False,
            comment="返品元倉庫種別 ",
        ),
        *timestamps(),
        schema="purchase",
    )

    op.create_check_constraint(
        "ck_return_quantity",
        "purchase_return_instructions",
        "return_quantity > 0",
        schema="purchase",
    )
    op.create_check_constraint(
        "ck_return_unit_price",
        "purchase_return_instructions",
        "return_unit_price > 0",
        schema="purchase",
    )
    op.create_foreign_key(
        "fk_operator_id",
        "purchase_return_instructions",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="purchase",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_wearhousing_detail_no",
        "purchase_return_instructions",
        "wearhousing_details",
        ["wearhousing_detail_no"],
        ["detail_no"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="purchase",
    )
    op.create_foreign_key(
        "fk_supplier_id",
        "purchase_return_instructions",
        "suppliers",
        ["supplier_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER purchase_return_instructions_modified
            BEFORE UPDATE
            ON purchase.purchase_return_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_purchase_return_instructions() RETURNS TRIGGER AS $$
        DECLARE
            rec record;
        BEGIN
            -- 処理日付を取得
            SELECT date INTO NEW.operation_date
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';

            IF NEW.wearhousing_detail_no IS NOT NULL THEN
                -- 入荷明細から当社商品ID、仕入先ID、返品単価を取得
                SELECT * INTO rec
                FROM purchase.wearhousing_details
                WHERE detail_no = NEW.wearhousing_detail_no
                FOR UPDATE;

                SELECT supplier_id INTO NEW.supplier_id
                FROM purchase.wearhousings
                WHERE wearhousing_no = rec.wearhousing_no;

                -- 入荷明細に返品数を登録
                UPDATE purchase.wearhousing_details
                SET return_quantity = rec.return_quantity + NEW.return_quantity
                WHERE detail_no = NEW.wearhousing_detail_no;

                NEW.product_id:= rec.product_id;
                NEW.return_unit_price:= rec.cost_price;

            END iF;

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_purchase_return_instructions
            BEFORE INSERT
            ON purchase.purchase_return_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.calc_purchase_return_instructions();
        """
    )

    # 在庫変動履歴/支払/買掛金変動履歴の登録TODO:
    op.execute(
        """
        CREATE FUNCTION purchase.set_inventories_and_payments_by_return() RETURNS TRIGGER AS $$
        DECLARE
            t_closing_date date;
            t_payment_deadline date;
            t_amount numeric;
            t_payment_no text;

            rec record;
        BEGIN
            -- 締日、支払期限の算出
            rec:=mst.calc_payment_deadline(New.operation_date, New.supplier_id);
            t_closing_date:=rec.closing_date;
            t_payment_deadline:=rec.payment_deadline;

            -- 在庫変動履歴の登録
            INSERT INTO inventory.transition_histories
            VALUES (
                default,
                NEW.operation_date,
                NEW.site_type,
                NEW.product_id,
                - NEW.return_quantity,
                - NEW.return_quantity * NEW.return_unit_price,
                'ORDERING_RETURN',
                NEW.no
            );

            -- 支払の登録、更新
            SELECT amount INTO t_amount
            FROM purchase.payments
            WHERE supplier_id = NEW.supplier_id
            AND closing_date = t_closing_date
            AND payment_deadline = t_payment_deadline
            FOR UPDATE;

            IF t_amount IS NOT NULL THEN
                UPDATE purchase.payments
                SET amount = t_amount - NEW.return_quantity * NEW.return_unit_price
                WHERE supplier_id = NEW.supplier_id
                AND closing_date = t_closing_date
                AND payment_deadline = t_payment_deadline;

            ELSE
                INSERT INTO purchase.payments
                VALUES (
                    default,
                    NEW.supplier_id,
                    t_closing_date,
                    t_payment_deadline,
                    - NEW.return_quantity * NEW.return_unit_price
                );
            END IF;

            -- 買掛変動履歴の登録
            SELECT payment_no INTO t_payment_no
            FROM purchase.payments
            WHERE supplier_id = NEW.supplier_id
            AND closing_date = t_closing_date
            AND payment_deadline = t_payment_deadline;

            INSERT INTO purchase.accounts_payable_histories
            VALUES (
                default,
                NEW.operation_date,
                NEW.supplier_id,
                - NEW.return_quantity * NEW.return_unit_price,
                'ORDERING_RETURN',
                NEW.no,
                t_payment_no
            );

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_purchase_return_instructions
            AFTER INSERT
            ON purchase.purchase_return_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.set_inventories_and_payments_by_return();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_other_purchase_instructions_table() -> None:
    op.create_table(
        "other_purchase_instructions",
        sa.Column("no", sa.Integer, primary_key=True, comment="雑仕入指示NO"),
        sa.Column(
            "operation_date",
            sa.Date,
            server_default=sa.func.now(),
            nullable=False,
            comment="指示日",
        ),
        sa.Column("operator_id", sa.String(5), nullable=True, comment="指示者ID"),
        sa.Column("instruction_cause", sa.Text, nullable=False, comment="変動理由"),
        sa.Column("supplier_id", sa.String(4), nullable=False, comment="仕入先ID"),
        sa.Column(
            "transition_amount",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="変動金額",
        ),
        *timestamps(),
        schema="purchase",
    )

    op.create_foreign_key(
        "fk_operator_id",
        "other_purchase_instructions",
        "profiles",
        ["operator_id"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="purchase",
        referent_schema="account",
    )
    op.create_foreign_key(
        "fk_supplier_id",
        "other_purchase_instructions",
        "suppliers",
        ["supplier_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="purchase",
        referent_schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER other_purchase_instructions_modified
            BEFORE UPDATE
            ON purchase.other_purchase_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    # 導出項目計算
    op.execute(
        """
        CREATE FUNCTION purchase.calc_other_purchase_instructions() RETURNS TRIGGER AS $$
        BEGIN
            -- 処理日付を取得
            SELECT date INTO NEW.operation_date
            FROM business_date
            WHERE date_type = 'BUSINESS_DATE';

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER insert_other_purchase_instructions
            BEFORE INSERT
            ON purchase.other_purchase_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.calc_other_purchase_instructions();
        """
    )

    # 支払/買掛金変動履歴の登録TODO:
    op.execute(
        """
        CREATE FUNCTION purchase.set_payments_by_other_instruction() RETURNS TRIGGER AS $$
        DECLARE
            t_closing_date date;
            t_payment_deadline date;
            t_amount numeric;
            t_payment_no text;

            rec record;
        BEGIN
            -- 締日、支払期限の算出
            rec:=mst.calc_payment_deadline(New.operation_date, New.supplier_id);
            t_closing_date:=rec.closing_date;
            t_payment_deadline:=rec.payment_deadline;

            -- 支払の登録、更新
            SELECT amount INTO t_amount
            FROM purchase.payments
            WHERE supplier_id = NEW.supplier_id
            AND closing_date = t_closing_date
            AND payment_deadline = t_payment_deadline
            FOR UPDATE;

            IF t_amount IS NOT NULL THEN
                UPDATE purchase.payments
                SET amount = t_amount + NEW.transition_amount
                WHERE supplier_id = NEW.supplier_id
                AND closing_date = t_closing_date
                AND payment_deadline = t_payment_deadline;

            ELSE
                INSERT INTO purchase.payments
                VALUES (
                    default,
                    NEW.supplier_id,
                    t_closing_date,
                    t_payment_deadline,
                    NEW.transition_amount
                );
            END IF;

            -- 買掛変動履歴の登録
            SELECT payment_no INTO t_payment_no
            FROM purchase.payments
            WHERE supplier_id = NEW.supplier_id
            AND closing_date = t_closing_date
            AND payment_deadline = t_payment_deadline;

            INSERT INTO purchase.accounts_payable_histories
            VALUES (
                default,
                NEW.operation_date,
                NEW.supplier_id,
                NEW.transition_amount,
                'OTHER_TRANSITION',
                NEW.no,
                t_payment_no
            );

            return NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER hook_insert_other_purchase_instructions
            AFTER INSERT
            ON purchase.other_purchase_instructions
            FOR EACH ROW
        EXECUTE PROCEDURE purchase.set_payments_by_other_instruction();
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_view() -> None:
    op.execute(
        """
        CREATE VIEW purchase.view_remaining_order AS
            SELECT
                OD.detail_no,
                OD.product_id,
                OD.quantity,
                OD.remaining_quantity,
                OD.estimate_arrival_date
            FROM purchase.ordering_details OD
            WHERE OD.remaining_quantity > 0
            ORDER BY OD.product_id, OD.estimate_arrival_date, OD.detail_no;
        """
    )
    op.execute(
        """
        CREATE VIEW purchase.view_payments AS
            WITH date_with AS (
                SELECT *
                FROM business_date
                WHERE date_type = 'BUSINESS_DATE'
            )
            SELECT
                PM.payment_no,
                PM.supplier_id,
                PM.closing_date,
                PM.payment_deadline,
                PM.amount,
                CASE
                    WHEN PM.payment_date IS NOT NULL THEN 'PAYMENT_PROCESSED'
                    WHEN PM.closing_date >= (SELECT date FROM date_with) THEN 'BEFORE_CLOSING'
                    WHEN PM.payment_deadline < (SELECT date FROM date_with) THEN 'OVERDUE_PAYMENT'
                    WHEN PM.payment_check_date IS NOT NULL THEN 'INVOICE_CONFIRMED'
                    ELSE 'CLOSING'
                END AS situation
            FROM purchase.payments PM;
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
    create_order_cancel_instructions_table()
    create_arrival_date_instructions_table()
    create_payment_instructions_table()
    create_payment_check_instructions_table()
    create_purchase_return_instructions_table()
    create_other_purchase_instructions_table()
    create_view()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS purchase.other_purchase_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase.purchase_return_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase.payment_check_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase.payment_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase.arrival_date_instructions CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase.order_cancel_instructions CASCADE;")
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
