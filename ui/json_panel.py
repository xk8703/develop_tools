"""
JSON 工具面板
实现 JSON 格式化、复制、保存和打开功能
使用树状视图显示 JSON 数据
支持多 Tab 页，每个 Tab 包含完整的输入框+按钮+结果
"""
import customtkinter as ctk
import json
import os
import random
from datetime import datetime
from tkinter import filedialog, ttk
import tkinter as tk


class JSONPanel(ctk.CTkFrame):
    """JSON 工具面板"""

    # 默认保存路径
    SAVE_DIR = r"D:\mytool\json"

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        # 确保保存目录存在
        self.ensure_save_dir()

        # Tab 管理数据
        self.tabs = {}
        self.tab_counter = 0

        # 创建界面
        self.create_ui()

    def ensure_save_dir(self):
        """确保保存目录存在"""
        if not os.path.exists(self.SAVE_DIR):
            try:
                os.makedirs(self.SAVE_DIR, exist_ok=True)
            except Exception as e:
                print(f"创建保存目录失败: {e}")

    def create_ui(self):
        """创建用户界面"""
        # --- 顶部按钮栏（tab 外面，全局） ---
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=10, pady=(10, 2))

        ctk.CTkButton(
            btn_bar, text="格式化", width=80,
            command=self.format_json
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_bar, text="复制结果", width=80,
            command=self.copy_result
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_bar, text="保存", width=60,
            command=self.save_data
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_bar, text="打开", width=60,
            command=self.open_data
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_bar, text="新建", width=60,
            command=self.add_new_tab
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_bar, text="清空", width=60,
            fg_color="gray", hover_color="gray40",
            command=self.clear_all
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_bar, text="关闭", width=60,
            fg_color=("gray65", "gray35"), hover_color=("gray55", "gray45"),
            command=self.close_current_tab
        ).pack(side="right")

        # --- Tab 区域，anchor="w" 让 tab 标题靠左 ---
        self.tabview = ctk.CTkTabview(self, anchor="w")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        # tab 标签字体改小，高亮颜色更醒目
        seg = self.tabview._segmented_button
        seg.configure(
            font=ctk.CTkFont(size=12),
            selected_color=("#3478F6", "#1F6AA5"),
            selected_hover_color=("#2B66D6", "#185D94"),
            unselected_color=("gray78", "gray25"),
            unselected_hover_color=("gray68", "gray30"),
        )

        self.add_new_tab()

    def add_new_tab(self):
        """新建一个 Tab"""
        self.tab_counter += 1
        tab_name = f"JSON {self.tab_counter}"

        tab_frame = self.tabview.add(tab_name)

        # --- 左右分栏，用 grid + 可拖拽分割线 ---
        tab_frame.grid_rowconfigure(0, weight=1)
        tab_frame.grid_columnconfigure(0, weight=0, minsize=300)
        tab_frame.grid_columnconfigure(1, weight=0, minsize=4)
        tab_frame.grid_columnconfigure(2, weight=1)

        # 左侧：输入框
        json_input = ctk.CTkTextbox(tab_frame)
        json_input.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)

        # 中间：可拖拽分割线
        div_color = "#555555" if ctk.get_appearance_mode() == "Dark" else "#AAAAAA"
        divider = tk.Frame(tab_frame, width=4, bg=div_color, cursor="sb_h_double_arrow")
        divider.grid(row=0, column=1, sticky="ns", pady=5)

        def on_divider_drag(event):
            x = event.x_root - tab_frame.winfo_rootx()
            tab_frame.grid_columnconfigure(0, minsize=max(100, x - 2))

        divider.bind("<B1-Motion>", on_divider_drag)

        # 右侧：树状视图
        tree, tree_data = self._create_treeview(tab_frame)

        self.tabs[tab_name] = {
            "json_input": json_input,
            "treeview": tree,
            "tree_data": tree_data,
            "json_data": None,
        }

        self.tabview.set(tab_name)

    def close_tab(self, tab_name):
        """关闭指定 Tab"""
        if tab_name not in self.tabs:
            return

        del self.tabs[tab_name]
        self.tabview.delete(tab_name)

        if not self.tabs:
            self.add_new_tab()
        else:
            # 延迟选中，避免 CTkTabview 内部 _grid_forget_all_tabs 延迟冲突
            last_tab = list(self.tabs.keys())[-1]
            self.after(150, lambda t=last_tab: self.tabview.set(t))

    def close_current_tab(self):
        """关闭当前 Tab"""
        if len(self.tabs) <= 1:
            return
        name = self._get_current_tab_name()
        if name:
            self.close_tab(name)

    def _create_treeview(self, parent):
        """创建树状视图，grid 放到 column=2"""
        bg_color = "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#ececec"
        tree_container = tk.Frame(parent, bg=bg_color)
        tree_container.grid(row=0, column=2, sticky="nsew", padx=(0, 5), pady=5)

        style = ttk.Style()
        style.configure("JsonTree.Treeview",
                        font=("Microsoft YaHei UI", 12),
                        rowheight=28)
        style.configure("JsonTree.Treeview.Heading",
                        font=("Microsoft YaHei UI", 12, "bold"))

        tree = ttk.Treeview(
            tree_container,
            columns=("value",),
            show="tree headings",
            selectmode="browse",
            style="JsonTree.Treeview"
        )

        tree.heading("#0", text="键", anchor="w")
        tree.heading("value", text="值", anchor="w")
        tree.column("#0", width=200, minwidth=100)
        tree.column("value", width=400, minwidth=200)

        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        tree_data = {}

        tree.bind("<Button-3>", lambda e, t=tree, td=tree_data: self.show_context_menu(e, t, td))
        tree.bind("<Button-2>", lambda e, t=tree, td=tree_data: self.show_context_menu(e, t, td))
        tree.bind("<Double-Button-1>", lambda e, t=tree: self.toggle_item(e, t))

        return tree, tree_data

    def _get_current_tab_name(self):
        """获取当前活跃 tab 的名称"""
        current = self.tabview.get()
        if current and current in self.tabs:
            return current
        if self.tabs:
            first_name = next(iter(self.tabs))
            self.tabview.set(first_name)
            return first_name
        return None

    def _ensure_tab(self):
        """确保至少有一个 tab，返回当前 tab_name"""
        if not self.tabs:
            self.add_new_tab()
        return self._get_current_tab_name()

    def toggle_item(self, event, tree):
        """切换节点的展开/折叠状态"""
        item = tree.selection()
        if item:
            item = item[0]
            if tree.parent(item):
                if tree.item(item, "open"):
                    tree.item(item, open=False)
                else:
                    tree.item(item, open=True)

    def show_context_menu(self, event, tree, tree_data):
        """显示右键菜单"""
        item = tree.identify_row(event.y)

        if item:
            tree.selection_set(item)

            node_data = tree_data.get(item, {})
            key = node_data.get("key", "")
            value = node_data.get("value", "")
            value_type = node_data.get("type", "")

            context_menu = tk.Menu(tree, tearoff=0)

            context_menu.add_command(
                label="复制值",
                command=lambda: self.copy_to_clipboard(str(value))
            )

            context_menu.add_command(
                label="复制 KEY",
                command=lambda: self.copy_to_clipboard(str(key))
            )

            if value_type in ["string", "number", "boolean", "null"]:
                kv_pair = f'"{key}": {json.dumps(value)}'
                context_menu.add_command(
                    label="复制键值对",
                    command=lambda: self.copy_to_clipboard(kv_pair)
                )

            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

    def format_json(self):
        """格式化 JSON 并显示在当前 tab 的树状视图中"""
        tab_name = self._ensure_tab()
        if tab_name is None or tab_name not in self.tabs:
            return

        tab_info = self.tabs[tab_name]
        json_input = tab_info["json_input"]
        json_str = json_input.get("1.0", "end").strip()

        if not json_str:
            self.show_error(tab_name, "请输入 JSON 字符串")
            return

        try:
            data = json.loads(json_str)

            tree = tab_info["treeview"]
            tree_data = tab_info["tree_data"]

            for item in tree.get_children():
                tree.delete(item)
            tree_data.clear()

            tab_info["json_data"] = data

            if isinstance(data, dict):
                self.fill_dict(data, "", tree, tree_data)
            elif isinstance(data, list):
                self.fill_list(data, "", tree, tree_data)
            else:
                tree.insert("", "end", text="root", values=(str(data),))

        except json.JSONDecodeError as e:
            self.show_error(tab_name, f"JSON 格式错误:\n{str(e)}\n\n请检查:\n1. 括号是否配对\n2. 键名是否使用双引号\n3. 字符串是否使用双引号\n4. 是否有尾随逗号")
        except Exception as e:
            self.show_error(tab_name, f"错误: {str(e)}")

    def fill_dict(self, data, parent, tree, tree_data):
        """填充字典到树状视图"""
        for key, value in data.items():
            node_id = tree.insert(parent, "end", text=str(key))

            value_type = self.get_value_type(value)
            tree_data[node_id] = {
                "key": key,
                "value": value,
                "type": value_type
            }

            if isinstance(value, dict):
                tree.set(node_id, "value", f"{{{len(value)} 项}}")
                self.fill_dict(value, node_id, tree, tree_data)
            elif isinstance(value, list):
                tree.set(node_id, "value", f"[{len(value)} 项]")
                self.fill_list(value, node_id, tree, tree_data)
            else:
                tree.set(node_id, "value", self.format_value(value))

    def fill_list(self, data, parent, tree, tree_data):
        """填充列表到树状视图"""
        for index, value in enumerate(data):
            node_id = tree.insert(parent, "end", text=f"[{index}]")

            value_type = self.get_value_type(value)
            tree_data[node_id] = {
                "key": index,
                "value": value,
                "type": value_type
            }

            if isinstance(value, dict):
                tree.set(node_id, "value", f"{{{len(value)} 项}}")
                self.fill_dict(value, node_id, tree, tree_data)
            elif isinstance(value, list):
                tree.set(node_id, "value", f"[{len(value)} 项]")
                self.fill_list(value, node_id, tree, tree_data)
            else:
                tree.set(node_id, "value", self.format_value(value))

    def get_value_type(self, value):
        """获取值类型"""
        if isinstance(value, dict):
            return "dict"
        elif isinstance(value, list):
            return "list"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, (int, float)):
            return "number"
        elif value is None:
            return "null"
        else:
            return "unknown"

    def format_value(self, value):
        """格式化值用于显示"""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif value is None:
            return "null"
        else:
            return str(value)

    def copy_result(self):
        """复制当前 tab 的格式化结果"""
        tab_name = self._get_current_tab_name()
        if tab_name is None or tab_name not in self.tabs:
            return

        tab_info = self.tabs[tab_name]
        if tab_info["json_data"] is None:
            return

        try:
            formatted = json.dumps(
                tab_info["json_data"],
                indent=2,
                ensure_ascii=False,
                sort_keys=False
            )
            self.copy_to_clipboard(formatted)
            print("结果已复制到剪贴板")
        except Exception as e:
            print(f"复制失败: {e}")

    def save_data(self):
        """保存当前 tab 的数据到文件"""
        tab_name = self._get_current_tab_name()
        if tab_name is None or tab_name not in self.tabs:
            return

        tab_info = self.tabs[tab_name]
        if tab_info["json_data"] is None:
            self.show_error(tab_name, "请先格式化 JSON 数据后再保存")
            return

        try:
            formatted = json.dumps(
                tab_info["json_data"],
                indent=2,
                ensure_ascii=False,
                sort_keys=False
            )
        except Exception as e:
            self.show_error(tab_name, f"格式化失败: {str(e)}")
            return

        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S")
        random_suffix = random.randint(100, 999)
        default_name = f"{timestamp}_{random_suffix}.json"

        try:
            file_path = filedialog.asksaveasfilename(
                initialdir=self.SAVE_DIR,
                defaultextension=".json",
                filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
                initialfile=default_name,
                title="保存 JSON 文件",
                parent=self.winfo_toplevel()
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(formatted)
                print(f"文件已保存到: {file_path}")

        except Exception as e:
            self.show_error(tab_name, f"保存失败: {str(e)}")

    def open_data(self):
        """打开已保存的数据"""
        tab_name = self._ensure_tab()
        if tab_name is None or tab_name not in self.tabs:
            return

        try:
            file_path = filedialog.askopenfilename(
                initialdir=self.SAVE_DIR,
                filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
                title="打开 JSON 文件",
                parent=self.winfo_toplevel()
            )

            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                json_input = self.tabs[tab_name]["json_input"]
                json_input.delete("1.0", "end")
                json_input.insert("1.0", content)

                self.format_json()

        except Exception as e:
            self.show_error(tab_name, f"打开失败: {str(e)}")

    def clear_all(self):
        """清空当前 tab 的输入框和树状视图"""
        tab_name = self._get_current_tab_name()
        if tab_name is None or tab_name not in self.tabs:
            return

        tab_info = self.tabs[tab_name]
        tab_info["json_input"].delete("1.0", "end")
        tab_info["json_data"] = None

        tree = tab_info["treeview"]
        tree_data = tab_info["tree_data"]
        for item in tree.get_children():
            tree.delete(item)
        tree_data.clear()

    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
        except Exception as e:
            print(f"复制失败: {e}")

    def show_error(self, tab_name, message):
        """在指定 tab 的输入框中显示错误消息"""
        if tab_name in self.tabs:
            json_input = self.tabs[tab_name]["json_input"]
            json_input.delete("1.0", "end")
            json_input.insert("1.0", f"/*\n错误:\n{message}\n*/")
