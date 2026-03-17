# -*- coding: utf-8 -*-
"""
测试 RollingGo API 返回的 image URL 是否有效
"""
import asyncio
import json
import httpx
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 加载 .env 文件
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# 设置输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# MCP client imports
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_API_BASE = "https://mcp.aigohotel.com/mcp"


async def test_image_urls():
    """测试酒店图片 URL 是否有效"""

    # 读取 API key
    api_key = os.environ.get('AIGOHOTEL_API_KEY', '')
    if not api_key:
        print("[ERROR] 未设置 AIGOHOTEL_API_KEY 环境变量")
        return

    print(f"[OK] API Key: {api_key[:10]}...")

    # 准备搜索参数
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    params = {
        'originQuery': '东京',
        'place': '东京',
        'placeType': 'city',
        'checkInDate': tomorrow,
        'stayNights': 1,
        'adultCount': 2,
        'size': 5  # 只获取5个酒店
    }

    print(f"\n[INFO] 搜索参数: {json.dumps(params, ensure_ascii=False, indent=2)}")

    # 调用 MCP API
    print("\n[INFO] 调用 RollingGo API...")

    http_client = httpx.AsyncClient(
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=httpx.Timeout(60.0, read=300.0)
    )

    async with http_client:
        async with streamable_http_client(
            MCP_API_BASE,
            http_client=http_client
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool('searchHotels', params)

                if result.isError:
                    print(f"[ERROR] API 错误: {result.content}")
                    return

                # 解析返回内容
                data = None
                for content in result.content:
                    if hasattr(content, 'type') and content.type == "text":
                        data = json.loads(content.text)
                        break

                if not data:
                    print("[ERROR] 未获取到数据")
                    return

    # 获取酒店列表
    hotels = data.get('hotelInformationList', data.get('hotels', []))
    print(f"\n[OK] 获取到 {len(hotels)} 家酒店\n")

    # 检查每个酒店的图片 URL
    print("=" * 80)
    print("检查图片 URL")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=10.0) as client:
        for i, hotel in enumerate(hotels, 1):
            name = hotel.get('name', '未知酒店')
            image_url = hotel.get('imageUrl')

            print(f"\n{i}. {name}")
            print(f"   imageUrl: {image_url}")

            if not image_url:
                print("   [X] 无图片 URL")
                continue

            # 测试 URL 是否可访问
            try:
                response = await client.head(image_url, follow_redirects=True)
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length', '')

                if response.status_code == 200:
                    if 'image' in content_type:
                        size_kb = int(content_length) / 1024 if content_length else '未知'
                        print(f"   [OK] 有效 - 类型: {content_type}, 大小: {size_kb:.1f} KB")
                    else:
                        print(f"   [WARN] 非图片类型: {content_type}")
                else:
                    print(f"   [X] HTTP {response.status_code}")

            except httpx.TimeoutException:
                print("   [X] 超时")
            except Exception as e:
                print(f"   [X] 错误: {e}")

    # 额外检查：获取一个酒店的详情，查看 images 字段
    if hotels:
        print("\n" + "=" * 80)
        print("检查酒店详情中的图片")
        print("=" * 80)

        hotel_id = hotels[0].get('hotelId')
        print(f"\n获取酒店详情: {hotel_id}")

        http_client2 = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(60.0, read=300.0)
        )

        async with http_client2:
            async with streamable_http_client(
                MCP_API_BASE,
                http_client=http_client2
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    detail_result = await session.call_tool('getHotelDetail', {
                        'hotelId': hotel_id,
                        'checkInDate': tomorrow,
                        'checkOutDate': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                        'adultCount': 2
                    })

                    if not detail_result.isError:
                        for content in detail_result.content:
                            if hasattr(content, 'type') and content.type == "text":
                                detail_data = json.loads(content.text)

                                # 检查 images 字段
                                images = detail_data.get('images', [])
                                print(f"\n详情页图片数量: {len(images)}")

                                async with httpx.AsyncClient(timeout=10.0) as client:
                                    for j, img_url in enumerate(images[:5], 1):  # 只检查前5张
                                        print(f"\n  图片 {j}: {img_url[:80]}...")
                                        try:
                                            response = await client.head(img_url, follow_redirects=True)
                                            if response.status_code == 200:
                                                content_type = response.headers.get('content-type', '')
                                                print(f"  [OK] 有效 - {content_type}")
                                            else:
                                                print(f"  [X] HTTP {response.status_code}")
                                        except Exception as e:
                                            print(f"  [X] 错误: {e}")

                                # 打印原始数据中的图片相关字段
                                print(f"\n原始数据中的图片字段:")
                                print(f"  - imageUrl: {detail_data.get('imageUrl', '无')}")
                                print(f"  - images: {len(images)} 张")

                                # 打印完整的原始数据结构（查看所有字段）
                                print(f"\n原始数据所有字段:")
                                for key in sorted(detail_data.keys()):
                                    value = detail_data[key]
                                    if isinstance(value, list):
                                        print(f"  - {key}: [{len(value)} 项]")
                                    elif isinstance(value, str) and len(value) > 100:
                                        print(f"  - {key}: {value[:100]}...")
                                    else:
                                        print(f"  - {key}: {value}")
                                break


if __name__ == "__main__":
    asyncio.run(test_image_urls())
