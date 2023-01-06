"""create mst tables

Revision ID: 139619b8894b
Revises: e85dfc42f48d
Create Date: 2022-12-09 07:22:27.697717

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM

from app.models.migrations.util import timestamps
from app.models.segment_values import MasterStatus, OrderPolicy

# revision identifiers, used by Alembic.
revision = "139619b8894b"
down_revision = "e85dfc42f48d"
branch_labels = None
depends_on = None

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def create_status_type() -> ENUM:
    return ENUM(
        *MasterStatus.list(),
        name="status",
        schema="mst",
        create_type=True,
        checkfirst=True,
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_companies_table(status_type: ENUM) -> None:
    companies_table = op.create_table(
        "companies",
        sa.Column("company_id", sa.String(4), primary_key=True, comment="企業ID"),
        sa.Column(
            "name",
            sa.String(30),
            unique=True,
            nullable=False,
            index=True,
            comment="企業名",
        ),
        sa.Column("postal_code", sa.String(8), nullable=False, comment="郵便番号"),
        sa.Column("address", sa.Text, nullable=False, comment="住所"),
        sa.Column("phone_no", sa.String(10), nullable=False, comment="電話番号"),
        sa.Column("fax_no", sa.String(10), nullable=True, comment="FAX番号"),
        sa.Column(
            "status",
            status_type,
            nullable=False,
            server_default=MasterStatus.ready,
            index=True,
            comment="ステータス",
        ),
        sa.Column("bank_code", sa.String(4), nullable=True, comment="取引銀行コード"),
        sa.Column("bank_branch_code", sa.String(3), nullable=True, comment="取引支店コード"),
        sa.Column("bank_name", sa.String(50), nullable=True, comment="取引銀行名称"),
        sa.Column(
            "bank_account_number", sa.String(50), nullable=True, comment="取引口座番号"
        ),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        *timestamps(),
        schema="mst",
    )

    # 「ステータス」が「取引中」の場合は、「取引銀行コード」「取引支店コード」「取引銀行名称」「取引口座番号」が必須
    ck_active: str = """
    CASE
        WHEN status='ACTIVE' AND bank_code IS NULL THEN FALSE
        WHEN status='ACTIVE' AND bank_branch_code IS NULL THEN FALSE
        WHEN status='ACTIVE' AND bank_name IS NULL THEN FALSE
        WHEN status='ACTIVE' AND bank_account_number IS NULL THEN FALSE
        ELSE TRUE
    END
    """
    op.create_check_constraint(
        "ck_status_active",
        "companies",
        ck_active,
        schema="mst",
    )
    op.create_check_constraint(
        "ck_postal_code",
        "companies",
        "postal_code ~* '^[0-9]{3}-[0-9]{4}$'",
        schema="mst",
    )
    op.create_check_constraint(
        "ck_phone_no",
        "companies",
        "phone_no ~* '^0[0-9]{9,10}$'",
        schema="mst",
    )
    op.create_check_constraint(
        "ck_fax_no",
        "companies",
        "fax_no ~* '^0[0-9]{9,10}$'",
        schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER companies_modified
            BEFORE UPDATE
            ON mst.companies
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )

    op.bulk_insert(
        companies_table,
        [
            {
                "company_id": "S001",
                "name": "桜木製薬株式会社",
                "postal_code": "104-0061",
                "address": "東京都中央区銀座4-2-11",
                "phone_no": "0335636611",
                "fax_no": "0335636611",
                "status": MasterStatus.active,
                "bank_code": "0001",
                "bank_branch_code": "035",
                "bank_name": "みずほ銀行 銀座支店",
                "bank_account_number": "0000001",
            },
            {
                "company_id": "S002",
                "name": "流川家具株式会社",
                "postal_code": "103-0022",
                "address": "東京都中央区日本橋室町4-3-18",
                "phone_no": "0332412321",
                "fax_no": None,
                "status": MasterStatus.active,
                "bank_code": "0001",
                "bank_branch_code": "038",
                "bank_name": "みずほ銀行 日本橋支店",
                "bank_account_number": "0000001",
            },
            {
                "company_id": "S003",
                "name": "赤木食品株式会社",
                "postal_code": "104-0045",
                "address": "東京都中央区築地2-11-21",
                "phone_no": "0335414561",
                "fax_no": None,
                "status": MasterStatus.active,
                "bank_code": "0005",
                "bank_branch_code": "025",
                "bank_name": "東京三菱UFJ銀行 築地支店",
                "bank_account_number": "0000003",
            },
            {
                "company_id": "S004",
                "name": "株式会社宮城水産",
                "postal_code": "105-0004",
                "address": "東京都港区新橋4-6-15",
                "phone_no": "0334316151",
                "fax_no": None,
                "status": MasterStatus.ready,
                "bank_code": None,
                "bank_branch_code": None,
                "bank_name": None,
                "bank_account_number": None,
            },
            {
                "company_id": "S005",
                "name": "三井鉄鋼株式会社",
                "postal_code": "115-0045",
                "address": "東京都北区赤羽1-7-8",
                "phone_no": "0339031131",
                "fax_no": None,
                "status": MasterStatus.stop_dealing,
                "bank_code": "0001",
                "bank_branch_code": "203",
                "bank_name": "みずほ銀行 赤羽支店",
                "bank_account_number": "0000005",
            },
            {
                "company_id": "C001",
                "name": "牧物産株式会社",
                "postal_code": "330-0062",
                "address": "埼玉県さいたま市浦和区仲町1-4-9",
                "phone_no": "0488225141",
                "fax_no": None,
                "status": MasterStatus.active,
                "bank_code": "0009",
                "bank_branch_code": "040",
                "bank_name": "三井住友銀行 浦和支店",
                "bank_account_number": "0000010",
            },
            {
                "company_id": "C002",
                "name": "仙道商事株式会社",
                "postal_code": "192-0081",
                "address": "東京都八王子市横山町15-3",
                "phone_no": "0426231111",
                "fax_no": None,
                "status": MasterStatus.active,
                "bank_code": "0001",
                "bank_branch_code": "260",
                "bank_name": "みずほ銀行 八王子支店",
                "bank_account_number": "0000013",
            },
            {
                "company_id": "C003",
                "name": "藤間物流株式会社",
                "postal_code": "141-0033",
                "address": "東京都品川区西品川1丁目1番1号",
                "phone_no": "0367121211",
                "fax_no": None,
                "status": MasterStatus.active,
                "bank_code": "0001",
                "bank_branch_code": "540",
                "bank_name": "みずほ銀行 大崎支店",
                "bank_account_number": "0000013",
            },
        ],
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_costomers_table() -> None:
    costomers_table = op.create_table(
        "costomers",
        sa.Column("company_id", sa.String(4), primary_key=True, comment="企業ID"),
        sa.Column(
            "cutoff_day", sa.Integer, nullable=False, server_default="99", comment="締日"
        ),
        sa.Column(
            "month_of_deposit_term",
            sa.Integer,
            nullable=False,
            server_default="1",
            comment="入金猶予月数",
        ),
        sa.Column(
            "deposit_day",
            sa.Integer,
            nullable=False,
            server_default="99",
            comment="入金予定日",
        ),
        sa.Column("sales_pic", sa.String(5), nullable=True, comment="営業担当者ID"),
        sa.Column("contact_person", sa.String(20), nullable=True, comment="相手先担当者名"),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        *timestamps(),
        schema="mst",
    )
    op.create_check_constraint(
        "ck_cutoff_day",
        "costomers",
        "cutoff_day > 0 and cutoff_day < 100",
        schema="mst",
    )
    op.create_check_constraint(
        "ck_month_of_deposit_term",
        "costomers",
        "month_of_deposit_term > 0",
        schema="mst",
    )
    op.create_check_constraint(
        "ck_deposit_day",
        "costomers",
        "deposit_day > 0 and deposit_day < 100",
        schema="mst",
    )
    op.execute(
        """
        CREATE TRIGGER costomers_modified
            BEFORE UPDATE
            ON mst.costomers
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )
    op.create_foreign_key(
        "fk_company_id",
        "costomers",
        "companies",
        ["company_id"],
        ["company_id"],
        ondelete="CASCADE",
        source_schema="mst",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_sales_pic",
        "costomers",
        "profiles",
        ["sales_pic"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="mst",
        referent_schema="account",
    )

    op.bulk_insert(
        costomers_table,
        [
            {
                "company_id": "C001",
                "cutoff_day": 10,
                "month_of_deposit_term": 1,
                "deposit_day": 20,
                "sales_pic": "T-901",
                "contact_person": "牧真一",
                "note": "海南大附属",
            },
            {
                "company_id": "C002",
                "cutoff_day": 99,
                "month_of_deposit_term": 1,
                "deposit_day": 5,
                "sales_pic": "T-902",
                "contact_person": "仙道彰",
                "note": "陵南",
            },
            {
                "company_id": "C003",
                "cutoff_day": 15,
                "month_of_deposit_term": 2,
                "deposit_day": 99,
                "sales_pic": None,
                "contact_person": None,
                "note": None,
            },
            {
                "company_id": "S001",
                "cutoff_day": 15,
                "month_of_deposit_term": 1,
                "deposit_day": 25,
                "sales_pic": "T-902",
                "contact_person": "桜木花道",
                "note": "湘北",
            },
        ],
    )

    # 請求締日、入金期限の計算TODO:
    op.execute(
        """
        CREATE FUNCTION mst.calc_deposit_deadline(
            operation_date date,
            coustomer_id text,
            OUT closing_date date,
            OUT deposit_deadline date,
            OUT dummy text
        ) AS $$
        DECLARE
            rec record;
            cuurent_last_date date;
            cutoff_day_interval interval;

            deposit_month_first_date date;
            deposit_month_last_date date;
            deposit_day_interval interval;

        BEGIN
            SELECT * INTO rec
            FROM mst.costomers
            WHERE company_id = coustomer_id;

            -- 締日の計算
            cuurent_last_date:=DATE(DATE_TRUNC('month', operation_date) + '1 month' +'-1 Day');
            cutoff_day_interval:=CAST((rec.cutoff_day - 1) || ' Day' AS interval);

            IF EXTRACT(day FROM cuurent_last_date) < rec.cutoff_day THEN
                closing_date:=cuurent_last_date;
                dummy:='※月末締';
            ELSEIF rec.cutoff_day < EXTRACT(day FROM operation_date) THEN
                closing_date:=DATE(DATE_TRUNC('month', operation_date) + '1 month' + cutoff_day_interval);
                dummy:='翌月締';
            ELSE
                closing_date:=DATE(DATE_TRUNC('month', operation_date) + cutoff_day_interval);
                dummy:='当月締';
            END IF;

            -- 支払期限日の計算
            deposit_month_first_date:=DATE(DATE_TRUNC('month', closing_date) + CAST(rec.month_of_deposit_term || ' month' AS interval));
            deposit_month_last_date:=deposit_month_first_date + CAST('1 month' AS interval) +CAST('-1 Day' AS interval);
            deposit_day_interval:=CAST((rec.deposit_day - 1) || ' Day' AS interval);

            IF EXTRACT(day FROM deposit_month_last_date) < rec.deposit_day THEN
                deposit_deadline:=deposit_month_last_date;
                dummy:=dummy || '、※入金期限は月末';
            ELSE
                deposit_deadline:=deposit_month_first_date + deposit_day_interval;
            END IF;

        END;
        $$ LANGUAGE plpgsql;
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_suppliers_table() -> None:
    suppliers_table = op.create_table(
        "suppliers",
        sa.Column("company_id", sa.String(4), primary_key=True, comment="企業ID"),
        sa.Column(
            "cutoff_day", sa.Integer, nullable=False, server_default="99", comment="締日"
        ),
        sa.Column(
            "month_of_payment_term",
            sa.Integer,
            nullable=False,
            server_default="1",
            comment="支払猶予月数",
        ),
        sa.Column(
            "payment_day",
            sa.Integer,
            nullable=False,
            server_default="99",
            comment="支払予定日",
        ),
        sa.Column("purchase_pic", sa.String(5), nullable=True, comment="仕入担当者ID"),
        sa.Column("contact_person", sa.String(20), nullable=True, comment="相手先担当者名"),
        sa.Column(
            "order_policy",
            sa.Enum(*OrderPolicy.list(), name="order_policy", schema="mst"),
            nullable=False,
            index=True,
            comment="発注方針",
        ),
        sa.Column(
            "order_week_num",
            sa.Integer,
            nullable=True,
            index=True,
            comment="発注曜日",
        ),
        sa.Column("days_to_arrive", sa.Integer, nullable=False, comment="標準入荷日数"),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        *timestamps(),
        schema="mst",
    )
    op.create_check_constraint(
        "ck_cutoff_day",
        "suppliers",
        "cutoff_day > 0 and cutoff_day < 100",
        schema="mst",
    )
    op.create_check_constraint(
        "ck_month_of_payment_term",
        "suppliers",
        "month_of_payment_term > 0",
        schema="mst",
    )
    op.create_check_constraint(
        "ck_payment_day",
        "suppliers",
        "payment_day > 0 and payment_day < 100",
        schema="mst",
    )
    op.create_check_constraint(
        "ck_days_to_arrive",
        "suppliers",
        "days_to_arrive > 0",
        schema="mst",
    )
    # 「発注方針」が「定期発注」の場合は、「発注曜日」が必須、「発注方針」が「随時発注」の場合は、「発注曜日」を指定してはいけない
    ck_order_week_num: str = """
    CASE
        WHEN order_policy='PERIODICALLY' AND order_week_num IS NULL THEN FALSE
        WHEN order_policy='AS_NEEDED' AND order_week_num IS NOT NULL THEN FALSE
        ELSE TRUE
    END
    """
    op.create_check_constraint(
        "ck_order_week_num",
        "suppliers",
        ck_order_week_num,
        schema="mst",
    )
    op.execute(
        """
        CREATE TRIGGER suppliers_modified
            BEFORE UPDATE
            ON mst.suppliers
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )
    op.create_foreign_key(
        "fk_company_id",
        "suppliers",
        "companies",
        ["company_id"],
        ["company_id"],
        ondelete="CASCADE",
        source_schema="mst",
        referent_schema="mst",
    )
    op.create_foreign_key(
        "fk_purchase_pic",
        "suppliers",
        "profiles",
        ["purchase_pic"],
        ["account_id"],
        ondelete="SET NULL",
        source_schema="mst",
        referent_schema="account",
    )

    op.bulk_insert(
        suppliers_table,
        [
            {
                "company_id": "S001",
                "cutoff_day": 5,
                "month_of_payment_term": 1,
                "payment_day": 99,
                "purchase_pic": "T-902",
                "contact_person": "桜木花道",
                "order_policy": OrderPolicy.periodically,
                "order_week_num": 4,
                "days_to_arrive": 10,
                "note": "湘北",
            },
            {
                "company_id": "S002",
                "cutoff_day": 99,
                "month_of_payment_term": 2,
                "payment_day": 15,
                "purchase_pic": "T-902",
                "contact_person": "流川楓",
                "order_policy": OrderPolicy.as_needed,
                "order_week_num": None,
                "days_to_arrive": 15,
                "note": "湘北",
            },
            {
                "company_id": "S003",
                "cutoff_day": 25,
                "month_of_payment_term": 1,
                "payment_day": 5,
                "purchase_pic": "T-902",
                "contact_person": "赤木剛憲",
                "order_policy": OrderPolicy.periodically,
                "order_week_num": 4,
                "days_to_arrive": 12,
                "note": "湘北",
            },
            {
                "company_id": "S004",
                "cutoff_day": 99,
                "month_of_payment_term": 2,
                "payment_day": 10,
                "purchase_pic": None,
                "contact_person": None,
                "order_policy": OrderPolicy.periodically,
                "order_week_num": 4,
                "days_to_arrive": 10,
                "note": "湘北",
            },
            {
                "company_id": "S005",
                "cutoff_day": 5,
                "month_of_payment_term": 2,
                "payment_day": 15,
                "purchase_pic": None,
                "contact_person": "三井寿",
                "order_policy": OrderPolicy.periodically,
                "order_week_num": 3,
                "days_to_arrive": 10,
                "note": "湘北",
            },
        ],
    )

    # 支払締日、支払期限の計算TODO:
    op.execute(
        """
        CREATE FUNCTION mst.calc_payment_deadline(
            operation_date date,
            supplier_id text,
            OUT closing_date date,
            OUT payment_deadline date,
            OUT dummy text
        ) AS $$
        DECLARE
            rec record;
            cuurent_last_date date;
            cutoff_day_interval interval;

            payment_month_first_date date;
            payment_month_last_date date;
            payment_day_interval interval;

        BEGIN
            SELECT * INTO rec
            FROM mst.suppliers
            WHERE company_id = supplier_id;

            -- 締日の計算
            cuurent_last_date:=DATE(DATE_TRUNC('month', operation_date) + '1 month' +'-1 Day');
            cutoff_day_interval:=CAST((rec.cutoff_day - 1) || ' Day' AS interval);

            IF EXTRACT(day FROM cuurent_last_date) < rec.cutoff_day THEN
                closing_date:=cuurent_last_date;
                dummy:='※月末締';
            ELSEIF rec.cutoff_day < EXTRACT(day FROM operation_date) THEN
                closing_date:=DATE(DATE_TRUNC('month', operation_date) + '1 month' + cutoff_day_interval);
                dummy:='翌月締';
            ELSE
                closing_date:=DATE(DATE_TRUNC('month', operation_date) + cutoff_day_interval);
                dummy:='当月締';
            END IF;

            -- 支払期限日の計算
            payment_month_first_date:=DATE(DATE_TRUNC('month', closing_date) + CAST(rec.month_of_payment_term || ' month' AS interval));
            payment_month_last_date:=payment_month_first_date + CAST('1 month' AS interval) +CAST('-1 Day' AS interval);
            payment_day_interval:=CAST((rec.payment_day - 1) || ' Day' AS interval);

            IF EXTRACT(day FROM payment_month_last_date) < rec.payment_day THEN
                payment_deadline:=payment_month_last_date;
                dummy:=dummy || '、※支払期限は月末';
            ELSE
                payment_deadline:=payment_month_first_date + payment_day_interval;
            END IF;

        END;
        $$ LANGUAGE plpgsql;
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_destination_address_table() -> None:
    destination_address_table = op.create_table(
        "destination_address",
        sa.Column("id", sa.Integer, primary_key=True, comment="送付先ID"),
        sa.Column(
            "company_id", sa.String(4), nullable=False, index=True, comment="企業ID"
        ),
        sa.Column("postal_code", sa.String(8), nullable=False, comment="郵便番号"),
        sa.Column("address", sa.Text, nullable=False, comment="住所"),
        sa.Column("phone_no", sa.String(10), nullable=False, comment="電話番号"),
        sa.Column("fax_no", sa.String(10), nullable=True, comment="FAX番号"),
        *timestamps(),
        schema="mst",
    )

    op.create_check_constraint(
        "ck_postal_code",
        "destination_address",
        "postal_code ~* '^[0-9]{3}-[0-9]{4}$'",
        schema="mst",
    )
    op.create_check_constraint(
        "ck_phone_no",
        "destination_address",
        "phone_no ~* '^0[0-9]{9,10}$'",
        schema="mst",
    )
    op.create_check_constraint(
        "ck_fax_no",
        "destination_address",
        "fax_no ~* '^0[0-9]{9,10}$'",
        schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER destination_address_modified
            BEFORE UPDATE
            ON mst.destination_address
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )
    op.create_foreign_key(
        "fk_company_id",
        "destination_address",
        "companies",
        ["company_id"],
        ["company_id"],
        ondelete="CASCADE",
        source_schema="mst",
        referent_schema="mst",
    )

    op.bulk_insert(
        destination_address_table,
        [
            {
                "company_id": "C001",
                "postal_code": "231-0005",
                "address": "神奈川県横浜市中区本町3-33",
                "phone_no": "0452112101",
                "fax_no": "0452112101",
            },
            {
                "company_id": "C001",
                "postal_code": "277-0005",
                "address": "千葉県柏市柏2-2-3",
                "phone_no": "0471642281",
                "fax_no": None,
            },
            {
                "company_id": "C002",
                "postal_code": "320-0033",
                "address": "栃木県宇都宮市本町5-14",
                "phone_no": "0286224271",
                "fax_no": None,
            },
        ],
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_products_table(status_type: ENUM) -> None:
    products_table = op.create_table(
        "products",
        sa.Column("product_id", sa.String(10), primary_key=True, comment="当社商品ID"),
        sa.Column("supplier_id", sa.String(4), nullable=False, comment="仕入先ID"),
        sa.Column("product_code", sa.String(30), nullable=False, comment="商品コード"),
        sa.Column("product_name", sa.String(50), nullable=False, comment="商品名"),
        sa.Column("capacity", sa.String(10), nullable=False, comment="容量"),
        sa.Column(
            "selling_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="標準売価",
        ),
        sa.Column(
            "cost_price",
            sa.Numeric,
            nullable=False,
            server_default="0.0",
            comment="標準原価",
        ),
        sa.Column("days_to_arrive", sa.Integer, nullable=True, comment="標準入荷日数"),
        sa.Column(
            "status",
            status_type,
            nullable=False,
            server_default=MasterStatus.ready,
            index=True,
            comment="ステータス",
        ),
        sa.Column("note", sa.Text, nullable=True, comment="摘要"),
        *timestamps(),
        schema="mst",
    )
    op.create_check_constraint(
        "ck_selling_price",
        "products",
        "selling_price >= 0.0",
        schema="mst",
    )
    op.create_check_constraint(
        "ck_cost_price",
        "products",
        "cost_price >= 0.0",
        schema="mst",
    )
    op.create_check_constraint(
        "ck_selling_price_upper_cost_price",
        "products",
        "selling_price >= cost_price",
        schema="mst",
    )
    op.create_check_constraint(
        "ck_days_to_arrive",
        "products",
        "days_to_arrive > 0",
        schema="mst",
    )

    op.execute(
        """
        CREATE TRIGGER products_modified
            BEFORE UPDATE
            ON mst.products
            FOR EACH ROW
        EXECUTE PROCEDURE set_modified_at();
        """
    )
    op.create_foreign_key(
        "fk_supplier_id",
        "products",
        "suppliers",
        ["supplier_id"],
        ["company_id"],
        ondelete="RESTRICT",
        source_schema="mst",
        referent_schema="mst",
    )
    op.create_unique_constraint(
        "uk_supplier_product_code",
        "products",
        ["supplier_id", "product_code"],
        schema="mst",
    )

    # 指定日付以降に発注した場合の発注日、納期予定日を計算TODO:
    op.execute(
        """
        CREATE FUNCTION mst.calc_ordering_date(
            operation_date date,
            i_product_id text,
            OUT estimate_ordering date,
            OUT estimate_weahousing date
        ) AS $$
        DECLARE
            product_rec record;
            supplier_rec record;

            weeknum_of_operation integer;
        BEGIN
            --商品マスタ、仕入先マスタの検索
            SELECT * INTO product_rec
            FROM mst.products
            WHERE product_id = i_product_id;

            SELECT * INTO supplier_rec
            FROM mst.suppliers
            WHERE company_id = product_rec.supplier_id;

            --最短発注日計算
            IF supplier_rec.order_policy = 'AS_NEEDED' THEN
                --随時発注の場合当日発注
                estimate_ordering:=operation_date;
            ELSE
                --定期発注の場合次の発注曜日を計算
                weeknum_of_operation:= date_part('dow', operation_date);
                estimate_ordering:=operation_date + CAST(
                    MOD(7 + supplier_rec.order_week_num - weeknum_of_operation, 7) || ' Day' AS interval
                );
            END IF;

            --納入予定日計算
            IF product_rec.days_to_arrive IS NULL THEN
                estimate_weahousing:=estimate_ordering + CAST(supplier_rec.days_to_arrive || ' Day' AS interval);
            ELSE
                estimate_weahousing:=estimate_ordering + CAST(product_rec.days_to_arrive || ' Day' AS interval);
            END IF;

        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.bulk_insert(
        products_table,
        [
            {
                "product_id": "S001-00001",
                "supplier_id": "S001",
                "product_code": "B00F4J8EZ0",
                "product_name": "EVA B錠（TABLETS 60錠）",
                "capacity": "100セット",
                "selling_price": 25000.00,
                "cost_price": 10000.00,
                "days_to_arrive": None,
                "status": MasterStatus.active,
                "note": None,
            },
            {
                "product_id": "S001-00002",
                "supplier_id": "S001",
                "product_code": "B09JYBSFS3",
                "product_name": "EVA B錠（TABLETS 90錠）",
                "capacity": "100セット",
                "selling_price": 30000.00,
                "cost_price": 12000.00,
                "days_to_arrive": None,
                "status": MasterStatus.active,
                "note": None,
            },
            {
                "product_id": "S001-00003",
                "supplier_id": "S001",
                "product_code": "B00F4KZ5J2",
                "product_name": "エムタックイム顆粒 14包",
                "capacity": "20セット",
                "selling_price": 15000.00,
                "cost_price": 8000.00,
                "days_to_arrive": 5,
                "status": MasterStatus.active,
                "note": None,
            },
            {
                "product_id": "S001-00004",
                "supplier_id": "S001",
                "product_code": "B083Q9N2TS",
                "product_name": "アレジウンFX 56錠",
                "capacity": "50セット",
                "selling_price": 150000.00,
                "cost_price": 100000.00,
                "days_to_arrive": None,
                "status": MasterStatus.stop_dealing,
                "note": "仕入先廃止商品",
            },
            {
                "product_id": "S001-00005",
                "supplier_id": "S001",
                "product_code": "B00F436RXM",
                "product_name": "ガストン10 12錠",
                "capacity": "20セット",
                "selling_price": 40000.00,
                "cost_price": 25000.00,
                "days_to_arrive": None,
                "status": MasterStatus.ready,
                "note": None,
            },
            {
                "product_id": "S002-00001",
                "supplier_id": "S002",
                "product_code": "Z0615",
                "product_name": "デスクチェア メッシュチェア ブラック",
                "capacity": "1脚",
                "selling_price": 40000.00,
                "cost_price": 20000.00,
                "days_to_arrive": None,
                "status": MasterStatus.active,
                "note": None,
            },
            {
                "product_id": "S003-00001",
                "supplier_id": "S003",
                "product_code": "B00F4J8EZ0",
                "product_name": "シルバーブレンド 120g",
                "capacity": "200本",
                "selling_price": 150000.00,
                "cost_price": 100000.00,
                "days_to_arrive": None,
                "status": MasterStatus.active,
                "note": None,
            },
            {
                "product_id": "S005-00001",
                "supplier_id": "S005",
                "product_code": "B01N9AQTQ0",
                "product_name": "H鋼 1000×100×6/8",
                "capacity": "1m",
                "selling_price": 5000.00,
                "cost_price": 3000.00,
                "days_to_arrive": None,
                "status": MasterStatus.active,
                "note": None,
            },
        ],
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def create_view() -> None:
    op.execute(
        """
        CREATE VIEW mst.view_destination_address AS
            SELECT
                company_id,
                0 AS seq_no,
                postal_code,
                address,
                phone_no,
                fax_no
            FROM mst.companies
            UNION
            SELECT
                company_id,
                ROW_NUMBER() OVER(partition by "company_id" order by "id") AS seq_no,
                postal_code,
                address,
                phone_no,
                fax_no
            FROM mst.destination_address
            ORDER BY company_id, seq_no
        """
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


# INFO:
def upgrade() -> None:
    status_type = create_status_type()

    create_companies_table(status_type)
    create_costomers_table()
    create_suppliers_table()
    create_destination_address_table()
    create_products_table(status_type)
    create_view()


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS mst.products CASCADE;")
    op.execute("DROP TABLE IF EXISTS mst.destination_address CASCADE;")
    op.execute("DROP TABLE IF EXISTS mst.suppliers CASCADE;")
    op.execute("DROP TABLE IF EXISTS mst.costomers CASCADE;")
    op.execute("DROP TABLE IF EXISTS mst.companies CASCADE;")
    op.execute("DROP TYPE IF EXISTS mst.order_policy;")
    op.execute("DROP TYPE IF EXISTS mst.status;")
