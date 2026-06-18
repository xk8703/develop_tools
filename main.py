"""
多功能工具箱 - 主程序入口
"""
import customtkinter as ctk


class MyApp(ctk.CTk):
    """主应用类"""

    def __init__(self):
        super().__init__()

        # 窗口配置
        self.title("多功能工具箱")
        self.geometry("1000x600")

        # 设置外观模式和主题颜色
        ctk.set_appearance_mode("dark")  # 模式: "System" (标准), "dark", "light"
        ctk.set_default_color_theme("blue")  # 主题: "blue" (标准), "green", "dark-blue"

        # 创建主框架
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 创建左侧菜单
        self.create_sidebar()

        # 创建右侧内容区
        self.create_content_area()

    def create_sidebar(self):
        """创建左侧菜单"""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)  # 添加弹性空间

        # 标题
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="工具箱",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # 菜单按钮
        self.create_sidebar_button("时间工具", 1, "time")
        self.create_sidebar_button("JSON工具", 2, "json")
        self.create_sidebar_button("字段格式化", 3, "format")
        self.create_sidebar_button("SQL工具", 4, "sql")

        # 外观模式切换按钮
        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event
        )
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=20)

    def create_sidebar_button(self, text, row, tool_type):
        """创建侧边栏按钮"""
        btn = ctk.CTkButton(
            self.sidebar,
            text=text,
            fg_color=("gray78", "gray28"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=lambda: self.select_tool(tool_type)
        )
        btn.grid(row=row, column=0, sticky="ew", padx=20, pady=10)
        return btn

    def create_content_area(self):
        """创建右侧内容区"""
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # 默认显示时间工具
        self.show_time_tool()

    def select_tool(self, tool_type):
        """选择工具"""
        # 清除当前内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # 根据类型显示对应工具
        if tool_type == "time":
            self.show_time_tool()
        elif tool_type == "json":
            self.show_json_tool()
        elif tool_type == "format":
            self.show_format_tool()
        elif tool_type == "sql":
            self.show_sql_tool()

    def show_time_tool(self):
        """显示时间工具"""
        from ui.time_panel import TimePanel
        time_panel = TimePanel(self.content_frame)
        time_panel.pack(fill="both", expand=True)

    def show_json_tool(self):
        """显示 JSON 工具"""
        from ui.json_panel import JSONPanel
        json_panel = JSONPanel(self.content_frame)
        json_panel.pack(fill="both", expand=True)

    def show_format_tool(self):
        """显示字段格式化工具"""
        from ui.field_format_panel import FieldFormatPanel
        format_panel = FieldFormatPanel(self.content_frame)
        format_panel.pack(fill="both", expand=True)

    def show_sql_tool(self):
        """显示 SQL 工具"""
        from ui.sql_panel import SQLPanel
        sql_panel = SQLPanel(self.content_frame)
        sql_panel.pack(fill="both", expand=True)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        """切换外观模式"""
        ctk.set_appearance_mode(new_appearance_mode.lower())


if __name__ == "__main__":
    app = MyApp()
    app.mainloop()
