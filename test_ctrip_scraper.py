"""
携程酒店爬虫测试脚本
测试能否获取携程酒店价格数据
"""
import sys
import io
# 设置标准输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time
import re
from datetime import datetime, timedelta

class CtripScraper:
    """携程酒店搜索爬虫"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://hotels.ctrip.com/',
            'Origin': 'https://hotels.ctrip.com',
        })

        # 城市ID映射
        self.city_ids = {
            '上海': 2,
            '北京': 1,
            '广州': 3,
            '深圳': 4,
            '杭州': 14,
            '成都': 28,
            '南京': 17,
            '武汉': 22,
            '西安': 10,
            '重庆': 132,
            '天津': 3,
            '苏州': 15,
        }

    def search_hotels(self, city_name: str, check_in: str, check_out: str, page: int = 1) -> dict:
        """
        搜索酒店

        Args:
            city_name: 城市名称
            check_in: 入住日期 YYYY-MM-DD
            check_out: 离店日期 YYYY-MM-DD
            page: 页码

        Returns:
            搜索结果字典
        """
        city_id = self.city_ids.get(city_name)
        if not city_id:
            print(f"未知城市: {city_name}")
            return {}

        # 方法1: 尝试 API 接口
        print(f"\n[方法1] 尝试 API 接口: {city_name} (cityId={city_id})")

        api_url = "https://hotels.ctrip.com/Domestic/tool/AjaxHotelList.aspx"

        timestamp = int(time.time() * 1000)
        callback = f"jQuery1830_{timestamp}"

        params = {
            'psid': '',
            'CityID': city_id,
            'city': city_id,
            'cityName': city_name,
            'checkIn': check_in,
            'checkOut': check_out,
            'checkInDate': check_in,
            'checkOutDate': check_out,
            'roomNum': 1,
            'adultNum': 2,
            'childrenNum': 0,
            'page': page,
            'pageSize': 20,
            'sortType': 9,  # 价格排序
            'sortDirection': 1,
            'callback': callback,
            '_': timestamp,
        }

        try:
            response = self.session.get(api_url, params=params, timeout=30)
            print(f"  状态码: {response.status_code}")
            print(f"  响应长度: {len(response.text)} 字符")

            if response.status_code == 200:
                # 尝试解析 JSONP
                if callback in response.text:
                    # 提取 JSON 部分
                    json_start = response.text.find('(') + 1
                    json_end = response.text.rfind(')')
                    if json_start > 0 and json_end > json_start:
                        json_str = response.text[json_start:json_end]
                        data = json.loads(json_str)
                        return data
                else:
                    # 可能是纯 JSON
                    try:
                        return response.json()
                    except Exception:
                        pass

                # 保存原始响应用于调试
                print(f"  响应前500字符: {response.text[:500]}")

        except Exception as e:
            print(f"  请求失败: {e}")

        return {}

    def search_via_mobile_api(self, city_name: str, check_in: str, check_out: str) -> dict:
        """
        方法2: 尝试移动端 API
        """
        print(f"\n[方法2] 尝试移动端 API")

        city_id = self.city_ids.get(city_name, 2)

        # 移动端 API
        url = "https://m.ctrip.com/restapi/soa2/16790/getHotelList"

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 CtripWireless/8.38.0',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        payload = {
            "head": {
                "cid": "09031072810241452413",
                "ctok": "",
                "cver": "8.38.0",
                "lang": "01",
                "sid": "8888",
                "syscode": "09",
                "auth": "",
                "extension": []
            },
            "hotelListCondition": {
                "cityId": city_id,
                "checkInDate": check_in,
                "checkOutDate": check_out,
                "roomGuestCount": [{"adultCount": 2, "childCount": 0}],
                "pageNo": 1,
                "pageSize": 20,
                "sortType": 9,
                "sourceFrom": "H5"
            }
        }

        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=30)
            print(f"  状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                return data

        except Exception as e:
            print(f"  请求失败: {e}")

        return {}

    def search_via_page(self, city_name: str, check_in: str, check_out: str) -> str:
        """
        方法3: 直接获取搜索页面 HTML
        """
        print(f"\n[方法3] 获取搜索页面 HTML")

        city_id = self.city_ids.get(city_name, 2)

        url = f"https://hotels.ctrip.com/hotels/list?city={city_id}"
        params = {
            'checkin': check_in,
            'checkout': check_out,
            'optionId': city_id,
            'display': city_name,
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            print(f"  状态码: {response.status_code}")
            print(f"  响应长度: {len(response.text)} 字符")

            if response.status_code == 200:
                # 检查是否有酒店数据
                if 'hotelName' in response.text or 'price' in response.text:
                    print("  ✓ 页面包含酒店数据")
                    # 保存 HTML 用于分析
                    with open('ctrip_page.html', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print("  已保存到 ctrip_page.html")
                else:
                    print("  ✗ 页面可能需要 JavaScript 渲染")

                return response.text[:1000]

        except Exception as e:
            print(f"  请求失败: {e}")

        return ""


def test_ctrip_scraper():
    """测试携程爬虫"""
    print("=" * 60)
    print("携程酒店爬虫测试")
    print("=" * 60)

    scraper = CtripScraper()

    # 设置搜索参数
    today = datetime.now()
    check_in = (today + timedelta(days=2)).strftime('%Y-%m-%d')
    check_out = (today + timedelta(days=3)).strftime('%Y-%m-%d')

    city = '上海'

    print(f"\n搜索参数:")
    print(f"  城市: {city}")
    print(f"  入住: {check_in}")
    print(f"  离店: {check_out}")

    # 测试各种方法
    result1 = scraper.search_hotels(city, check_in, check_out)
    result2 = scraper.search_via_mobile_api(city, check_in, check_out)
    result3 = scraper.search_via_page(city, check_in, check_out)

    # 分析结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    success = False

    if result1:
        print("\n✓ 方法1 (API) 获取到数据")
        hotels = result1.get('hotelList', result1.get('data', []))
        if isinstance(hotels, list) and len(hotels) > 0:
            print(f"  找到 {len(hotels)} 家酒店")
            success = True
        else:
            print(f"  数据结构: {list(result1.keys())[:5]}")

    if result2:
        print("\n✓ 方法2 (移动端API) 获取到数据")
        hotels = result2.get('hotelList', result2.get('response', {}).get('hotelList', []))
        if isinstance(hotels, list) and len(hotels) > 0:
            print(f"  找到 {len(hotels)} 家酒店")
            success = True
        else:
            print(f"  数据结构: {list(result2.keys())[:5]}")

    if result3:
        print("\n✓ 方法3 (页面HTML) 获取到内容")

    if not success:
        print("\n✗ 所有方法均未能获取酒店数据")
        print("\n可能的原因:")
        print("  1. 需要登录/cookie")
        print("  2. 需要 JavaScript 渲染")
        print("  3. IP 被限制")
        print("  4. API 接口已变更")

    return success


if __name__ == '__main__':
    test_ctrip_scraper()
