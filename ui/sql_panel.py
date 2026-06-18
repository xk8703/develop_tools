"""
SQL 工具面板

功能：
1. 表字段查询 - 连接数据库，查看表结构详情
   并根据字段名、类型、注解生成 Java Entity 类代码
   支持 MySQL、PostgreSQL、SQLite
"""

import customtkinter as ctk
import json
import os
import re
from tkinter import filedialog, ttk
import tkinter as tk

# 数据库连接配置文件路径
DB_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db_connections.json")

# ==================== MySQL 类型 → Java 类型映射 ====================

MYSQL_TYPE_MAP = {
    "bigint": "Long",
    "int": "Integer",
    "integer": "Integer",
    "tinyint": "Integer",
    "smallint": "Integer",
    "mediumint": "Integer",
    "varchar": "String",
    "char": "String",
    "text": "String",
    "longtext": "String",
    "mediumtext": "String",
    "tinytext": "String",
    "decimal": "BigDecimal",
    "numeric": "BigDecimal",
    "float": "Float",
    "double": "Double",
    "datetime": "LocalDateTime",
    "timestamp": "LocalDateTime",
    "date": "LocalDate",
    "time": "LocalTime",
    "boolean": "Boolean",
    "bit": "Boolean",
    "blob": "byte[]",
    "binary": "byte[]",
    "varbinary": "byte[]",
    "json": "String",
}

PG_TYPE_MAP = {
    "bigint": "Long",
    "bigserial": "Long",
    "int8": "Long",
    "integer": "Integer",
    "int": "Integer",
    "int4": "Integer",
    "serial": "Integer",
    "smallint": "Integer",
    "int2": "Integer",
    "smallserial": "Integer",
    "tinyint": "Integer",
    "character varying": "String",
    "varchar": "String",
    "character": "String",
    "char": "String",
    "text": "String",
    "name": "String",
    "numeric": "BigDecimal",
    "decimal": "BigDecimal",
    "real": "Float",
    "float4": "Float",
    "double precision": "Double",
    "float8": "Double",
    "timestamp without time zone": "LocalDateTime",
    "timestamp with time zone": "LocalDateTime",
    "timestamp": "LocalDateTime",
    "date": "LocalDate",
    "time without time zone": "LocalTime",
    "time with time zone": "LocalTime",
    "time": "LocalTime",
    "boolean": "Boolean",
    "bool": "Boolean",
    "bit": "Boolean",
    "bytea": "byte[]",
    "json": "String",
    "jsonb": "String",
    "uuid": "String",
}

SQLITE_TYPE_MAP = {
    "integer": "Integer",
    "int": "Integer",
    "bigint": "Long",
    "text": "String",
    "varchar": "String",
    "char": "String",
    "blob": "byte[]",
    "real": "Double",
    "float": "Float",
    "double": "Double",
    "decimal": "BigDecimal",
    "numeric": "BigDecimal",
    "boolean": "Boolean",
    "datetime": "LocalDateTime",
    "date": "LocalDate",
    "time": "LocalTime",
    "timestamp": "LocalDateTime",
}


