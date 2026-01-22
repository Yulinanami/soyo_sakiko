"""AO3 数据整理"""

from typing import Any, List, Optional
from bs4 import BeautifulSoup
from app.adapters.utils import to_iso_date
from app.schemas.novel import Novel, NovelSource


def map_sort(sort_by: str) -> str:
    """转换排序名称"""
    mapping = {
        "date": "revised_at",
        "kudos": "kudos_count",
        "hits": "hits",
        "wordCount": "word_count",
    }
    return mapping.get(sort_by, "revised_at")


def parse_search_results_html(html: str) -> List[Novel]:
    """解析 AO3 搜索结果 HTML"""
    if not html or html == "EMPTY":
        return []

    soup = BeautifulSoup(html, "lxml")
    works = soup.select("li.work.blurb.group")
    novels = []

    for work in works:
        try:
            # ID
            work_id = work.get("id", "").replace("work_", "")
            if not work_id:
                continue

            # Title & Link
            heading = work.select_one('h4.heading a[href^="/works/"]')
            title = heading.get_text(strip=True) if heading else "Untitled"
            source_url = f"https://archiveofourown.org/works/{work_id}"

            # Author
            author_el = work.select_one('a[rel="author"]')
            author = author_el.get_text(strip=True) if author_el else "Anonymous"
            author_url = (
                f"https://archiveofourown.org{author_el.get('href')}"
                if author_el
                else None
            )

            # Summary
            summary_el = work.select_one("blockquote.userstuff.summary")
            summary = summary_el.get_text(strip=True) if summary_el else ""

            # Tags
            tags = []
            tag_els = work.select(
                "li.characters a.tag, li.relationships a.tag, li.freeforms a.tag"
            )
            for tel in tag_els:
                tags.append(tel.get_text(strip=True))

            # Stats
            stats_dl = work.select_one("dl.stats")
            word_count = 0
            chapter_count = 1
            kudos = 0
            hits = 0

            if stats_dl:
                # Words
                words_el = stats_dl.select_one("dd.words")
                if words_el:
                    try:
                        word_count = int(words_el.get_text(strip=True).replace(",", ""))
                    except ValueError:
                        word_count = 0

                # Chapters
                chapters_el = stats_dl.select_one("dd.chapters")
                if chapters_el:
                    text = chapters_el.get_text(strip=True)
                    if "/" in text:
                        try:
                            chapter_count = int(text.split("/")[0])
                        except ValueError:
                            chapter_count = 1

                # Kudos
                kudos_el = stats_dl.select_one("dd.kudos")
                if kudos_el:
                    try:
                        kudos = int(kudos_el.get_text(strip=True).replace(",", ""))
                    except ValueError:
                        kudos = 0

                # Hits
                hits_el = stats_dl.select_one("dd.hits")
                if hits_el:
                    try:
                        hits = int(hits_el.get_text(strip=True).replace(",", ""))
                    except ValueError:
                        hits = 0

            # Date
            date_el = work.select_one("p.datetime")
            updated_at = to_iso_date(date_el.get_text(strip=True)) if date_el else None

            # Rating
            rating_el = work.select_one("span.rating")
            rating = rating_el.get_text(strip=True) if rating_el else None

            # Completion status
            status_el = work.select_one("ul.required-tags span.complete-yes")
            is_complete = status_el is not None

            novels.append(
                Novel(
                    id=work_id,
                    source=NovelSource.AO3,
                    title=title,
                    author=author,
                    author_url=author_url,
                    summary=summary,
                    tags=tags,
                    rating=rating,
                    word_count=word_count,
                    chapter_count=chapter_count,
                    kudos=kudos,
                    hits=hits,
                    published_at=updated_at or "",  # 列表页通常只有更新时间
                    updated_at=updated_at,
                    source_url=source_url,
                    is_complete=is_complete,
                )
            )
        except Exception as e:
            logger.warning(f"AO3: Failed to parse a work blurb: {e}")
            continue

    return novels


def parse_work_detail_html(html: str, work_id: str) -> Optional[Novel]:
    """从详情页 HTML 解析作品信息"""
    if not html:
        return None

    soup = BeautifulSoup(html, "lxml")

    # Title
    title_el = soup.select_one("h2.title.heading")
    title = title_el.get_text(strip=True) if title_el else "Untitled"

    # Author
    author_el = soup.select_one('a[rel="author"]')
    author = author_el.get_text(strip=True) if author_el else "Anonymous"
    author_url = (
        f"https://archiveofourown.org{author_el.get('href')}" if author_el else None
    )

    # Summary
    summary_el = soup.select_one(".summary.module blockquote.userstuff")
    summary = summary_el.get_text(strip=True) if summary_el else ""

    # Tags
    tags = []
    for tag_el in soup.select("dd.tag a.tag"):
        tags.append(tag_el.get_text(strip=True))

    # Stats
    word_count = 0
    chapter_count = 1
    kudos = 0
    hits = 0

    words_el = soup.select_one("dd.words")
    if words_el:
        try:
            word_count = int(words_el.get_text(strip=True).replace(",", ""))
        except:
            pass

    chapters_el = soup.select_one("dd.chapters")
    if chapters_el:
        try:
            chapter_count = int(chapters_el.get_text(strip=True).split("/")[0])
        except:
            pass

    kudos_el = soup.select_one("dd.kudos")
    if kudos_el:
        try:
            kudos = int(kudos_el.get_text(strip=True).replace(",", ""))
        except:
            pass

    hits_el = soup.select_one("dd.hits")
    if hits_el:
        try:
            hits = int(hits_el.get_text(strip=True).replace(",", ""))
        except:
            pass

    # Completion status
    is_complete = False
    status_el = soup.select_one("dd.chapters")
    if status_el:
        status_text = status_el.get_text(strip=True)
        if "/" in status_text:
            parts = status_text.split("/")
            if parts[0] == parts[1]:
                is_complete = True

    return Novel(
        id=work_id,
        source=NovelSource.AO3,
        title=title,
        author=author,
        author_url=author_url,
        summary=summary,
        tags=tags,
        word_count=word_count,
        chapter_count=chapter_count,
        kudos=kudos,
        hits=hits,
        source_url=f"https://archiveofourown.org/works/{work_id}",
        is_complete=is_complete,
        published_at="",
        updated_at=None,
    )
