"""
Search Intent Parser
Uses GLM-4-flash to extract structured search parameters from user input.
Falls back to keyword matching when LLM is unavailable.
"""
import json
import logging
import os
import re

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = '''你是参数提取器。从用户输入提取酒店搜索参数，只返回JSON：
{"city":"","place":"","placeType":"","minStar":null,"maxPrice":null}
placeType必须是：城市、机场、景点、火车站、地铁站、酒店、区/县、详细地址 之一。
不要markdown代码块，只返回纯JSON。'''

VALID_PLACE_TYPES = {'城市', '机场', '景点', '火车站', '地铁站', '酒店', '区/县', '详细地址'}


def _keyword_fallback(text: str) -> dict:
    """Keyword-based placeType inference (fallback when LLM unavailable)."""
    lower = text.lower()
    if any(k in lower for k in ['机场', 'airport', '航站楼']):
        return {'placeType': '机场'}
    if any(k in lower for k in ['火车站', '高铁站', '南站', '北站', '东站', '西站']):
        return {'placeType': '火车站'}
    if any(k in lower for k in ['地铁站', 'metro', '号线']):
        return {'placeType': '地铁站'}
    if any(k in lower for k in ['饭店', '酒店', '宾馆', '旅馆', 'hotel']):
        return {'placeType': '酒店'}
    if any(k in lower for k in ['区', '县']):
        return {'placeType': '区/县'}
    return {'placeType': '详细地址'}


class SearchIntentParser:
    """Parses user input into structured search parameters using LLM."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from zhipuai import ZhipuAI
            api_key = os.environ.get('ZHIPU_API_KEY', '')
            if not api_key:
                return None
            self._client = ZhipuAI(api_key=api_key)
        return self._client

    def parse(self, user_input: str) -> dict | None:
        """
        Parse user input into structured search parameters.

        Args:
            user_input: Combined city + landmark text, e.g. "北京首都机场"

        Returns:
            Dict with city, place, placeType, minStar, maxPrice or None on failure.
        """
        if not user_input or not user_input.strip():
            return None

        # Try LLM first
        result = self._parse_via_llm(user_input)
        if result:
            return result

        # Fallback to keywords
        logger.info(f"LLM parsing failed, using keyword fallback for '{user_input}'")
        fallback = _keyword_fallback(user_input)
        return {
            'city': '',
            'place': user_input,
            'placeType': fallback['placeType'],
            'minStar': None,
            'maxPrice': None,
        }

    def _parse_via_llm(self, user_input: str) -> dict | None:
        """Call GLM-4-flash to extract structured params."""
        client = self.client
        if not client:
            return None

        try:
            resp = client.chat.completions.create(
                model='glm-4-flash',
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_input},
                ],
                temperature=0,
                max_tokens=200,
                timeout=5.0,
            )
            content = resp.choices[0].message.content.strip()

            # Strip markdown code block if present
            if content.startswith('```'):
                content = content.split('\n', 1)[-1].rstrip('`').strip()

            data = json.loads(content)

            # Validate placeType
            if data.get('placeType') not in VALID_PLACE_TYPES:
                data['placeType'] = '详细地址'

            logger.info(f"LLM parsed '{user_input}' → {data}")
            return data

        except Exception as e:
            logger.warning(f"LLM intent parsing failed: {e}")
            return None


# Singleton
_parser = None


def get_intent_parser() -> SearchIntentParser:
    global _parser
    if _parser is None:
        _parser = SearchIntentParser()
    return _parser
