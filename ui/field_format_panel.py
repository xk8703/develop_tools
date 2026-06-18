"""
字段格式化工具面板

功能：
1. 手动输入字段，自动添加 camelCase 别名（含下划线的字段）
2. 连接数据库查询表字段，自动格式化输出
   支持 MySQL、PostgreSQL、SQLite

特殊字段映射（可在界面中编辑）：
  tid → id, gsid → companyId, used_tag → isEffective, version_no → version
"""

import customtkinter as ctk
import json
import os
from tkinter import filedialog

# 数据库连接配置文件路径
DB_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db_connections.json")


# 默认特殊字段映射
DEFAULT_SPECIAL_MAPPINGS = {
    "tid": "id",
    "gsid": "companyId",
    "used_tag": "isEffective",
    "version_no": "version",
}


class _SaveConfigDialog(ctk.CTkToplevel):
    """保存配置的自定义弹窗"""

    def __init__(self, master):
        super().__init__(master)
        self.title("保存配置")
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # 居中显示
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - 400) // 2
        y = master.winfo_y() + (master.winfo_height() - 200) // 2
        self.geometry(f"+{x}+{y}")

        self.result = None

        # 内容区
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=20)

        # 标题
        ctk.CTkLabel(
            content, text="保存数据库连接配置",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(0, 20))

        # 输入行
        input_row = ctk.CTkFrame(content, fg_color="transparent")
        input_row.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(input_row, text="配置名称:", font=ctk.CTkFont(size=14)).pack(
            side="left", padx=(0, 10)
        )
        self.entry = ctk.CTkEntry(input_row, height=36, font=ctk.CTkFont(size=14),
                                  placeholder_text="例如：本地MySQL")
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.focus_set()

        # 按钮行
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

        # 回车确认
        self.entry.bind("<Return>", lambda e: self._on_save())
        self.bind("<Escape>", lambda e: self._on_cancel())

        # 等待窗口关闭
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


