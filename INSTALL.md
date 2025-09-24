# 懂车帝Model Y车友圈问答区爬虫 - 安装和使用指南

## 环境要求

- Python 3.7+
- Chrome浏览器
- ChromeDriver（会自动下载）

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 安装ChromeDriver（可选）

脚本会自动下载ChromeDriver，但如果需要手动安装：

- 下载与Chrome浏览器版本匹配的ChromeDriver
- 将ChromeDriver放在系统PATH中或项目目录下

### 3. 配置（可选）

编辑 `config.py` 文件来调整爬虫参数：

- `BROWSER_CONFIG`: 浏览器配置
- `DELAY_CONFIG`: 延时配置
- `LIMITS`: 抓取限制
- `OUTPUT_CONFIG`: 输出配置

## 使用方法

### 基本使用

```bash
python scraper.py
```

### 高级使用

可以修改 `scraper.py` 中的参数：

```python
# 修改目标URL
scraper.base_url = "https://www.dongchedi.com/community/4363/wenda"

# 修改延时设置
scraper.min_delay = 1
scraper.max_delay = 3

# 修改最大页数
max_pages = 50
```

## 输出文件

- `output.json`: 主要输出文件，包含所有抓取的帖子和评论
- `scraper.log`: 运行日志
- `scrape_report.json`: 抓取统计报告
- `output_backup_*.json`: 备份文件（每10个帖子自动备份）

## 输出格式

```json
[
  {
    "title": "帖子标题",
    "author": "作者名",
    "publish_time": "2024-01-01 12:00:00",
    "content": "帖子正文内容",
    "comments": [
      {
        "commenter": "评论者名",
        "comment_time": "2024-01-01 12:30:00",
        "comment_content": "评论内容"
      }
    ]
  }
]
```

## 注意事项

1. **遵守网站规则**: 请遵守目标网站的robots.txt和使用条款
2. **合理延时**: 脚本已设置合理延时，避免对服务器造成压力
3. **数据使用**: 抓取的数据仅供学习和研究使用
4. **法律责任**: 使用者需承担相应的法律责任

## 故障排除

### 常见问题

1. **ChromeDriver版本不匹配**
   - 更新Chrome浏览器到最新版本
   - 删除旧的ChromeDriver，让脚本自动下载

2. **页面加载超时**
   - 检查网络连接
   - 增加 `page_load_timeout` 值

3. **找不到元素**
   - 网站可能更新了页面结构
   - 检查并更新CSS选择器

4. **反爬虫检测**
   - 增加延时时间
   - 使用代理IP
   - 更换User-Agent

### 调试模式

设置日志级别为DEBUG：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 技术支持

如遇到问题，请检查：

1. 日志文件 `scraper.log`
2. 网络连接状态
3. Chrome浏览器版本
4. Python依赖包版本

## 免责声明

本工具仅供学习和研究使用。使用者应当遵守相关法律法规和网站使用条款，不得用于商业用途或其他违法行为。开发者不承担因使用本工具而产生的任何法律责任。
