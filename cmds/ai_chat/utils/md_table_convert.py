import markdown
from bs4 import BeautifulSoup
from urllib.parse import quote
import asyncio
from pathlib import Path
import base64

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# 假設字體檔名 (請根據您下載的檔案名稱修改)
font_file_path = Path('./assets/fonts/Iansui-Regular.ttf')
with open(font_file_path, "rb") as f:
    font_base64 = base64.b64encode(f.read()).decode("utf-8")

css_style = f"""
<style>
    @font-face {{
        font-family: 'Iansui';
        src: url(data:font/ttf;base64,{font_base64}) format('truetype');
        font-display: swap; 
    }}
    body {{ 
        font-family: 'Iansui', 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
        padding: 30px; 
        background-color: #f8f8f8;
    }}
    .table-container {{
        padding: 20px;
        background-color: white;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        border-radius: 12px;
        max-width: 1200px;
        margin: 0 auto;
    }}
    .table-title {{
        margin-top: 30px;
        margin-bottom: 10px;
        color: #34495e;
        border-bottom: 2px solid #3498db;
        padding-bottom: 5px;
    }}
    .styled-markdown-table {{ 
        border-collapse: collapse; 
        width: 100%;
        min-width: 800px;
        margin: 20px 0; 
        font-size: 14pt; 
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05); 
        border-radius: 8px;
        overflow: hidden; 
    }}
    .spacer {{ height: 40px; }}
    /* ... 其他表格樣式保持不變 ... */
    .styled-markdown-table thead tr {{ background-color: #2c3e50; color: #ffffff; text-align: center; font-weight: bold; }}
    .styled-markdown-table th, .styled-markdown-table td {{ padding: 15px 20px; border: 1px solid #e0e0e0; vertical-align: top; line-height: 1.5; text-align: left; }}
    .styled-markdown-table tbody tr:nth-of-type(even) {{ background-color: #fcfcfc; }}
    .styled-markdown-table tbody tr:hover {{ background-color: #e8f0fe; transition: background-color 0.3s ease; }}
</style>
"""

FULL_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>Multiple Tables Screenshot</title>
    {css_style}
</head>
<body>
    <div class="table-container">
        {html_content}
    </div>
</body>
</html>
"""

def _get_png(full_html: str) -> bytes:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("data:text/html;charset=utf-8," + quote(full_html))
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.styled-markdown-table"))
        )
        driver.execute_script("document.body.style.overflow = 'hidden';")
        table = driver.find_element(By.CSS_SELECTOR, "table.styled-markdown-table")
        box = table.rect
        driver.set_window_size(box["width"]+100, box["height"]+290)
        png_bytes = driver.get_screenshot_as_png()
    finally:
        driver.quit()

    return png_bytes

async def md_table_convert(text: str) -> bytes | None:
    # get full html
    html = markdown.markdown(text, extensions=["tables"])
    if not html: return

    # find tables
    soup = BeautifulSoup(html, "html.parser")
    found_table = False
    for table in soup.find_all("table"):
        table["class"] = table.get("class", []) + ["styled-markdown-table"]
        found_table = True
    if not found_table: return

    html_content = str(soup)
    if not html_content: return
    full_html = FULL_HTML_TEMPLATE.format(css_style=css_style, html_content=html_content)

    # open selenium
    return await asyncio.to_thread(_get_png, full_html)