class SQLPanel(ctk.CTkFrame):
    """SQL 工具面板"""

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        # 创建选项卡视图
        self.tabview = ctk.CTkTabview(self, width=600, height=500)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_fields = self.tabview.add("表字段")

        self._columns_data = []
        self._auto_loading = False

        self._create_table_fields_tab()

    # ==================== 表字段选项卡 ====================

    def _create_table_fields_tab(self):
        frame = ctk.CTkFrame(self.tab_fields)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- 数据库类型 ---
        type_frame = ctk.CTkFrame(frame)
        type_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(type_frame, text="类型:", width=60, anchor="w").pack(
            side="left", padx=(10, 5)
        )
        self.db_type_var = ctk.StringVar(value="MySQL")
        ctk.CTkOptionMenu(
            type_frame, values=["MySQL", "PostgreSQL", "SQLite"],
            variable=self.db_type_var, command=self._on_db_type_change, width=150
        ).pack(side="left")

        # --- 保存/加载连接配置 ---
        save_frame = ctk.CTkFrame(frame)
        save_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(save_frame, text="配置:", width=60, anchor="w").pack(
            side="left", padx=(10, 5)
        )
        self.conn_combo = ctk.CTkComboBox(save_frame, width=160, values=self._load_config_names())
        self.conn_combo.pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            save_frame, text="加载", width=60, command=self._load_conn
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            save_frame, text="保存", width=60, command=self._save_conn
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            save_frame, text="删除", width=60,
            fg_color="gray", hover_color="gray40",
            command=self._delete_conn
        ).pack(side="left")

        # --- 可折叠的连接详情区域 ---
        self._conn_expanded = True
        self._save_frame_ref = save_frame

        toggle_row = ctk.CTkFrame(frame, fg_color="transparent")
        toggle_row.pack(fill="x", pady=(0, 2))

        self._toggle_btn = ctk.CTkButton(
            toggle_row, text="▼ 连接详情", width=120, height=28,
            anchor="w", fg_color="transparent",
            hover_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._toggle_conn_section
        )
        self._toggle_btn.pack(side="left", padx=(5, 0))
        self._toggle_row_ref = toggle_row

        # 连接详情容器
        self.conn_container = ctk.CTkFrame(frame, fg_color="transparent")

        # --- MySQL/PostgreSQL 连接框 ---
        self.conn_frame = ctk.CTkFrame(self.conn_container)
        self.conn_frame.pack(fill="x")

        # Row 0: host + port
        ctk.CTkLabel(self.conn_frame, text="主机:", width=80, anchor="w").grid(
            row=0, column=0, padx=(10, 5), pady=2, sticky="w"
        )
        self.host_entry = ctk.CTkEntry(self.conn_frame, width=160)
        self.host_entry.grid(row=0, column=1, padx=5, pady=2)
        self.host_entry.insert(0, "localhost")

        ctk.CTkLabel(self.conn_frame, text="端口:", width=60, anchor="w").grid(
            row=0, column=2, padx=(10, 5), pady=2, sticky="w"
        )
        self.port_entry = ctk.CTkEntry(self.conn_frame, width=80)
        self.port_entry.grid(row=0, column=3, padx=5, pady=2)
        self.port_entry.insert(0, "3306")

        # Row 1: user + password
        ctk.CTkLabel(self.conn_frame, text="用户名:", width=80, anchor="w").grid(
            row=1, column=0, padx=(10, 5), pady=2, sticky="w"
        )
        self.user_entry = ctk.CTkEntry(self.conn_frame, width=160)
        self.user_entry.grid(row=1, column=1, padx=5, pady=2)

        ctk.CTkLabel(self.conn_frame, text="密码:", width=60, anchor="w").grid(
            row=1, column=2, padx=(10, 5), pady=2, sticky="w"
        )
        self.pwd_entry = ctk.CTkEntry(self.conn_frame, width=80, show="*")
        self.pwd_entry.grid(row=1, column=3, padx=5, pady=2)

        # Row 2: database name
        ctk.CTkLabel(self.conn_frame, text="数据库:", width=80, anchor="w").grid(
            row=2, column=0, padx=(10, 5), pady=2, sticky="w"
        )
        self.db_entry = ctk.CTkEntry(self.conn_frame, width=160)
        self.db_entry.grid(row=2, column=1, padx=5, pady=2)

        # Row 3: schema（PostgreSQL 专用，初始隐藏）
        self._schema_label = ctk.CTkLabel(self.conn_frame, text="Schema:", width=80, anchor="w")
        self._schema_entry = ctk.CTkEntry(self.conn_frame, width=160)
        self._schema_entry.insert(0, "public")
        # 不 grid，选 PostgreSQL 时才显示

        # --- SQLite 连接框（初始隐藏） ---
        self.sqlite_frame = ctk.CTkFrame(self.conn_container)

        ctk.CTkLabel(self.sqlite_frame, text="文件:", width=60, anchor="w").pack(
            side="left", padx=(10, 5)
        )
        self.sqlite_path = ctk.CTkEntry(
            self.sqlite_frame, placeholder_text="SQLite 数据库文件路径"
        )
        self.sqlite_path.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            self.sqlite_frame, text="浏览", width=60, command=self._browse_sqlite
        ).pack(side="left", padx=(0, 10))

        # 默认展开
        self.conn_container.pack(fill="x", pady=(0, 5), after=self._toggle_row_ref)

        # --- 表名输入 + 按钮 ---
        query_frame = ctk.CTkFrame(frame)
        query_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(query_frame, text="表名:", width=60, anchor="w").pack(
            side="left", padx=(10, 5)
        )
        self.table_entry = ctk.CTkEntry(query_frame, width=160)
        self.table_entry.pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            query_frame, text="查询并生成", command=self._query_and_generate, width=120
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            query_frame, text="查询所有表", command=self._query_all_tables, width=100
        ).pack(side="left", padx=(0, 5))

        # --- Entity 类名输入 ---
        entity_frame = ctk.CTkFrame(frame)
        entity_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(entity_frame, text="类名:", width=60, anchor="w").pack(
            side="left", padx=(10, 5)
        )
        self.entity_name_entry = ctk.CTkEntry(entity_frame, width=160, placeholder_text="留空则自动从表名生成")
        self.entity_name_entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            entity_frame, text="生成Entity", command=self._generate_entity, width=100
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            entity_frame, text="复制代码", command=self._copy_entity_code, width=100
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            entity_frame, text="复制字段名", command=self._copy_field_names, width=100
        ).pack(side="left")

        # --- 结果区：上面字段列表，下面 Entity 代码 ---
        result_paned = ctk.CTkFrame(frame, fg_color="transparent")
        result_paned.pack(fill="both", expand=True, padx=10, pady=(5, 0))

        # 上半部分：字段列表
        tree_label = ctk.CTkLabel(result_paned, text="字段列表:", anchor="w")
        tree_label.pack(fill="x", pady=(0, 2))

        self._create_treeview(result_paned)

        # 下半部分：Entity 代码输出
        code_label = ctk.CTkLabel(result_paned, text="Entity 代码:", anchor="w")
        code_label.pack(fill="x", pady=(5, 2))

        self.entity_output = ctk.CTkTextbox(result_paned, height=200)
        self.entity_output.pack(fill="both", expand=True, pady=(0, 0))

    def _create_treeview(self, parent):
        """创建表字段结果树状视图"""
        bg_color = "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#ececec"

        self.tree_container = tk.Frame(parent, bg=bg_color, height=160)
        self.tree_container.pack(fill="x", pady=(0, 0))

        style = ttk.Style()
        style.configure("SqlTree.Treeview",
                        font=("Microsoft YaHei UI", 12),
                        rowheight=28)
        style.configure("SqlTree.Treeview.Heading",
                        font=("Microsoft YaHei UI", 12, "bold"))

        columns = ("name", "comment", "type", "default")
        self.tree = ttk.Treeview(
            self.tree_container,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="SqlTree.Treeview",
            height=5,
        )

        self.tree.heading("name", text="列名", anchor="w")
        self.tree.heading("comment", text="备注", anchor="w")
        self.tree.heading("type", text="类型", anchor="w")
        self.tree.heading("default", text="默认值", anchor="w")

        self.tree.column("name", width=160, minwidth=80)
        self.tree.column("comment", width=200, minwidth=80)
        self.tree.column("type", width=140, minwidth=80)
        self.tree.column("default", width=120, minwidth=60)

        vsb = ttk.Scrollbar(self.tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree_container.grid_rowconfigure(0, weight=1)
        self.tree_container.grid_columnconfigure(0, weight=1)

        self._field_data = []

    # ==================== Entity 生成逻辑 ====================

    @staticmethod
    def _snake_to_camel(name):
        """snake_case → camelCase"""
        parts = name.split("_")
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])

    @staticmethod
    def _snake_to_pascal(name):
        """snake_case → PascalCase"""
        return "".join(p.capitalize() for p in name.split("_"))

    def _db_type_to_java(self, db_type_str, db_type):
        """将数据库类型字符串映射为 Java 类型"""
        if not db_type_str:
            return "String"

        # 去掉括号内的内容，如 varchar(255) → varchar, decimal(10,2) → decimal
        base_type = re.sub(r'\(.*\)', '', db_type_str).strip().lower()

        if db_type == "MySQL":
            java_type = MYSQL_TYPE_MAP.get(base_type)
        elif db_type == "PostgreSQL":
            java_type = PG_TYPE_MAP.get(base_type)
        elif db_type == "SQLite":
            java_type = SQLITE_TYPE_MAP.get(base_type)
        else:
            java_type = None

        return java_type or "String"

    def _generate_entity(self):
        """根据已查询的字段数据生成 Java Entity 类"""
        if not self._columns_data:
            self._set_text(self.entity_output, "请先查询表字段")
            return

        table_name = self.table_entry.get().strip()

        # 类名：手动输入 or 自动从表名生成
        class_name = self.entity_name_entry.get().strip()
        if not class_name:
            class_name = self._snake_to_pascal(table_name)

        db_type = self.db_type_var.get()
        lines = []

        lines.append("/**")
        lines.append(f" * 表 {table_name} 对应实体类")
        lines.append(" */")
        lines.append("@Data")
        lines.append(f'@TableName("{table_name}")')
        lines.append(f"public class {class_name} {{")
        lines.append("")

        for col in self._columns_data:
            name = col["name"]
            col_type = col["type"]
            key = col.get("key", "")
            comment = col.get("comment", "")

            java_type = self._db_type_to_java(col_type, db_type)
            java_name = self._snake_to_camel(name)

            # 注释（始终输出）
            if comment:
                lines.append(f"    /** {comment} */")
            else:
                lines.append("    /**  */")

            # 注解：主键用 @TableId，其余用 @TableField
            if key in ("PRI", "PK"):
                lines.append(f'    @TableId(value = "{name}", type = IdType.ASSIGN_ID)')
            else:
                lines.append(f'    @TableField("{name}")')

            lines.append(f"    private {java_type} {java_name};")
            lines.append("")

        lines.append("}")

        code = "\n".join(lines)
        self._set_text(self.entity_output, code)

    # ==================== 连接配置保存/加载 ====================

    @staticmethod
    def _read_all_configs():
        if not os.path.exists(DB_CONFIG_FILE):
            return {}
        try:
            with open(DB_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _write_all_configs(configs):
        with open(DB_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)

    def _load_config_names(self):
        """按当前数据库类型过滤配置名称"""
        db_type = self.db_type_var.get()
        configs = self._read_all_configs()
        matched = [name for name, cfg in configs.items() if cfg.get("type") == db_type]
        return matched if matched else ["(无已保存配置)"]

    def _refresh_config_combo(self):
        """刷新下拉列表，只有一个配置时自动加载"""
        names = self._load_config_names()
        self.conn_combo.configure(values=names)
        if names and names[0] != "(无已保存配置)":
            self.conn_combo.set(names[0])
            if len(names) == 1 and not self._auto_loading:
                self._auto_loading = True
                self._load_conn()
                self._auto_loading = False
        elif names:
            self.conn_combo.set(names[0])

    def _save_conn(self):
        dialog = _SaveConfigDialog(self.winfo_toplevel())
        name = dialog.get_input()
        if not name:
            return

        db_type = self.db_type_var.get()
        config = {"type": db_type}

        if db_type == "SQLite":
            config["path"] = self.sqlite_path.get()
        else:
            config["host"] = self.host_entry.get()
            config["port"] = self.port_entry.get()
            config["user"] = self.user_entry.get()
            config["password"] = self.pwd_entry.get()
            config["database"] = self.db_entry.get()
            if db_type == "PostgreSQL":
                config["schema"] = self._schema_entry.get()

        configs = self._read_all_configs()
        configs[name] = config
        self._write_all_configs(configs)

        self._refresh_config_combo()
        self.conn_combo.set(name)

    def _load_conn(self):
        name = self.conn_combo.get()
        if not name or name == "(无已保存配置)":
            return

        configs = self._read_all_configs()
        if name not in configs:
            return

        config = configs[name]
        db_type = config.get("type", "MySQL")
        self.db_type_var.set(db_type)
        self._on_db_type_change(db_type)

        if db_type == "SQLite":
            self.sqlite_path.delete(0, "end")
            self.sqlite_path.insert(0, config.get("path", ""))
        else:
            self.host_entry.delete(0, "end")
            self.host_entry.insert(0, config.get("host", "localhost"))

            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, config.get("port", "3306"))

            self.user_entry.delete(0, "end")
            self.user_entry.insert(0, config.get("user", ""))

            self.pwd_entry.delete(0, "end")
            self.pwd_entry.insert(0, config.get("password", ""))

            self.db_entry.delete(0, "end")
            self.db_entry.insert(0, config.get("database", ""))

            if db_type == "PostgreSQL":
                self._schema_entry.delete(0, "end")
                self._schema_entry.insert(0, config.get("schema", "public"))

    def _delete_conn(self):
        name = self.conn_combo.get()
        if not name or name == "(无已保存配置)":
            return

        configs = self._read_all_configs()
        if name in configs:
            del configs[name]
            self._write_all_configs(configs)

        self._refresh_config_combo()

    # ==================== 连接详情折叠/展开 ====================

    def _toggle_conn_section(self):
        self._conn_expanded = not self._conn_expanded
        if self._conn_expanded:
            self.conn_container.pack(fill="x", pady=(0, 5), after=self._toggle_row_ref)
            self._toggle_btn.configure(text="▼ 连接详情")
        else:
            self.conn_container.pack_forget()
            self._toggle_btn.configure(text="▶ 连接详情")

    def _on_db_type_change(self, choice):
        # 隐藏 schema 行
        self._schema_label.grid_forget()
        self._schema_entry.grid_forget()

        if choice == "SQLite":
            self.conn_frame.pack_forget()
            self.sqlite_frame.pack(fill="x")
        else:
            self.sqlite_frame.pack_forget()
            self.conn_frame.pack(fill="x")
            if choice == "MySQL":
                self.port_entry.delete(0, "end")
                self.port_entry.insert(0, "3306")
            elif choice == "PostgreSQL":
                self.port_entry.delete(0, "end")
                self.port_entry.insert(0, "5432")
                # 显示 schema 行
                self._schema_label.grid(row=3, column=0, padx=(10, 5), pady=2, sticky="w")
                self._schema_entry.grid(row=3, column=1, padx=5, pady=2, sticky="w")

        # 刷新配置下拉（按类型过滤，只有一个时自动加载；自动加载中不重复触发）
        if not self._auto_loading:
            self._refresh_config_combo()

    def _browse_sqlite(self):
        path = filedialog.askopenfilename(
            filetypes=[("SQLite", "*.db *.sqlite *.sqlite3"), ("所有文件", "*.*")]
        )
        if path:
            self.sqlite_path.delete(0, "end")
            self.sqlite_path.insert(0, path)

    # ==================== 查询逻辑 ====================

    def _query_and_generate(self):
        """查询表字段并自动生成 Entity 代码"""
        db_type = self.db_type_var.get()
        table_name = self.table_entry.get().strip()

        if not table_name:
            self._clear_tree()
            self._set_text(self.entity_output, "请输入表名")
            return

        if not all(c.isalnum() or c == "_" for c in table_name):
            self._clear_tree()
            self._set_text(self.entity_output, "表名只能包含字母、数字和下划线")
            return

        try:
            columns = self._fetch_columns_detail(db_type, table_name)
        except ImportError:
            drivers = {"MySQL": "pymysql", "PostgreSQL": "psycopg2", "SQLite": "内置模块"}
            driver = drivers.get(db_type, "")
            self._set_text(self.entity_output, f"缺少数据库驱动，请安装:\npip install {driver}")
            return
        except Exception as e:
            self._set_text(self.entity_output, f"查询失败: {str(e)}")
            return

        if not columns:
            self._set_text(self.entity_output, f"表 '{table_name}' 未找到或没有字段")
            return

        self._fill_tree(columns)
        self._generate_entity()

    def _query_all_tables(self):
        """查询数据库中所有表"""
        db_type = self.db_type_var.get()

        try:
            tables = self._fetch_all_tables(db_type)
        except Exception as e:
            self._set_text(self.entity_output, f"查询失败: {str(e)}")
            return

        self._clear_tree()
        self._columns_data = []
        self._field_data = []
        for t in tables:
            table_name = t[0]
            self.tree.insert("", "end", values=(
                table_name,
                "", "", ""
            ))
            self._field_data.append(table_name)
        self._set_text(self.entity_output, f"共查询到 {len(tables)} 张表")

    def _fetch_all_tables(self, db_type):
        if db_type == "MySQL":
            return self._fetch_mysql_tables()
        elif db_type == "PostgreSQL":
            return self._fetch_pg_tables()
        elif db_type == "SQLite":
            return self._fetch_sqlite_tables()
        return []

    def _fetch_mysql_tables(self):
        import pymysql
        conn = pymysql.connect(
            host=self.host_entry.get(),
            port=int(self.port_entry.get()),
            user=self.user_entry.get(),
            password=self.pwd_entry.get(),
            database=self.db_entry.get(),
            charset="utf8mb4",
        )
        try:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLE STATUS")
            return [(row[0], row[1]) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _fetch_pg_tables(self):
        import psycopg2
        conn = psycopg2.connect(
            host=self.host_entry.get(),
            port=int(self.port_entry.get()),
            user=self.user_entry.get(),
            password=self.pwd_entry.get(),
            dbname=self.db_entry.get(),
        )
        try:
            schema = self._schema_entry.get().strip() or "public"
            cursor = conn.cursor()
            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = %s ORDER BY table_name",
                (schema,)
            )
            return [(row[0],) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _fetch_sqlite_tables(self):
        import sqlite3
        path = self.sqlite_path.get().strip()
        if not path:
            return []
        conn = sqlite3.connect(path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            return cursor.fetchall()
        finally:
            conn.close()

    def _fetch_columns_detail(self, db_type, table_name):
        """获取表的字段详细信息"""
        if db_type == "MySQL":
            return self._fetch_mysql_columns(table_name)
        elif db_type == "PostgreSQL":
            return self._fetch_pg_columns(table_name)
        elif db_type == "SQLite":
            return self._fetch_sqlite_columns(table_name)
        return []

    def _fetch_mysql_columns(self, table_name):
        """MySQL: SHOW FULL COLUMNS 返回详细列信息"""
        import pymysql
        conn = pymysql.connect(
            host=self.host_entry.get(),
            port=int(self.port_entry.get()),
            user=self.user_entry.get(),
            password=self.pwd_entry.get(),
            database=self.db_entry.get(),
            charset="utf8mb4",
        )
        try:
            cursor = conn.cursor()
            db_name = self.db_entry.get()
            cursor.execute(
                "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, "
                "COLUMN_DEFAULT, COLUMN_COMMENT "
                "FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
                "ORDER BY ORDINAL_POSITION",
                (db_name, table_name)
            )
            result = []
            for row in cursor.fetchall():
                result.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2],
                    "key": row[3] or "",
                    "default": str(row[4]) if row[4] is not None else "",
                    "comment": row[5] or "",
                })
            return result
        finally:
            conn.close()

    def _fetch_pg_columns(self, table_name):
        """PostgreSQL: 通过 pg_description 获取字段注释"""
        import psycopg2
        conn = psycopg2.connect(
            host=self.host_entry.get(),
            port=int(self.port_entry.get()),
            user=self.user_entry.get(),
            password=self.pwd_entry.get(),
            dbname=self.db_entry.get(),
        )
        try:
            schema = self._schema_entry.get().strip() or "public"
            with conn.cursor() as cur:
                # 查字段 + 注释
                cur.execute(
                    """
                    SELECT
                        c.column_name,
                        COALESCE(c.udt_name, c.data_type) AS data_type,
                        c.is_nullable,
                        c.column_default,
                        pgd.description AS comment
                    FROM information_schema.columns c
                    LEFT JOIN pg_catalog.pg_statio_all_tables st
                           ON st.schemaname = c.table_schema
                          AND st.relname    = c.table_name
                    LEFT JOIN pg_catalog.pg_description pgd
                           ON pgd.objoid    = st.relid
                          AND pgd.objsubid  = c.ordinal_position
                    WHERE c.table_schema = %s
                      AND c.table_name   = %s
                    ORDER BY c.ordinal_position
                    """,
                    (schema, table_name)
                )
                rows = cur.fetchall()

                # 查主键
                cur.execute(
                    """
                    SELECT a.attname
                    FROM pg_index i
                    JOIN pg_attribute a
                      ON a.attrelid = i.indrelid
                     AND a.attnum  = ANY(i.indkey)
                    WHERE i.indrelid = (%s || '.' || %s)::regclass
                      AND i.indisprimary
                    """,
                    (schema, table_name)
                )
                pk_cols = {r[0] for r in cur.fetchall()}

            result = []
            for row in rows:
                col_name = row[0]
                comment = (row[4] or "").strip() if row[4] else ""
                result.append({
                    "name": col_name,
                    "type": row[1],
                    "nullable": row[2],
                    "key": "PRI" if col_name in pk_cols else "",
                    "default": str(row[3]) if row[3] else "",
                    "comment": comment,
                })
            return result
        finally:
            conn.close()

    def _fetch_sqlite_columns(self, table_name):
        """SQLite: PRAGMA table_info"""
        import sqlite3
        path = self.sqlite_path.get().strip()
        if not path:
            return []
        conn = sqlite3.connect(path)
        try:
            cursor = conn.cursor()
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            result = []
            for row in cursor.fetchall():
                result.append({
                    "name": row[1],
                    "type": row[2] or "",
                    "nullable": "NO" if row[3] else "YES",
                    "key": "PK" if row[5] else "",
                    "default": str(row[4]) if row[4] is not None else "",
                    "comment": "",
                })
            return result
        finally:
            conn.close()

    def _fill_tree(self, columns):
        """将字段信息填入树状视图（按列名去重）"""
        self._clear_tree()
        seen = set()
        deduped = []
        for col in columns:
            if col["name"] not in seen:
                seen.add(col["name"])
                deduped.append(col)
        self._columns_data = deduped
        self._field_data = []
        for col in deduped:
            self.tree.insert("", "end", values=(
                col["name"],
                col.get("comment", ""),
                col["type"],
                col.get("default", ""),
            ))
            self._field_data.append(col["name"])

    def _clear_tree(self):
        """清空树状视图"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._field_data = []
        self._columns_data = []

    def _copy_field_names(self):
        """复制所有字段名到剪贴板"""
        if not self._field_data:
            return
        text = ", ".join(self._field_data)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def _copy_entity_code(self):
        """复制 Entity 代码到剪贴板"""
        code = self.entity_output.get("1.0", "end").strip()
        if code:
            self.clipboard_clear()
            self.clipboard_append(code)
            self.update()

    @staticmethod
    def _set_text(textbox, text):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)


class _SaveConfigDialog(ctk.CTkToplevel):
    """保存配置的自定义弹窗"""

    def __init__(self, master):
        super().__init__(master)
        self.title("保存配置")
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - 400) // 2
        y = master.winfo_y() + (master.winfo_height() - 200) // 2
        self.geometry(f"+{x}+{y}")

        self.result = None

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            content, text="保存数据库连接配置",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(0, 20))

        input_row = ctk.CTkFrame(content, fg_color="transparent")
        input_row.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(input_row, text="配置名称:", font=ctk.CTkFont(size=14)).pack(
            side="left", padx=(0, 10)
        )
        self.entry = ctk.CTkEntry(input_row, height=36, font=ctk.CTkFont(size=14),
                                  placeholder_text="例如：本地MySQL")
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.focus_set()

        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.pack()

        ctk.CTkButton(
            btn_row, text="取消", width=100, height=36,
            fg_color="gray", hover_color="gray40",
            command=self._on_cancel
        ).pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            btn_row, text="保存", width=100, height=36,
            command=self._on_save
        ).pack(side="left")

        self.entry.bind("<Return>", lambda e: self._on_save())
        self.bind("<Escape>", lambda e: self._on_cancel())

        self.wait_window()

    def _on_save(self):
        val = self.entry.get().strip()
        if val:
            self.result = val
            self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()

    def get_input(self):
        return self.result
