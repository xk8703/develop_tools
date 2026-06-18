# 多功能工具箱

一个基于 Python 和 CustomTkinter 开发的多功能工具集合。

## 功能特性

### 已实现功能
- **时间工具**
  - 时间戳格式化：将时间戳转换为多种日期格式
    - YYYYMMDD
    - YYYY/MM/DD
    - YYYY-MM-DD
    - YYYY-MM-DD HH:mm:ss
    - YYYY-MM-DD HH:mm:ss:SSS
  - 时间转时间戳：将日期时间转换为时间戳（秒/毫秒）
    - 日期选择器：日历选择
    - 时间选择器：时/分/秒下拉选择

- **JSON 工具**
  - JSON 格式化：美化 JSON 输出
  - 复制结果：一键复制格式化后的 JSON
  - 保存数据：保存为 .json 文件到 `D:\mytool\json`
  - 打开已存数据：从文件加载 JSON
  - 右键菜单：
    - 复制值
    - 复制 KEY
    - 复制键值对

### 待实现功能
- 字段格式化
- SQL 工具

## 安装

1. 克隆或下载本项目

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 运行

### Windows
双击 `run.bat` 文件

### Linux/Mac
```bash
bash run.sh
```

### 或直接运行 Python
```bash
python main.py
```

## 技术栈

- Python 3.14
- CustomTkinter 5.2.0+

## 界面预览

- 左侧菜单：快速切换不同工具
- 右侧内容区：显示当前工具的功能界面
- 支持深色/浅色主题切换

## 开发计划

- [x] 基础界面框架
- [x] 时间工具（时间戳格式化）
- [x] 时间工具（时间转时间戳）
- [x] JSON 工具（格式化、复制、保存、打开）
- [ ] 字段格式化工具
- [ ] SQL 工具

## 许可证

MIT License
