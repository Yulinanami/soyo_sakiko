"""
Lofter Adapter
Uses DWR (Direct Web Remoting) API to search for novels by tag
"""

import asyncio
import re
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

        # Use first tag for search
        search_tags = list(set(tags + self.SOYOSAKI_TAGS))
        search_tag = search_tags[0] if search_tags else "素祥"

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
        novels = await loop.run_in_executor(
            self._executor,
            self._search_sync,
            search_tag,
            ranking_type,
            page_size,
            offset,
            exclude_tags,
            cookie,
        )

        return novels

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

            # Build DWR request body
            body = {
                "callCount": "1",
                "scriptSessionId": "${scriptSessionId}187",
                "httpSessionId": "",
                "c0-scriptName": "TagBean",
                "c0-methodName": "search",
                "c0-id": "0",
                "c0-param0": f"string:{tag}",  # Raw tag, not encoded
                "c0-param1": "number:0",
                "c0-param2": "string:",
                "c0-param3": f"string:{ranking_type}",
                "c0-param4": "boolean:false",
                "c0-param5": "number:0",
                "c0-param6": f"number:{page_size}",
                "c0-param7": f"number:{offset}",
                "c0-param8": "number:0",
                "batchId": "493053",
            }

            headers = {
                "Referer": f"https://www.lofter.com/tag/{encoded_tag}",
                "Cookie": cookie,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Origin": "https://www.lofter.com",
            }

            # Convert body to URL encoded format and encode as bytes
            body_str = "&".join(f"{k}={v}" for k, v in body.items())
            body_bytes = body_str.encode("utf-8")

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
            # DWR returns JavaScript code, we need to extract data using regex
            # Pattern to match post objects
            post_pattern = re.compile(r"s(\d+)\.post=s(\d+);")

            # Extract all assignment patterns
            assignments = {}

            # Match variable assignments like s0.xxx=yyy
            var_pattern = re.compile(r"s(\d+)\.(\w+)=([^;]+);")
            for match in var_pattern.finditer(response_text):
                var_id, prop, value = match.groups()
                key = f"s{var_id}"
                if key not in assignments:
                    assignments[key] = {}
                assignments[key][prop] = value.strip("\"'")

            # Match string values
            str_pattern = re.compile(r's(\d+)\.(\w+)="([^"]*)"')
            for match in str_pattern.finditer(response_text):
                var_id, prop, value = match.groups()
                key = f"s{var_id}"
                if key not in assignments:
                    assignments[key] = {}
                assignments[key][prop] = value

            # Find posts and their properties
            post_refs = re.findall(r"s(\d+)\.post=s(\d+);", response_text)
            print(f"📊 Lofter DWR: found {len(post_refs)} post references")

            parsed_count = 0
            skipped_no_url = 0
            skipped_no_blog = 0

            for entry_id, post_id in post_refs:
                entry_key = f"s{entry_id}"
                post_key = f"s{post_id}"

                if post_key not in assignments:
                    continue

                post = assignments[post_key]

                # Get title and decode Unicode escapes
                title = post.get("title", "")
                title = self._decode_unicode(title) if title else ""
                if not title:
                    # Try to get from digest
                    digest = post.get("digest", "")
                    title = self._clean_html(digest)[:50] if digest else "无标题"

                # Check exclude tags
                if any(pattern in title for pattern in exclude_tags):
                    continue

                # Get blog info
                blog_info_ref = post.get("blogInfo", "")
                blog_info = {}
                if blog_info_ref.startswith("s"):
                    blog_info = assignments.get(blog_info_ref, {})

                author = blog_info.get("blogNickName", "Unknown")
                blog_name = blog_info.get("blogName", "")

                # Skip if no blog name (can't construct URL)
                if not blog_name:
                    skipped_no_blog += 1
                    continue

                # Get other properties
                publish_time = post.get("publishTime", "")
                blog_page_url = post.get("blogPageUrl", "")

                # If no blogPageUrl, try to construct from other data
                if not blog_page_url:
                    skipped_no_url += 1
                    # Try to use blog_name and publishTime as fallback
                    if blog_name and publish_time:
                        blog_page_url = (
                            f"https://{blog_name}.lofter.com/post/{publish_time}"
                        )

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

                # Get hot/bookmark count
                hot = post.get("hot", "0")
                try:
                    kudos = int(hot) if hot.isdigit() else 0
                except:
                    kudos = 0

                # Get digest as summary
                digest = post.get("digest", "")
                summary = self._clean_html(digest) if digest else "暂无简介"

                # Extract post ID from URL and combine with blog_name
                # URL format: https://blogName.lofter.com/post/postId
                post_id_match = re.search(r"post/([a-f0-9]+_[a-f0-9]+)", blog_page_url)
                post_id = post_id_match.group(1) if post_id_match else publish_time
                # Store as blogName:postId so we can reconstruct the URL later
                novel_id = f"{blog_name}:{post_id}" if blog_name else post_id

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

    def _proxy_lofter_images(self, html_content: str) -> str:
        """Replace Lofter image URLs with proxy URLs"""
        from urllib.parse import quote

        # Pattern to match image URLs in src attributes
        # Lofter images come from various domains
        lofter_domains = [
            "lf127.net",
            "126.net",
            "lofter.com",
            "imglf",
            "nos.netease.com",
            "nosdn.127.net",
        ]

        def replace_img_src(match):
            img_url = match.group(1)
            if any(domain in img_url for domain in lofter_domains):
                # Replace with proxy URL
                proxy_url = f"/api/proxy/lofter?url={quote(img_url, safe='')}"
                return f'src="{proxy_url}"'
            return match.group(0)

        # Replace src="..." patterns
        result = re.sub(r'src="([^"]+)"', replace_img_src, html_content)
        result = re.sub(r"src='([^']+)'", replace_img_src, result)

        return result

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

                # Try to find the post content with Lofter-specific patterns
                content_parts = []

                # Pattern 1: Extract images from bigimgsrc attribute (Lofter's image viewer)
                # Format: <a ... bigimgsrc="https://imglf3.lf127.net/..." ...>
                big_imgs = re.findall(
                    r'bigimgsrc=["\']([^"\']+)["\']', html, re.IGNORECASE
                )
                for img_url in big_imgs:
                    # Decode HTML entities
                    img_url = img_url.replace("&amp;", "&")
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
                    # Skip empty text divs
                    cleaned = re.sub(r"<[^>]+>", "", text_content).strip()
                    if cleaned:
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
                    return content

                # Fallback: provide link to view on Lofter
                return f"<p>无法解析文章内容</p><p><a href='{post_url}' target='_blank'>点击在新窗口查看原文</a></p>"

        except Exception as e:
            print(f"Lofter fetch error: {e}")
            return f"<p>获取内容失败: {e}</p>"
