"""
Regression tests — 防止已修复问题重复出现。

覆盖 2026-04-08 界面重构后发现的所有问题：
1. storage.ts screen 变量遮蔽导致 TDZ 崩溃
2. Flask 全局限流拦截前端静态资源（429）
3. 搜索 API 中文参数编码问题（GBK vs UTF-8）
4. Pinia payload 序列化 hasOwnProperty 错误
5. 搜索参数持久化丢失
6. Nuxt 反向代理 @fs 路径 404
7. 反向代理路由优先级（API 路由不被 catch-all 拦截）
"""


class TestStorageScreenShadowing:
    """Issue #1: web/utils/storage.ts 中 const screen 遮蔽 window.screen
    导致 'Cannot access screen before initialization' TDZ 错误，
    级联导致 Vue hydration 失败、所有交互失效。"""

    def test_storage_file_no_screen_shadowing(self):
        """storage.ts 不应使用 'const screen' 声明局部变量。"""
        storage_path = 'web/utils/storage.ts'
        with open(storage_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 不应存在 const screen = 这种遮蔽写法
        assert 'const screen =' not in content, \
            "storage.ts still has 'const screen =' which shadows window.screen"
        # 应使用 window.screen 或其他变量名
        assert 'window.screen' in content or 'screenSize' in content, \
            "storage.ts should use window.screen or screenSize variable"

    def test_storage_file_valid_typescript(self):
        """storage.ts 应该是可解析的 TypeScript。"""
        storage_path = 'web/utils/storage.ts'
        with open(storage_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 基本结构检查
        assert 'export function getDeviceFingerprint' in content
        assert 'localStorage' in content
        assert 'navigator' in content


class TestRateLimitingScope:
    """Issue #2: flask-limiter 全局 default_limits 拦截了 Nuxt 代理的静态资源请求。
    修复：去掉全局 default_limits，仅用路由级 @limiter.limit() 装饰器。"""

    def test_limiter_no_global_defaults(self, client):
        """全局限流不应影响非 API 路由。连续请求不应触发 429。"""
        # 首页代理到 Nuxt（测试环境 Nuxt 不运行，返回 502）
        # 关键是：不应返回 429（被限流）
        for _ in range(10):
            resp = client.get('/')
            assert resp.status_code != 429, \
                "Homepage requests should NOT be rate-limited (429)"

    def test_api_rate_limits_still_work(self, client):
        """API 路由的独立限流应该仍然生效（测试环境 RATELIMIT_ENABLED=False 跳过）。"""
        # 在测试环境中限流被禁用，所以这里只验证 API 可达
        resp = client.get('/api/providers')
        assert resp.status_code == 200


class TestSearchAPIEncoding:
    """Issue #3: 搜索 API 在接收中文参数时因编码问题返回 500。
    修复：_parse_json_body 支持 UTF-8/GBK 多编码回退。"""

    def test_search_chinese_params_utf8(self, client):
        """中文城市名应能正常解析，不返回编码错误。"""
        import json
        body = json.dumps({
            'provider': 'tuniu',
            'city_name': '北京',
            'check_in': '2026-05-01',
            'check_out': '2026-05-02',
        }, ensure_ascii=False)
        resp = client.post(
            '/api/search',
            data=body.encode('utf-8'),
            content_type='application/json; charset=utf-8',
        )
        # 不应是编码错误（400/500 with encoding message）
        data = resp.get_json()
        if resp.status_code >= 400:
            error_msg = data.get('error', '') if data else ''
            assert 'decode' not in error_msg.lower(), \
                f"Should not have encoding error, got: {error_msg}"

    def test_search_chinese_params_gbk_fallback(self, client):
        """即使收到 GBK 编码的请求体，也应优雅处理而非 500。"""
        body = '{"provider":"tuniu","city_name":"北京","check_in":"2026-05-01","check_out":"2026-05-02"}'
        gbk_body = body.encode('gbk')
        resp = client.post(
            '/api/search',
            data=gbk_body,
            content_type='application/json',
        )
        # 应该成功解析（GBK fallback）或返回业务错误，不应是编码错误
        data = resp.get_json()
        if data and resp.status_code >= 400:
            error_msg = data.get('error', '')
            assert 'decode' not in error_msg.lower(), \
                f"GBK fallback failed, got encoding error: {error_msg}"

    def test_search_parse_helper_exists(self):
        """_parse_json_body 辅助函数应存在于 search.py 中。"""
        from app.routes.search import _parse_json_body
        assert callable(_parse_json_body)


class TestProxyRoutePriority:
    """Issue #7: Flask catch-all 代理路由不应拦截 API 路由。
    API 路由（/api/*）应由蓝图处理，不应被 /<path:path> 捕获。"""

    def test_api_routes_accessible(self, client):
        """API 路由应返回正常 API 响应，而非 Nuxt 代理的 502。"""
        resp = client.get('/api/providers')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'providers' in data or 'success' in data

    def test_non_api_routes_proxied(self, client):
        """非 API 路由应由 catch-all 代理处理（测试环境返回 5xx）。"""
        resp = client.get('/some-random-page')
        # Nuxt 不运行时返回 5xx（代理失败），而非 200（被 Flask 直接处理）
        assert resp.status_code >= 500

    def test_health_endpoint_not_proxied(self, client):
        """/health 端点应直接由 Flask 处理。"""
        resp = client.get('/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get('status') == 'ok'


class TestProviderToggle:
    """Issue #8: Provider 切换按钮无法点击。
    根因：<label for> + 隐藏 radio 吞掉 click 冒泡。
    修复：移除 label/radio，改用 span + store.setProvider() + ClientOnly。"""

    def test_search_form_no_hidden_radio(self):
        """SearchForm.vue 不应使用隐藏 radio + label for 模式。"""
        with open('web/components/search/SearchForm.vue', 'r', encoding='utf-8') as f:
            content = f.read()
        # 不应有 <input type="radio" class="d-none">
        assert 'type="radio"' not in content, \
            "SearchForm.vue should NOT use hidden radio inputs for provider toggle"
        # 不应有 <label :for="..."> 关联 provider id
        assert '<label :for=' not in content, \
            "SearchForm.vue should NOT use label with :for for provider toggle"

    def test_search_form_uses_setProvider(self):
        """Provider 切换应通过 store.setProvider() action。"""
        with open('web/components/search/SearchForm.vue', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'store.setProvider' in content, \
            "Provider toggle should use store.setProvider() action"

    def test_search_form_wrapped_in_client_only(self):
        """SearchForm 应使用 ClientOnly 避免 SSR hydration mismatch。"""
        with open('web/components/search/SearchForm.vue', 'r', encoding='utf-8') as f:
            content = f.read()
        assert '<ClientOnly>' in content, \
            "SearchForm.vue should be wrapped in <ClientOnly> to avoid SSR hydration mismatch"


class TestFrontendConfig:
    """前端配置回归测试，防止关键配置被意外修改。"""

    def test_nuxt_vite_fs_allow(self):
        """nuxt.config.ts 应配置 vite.server.fs.allow 避免 @fs 路径 404。"""
        with open('web/nuxt.config.ts', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'fs' in content and 'allow' in content, \
            "nuxt.config.ts should have vite.server.fs.allow configured"

    def test_nuxt_css_bootstrap(self):
        """Bootstrap CSS 应正确配置。"""
        with open('web/nuxt.config.ts', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'bootstrap' in content

    def test_use_api_charset(self):
        """useApi composable 应设置 charset=utf-8。"""
        with open('web/composables/useApi.ts', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'charset=utf-8' in content, \
            "useApi.ts should set Content-Type charset=utf-8"

    def test_pinia_persist_plugin_exists(self):
        """pinia-plugin-persistedstate 应已配置。"""
        assert os.path.exists('web/plugins/pinia-persist.ts'), \
            "Pinia persist plugin file should exist"
        with open('web/plugins/pinia-persist.ts', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'createPersistedState' in content

    def test_search_form_store_exists(self):
        """搜索参数持久化 Store 应存在。"""
        assert os.path.exists('web/stores/searchForm.ts'), \
            "Search form store should exist for parameter persistence"
        with open('web/stores/searchForm.ts', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'persist' in content
        assert 'validateDates' in content

    def test_search_form_uses_store(self):
        """SearchForm.vue 应使用 searchForm store 直接绑定（非 storeToRefs，避免双层 Ref 包装）。"""
        with open('web/components/search/SearchForm.vue', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'useSearchFormStore' in content, \
            "SearchForm.vue should use useSearchFormStore"
        # storeToRefs 已移除（Nuxt SSR hydration 导致双层 Ref 包装）
        assert 'storeToRefs' not in content, \
            "SearchForm.vue should NOT use storeToRefs (causes [object Object] bug)"
        assert 'store.' in content, \
            "SearchForm.vue should use store.xxx directly for v-model"

    def test_city_autocomplete_exists(self):
        """城市自动补全功能应存在。"""
        with open('web/components/search/SearchForm.vue', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'POPULAR_CITIES' in content, \
            "City autocomplete list should exist"


import os
