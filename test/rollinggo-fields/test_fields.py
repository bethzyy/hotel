"""
RollingGo 酒店字段测试程序
查询指定酒店并将所有返回字段以 HTML 格式展示
"""
import os
import sys
import json
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))

from app.services.rollinggo import RollingGoService


def is_image_url(url: str) -> bool:
    """检查 URL 是否为图片链接"""
    if not url or not isinstance(url, str):
        return False
    url_lower = url.lower()
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
    return any(ext in url_lower for ext in image_extensions)


def is_url(url: str) -> bool:
    """检查字符串是否为 URL"""
    if not url or not isinstance(url, str):
        return False
    return url.startswith('http://') or url.startswith('https://')


def escape_html(text: str) -> str:
    """转义 HTML 特殊字符"""
    if not isinstance(text, str):
        text = str(text)
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def render_value_to_html(key: str, value, indent: int = 0) -> str:
    """
    递归渲染值为 HTML

    Args:
        key: 字段名
        value: 字段值
        indent: 缩进级别

    Returns:
        HTML 字符串
    """
    indent_style = f"margin-left: {indent * 20}px;"

    if value is None:
        return f'<div class="field" style="{indent_style}"><span class="key">{escape_html(key)}:</span> <span class="null">null</span></div>'

    elif isinstance(value, bool):
        bool_class = "true" if value else "false"
        return f'<div class="field" style="{indent_style}"><span class="key">{escape_html(key)}:</span> <span class="bool {bool_class}">{value}</span></div>'

    elif isinstance(value, (int, float)):
        return f'<div class="field" style="{indent_style}"><span class="key">{escape_html(key)}:</span> <span class="number">{value}</span></div>'

    elif isinstance(value, str):
        # 检查是否为图片 URL
        if is_image_url(value):
            return f'''<div class="field" style="{indent_style}">
                <span class="key">{escape_html(key)}:</span>
                <a href="{escape_html(value)}" target="_blank" class="url">{escape_html(value)}</a>
                <br><img src="{escape_html(value)}" style="max-width: 300px; max-height: 200px; border: 1px solid #ccc; margin-top: 5px;">
            </div>'''
        # 检查是否为普通 URL
        elif is_url(value):
            return f'<div class="field" style="{indent_style}"><span class="key">{escape_html(key)}:</span> <a href="{escape_html(value)}" target="_blank" class="url">{escape_html(value)}</a></div>'
        else:
            return f'<div class="field" style="{indent_style}"><span class="key">{escape_html(key)}:</span> <span class="string">"{escape_html(value)}"</span></div>'

    elif isinstance(value, list):
        if len(value) == 0:
            return f'<div class="field" style="{indent_style}"><span class="key">{escape_html(key)}:</span> <span class="empty-list">[]</span></div>'

        # 检查是否为简单列表（所有元素都是基本类型）
        if all(isinstance(v, (str, int, float, bool, type(None))) for v in value):
            items = ', '.join(f'"{escape_html(str(v))}"' if isinstance(v, str) else str(v) for v in value)
            return f'<div class="field" style="{indent_style}"><span class="key">{escape_html(key)}:</span> <span class="array">[{items}]</span></div>'

        # 复杂列表，递归渲染
        html_parts = [f'<div class="field" style="{indent_style}"><span class="key">{escape_html(key)}:</span> <span class="array">[</span></div>']
        for i, item in enumerate(value):
            html_parts.append(render_value_to_html(f"[{i}]", item, indent + 1))
        html_parts.append(f'<div class="field" style="{indent_style}"><span class="array">]</span></div>')
        return '\n'.join(html_parts)

    elif isinstance(value, dict):
        if len(value) == 0:
            return f'<div class="field" style="{indent_style}"><span class="key">{escape_html(key)}:</span> <span class="empty-object">{{"}}"</span></div>'

        html_parts = [f'<div class="field" style="{indent_style}"><span class="key">{escape_html(key)}:</span> <span class="object">{{" "</span></div>']
        for k, v in value.items():
            html_parts.append(render_value_to_html(k, v, indent + 1))
        html_parts.append(f'<div class="field" style="{indent_style}"><span class="object">"}}"</span></div>')
        return '\n'.join(html_parts)

    else:
        return f'<div class="field" style="{indent_style}"><span class="key">{escape_html(key)}:</span> <span class="unknown">{escape_html(str(value))}</span></div>'