class FieldFormatPanel(ctk.CTkFrame):
    """字段格式化工具面板"""

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        self.special_mappings = dict(DEFAULT_SPECIAL_MAPPINGS)

        # 创建选项卡视图
        self.tabview = ctk.CTkTabview(self, width=600, height=500)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_manual = self.tabview.add("字段格式化")
        self.tab_database = self.tabview.add("数据库查询")

        self._create_manual_tab()
        self._create_database_tab()

    # ==================== 核心格式化逻辑 ====================

    @staticmethod
    def _parse_mappings(text):
        """解析特殊映射文本 'tid=id, gsid=companyId' → dict"""
        mappings = {}
        if not text:
            return mappings
        for pair in text.split(","):
            pair = pair.strip()
            if "=" in pair:
                key, value = pair.split("=", 1)
                key, value = key.strip(), value.strip()
                if key and value:
                    mappings[key] = value
        return mappings

    @staticmethod
    def _mappings_to_str(mappings):
        return ", ".join(f"{k}={v}" for k, v in mappings.items())

    @staticmethod
    def _snake_to_camel(name):
        """snake_case → camelCase"""
        parts = name.split("_")
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])

    def _format_field(self, field, mappings):
        """格式化单个字段，返回 'field alias' 或 'field'"""
        field = field.strip()
        if not field:
            return ""

        # 分离前缀（如 "a."）
        if "." in field:
            prefix, field_name = field.rsplit(".", 1)
            dot_prefix = prefix + "."
        else:
            dot_prefix = ""
            field_name = field

        # 1. 特殊映射优先（忽略大小写）
        if field_name.lower() in {k.lower(): v for k, v in mappings.items()}:
            alias = {k.lower(): v for k, v in mappings.items()}[field_name.lower()]
            return f"{field} {alias}"

        # 2. 无下划线，不加别名
        if "_" not in field_name:
            return field

        # 3. snake_case → camelCase
        alias = self._snake_to_camel(field_name)
        return f"{field} {alias}"

    def _format_fields_text(self, input_text, mappings):
        """格式化输入文本中的所有字段"""
        fields = []
        for line in input_text.replace("\n", ",").split(","):
            f = line.strip()
            if f:
                fields.append(f)
        formatted = [self._format_field(f, mappings) for f in fields]
        return ", ".join(formatted)

    # ==================== 手动格式化选项卡 ====================

    def _create_manual_tab(self):
        frame = ctk.CTkFrame(self.tab_manual)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 特殊映射
        map_frame = ctk.CTkFrame(frame)
        map_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(map_frame, text="特殊映射:", width=80, anchor="w").pack(
            side="left", padx=(10, 5)
        )
        self.manual_mapping = ctk.CTkEntry(
            map_frame, placeholder_text="tid=id, gsid=companyId"
        )
        self.manual_mapping.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.manual_mapping.insert(0, self._mappings_to_str(self.special_mappings))

        # 输入区
        ctk.CTkLabel(frame, text="输入字段（逗号或换行分隔）:", anchor="w").pack(
            fill="x", padx=10, pady=(5, 2)
        )
        self.manual_input = ctk.CTkTextbox(frame, height=120)
        self.manual_input.pack(fill="x", padx=10, pady=(0, 10))
        self.manual_input.insert("1.0", "a.name, a.full_name, a.brand_id, a.tid, a.gsid")

        # 按钮
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            btn_frame, text="格式化", command=self._on_manual_format, width=100
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_frame, text="复制结果", command=self._copy_manual_result, width=100
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_frame, text="清空", width=80,
            fg_color="gray", hover_color="gray40",
            command=self._clear_manual
        ).pack(side="left")

        # 输出区
        ctk.CTkLabel(frame, text="格式化结果:", anchor="w").pack(
            fill="x", padx=10, pady=(5, 2)
        )
        self.manual_output = ctk.CTkTextbox(frame, height=150)
        self.manual_output.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _on_manual_format(self):
        mappings = self._parse_mappings(self.manual_mapping.get())
        input_text = self.manual_input.get("1.0", "end").strip()
        if not input_text:
            self._set_text(self.manual_output, "请输入字段")
            return
        result = self._format_fields_text(input_text, mappings)
        self._set_text(self.manual_output, result)

    def _copy_manual_result(self):
        self._copy_to_clipboard(self.manual_output.get("1.0", "end").strip())

    def _clear_manual(self):
        self.manual_input.delete("1.0", "end")
        self.manual_output.delete("1.0", "end")

    # ==================== 数据库查询选项卡 ====================

    def _create_database_tab(self):
        frame = ctk.CTkFrame(self.tab_database)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 数据库类型（始终可见）
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

        # 保存/加载连接配置（始终可见）
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

        # ====== 可折叠的连接详情区域 ======
        self._conn_expanded = True
        self._save_frame_ref = save_frame  # 用于 pack(after=...) 定位

        # 折叠按钮
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
        self._toggle_row_ref = toggle_row  # 用于 pack(after=...) 定位

        # 连接详情（可折叠）
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

        # 表名 + 别名前缀
        query_frame = ctk.CTkFrame(frame)
        query_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(query_frame, text="表名:", width=60, anchor="w").pack(
            side="left", padx=(10, 5)
        )
        self.table_entry = ctk.CTkEntry(query_frame, width=160)
        self.table_entry.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(query_frame, text="前缀:", width=50, anchor="w").pack(
            side="left", padx=(0, 5)
        )
        self.alias_prefix = ctk.CTkEntry(query_frame, width=60)
        self.alias_prefix.pack(side="left")
        self.alias_prefix.insert(0, "a")

        # 特殊映射
        map_frame2 = ctk.CTkFrame(frame)
        map_frame2.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(map_frame2, text="特殊映射:", width=80, anchor="w").pack(
            side="left", padx=(10, 5)
        )
        self.db_mapping = ctk.CTkEntry(
            map_frame2, placeholder_text="tid=id, gsid=companyId"
        )
        self.db_mapping.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.db_mapping.insert(0, self._mappings_to_str(self.special_mappings))

        # 按钮
        btn_frame2 = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame2.pack(fill="x", padx=10, pady=(5, 5))

        ctk.CTkButton(
            btn_frame2, text="查询并格式化", command=self._query_database, width=140
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_frame2, text="复制结果", command=self._copy_db_result, width=100
        ).pack(side="left")

        # 输出区
        ctk.CTkLabel(frame, text="格式化结果:", anchor="w").pack(
            fill="x", padx=10, pady=(5, 2)
        )
        self.db_output = ctk.CTkTextbox(frame, height=150)
        self.db_output.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ==================== 连接配置保存/加载 ====================

    @staticmethod
    def _read_all_configs():
        """读取所有保存的连接配置"""
        if not os.path.exists(DB_CONFIG_FILE):
            return {}
        try:
            with open(DB_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _write_all_configs(configs):
        """写入所有连接配置"""
        with open(DB_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)

    def _load_config_names(self):
        """获取所有保存的配置名称列表"""
        configs = self._read_all_configs()
        return list(configs.keys()) if configs else ["(无已保存配置)"]

    def _refresh_config_combo(self):
        """刷新配置下拉框"""
        names = self._load_config_names()
        self.conn_combo.configure(values=names)
        if names:
            self.conn_combo.set(names[0])

    def _save_conn(self):
        """保存当前连接配置"""
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

        configs = self._read_all_configs()
        configs[name] = config
        self._write_all_configs(configs)

        self._refresh_config_combo()
        self.conn_combo.set(name)

    def _load_conn(self):
        """加载选中的连接配置"""
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

    def _delete_conn(self):
        """删除选中的连接配置"""
        name = self.conn_combo.get()
        if not name or name == "(无已保存配置)":
            return

        configs = self._read_all_configs()
        if name in configs:
            del configs[name]
            self._write_all_configs(configs)

        self._refresh_config_combo()

    # ==================== 数据库切换与查询 ====================

    def _toggle_conn_section(self):
        """折叠/展开连接详情"""
        self._conn_expanded = not self._conn_expanded
        if self._conn_expanded:
            self.conn_container.pack(fill="x", pady=(0, 5), after=self._toggle_row_ref)
            self._toggle_btn.configure(text="▼ 连接详情")
        else:
            self.conn_container.pack_forget()
            self._toggle_btn.configure(text="▶ 连接详情")

    def _on_db_type_change(self, choice):
        """切换数据库类型时显示对应的连接界面"""
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

    def _browse_sqlite(self):
        """浏览选择 SQLite 文件"""
        path = filedialog.askopenfilename(
            filetypes=[("SQLite", "*.db *.sqlite *.sqlite3"), ("所有文件", "*.*")]
        )
        if path:
            self.sqlite_path.delete(0, "end")
            self.sqlite_path.insert(0, path)

    def _query_database(self):
        """查询数据库并格式化字段"""
        db_type = self.db_type_var.get()
        table_name = self.table_entry.get().strip()

        if not table_name:
            self._set_text(self.db_output, "请输入表名")
            return

        if not all(c.isalnum() or c == "_" for c in table_name):
            self._set_text(self.db_output, "表名只能包含字母、数字和下划线")
            return

        try:
            columns = self._fetch_columns(db_type, table_name)
        except ImportError:
            drivers = {"MySQL": "pymysql", "PostgreSQL": "psycopg2", "SQLite": "内置模块"}
            driver = drivers.get(db_type, "")
            self._set_text(self.db_output, f"缺少数据库驱动，请安装:\npip install {driver}")
            return
        except Exception as e:
            self._set_text(self.db_output, f"查询失败: {str(e)}")
            return

        if not columns:
            self._set_text(self.db_output, f"表 '{table_name}' 未找到或没有字段")
            return

        # 添加前缀
        prefix = self.alias_prefix.get().strip()
        if prefix:
            fields = [f"{prefix}.{col}" for col in columns]
        else:
            fields = list(columns)

        mappings = self._parse_mappings(self.db_mapping.get())
        formatted = [self._format_field(f, mappings) for f in fields]
        self._set_text(self.db_output, ", ".join(formatted))

    def _fetch_columns(self, db_type, table_name):
        """根据数据库类型获取表字段列表"""
        if db_type == "MySQL":
            return self._fetch_mysql(table_name)
        elif db_type == "PostgreSQL":
            return self._fetch_pg(table_name)
        elif db_type == "SQLite":
            return self._fetch_sqlite(table_name)
        return []

    def _fetch_mysql(self, table_name):
        import pymysql
        conn = pymysql.connect(
            host=self.host_entry.get(),
            port=int(self.port_entry.get()),
            user=self.user_entry.get(),
            password=self.pwd_entry.get(),
            database=self.db_entry.get(),
        )
        try:
            cursor = conn.cursor()
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def _fetch_pg(self, table_name):
        import psycopg2
        conn = psycopg2.connect(
            host=self.host_entry.get(),
            port=int(self.port_entry.get()),
            user=self.user_entry.get(),
            password=self.pwd_entry.get(),
            dbname=self.db_entry.get(),
        )
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = %s ORDER BY ordinal_position",
                (table_name,),
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def _fetch_sqlite(self, table_name):
        import sqlite3
        path = self.sqlite_path.get().strip()
        if not path:
            raise ValueError("请选择 SQLite 数据库文件")
        conn = sqlite3.connect(path)
        try:
            cursor = conn.cursor()
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            return [row[1] for row in cursor.fetchall()]
        finally:
            conn.close()

    def _copy_db_result(self):
        self._copy_to_clipboard(self.db_output.get("1.0", "end").strip())

    # ==================== 工具方法 ====================

    @staticmethod
    def _set_text(textbox, text):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)

    def _copy_to_clipboard(self, text):
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
