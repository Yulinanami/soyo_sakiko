"""
Test script for AO3 adapter
Run with: python test_ao3.py
"""

import asyncio


async def test_ao3():
    print("🔍 Testing AO3 API connection...")
    print("-" * 50)

    # Try to import AO3
    try:
        import AO3

        print("✅ ao3-api library imported successfully")
    except ImportError:
        print("❌ ao3-api not installed. Run: pip install ao3-api")
        return

    # Test search
    print("\n📚 Searching for SoyoSaki fanfics...")
    try:
        search = AO3.Search(
            any_field='"Nagasaki Soyo/Toyokawa Sakiko" OR "素祥"',
            sort_column="revised_at",
            sort_direction="desc",
        )
        search.update()

        print(f"✅ Found {len(search.results)} results!")

        if search.results:
            print("\n📖 Top 5 Results:")
            print("-" * 50)
            for i, work in enumerate(search.results[:5], 1):
                print(f"\n{i}. {work.title}")
                print(
                    f"   Author: {work.authors[0].username if work.authors else 'Anonymous'}"
                )
                print(f"   Words: {work.words}")
                print(f"   Kudos: {work.kudos}")
                print(f"   URL: {work.url}")
        else:
            print("⚠️ No results found. Try different tags.")

    except Exception as e:
        print(f"❌ Search error: {e}")
        return

    print("\n" + "=" * 50)
    print("✅ AO3 API test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_ao3())
