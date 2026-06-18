"""
Generate a Java Entity class (MyBatis-Plus style) from a PostgreSQL table.

Usage:
    python pg_to_entity.py \
        --host localhost --port 5432 --db mydb \
        --user postgres --password secret \
        --schema public --table user_info \
        --package com.example.entity \
        --output ./out

Requires: psycopg2-binary  (pip install psycopg2-binary)
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import Optional

import psycopg2


# PostgreSQL data type -> (Java type, required import or None)
PG_TO_JAVA = {
    "smallint": ("Short", None),
    "int2": ("Short", None),
    "integer": ("Integer", None),
    "int": ("Integer", None),
    "int4": ("Integer", None),
    "bigint": ("Long", None),
    "int8": ("Long", None),
    "serial": ("Integer", None),
    "bigserial": ("Long", None),

    "real": ("Float", None),
    "float4": ("Float", None),
    "double precision": ("Double", None),
    "float8": ("Double", None),
    "numeric": ("BigDecimal", "java.math.BigDecimal"),
    "decimal": ("BigDecimal", "java.math.BigDecimal"),
    "money": ("BigDecimal", "java.math.BigDecimal"),

    "boolean": ("Boolean", None),
    "bool": ("Boolean", None),

    "char": ("String", None),
    "character": ("String", None),
    "varchar": ("String", None),
    "character varying": ("String", None),
    "text": ("String", None),
    "citext": ("String", None),
    "name": ("String", None),
    "uuid": ("String", None),
    "json": ("String", None),
    "jsonb": ("String", None),
    "xml": ("String", None),
    "inet": ("String", None),
    "cidr": ("String", None),
    "macaddr": ("String", None),

    "date": ("LocalDate", "java.time.LocalDate"),
    "time": ("LocalTime", "java.time.LocalTime"),
    "time without time zone": ("LocalTime", "java.time.LocalTime"),
    "time with time zone": ("OffsetTime", "java.time.OffsetTime"),
    "timestamp": ("LocalDateTime", "java.time.LocalDateTime"),
    "timestamp without time zone": ("LocalDateTime", "java.time.LocalDateTime"),
    "timestamp with time zone": ("OffsetDateTime", "java.time.OffsetDateTime"),
    "timestamptz": ("OffsetDateTime", "java.time.OffsetDateTime"),
    "interval": ("Duration", "java.time.Duration"),

    "bytea": ("byte[]", None),
}


@dataclass
class Column:
    name: str
    pg_type: str
    is_pk: bool
    is_nullable: bool
    comment: Optional[str]


def snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def snake_to_pascal(name: str) -> str:
    return "".join(p.capitalize() for p in name.split("_"))


def map_java_type(pg_type: str) -> tuple[str, Optional[str]]:
    key = pg_type.lower().strip()
    # Strip length / precision: "character varying(255)" -> "character varying"
    key = re.sub(r"\(.*\)", "", key).strip()
    if key in PG_TO_JAVA:
        return PG_TO_JAVA[key]
    # Array types: e.g. _int4, integer[]
    if key.endswith("[]") or key.startswith("_"):
        return ("Object[]", None)
    return ("String", None)


def fetch_columns(conn, schema: str, table: str) -> list[Column]:
    sql_cols = """
        SELECT
            c.column_name,
            COALESCE(c.udt_name, c.data_type)               AS data_type,
            c.is_nullable = 'YES'                           AS is_nullable,
            pgd.description                                 AS comment
        FROM information_schema.columns c
        LEFT JOIN pg_catalog.pg_statio_all_tables st
               ON st.schemaname = c.table_schema
              AND st.relname    = c.table_name
        LEFT JOIN pg_catalog.pg_description pgd
               ON pgd.objoid    = st.relid
              AND pgd.objsubid  = c.ordinal_position
        WHERE c.table_schema = %s
          AND c.table_name   = %s
        ORDER BY c.ordinal_position;
    """
    sql_pk = """
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = (%s || '.' || %s)::regclass
          AND i.indisprimary;
    """
    with conn.cursor() as cur:
        cur.execute(sql_cols, (schema, table))
        rows = cur.fetchall()
        if not rows:
            raise SystemExit(f"Table {schema}.{table} not found or has no columns.")

        cur.execute(sql_pk, (schema, table))
        pk_names = {r[0] for r in cur.fetchall()}

    return [
        Column(
            name=r[0],
            pg_type=r[1],
            is_pk=r[0] in pk_names,
            is_nullable=r[2],
            comment=(r[3] or "").strip() or None,
        )
        for r in rows
    ]


def fetch_table_comment(conn, schema: str, table: str) -> Optional[str]:
    sql = """
        SELECT obj_description((%s || '.' || %s)::regclass, 'pg_class');
    """
    with conn.cursor() as cur:
        cur.execute(sql, (schema, table))
        row = cur.fetchone()
        return (row[0] or "").strip() if row and row[0] else None


def render_entity(
    package: str,
    table: str,
    schema: str,
    table_comment: Optional[str],
    columns: list[Column],
) -> str:
    class_name = snake_to_pascal(table)

    imports: set[str] = set()
    imports.add("com.baomidou.mybatisplus.annotation.TableName")
    imports.add("com.baomidou.mybatisplus.annotation.TableId")
    imports.add("com.baomidou.mybatisplus.annotation.TableField")
    imports.add("com.baomidou.mybatisplus.annotation.IdType")
    imports.add("lombok.Getter")
    imports.add("lombok.Setter")

    field_blocks: list[str] = []
    for col in columns:
        java_type, extra_import = map_java_type(col.pg_type)
        if extra_import:
            imports.add(extra_import)

        java_name = snake_to_camel(col.name)
        lines: list[str] = []

        if col.comment:
            comment = "    /**"
            for cline in col.comment.splitlines():
                comment = comment + (f" {cline}")
            comment = comment + "*/"
            # lines.append("    /**")
            # for cline in col.comment.splitlines():
            #     lines.append(f"     * {cline}")
            # lines.append("     */")
            lines.append(comment)

        if col.is_pk:
            lines.append(f'    @TableId(value = "{col.name}", type = IdType.AUTO)')
        else:
            lines.append(f'    @TableField("{col.name}")')

        lines.append(f"    private {java_type} {java_name};")
        field_blocks.append("\n".join(lines))


    header_lines = [f"package {package};", ""]
    for imp in sorted(imports):
        header_lines.append(f"import {imp};")
    header_lines.append("")

    if table_comment:
        header_lines.append("/**")
        for cline in table_comment.splitlines():
            header_lines.append(f" * {cline}")
        header_lines.append(" */")

    header_lines.append("@Getter")
    header_lines.append("@Setter")
    # full_table = f"{schema}.{table}" if schema and schema != "public" else table
    # header_lines.append(f'@TableName("{full_table}")')
    header_lines.append(f'@TableName("{table}")')
    header_lines.append(f"public class {class_name} {{")
    header_lines.append("")

    body = "\n\n".join(field_blocks)
    return "\n".join(header_lines) + "\n" + body + "\n}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--db", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--schema", default="public")
    parser.add_argument("--table", required=True, help="Table name, or 'ALL' to dump every table in the schema")
    parser.add_argument("--package", default="com.example.entity")
    parser.add_argument("--output", default="./out", help="Output directory for .java files")
    args = parser.parse_args()

    conn = psycopg2.connect(
        host=args.host, port=args.port, dbname=args.db,
        user=args.user, password=args.password,
    )
    try:
        if args.table.upper() == "ALL":
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname = %s ORDER BY tablename",
                    (args.schema,),
                )
                tables = [r[0] for r in cur.fetchall()]
        else:
            tables = [args.table]

        os.makedirs(args.output, exist_ok=True)
        for tbl in tables:
            cols = fetch_columns(conn, args.schema, tbl)
            tbl_comment = fetch_table_comment(conn, args.schema, tbl)
            code = render_entity(args.package, tbl, args.schema, tbl_comment, cols)

            class_name = snake_to_pascal(tbl)
            out_path = os.path.join(args.output, f"{class_name}.java")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"Generated {out_path}")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
