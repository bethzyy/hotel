# -*- coding: utf-8 -*-
"""
Playwright Ctrip Scraper Test
"""
import asyncio
import json
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

CITY_IDS = {
    'shanghai': 2,
    'beijing': 1,
    'guangzhou': 3,
    'shenzhen': 4,
    'hangzhou': 14,
    'chengdu': 28,
    'nanjing': 17,
}

async def scrape_ctrip():
    city_id = 2
    city_name = 'Shanghai'

    today = datetime.now()
    check_in = (today + timedelta(days=2)).strftime('%Y-%m-%d')
    check_out = (today + timedelta(days=3)).strftime('%Y-%m-%d')

    url = f"https://hotels.ctrip.com/hotels/list?city={city_id}&checkin={check_in}&checkout={check_out}"

    print(f"Scraping Ctrip...")
    print(f"URL: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            locale='zh-CN'
        )
        page = await context.new_page()

        # Track API responses
        api_data = []

        async def handle_response(response):
            if 'hotel' in response.url.lower() or 'price' in response.url.lower():
                try:
                    if response.status == 200:
                        ct = response.headers.get('content-type', '')
                        if 'json' in ct:
                            data = await response.json()
                            api_data.append({'url': response.url, 'data': data})
                except:
                    pass

        page.on('response', handle_response)

        try:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            print("Page loaded, waiting for content...")
            await asyncio.sleep(5)

            # Screenshot
            await page.screenshot(path='ctrip_screenshot.png')
            print("Screenshot saved")

            # Get content
            content = await page.content()
            print(f"Content length: {len(content)} chars")

            # Extract hotel IDs and names
            hotel_ids = re.findall(r'data-offline-hotelid="(\d+)"', content)
            hotel_names = re.findall(r'class="hotelName"[^>]*>([^<]+)<', content)

            print(f"\nHotel IDs found: {len(hotel_ids)}")
            print(f"Hotel names found: {len(hotel_names)}")

            hotels = []
            for i in range(min(len(hotel_ids), len(hotel_names))):
                hotels.append({
                    'hotel_id': hotel_ids[i],
                    'name': hotel_names[i],
                    'provider': 'ctrip'
                })

            # Check API data for prices
            print(f"\nAPI responses captured: {len(api_data)}")
            for item in api_data:
                print(f"  URL: {item['url'][:80]}...")

            # Save results
            with open('ctrip_hotels.json', 'w', encoding='utf-8') as f:
                json.dump(hotels, f, ensure_ascii=False, indent=2)

            print(f"\nSaved {len(hotels)} hotels to ctrip_hotels.json")
            for h in hotels[:5]:
                print(f"  {h['hotel_id']}: {h['name']}")

            return hotels

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(scrape_ctrip())
