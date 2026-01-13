"""
Test script for Pixiv adapter
Run with: .venv\Scripts\python.exe test_pixiv.py
"""

import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()


def test_pixiv():
    print("🔍 Testing Pixiv API connection...")
    print("-" * 50)

    # Check token
    token = os.getenv("PIXIV_REFRESH_TOKEN")
    if not token:
        print("❌ PIXIV_REFRESH_TOKEN not found in environment")
        return
    print(f"✅ Token found: {token[:20]}...")

    # Try to import pixivpy3
    try:
        from pixivpy3 import AppPixivAPI

        print("✅ pixivpy3 imported successfully")
    except ImportError:
        print("❌ pixivpy3 not installed. Run: pip install pixivpy3")
        return

    # Try to authenticate
    print("\n🔐 Authenticating...")
    try:
        api = AppPixivAPI()
        api.auth(refresh_token=token)
        print("✅ Authentication successful!")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

    # Test search
    print("\n📚 Searching for 素祥 novels...")
    try:
        result = api.search_novel(
            word="素祥",
            sort="date_desc",
            search_target="partial_match_for_tags",
        )

        novels = result.get("novels", [])
        print(f"✅ Found {len(novels)} results!")

        if novels:
            print("\n📖 Top 3 Results:")
            print("-" * 50)
            for i, novel in enumerate(novels[:3], 1):
                print(f"\n{i}. {novel.get('title', 'Unknown')}")
                print(f"   Author: {novel.get('user', {}).get('name', 'Unknown')}")
                print(f"   Words: {novel.get('text_length', 0)}")
                print(f"   Bookmarks: {novel.get('total_bookmarks', 0)}")
        else:
            print("⚠️ No novels found with this tag. Try different tags.")

    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 50)
    print("✅ Pixiv API test completed!")


if __name__ == "__main__":
    test_pixiv()