def generate_html_report(hotel_name: str, search_result: dict, detail_result: dict) -> str:
    """
    生成 HTML 报告

    Args:
        hotel_name: 酒店名称
        search_result: 搜索结果
        detail_result: 详情结果

    Returns:
        HTML 字符串
    """
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RollingGo 酒店字段测试 - {escape_html(hotel_name)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            margin-bottom: 15px;
            padding: 10px;
            background: #f0f0f0;
            border-left: 4px solid #4CAF50;
        }}
        .meta {{
            color: #888;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .field {{
            padding: 5px 0;
            border-bottom: 1px dotted #eee;
        }}
        .key {{
            color: #0066cc;
            font-weight: 600;
        }}
        .string {{
            color: #28a745;
        }}
        .number {{
            color: #d63384;
        }}
        .bool.true {{
            color: #28a745;
            font-weight: bold;
        }}
        .bool.false {{
            color: #dc3545;
        }}
        .null {{
            color: #888;
            font-style: italic;
        }}
        .url {{
            color: #0066cc;
            text-decoration: none;
        }}
        .url:hover {{
            text-decoration: underline;
        }}
        .array, .object {{
            color: #888;
        }}
        .empty-list, .empty-object {{
            color: #aaa;
            font-style: italic;
        }}
        .unknown {{
            color: #666;
            font-style: italic;
        }}
        img {{
            border-radius: 4px;
            display: block;
        }}
        .raw-json {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: "Fira Code", Consolas, monospace;
            font-size: 12px;
            white-space: pre-wrap;
            word-break: break-all;
        }}
        .toggle-btn {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 10px;
        }}
        .toggle-btn:hover {{
            background: #45a049;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏨 RollingGo 酒店字段测试</h1>
        <p class="meta">查询酒店: <strong>{escape_html(hotel_name)}</strong> | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>📋 搜索结果字段</h2>
        <div class="section">
            {render_dict_to_html(search_result)}
        </div>

        <h2>📄 详情结果字段</h2>
        <div class="section">
            {render_dict_to_html(detail_result)}
        </div>

        <h2>📝 原始 JSON 数据</h2>
        <button class="toggle-btn" onclick="toggleJson()">显示/隐藏原始 JSON</button>
        <div id="raw-json" class="raw-json" style="display: none;">
<strong>// 搜索结果:</strong>
{escape_html(json.dumps(search_result, ensure_ascii=False, indent=2))}

<strong>// 详情结果:</strong>
{escape_html(json.dumps(detail_result, ensure_ascii=False, indent=2))}
        </div>
    </div>

    <script>
        function toggleJson() {{
            const el = document.getElementById('raw-json');
            el.style.display = el.style.display === 'none' ? 'block' : 'none';
        }}
    </script>
</body>
</html>'''
    return html


def render_dict_to_html(data: dict) -> str:
    """渲染字典为 HTML"""
    if not data:
        return '<p class="null">无数据</p>'

    html_parts = []
    for key, value in data.items():
        html_parts.append(render_value_to_html(key, value))
    return '\n'.join(html_parts)


def main():
    """主函数"""
    # 配置
    hotel_query = "杭州武林万怡酒店"
    place = "杭州"
    place_type = "城市"

    # 计算日期（明天入住，住1晚）
    today = datetime.now()
    check_in = (today + timedelta(days=1)).strftime('%Y-%m-%d')
    check_out = (today + timedelta(days=2)).strftime('%Y-%m-%d')

    print(f"[Search] Query: {hotel_query}")
    print(f"[Date] Check-in: {check_in} - Check-out: {check_out}")
    print(f"[Config] API Key: {'OK' if os.environ.get('AIGOHOTEL_API_KEY') else 'NOT SET'}")
    print()

    # 初始化服务
    api_key = os.environ.get('AIGOHOTEL_API_KEY')
    if not api_key:
        print("[Error] AIGOHOTEL_API_KEY not found in environment")
        print("Please configure AIGOHOTEL_API_KEY in .env file")
        sys.exit(1)

    service = RollingGoService(api_key=api_key)

    # 1. 搜索酒店
    print("[API] Calling search API...")
    try:
        search_result = service.search_hotels(
            query=hotel_query,
            place=place,
            place_type=place_type,
            check_in_date=check_in,
            stay_nights=1,
            adult_count=2,
            size=5
        )
        print(f"[OK] Search completed, found {len(search_result.get('hotels', []))} hotels")
    except Exception as e:
        print(f"[Error] Search failed: {e}")
        search_result = {"error": str(e)}

    # 获取第一个酒店的 ID
    hotel_id = None
    if search_result and 'hotels' in search_result and len(search_result['hotels']) > 0:
        hotel_id = search_result['hotels'][0].get('hotelId') or search_result['hotels'][0].get('hotel_id')
        print(f"[Hotel] Found hotel ID: {hotel_id}")

    # 2. 获取酒店详情
    detail_result = {}
    if hotel_id:
        print("[API] Calling detail API...")
        try:
            detail_result = service.get_hotel_detail(
                hotel_id=hotel_id,
                check_in_date=check_in,
                check_out_date=check_out,
                adult_count=2
            )
            print(f"[OK] Detail fetched")
            print(f"   - Room plans: {len(detail_result.get('roomPlans') or detail_result.get('room_plans') or [])}")
            print(f"   - Images: {len(detail_result.get('images', []))}")
        except Exception as e:
            print(f"[Error] Detail fetch failed: {e}")
            detail_result = {"error": str(e)}

    # 3. 生成 HTML 报告
    output_path = os.path.join(os.path.dirname(__file__), 'output.html')
    print(f"\n[Report] Generating HTML: {output_path}")

    html = generate_html_report(hotel_query, search_result, detail_result)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] Report generated!")
    print(f"\n[Open] Please open in browser: {output_path}")


if __name__ == '__main__':
    main()
