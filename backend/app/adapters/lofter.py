"""
Lofter Adapter
Uses DWR (Direct Web Remoting) API to search for novels by tag
"""

import asyncio
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Optional

import httpx

from app.adapters.base import BaseAdapter
from app.schemas.novel import Novel, NovelSource
from app.config import settings


class LofterAdapter(BaseAdapter):
    """Adapter for Lofter platform"""

    source_name = "lofter"
    _executor = ThreadPoolExecutor(max_workers=2)

    # SoyoSaki related tags on Lofter
    SOYOSAKI_TAGS = ["素祥", "祥素", "そよさき"]
    LOFTER_IMAGE_DOMAINS = [
        "lf127.net",
        "126.net",
        "lofter.com",
        "imglf",
        "nos.netease.com",
        "nosdn.127.net",
        "netease.com",
    ]
    _SURROGATE_RE = re.compile(r"[\ud800-\udfff]")
    _dynamic_cache = {}
    _dynamic_cache_ttl_seconds = 300

    def _get_cookie(self) -> Optional[str]:
        """Get Lofter cookie from settings"""
        return settings.LOFTER_COOKIE if settings.LOFTER_COOKIE else None

    async def search(
        self,
        tags: List[str],
        exclude_tags: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "date",
    ) -> List[Novel]:
        """Search for novels by tags on Lofter"""
        cookie = self._get_cookie()
        if not cookie:
            print("⚠️ Lofter: No cookie configured, skipping")
            return []

        exclude_tags = exclude_tags or []

        max_page_size = settings.LOFTER_MAX_PAGE_SIZE or settings.LOFTER_DYNAMIC_MAX_ITEMS
        if max_page_size and page_size > max_page_size:
            page_size = max_page_size

        # Use multiple tags and merge results to increase coverage
        search_tags = list(dict.fromkeys(tags + self.SOYOSAKI_TAGS))
        if not search_tags:
            search_tags = ["素祥"]

        # Prefer the main tag page for better coverage and structure
        primary_tag = "素祥" if "素祥" in search_tags else search_tags[0]

        # Map sort_by to Lofter's ranking type
        ranking_type = {
            "date": "new",
            "kudos": "total",
            "hits": "total",
            "wordCount": "new",
        }.get(sort_by, "new")

        # Calculate offset
        offset = (page - 1) * page_size

        loop = asyncio.get_running_loop()
        if not settings.LOFTER_DYNAMIC_ENABLED:
            print("⚠️ Lofter: dynamic crawling disabled, skipping")
            return []

        cache_key = self._dynamic_cache_key(primary_tag, ranking_type, exclude_tags)
        cache_entry = self._get_dynamic_cache(cache_key)
        cached_items = cache_entry["items"] if cache_entry else []
        if cache_entry and len(cached_items) >= offset + page_size:
            return cached_items[offset : offset + page_size]

        target_total = max(offset + page_size, len(cached_items) + page_size)
        ordered = await loop.run_in_executor(
            self._executor,
            self._search_dynamic_sync,
            primary_tag,
            ranking_type,
            page_size,
            offset,
            exclude_tags,
            cookie,
            target_total,
            True,
        )

        merged = list(cached_items) if cached_items else []
        seen_ids = {f"{n.source}:{n.id}" for n in merged}
        for novel in ordered:
            key = f"{novel.source}:{novel.id}"
            if key in seen_ids:
                continue
            seen_ids.add(key)
            merged.append(novel)

        self._set_dynamic_cache(cache_key, merged, False)

        if offset >= len(merged):
            return []
        novels = merged[offset : offset + page_size]

        if len(novels) > page_size:
            novels = novels[:page_size]

        return novels

    def _dynamic_cache_key(
        self, tag: str, ranking_type: str, exclude_tags: List[str]
    ) -> str:
        exclude_key = ",".join(sorted(exclude_tags)) if exclude_tags else ""
        return f"{tag}:{ranking_type}:{exclude_key}"

    def _get_dynamic_cache(self, key: str):
        entry = self._dynamic_cache.get(key)
        if not entry:
            return None
        ttl = settings.LOFTER_DYNAMIC_CACHE_TTL or self._dynamic_cache_ttl_seconds
        if time.time() - entry["timestamp"] > ttl:
            self._dynamic_cache.pop(key, None)
            return None
        return entry

    def _set_dynamic_cache(self, key: str, items: List[Novel], exhausted: bool) -> None:
        self._dynamic_cache[key] = {
            "items": items,
            "timestamp": time.time(),
            "exhausted": exhausted,
        }

    def _search_tag_page_sync(
        self,
        tag: str,
        ranking_type: str,
        page: int,
        page_size: int,
        exclude_tags: List[str],
        cookie: str,
    ) -> List[Novel]:
        """Search by parsing tag page HTML (more complete than DWR for page 1)"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            print("⚠️ Lofter: beautifulsoup4 not installed, fallback to DWR")
            return []

        try:
            from urllib.parse import quote

            tag_path = "new" if ranking_type == "new" else "total"
            encoded_tag = quote(tag, safe="")
            url = f"https://www.lofter.com/tag/{encoded_tag}/{tag_path}"
            if page > 1:
                url = f"{url}?page={page}"

            headers = {
                "Referer": f"https://www.lofter.com/tag/{encoded_tag}",
                "Cookie": cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=headers)
                if response.status_code != 200:
                    print(f"Lofter tag page error: {response.status_code}")
                    return []

            return self._parse_tag_page_html(
                response.text,
                exclude_tags,
                ranking_type,
                limit=page_size,
            )
        except Exception as e:
            print(f"Lofter tag page parse error: {e}")
            return []

    def _parse_tag_page_html(
        self,
        html: str,
        exclude_tags: List[str],
        ranking_type: str,
        limit: Optional[int] = None,
    ) -> List[Novel]:
        """Parse tag page HTML into novel list."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("div.m-mlist")

        novels: List[Novel] = []
        seen_ids = set()
        for item in items:
            author_el = item.select_one(".publishernick")
            author = (
                self._sanitize_text(author_el.get_text(strip=True))
                if author_el
                else "Unknown"
            )
            author_url = author_el.get("href") if author_el else ""
            if author_url and author_url.startswith("//"):
                author_url = f"https:{author_url}"

            post_link_el = item.select_one(".isayt a.isayc")
            post_link = post_link_el.get("href") if post_link_el else ""
            if not post_link:
                link = item.select_one('a[href*="/post/"]')
                post_link = link.get("href") if link else ""
            if post_link and post_link.startswith("//"):
                post_link = f"https:{post_link}"
            if not post_link:
                continue

            blog_name = self._extract_blog_name(author_url or post_link)
            post_id = self._extract_post_id(post_link)
            if not post_id:
                continue
            if not blog_name:
                continue
            novel_id = f"{blog_name}:{post_id}"
            if novel_id in seen_ids:
                continue
            seen_ids.add(novel_id)

            title = ""
            title_el = item.select_one(".m-long-post-icnt .tit")
            if title_el:
                title = self._sanitize_text(title_el.get_text(strip=True))
            if not title:
                title_el = item.select_one(".m-icnt .ttl") or item.select_one(
                    ".m-icnt .title"
                )
                if title_el:
                    title = self._sanitize_text(title_el.get_text(strip=True))

            summary = ""
            pre_el = item.select_one(".m-long-post-icnt .pre")
            if pre_el:
                summary = self._sanitize_text(pre_el.get_text(strip=True))
            if not summary:
                txt_el = item.select_one(".m-icnt .txt")
                if txt_el:
                    summary = self._sanitize_text(txt_el.get_text(strip=True))

            tags = [
                self._sanitize_text(t.get_text(strip=True))
                for t in item.select(".w-opt .opta a span")
                if t.get_text(strip=True)
            ]

            if title and any(pattern in title for pattern in exclude_tags):
                continue

            kudos = None
            opt_text = item.get_text(" ", strip=True)
            hot_match = re.search(r"热度\\((\\d+)\\)", opt_text)
            if hot_match:
                kudos = int(hot_match.group(1))

            published_at = datetime.now().isoformat()
            title_attr = post_link_el.get("title", "") if post_link_el else ""
            date_match = re.search(r"(\\d{2})/(\\d{2})\\s+(\\d{2}:\\d{2})", title_attr)
            if date_match:
                month, day, hm = date_match.groups()
                try:
                    published_at = datetime(
                        datetime.now().year,
                        int(month),
                        int(day),
                        int(hm[:2]),
                        int(hm[3:]),
                    ).isoformat()
                except Exception:
                    pass

            cover_image = None
            img_el = item.select_one(".m-icnt img")
            if img_el:
                cover_image = (
                    img_el.get("large")
                    or img_el.get("data-src")
                    or img_el.get("data-original")
                    or img_el.get("src")
                )
            if cover_image:
                cover_image = self._normalize_lofter_image_url(cover_image)
                if cover_image.startswith("./") or cover_image.startswith("/"):
                    cover_image = None

            novel = Novel(
                id=novel_id,
                source=NovelSource.LOFTER,
                title=title if title else "无标题",
                author=author,
                author_url=author_url
                or (f"https://{blog_name}.lofter.com" if blog_name else ""),
                summary=summary[:500] if summary else "暂无简介",
                tags=tags[:10],
                word_count=None,
                chapter_count=1,
                kudos=kudos,
                hits=None,
                rating=None,
                published_at=published_at,
                updated_at=published_at,
                source_url=post_link,
                cover_image=cover_image,
                is_complete=True,
            )
            novels.append(novel)

        if ranking_type == "total":
            novels.sort(key=lambda n: n.kudos or 0, reverse=True)

        if limit:
            return novels[:limit]
        return novels

    def _parse_cookie_header(self, cookie: str) -> List[dict]:
        cookies = []
        for part in cookie.split(";"):
            part = part.strip()
            if not part or "=" not in part:
                continue
            name, value = part.split("=", 1)
            cookies.append(
                {
                    "name": name,
                    "value": value,
                    "url": "https://www.lofter.com",
                }
            )
        return cookies

    def _search_dynamic_sync(
        self,
        tag: str,
        ranking_type: str,
        page_size: int,
        offset: int,
        exclude_tags: List[str],
        cookie: str,
        target_total: Optional[int] = None,
        return_all: bool = False,
    ) -> List[Novel]:
        """Use Playwright to scroll tag page and collect more posts."""
        if not settings.LOFTER_DYNAMIC_ENABLED:
            return []
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
        except ImportError:
            print("⚠️ Lofter: Playwright not installed, skip dynamic crawl")
            return []

        try:
            from urllib.parse import quote

            encoded_tag = quote(tag, safe="")
            tag_path = "new" if ranking_type == "new" else "total"
            url = f"https://www.lofter.com/tag/{encoded_tag}/{tag_path}"

            headers = {
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
            if settings.LOFTER_CAPTTOKEN:
                headers["capttoken"] = settings.LOFTER_CAPTTOKEN

            if target_total is None:
                target_total = offset + page_size
            base_scrolls = settings.LOFTER_DYNAMIC_MAX_SCROLLS or 8
            max_scrolls = max(base_scrolls, target_total // 8 + 6)
            scroll_wait_ms = settings.LOFTER_DYNAMIC_SCROLL_WAIT_MS or 1200
            initial_wait_ms = settings.LOFTER_DYNAMIC_INITIAL_WAIT_MS or 1500

            dwr_payloads: List[str] = []

            def on_response(response):
                try:
                    if "TagBean.search.dwr" in response.url:
                        dwr_payloads.append(response.text())
                except Exception:
                    return

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    locale="zh-CN",
                    extra_http_headers=headers,
                )
                context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                )
                cookies = self._parse_cookie_header(cookie)
                if cookies:
                    context.add_cookies(cookies)

                page = context.new_page()
                page.on("response", on_response)
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    page.wait_for_load_state("networkidle", timeout=20000)
                except PWTimeout:
                    pass
                try:
                    page.wait_for_selector("div.m-mlist", timeout=20000)
                except PWTimeout:
                    print("⚠️ Lofter: tag page did not load list in time")
                page.wait_for_timeout(initial_wait_ms)

                ordered: List[Novel] = []
                seen = set()
                processed_dwr = 0
                last_count = 0
                last_dwr = 0
                stable_rounds = 0
                scrolls = 0

                while (
                    scrolls < max_scrolls
                    and len(ordered) < target_total
                    and stable_rounds < 4
                ):
                    html = page.content()
                    parsed = self._parse_tag_page_html(
                        html, exclude_tags, ranking_type, limit=target_total
                    )
                    for novel in parsed:
                        key = f"{novel.source}:{novel.id}"
                        if key in seen:
                            continue
                        seen.add(key)
                        ordered.append(novel)

                    while processed_dwr < len(dwr_payloads):
                        payload = dwr_payloads[processed_dwr]
                        processed_dwr += 1
                        for novel in self._parse_dwr_response(payload, exclude_tags):
                            key = f"{novel.source}:{novel.id}"
                            if key in seen:
                                continue
                            seen.add(key)
                            ordered.append(novel)

                    if len(ordered) == last_count:
                        if processed_dwr == last_dwr:
                            stable_rounds += 1
                        else:
                            stable_rounds = 0
                    else:
                        stable_rounds = 0
                    last_count = len(ordered)
                    last_dwr = processed_dwr

                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(scroll_wait_ms)
                    scrolls += 1

                context.close()
                browser.close()

            while processed_dwr < len(dwr_payloads):
                payload = dwr_payloads[processed_dwr]
                processed_dwr += 1
                for novel in self._parse_dwr_response(payload, exclude_tags):
                    key = f"{novel.source}:{novel.id}"
                    if key in seen:
                        continue
                    seen.add(key)
                    ordered.append(novel)

            if not ordered:
                print("⚠️ Lofter: dynamic crawl found 0 items")
            else:
                print(f"✅ Lofter: dynamic crawl collected {len(ordered)} items")

            if return_all:
                return ordered
            if offset >= len(ordered):
                return []
            return ordered[offset : offset + page_size]
        except Exception as e:
            print(f"Lofter dynamic crawl error: {e}")
            return []

    def _search_multi_sync(
        self,
        tags: List[str],
        ranking_type: str,
        page_size: int,
        offset: int,
        exclude_tags: List[str],
        cookie: str,
    ) -> List[Novel]:
        """Search multiple tags and merge results"""
        all_novels: List[Novel] = []
        seen_ids = set()

        for tag in tags:
            novels = self._search_sync(
                tag, ranking_type, page_size, offset, exclude_tags, cookie
            )
            for novel in novels:
                novel_key = f"{novel.source}:{novel.id}"
                if novel_key in seen_ids:
                    continue
                seen_ids.add(novel_key)
                all_novels.append(novel)

        if ranking_type == "new":
            all_novels.sort(key=lambda n: n.published_at or "", reverse=True)
        elif ranking_type == "total":
            all_novels.sort(key=lambda n: n.kudos or 0, reverse=True)

        return all_novels[:page_size]

    def _search_sync(
        self,
        tag: str,
        ranking_type: str,
        page_size: int,
        offset: int,
        exclude_tags: List[str],
        cookie: str,
    ) -> List[Novel]:
        """Synchronous search implementation"""
        try:
            from urllib.parse import quote

            api_url = "https://www.lofter.com/dwr/call/plaincall/TagBean.search.dwr"

            # URL encode the tag for use in URL/headers
            encoded_tag = quote(tag, safe="")

            headers = {
                "Referer": f"https://www.lofter.com/tag/{encoded_tag}",
                "Cookie": cookie,
                "Content-Type": "text/plain",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Origin": "https://www.lofter.com",
            }
            if settings.LOFTER_CAPTTOKEN:
                headers["capttoken"] = settings.LOFTER_CAPTTOKEN

            body_lines = [
                "callCount=1",
                "scriptSessionId=${scriptSessionId}187",
                "httpSessionId=",
                "c0-scriptName=TagBean",
                "c0-methodName=search",
                "c0-id=0",
                f"c0-param0=string:{encoded_tag}",
                "c0-param1=number:0",
                "c0-param2=string:",
                f"c0-param3=string:{ranking_type}",
                "c0-param4=boolean:false",
                "c0-param5=number:0",
                f"c0-param6=number:{page_size}",
                f"c0-param7=number:{offset}",
                "c0-param8=number:0",
                "batchId=565555",
            ]

            body_bytes = "\n".join(body_lines).encode("utf-8")

            with httpx.Client(timeout=30.0) as client:
                response = client.post(api_url, content=body_bytes, headers=headers)

                if response.status_code != 200:
                    print(f"Lofter API error: {response.status_code}")
                    return []

                # Debug: print response preview
                print(f"📝 Lofter response length: {len(response.text)} bytes")
                if len(response.text) < 500:
                    print(f"📝 Full response: {response.text}")
                else:
                    print(f"📝 Response preview: {response.text[:500]}...")

                # Parse DWR response
                novels = self._parse_dwr_response(response.text, exclude_tags)
                return novels

        except Exception as e:
            print(f"Lofter search error: {e}")
            import traceback

            traceback.print_exc()
            return []

    def _parse_dwr_response(
        self, response_text: str, exclude_tags: List[str]
    ) -> List[Novel]:
        """Parse DWR response format"""
        novels = []

        try:
            # DWR returns JavaScript code, extract assignments first
            assignments = {}

            # Match variable assignments like s0.xxx=yyy
            var_pattern = re.compile(r"s(\d+)\.(\w+)\s*=\s*([^;]+);")
            for match in var_pattern.finditer(response_text):
                var_id, prop, value = match.groups()
                key = f"s{var_id}"
                if key not in assignments:
                    assignments[key] = {}
                assignments[key][prop] = self._strip_quotes(value)

            # Match string values
            str_pattern = re.compile(r's(\d+)\.(\w+)\s*=\s*"([^"]*)"')
            for match in str_pattern.finditer(response_text):
                var_id, prop, value = match.groups()
                key = f"s{var_id}"
                if key not in assignments:
                    assignments[key] = {}
                assignments[key][prop] = value

            # Find posts by post references if present; else fall back to post-like objects
            post_candidates = []
            post_refs = re.findall(r"s(\\d+)\\.post=s(\\d+);", response_text)
            if post_refs:
                for _, post_id in post_refs:
                    post_key = f"s{post_id}"
                    if post_key in assignments:
                        post_candidates.append((post_key, assignments[post_key]))
            else:
                for key, data in assignments.items():
                    if self._looks_like_post(data):
                        post_candidates.append((key, data))

            print(f"📊 Lofter DWR: found {len(post_candidates)} post candidates")

            parsed_count = 0
            skipped_no_url = 0
            skipped_no_blog = 0
            seen_ids = set()

            for _, post in post_candidates:

                # Get title and decode Unicode escapes
                title = post.get("title", "")
                title = self._sanitize_text(title) if title else ""
                if not title:
                    # Try to get from digest
                    digest = post.get("digest", "")
                    title = self._sanitize_text(self._clean_html(digest))[:50] if digest else "无标题"

                # Check exclude tags
                if any(pattern in title for pattern in exclude_tags):
                    continue

                # Get blog info
                blog_info_ref = post.get("blogInfo", "")
                blog_info = {}
                if blog_info_ref.startswith("s"):
                    blog_info = assignments.get(blog_info_ref, {})

                author = self._sanitize_text(blog_info.get("blogNickName", "Unknown"))
                blog_name = self._sanitize_text(blog_info.get("blogName", ""))

                # Get other properties
                publish_time = post.get("publishTime", "")
                blog_page_url = post.get("blogPageUrl", "")
                post_id = post.get("postId", "") or post.get("id", "")

                # If no blogPageUrl, try to construct from other data
                if not blog_page_url:
                    skipped_no_url += 1
                    # Try to use blog_name and postId/publishTime as fallback
                    fallback_id = post_id or publish_time
                    if blog_name and fallback_id:
                        blog_page_url = f"https://{blog_name}.lofter.com/post/{fallback_id}"

                if not blog_name and blog_page_url:
                    blog_name = self._extract_blog_name(blog_page_url)
                if not blog_name:
                    skipped_no_blog += 1
                    continue

                # Parse date
                try:
                    if publish_time and publish_time.isdigit():
                        published_at = datetime.fromtimestamp(
                            int(publish_time) / 1000
                        ).isoformat()
                    else:
                        published_at = datetime.now().isoformat()
                except:
                    published_at = datetime.now().isoformat()

                # Get tags
                tag_list_str = post.get("tagList", "")
                tags = []
                if tag_list_str:
                    # Parse tag list from JavaScript array format
                    tag_matches = re.findall(r'"([^"]+)"', tag_list_str)
                    tags = tag_matches if tag_matches else []
                tags = [self._sanitize_text(tag) for tag in tags if tag]

                # Get hot/bookmark count
                hot = post.get("hot", "0")
                try:
                    kudos = int(hot) if hot.isdigit() else 0
                except:
                    kudos = 0

                # Get digest as summary
                digest = post.get("digest", "")
                summary = self._sanitize_text(self._clean_html(digest)) if digest else "暂无简介"

                # Extract post ID from URL and combine with blog_name
                post_id_match = re.search(r"/post/([^/?#]+)", blog_page_url or "")
                post_id = post_id_match.group(1) if post_id_match else (post_id or publish_time)
                # Store as blogName:postId so we can reconstruct the URL later
                novel_id = f"{blog_name}:{post_id}" if blog_name else post_id
                if not novel_id or novel_id in seen_ids:
                    continue
                seen_ids.add(novel_id)

                novel = Novel(
                    id=novel_id,
                    source=NovelSource.LOFTER,
                    title=title if title else "无标题",
                    author=author,
                    author_url=f"https://{blog_name}.lofter.com" if blog_name else "",
                    summary=summary[:500],
                    tags=tags[:10],
                    word_count=None,
                    chapter_count=1,
                    kudos=kudos,
                    hits=None,
                    rating=None,
                    published_at=published_at,
                    updated_at=published_at,
                    source_url=blog_page_url,
                    cover_image=None,  # Lofter posts may have images in content
                    is_complete=True,
                )

                novels.append(novel)
                parsed_count += 1

            print(
                f"📊 Lofter DWR stats: {parsed_count} parsed, {skipped_no_blog} skipped (no blog), {skipped_no_url} had no URL (used fallback)"
            )
            print(f"✅ Lofter: parsed {len(novels)} novels from response")
            return novels

        except Exception as e:
            print(f"Lofter parse error: {e}")
            import traceback

            traceback.print_exc()
            return []

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from string"""
        clean = re.sub(r"<[^>]+>", "", html)
        clean = clean.replace("&nbsp;", " ")
        clean = clean.replace("&lt;", "<")
        clean = clean.replace("&gt;", ">")
        clean = clean.replace("&amp;", "&")
        # Decode Unicode escapes
        clean = self._decode_unicode(clean)
        return clean.strip()

    def _strip_quotes(self, value: str) -> str:
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]
        return value

    def _looks_like_post(self, data: dict) -> bool:
        if ("blogInfo" in data or "blogName" in data) and (
            "publishTime" in data or "blogPageUrl" in data or "title" in data
        ):
            return True
        return False

    def _decode_unicode(self, text: str) -> str:
        """Decode Unicode escape sequences like \\u53EA"""
        try:
            # Handle \uXXXX patterns
            def replace_unicode(match):
                try:
                    return chr(int(match.group(1), 16))
                except:
                    return match.group(0)

            text = re.sub(r"\\u([0-9a-fA-F]{4})", replace_unicode, text)
            return text
        except:
            return text

    def _sanitize_text(self, text: str) -> str:
        if not text:
            return text
        text = self._decode_unicode(text)
        return self._SURROGATE_RE.sub("", text)

    def _sanitize_html(self, html: str) -> str:
        if not html:
            return html
        return self._SURROGATE_RE.sub("", html)

    def _extract_blog_name(self, url: str) -> str:
        if not url:
            return ""
        if url.startswith("//"):
            url = f"https:{url}"
        match = re.search(r"https?://([^/.]+)\\.lofter\\.com", url)
        return match.group(1) if match else ""

    def _extract_post_id(self, url: str) -> str:
        if not url:
            return ""
        match = re.search(r"/post/([^/?#]+)", url)
        if match:
            return match.group(1)
        match = re.search(r"/lpost/([^/?#]+)", url)
        if match:
            return match.group(1)
        return ""

    def _normalize_lofter_image_url(self, url: str) -> str:
        url = url.strip().replace("&amp;", "&")
        if url.startswith("//"):
            return f"https:{url}"
        return url

    def _proxy_lofter_images(self, html_content: str) -> str:
        """Replace Lofter image URLs with proxy URLs"""
        from urllib.parse import quote
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            # Fallback: only replace src attributes
            def replace_img_src(match):
                img_url = self._normalize_lofter_image_url(match.group(1))
                if any(domain in img_url for domain in self.LOFTER_IMAGE_DOMAINS):
                    proxy_url = f"/api/proxy/lofter?url={quote(img_url, safe='')}"
                    return f'src="{proxy_url}"'
                return match.group(0)

            result = re.sub(r'src="([^"]+)"', replace_img_src, html_content)
            result = re.sub(r"src='([^']+)'", replace_img_src, result)
            return result

        soup = BeautifulSoup(html_content, "html.parser")
        for img in soup.find_all("img"):
            raw_url = (
                img.get("large")
                or img.get("data-src")
                or img.get("data-original")
                or img.get("data-origin")
                or img.get("src")
            )
            parent = img.parent
            if parent and hasattr(parent, "attrs") and parent.attrs.get("bigimgsrc"):
                raw_url = parent.attrs.get("bigimgsrc") or raw_url
            if not raw_url:
                continue
            raw_url = self._normalize_lofter_image_url(raw_url)
            if any(domain in raw_url for domain in self.LOFTER_IMAGE_DOMAINS):
                img["src"] = f"/api/proxy/lofter?url={quote(raw_url, safe='')}"
            else:
                img["src"] = raw_url
            for attr in ["data-src", "data-original", "data-origin"]:
                if attr in img.attrs:
                    del img.attrs[attr]
            if "large" in img.attrs:
                del img.attrs["large"]

        return str(soup)

    async def get_detail(self, novel_id: str) -> Optional[Novel]:
        """Get novel details - for Lofter we redirect to source URL"""
        # Lofter posts don't have a detail API, we use the source_url directly
        # Return None to indicate detail should be fetched fresh
        return None

    async def get_chapters(self, novel_id: str) -> List[dict]:
        """Get chapter list - Lofter posts are typically single chapter"""
        return [{"chapter": 1, "title": "正文"}]

    async def get_chapter_content(self, novel_id: str, chapter: int) -> Optional[str]:
        """Get chapter content by fetching the blog post page"""
        cookie = self._get_cookie()
        if not cookie:
            return "<p>请配置 LOFTER_COOKIE 后重试</p>"

        # novel_id format: postId (e.g., "4cefde3_2hdf80424") or blogName_timestamp
        # We need to construct the post URL
        try:
            loop = asyncio.get_running_loop()
            content = await loop.run_in_executor(
                self._executor,
                self._fetch_post_content,
                novel_id,
                cookie,
            )
            return content
        except Exception as e:
            print(f"Lofter content fetch error: {e}")
            return f"<p>获取内容失败: {e}</p>"

    def _fetch_post_content(self, novel_id: str, cookie: str) -> str:
        """Fetch post content from Lofter"""
        try:
            # Construct post URL - novel_id format is blogName:postId
            if ":" in novel_id:
                parts = novel_id.split(":", 1)
                if len(parts) == 2:
                    blog_name, post_id = parts
                    # Standard post URL format
                    post_url = f"https://{blog_name}.lofter.com/post/{post_id}"
                else:
                    return "<p>无效的文章 ID 格式</p>"
            else:
                return f"<p>无效的文章 ID 格式: {novel_id}</p>"

            headers = {
                "Cookie": cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }

            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(post_url, headers=headers)

                if response.status_code != 200:
                    return f"<p>获取内容失败 (HTTP {response.status_code})</p><p><a href='{post_url}' target='_blank'>点击在新窗口查看原文</a></p>"

                # Get text and handle encoding issues (remove surrogates)
                html = response.text.encode("utf-8", errors="surrogatepass").decode(
                    "utf-8", errors="replace"
                )

                # Prefer DOM-based extraction for stability
                try:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(html, "html.parser")
                    container = (
                        soup.select_one("div.postwrapper .content")
                        or soup.select_one("div#postwrapper .content")
                        or soup.select_one("div.post .content")
                    )
                    if container:
                        content = str(container)
                        content = self._proxy_lofter_images(content)
                        return self._sanitize_html(content)
                except ImportError:
                    pass

                # Try to find the post content with Lofter-specific patterns
                content_parts = []

                # Pattern 1: Extract images from bigimgsrc attribute (Lofter's image viewer)
                big_imgs = re.findall(
                    r'bigimgsrc=["\']([^"\']+)["\']', html, re.IGNORECASE
                )
                for img_url in big_imgs:
                    img_url = self._normalize_lofter_image_url(img_url)
                    content_parts.append(
                        f'<img src="{img_url}" style="max-width:100%;"/>'
                    )

                # Pattern 2: Extract text from div.text
                text_matches = re.findall(
                    r'<div[^>]*class="text"[^>]*>(.*?)</div>',
                    html,
                    re.DOTALL | re.IGNORECASE,
                )
                for text_content in text_matches:
                    cleaned = re.sub(r"<[^>]+>", "", text_content).strip()
                    if cleaned:
                        if "<p" in text_content:
                            content_parts.append(text_content)
                        else:
                            content_parts.append(f"<p>{text_content}</p>")

                # Pattern 3: Fallback - div.content
                if not content_parts:
                    content_match = re.search(
                        r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
                        html,
                        re.DOTALL | re.IGNORECASE,
                    )
                    if content_match:
                        content_parts.append(content_match.group(1))

                # Pattern 4: Fallback - any img with imglf in src
                if not content_parts:
                    imgs = re.findall(
                        r'<img[^>]+src=["\']([^"\']*(?:imglf|lf127)[^"\']*)["\'][^>]*>',
                        html,
                        re.IGNORECASE,
                    )
                    for img in imgs:
                        content_parts.append(
                            f'<img src="{img}" style="max-width:100%;"/>'
                        )

                if content_parts:
                    content = "\n".join(content_parts)
                    # Replace Lofter image URLs with proxy URLs
                    content = self._proxy_lofter_images(content)
                    return self._sanitize_html(content)

                # Fallback: provide link to view on Lofter
                return self._sanitize_html(
                    f"<p>无法解析文章内容</p><p><a href='{post_url}' target='_blank'>点击在新窗口查看原文</a></p>"
                )

        except Exception as e:
            print(f"Lofter fetch error: {e}")
            return self._sanitize_html(f"<p>获取内容失败: {e}</p>")
