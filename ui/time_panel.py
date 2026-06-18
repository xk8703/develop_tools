"""
时间工具面板
实现时间戳格式化和时间转时间戳功能
"""
import customtkinter as ctk
from datetime import datetime
import calendar


class TimePanel(ctk.CTkFrame):
    """时间工具面板"""

    def __init__(self, master):
        super().__init__(master)

        self.pack(fill="both", expand=True)

        # 创建选项卡视图
        self.tabview = ctk.CTkTabview(self, width=600, height=500)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # 创建两个选项卡
        self.tab_timestamp = self.tabview.add("时间戳格式化")
        self.tab_datetime = self.tabview.add("时间转时间戳")

        # 初始化各个选项卡的内容
        self.create_timestamp_tab()
        self.create_datetime_tab()

    def create_timestamp_tab(self):
        """创建时间戳格式化选项卡"""
        frame = ctk.CTkFrame(self.tab_timestamp)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 标题
        title = ctk.CTkLabel(
            frame,
            text="时间戳格式化",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 20))

        # 时间戳输入
        input_frame = ctk.CTkFrame(frame)
        input_frame.pack(fill="x", pady=(0, 15))

        input_label = ctk.CTkLabel(input_frame, text="时间戳:", width=100, anchor="w")
        input_label.pack(side="left", padx=(10, 5))

        self.timestamp_entry = ctk.CTkEntry(input_frame, placeholder_text="请输入时间戳（秒或毫秒）")
        self.timestamp_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # 格式选择
        format_frame = ctk.CTkFrame(frame)
        format_frame.pack(fill="x", pady=(0, 15))

        format_label = ctk.CTkLabel(format_frame, text="输出格式:", width=100, anchor="w")
        format_label.pack(side="left", padx=(10, 5))

        self.format_var = ctk.StringVar(value="YYYY-MM-DD HH:mm:ss")
        format_options = [
            "YYYYMMDD",
            "YYYY/MM/DD",
            "YYYY-MM-DD",
            "YYYY-MM-DD HH:mm:ss",
            "YYYY-MM-DD HH:mm:ss:SSS"
        ]
        format_menu = ctk.CTkOptionMenu(
            format_frame,
            values=format_options,
            variable=self.format_var,
            width=250
        )
        format_menu.pack(side="left", padx=(0, 10))

        # 转换按钮
        convert_btn = ctk.CTkButton(
            format_frame,
            text="转换",
            command=self.convert_timestamp,
            width=100
        )
        convert_btn.pack(side="left")

        # 结果显示
        result_frame = ctk.CTkFrame(frame)
        result_frame.pack(fill="both", expand=True, pady=(15, 0))

        result_label = ctk.CTkLabel(result_frame, text="转换结果:", width=100, anchor="w")
        result_label.pack(side="top", fill="x", padx=(10, 5), pady=(10, 5))

        self.timestamp_result = ctk.CTkTextbox(result_frame, height=100)
        self.timestamp_result.pack(fill="both", expand=True, padx=(10, 10), pady=(0, 10))
        self.timestamp_result.insert("1.0", "等待转换...")
        self.timestamp_result.configure(state="disabled")

    def create_datetime_tab(self):
        """创建时间转时间戳选项卡"""
        frame = ctk.CTkFrame(self.tab_datetime)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 标题
        title = ctk.CTkLabel(
            frame,
            text="时间转时间戳",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 20))

        # 获取当前日期时间作为默认值
        now = datetime.now()

        # 日期选择区域
        date_frame = ctk.CTkFrame(frame)
        date_frame.pack(fill="x", pady=(0, 15))

        date_label = ctk.CTkLabel(date_frame, text="日期:", width=100, anchor="w")
        date_label.pack(side="left", padx=(10, 5))

        # 创建日期选择器容器
        date_selector_container = ctk.CTkFrame(date_frame)
        date_selector_container.pack(side="left", fill="x", expand=True)

        # 年份选择
        self.year_var = ctk.StringVar(value=str(now.year))
        years = [str(y) for y in range(now.year - 50, now.year + 51)]
        year_label = ctk.CTkLabel(date_selector_container, text="年")
        year_label.pack(side="left", padx=(0, 5))

        self.year_combo = ctk.CTkComboBox(
            date_selector_container,
            values=years,
            variable=self.year_var,
            width=100,
            command=self.update_date_display
        )
        self.year_combo.pack(side="left", padx=(0, 10))

        # 月份选择
        self.month_var = ctk.StringVar(value=f"{now.month:02d}")
        months = [f"{m:02d}" for m in range(1, 13)]
        month_label = ctk.CTkLabel(date_selector_container, text="月")
        month_label.pack(side="left", padx=(0, 5))

        self.month_combo = ctk.CTkComboBox(
            date_selector_container,
            values=months,
            variable=self.month_var,
            width=80,
            command=self.update_date_display
        )
        self.month_combo.pack(side="left", padx=(0, 10))

        # 日期选择
        self.day_var = ctk.StringVar(value=f"{now.day:02d}")
        days = [f"{d:02d}" for d in range(1, 32)]
        day_label = ctk.CTkLabel(date_selector_container, text="日")
        day_label.pack(side="left", padx=(0, 5))

        self.day_combo = ctk.CTkComboBox(
            date_selector_container,
            values=days,
            variable=self.day_var,
            width=80,
            command=self.update_date_display
        )
        self.day_combo.pack(side="left", padx=(0, 10))

        # 日期显示标签
        self.date_display = ctk.CTkLabel(
            date_selector_container,
            text=now.strftime("%Y-%m-%d"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.date_display.pack(side="left", padx=10)

        # 时间选择区域
        time_frame = ctk.CTkFrame(frame)
        time_frame.pack(fill="x", pady=(0, 15))

        time_label = ctk.CTkLabel(time_frame, text="时间:", width=100, anchor="w")
        time_label.pack(side="left", padx=(10, 5))

        # 创建时间选择器容器
        time_selector_container = ctk.CTkFrame(time_frame)
        time_selector_container.pack(side="left", fill="x", expand=True)

        # 小时选择
        self.hour_var = ctk.StringVar(value=f"{now.hour:02d}")
        hours = [f"{h:02d}" for h in range(24)]
        hour_label = ctk.CTkLabel(time_selector_container, text="时")
        hour_label.pack(side="left", padx=(0, 5))

        self.hour_combo = ctk.CTkComboBox(
            time_selector_container,
            values=hours,
            variable=self.hour_var,
            width=80,
            command=self.update_time_display
        )
        self.hour_combo.pack(side="left", padx=(0, 10))

        # 分钟选择
        self.minute_var = ctk.StringVar(value=f"{now.minute:02d}")
        minutes = [f"{m:02d}" for m in range(60)]
        minute_label = ctk.CTkLabel(time_selector_container, text="分")
        minute_label.pack(side="left", padx=(0, 5))

        self.minute_combo = ctk.CTkComboBox(
            time_selector_container,
            values=minutes,
            variable=self.minute_var,
            width=80,
            command=self.update_time_display
        )
        self.minute_combo.pack(side="left", padx=(0, 10))

        # 秒选择
        self.second_var = ctk.StringVar(value=f"{now.second:02d}")
        seconds = [f"{s:02d}" for s in range(60)]
        second_label = ctk.CTkLabel(time_selector_container, text="秒")
        second_label.pack(side="left", padx=(0, 5))

        self.second_combo = ctk.CTkComboBox(
            time_selector_container,
            values=seconds,
            variable=self.second_var,
            width=80,
            command=self.update_time_display
        )
        self.second_combo.pack(side="left", padx=(0, 10))

        # 时间显示标签
        self.time_display = ctk.CTkLabel(
            time_selector_container,
            text=f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.time_display.pack(side="left", padx=10)

        # 转换按钮
        convert_btn = ctk.CTkButton(
            time_frame,
            text="转换",
            command=self.convert_datetime,
            width=100
        )
        convert_btn.pack(side="left")

        # 结果显示
        result_frame = ctk.CTkFrame(frame)
        result_frame.pack(fill="both", expand=True, pady=(15, 0))

        result_label = ctk.CTkLabel(result_frame, text="时间戳结果:", width=100, anchor="w")
        result_label.pack(side="top", fill="x", padx=(10, 5), pady=(10, 5))

        self.datetime_result = ctk.CTkTextbox(result_frame, height=100)
        self.datetime_result.pack(fill="both", expand=True, padx=(10, 10), pady=(0, 10))
        self.datetime_result.insert("1.0", "等待转换...")
        self.datetime_result.configure(state="disabled")

        # 初始化显示
        self.update_date_display()
        self.update_time_display()

    def convert_timestamp(self):
        """转换时间戳为日期时间"""
        timestamp_str = self.timestamp_entry.get().strip()

        if not timestamp_str:
            self.show_result(self.timestamp_result, "请输入时间戳")
            return

        try:
            # 尝试解析时间戳
            timestamp = float(timestamp_str)

            # 判断是秒还是毫秒（毫秒时间戳通常大于 10 位）
            if timestamp > 9999999999:
                timestamp = timestamp / 1000

            # 转换为 datetime 对象
            dt = datetime.fromtimestamp(timestamp)

            # 根据选择的格式格式化输出
            format_str = self.format_var.get()
            result = self.format_datetime(dt, format_str)

            self.show_result(
                self.timestamp_result,
                f"原始时间戳: {timestamp_str}\n\n转换结果:\n{result}\n\n时间戳（秒）: {int(timestamp)}\n时间戳（毫秒）: {int(timestamp * 1000)}"
            )

        except ValueError:
            self.show_result(self.timestamp_result, "错误: 请输入有效的数字格式时间戳")
        except (OSError, OverflowError) as e:
            self.show_result(self.timestamp_result, f"错误: 时间戳超出有效范围")

    def update_date_display(self, choice=None):
        """更新日期显示"""
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())

            # 根据选择的月份更新天数
            days_in_month = calendar.monthrange(year, month)[1]
            days = [f"{d:02d}" for d in range(1, days_in_month + 1)]

            # 更新天数下拉框
            current_day = self.day_var.get()
            self.day_combo.configure(values=days)

            # 如果当前日期超过该月最大天数，调整为最后一天
            if int(current_day) > days_in_month:
                self.day_var.set(f"{days_in_month:02d}")

            # 重新获取日期值以应用可能的调整
            day = int(self.day_var.get())

            # 更新日期显示
            self.date_display.configure(text=f"{year}-{month:02d}-{day:02d}")
        except (ValueError, AttributeError):
            pass

    def update_time_display(self, choice=None):
        """更新时间显示"""
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            second = int(self.second_var.get())
            self.time_display.configure(text=f"{hour:02d}:{minute:02d}:{second:02d}")
        except (ValueError, AttributeError):
            pass

    def convert_datetime(self):
        """转换日期时间为时间戳"""
        try:
            # 从下拉框获取日期
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())

            # 从下拉框获取时间
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            second = int(self.second_var.get())

            # 创建 datetime 对象
            dt = datetime(year, month, day, hour, minute, second)

            # 转换为时间戳
            timestamp_seconds = int(dt.timestamp())
            timestamp_milliseconds = timestamp_seconds * 1000

            result_text = (
                f"选择时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"时间戳（秒）: {timestamp_seconds}\n"
                f"时间戳（毫秒）: {timestamp_milliseconds}"
            )

            self.show_result(self.datetime_result, result_text)

        except ValueError as e:
            self.show_result(self.datetime_result, f"错误: 日期或时间选择不正确\n\n{str(e)}")
        except Exception as e:
            self.show_result(self.datetime_result, f"错误: {str(e)}")

    def format_datetime(self, dt, format_str):
        """根据格式字符串格式化日期时间"""
        if format_str == "YYYYMMDD":
            return dt.strftime("%Y%m%d")
        elif format_str == "YYYY/MM/DD":
            return dt.strftime("%Y/%m/%d")
        elif format_str == "YYYY-MM-DD":
            return dt.strftime("%Y-%m-%d")
        elif format_str == "YYYY-MM-DD HH:mm:ss":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format_str == "YYYY-MM-DD HH:mm:ss:SSS":
            # 添加毫秒
            milliseconds = dt.microsecond // 1000
            return dt.strftime("%Y-%m-%d %H:%M:%S") + f":{milliseconds:03d}"
        else:
            return str(dt)

    def show_result(self, textbox, text):
        """在文本框中显示结果"""
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)
        textbox.configure(state="disabled")
