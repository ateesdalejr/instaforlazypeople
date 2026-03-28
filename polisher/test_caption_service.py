"""
Test script for caption generation service
Tests the POST /captions endpoint with real-world data
"""
import requests
import json
import time

# Test data: Real-world Instagram video script examples
TEST_CASES = [
    {
        "name": "Motivational Content",
        "script": """
        You know what separates dreamers from achievers? Action.

        Every single day, you have 24 hours. The same 24 hours as everyone else.

        Stop waiting for the perfect moment. Stop waiting to feel ready.

        The truth is, you'll never feel 100% ready. And that's okay.

        Start where you are. Use what you have. Do what you can.

        Because five years from now, you'll wish you started today.

        So what are you waiting for?
        """,
        "video_url": "https://www.instagram.com/p/example-motivational-video/",
        "expected_elements": ["hook", "call-to-action", "hashtags", "emojis"]
    },
    {
        "name": "Educational Tech Content",
        "script": """
        Here's why your website is slow - and how to fix it in under 5 minutes.

        Most people don't realize that unoptimized images can slow down your site by up to 80%.

        Here's the fix:
        1. Compress your images before uploading
        2. Use modern formats like WebP
        3. Implement lazy loading

        I've seen sites go from 8 seconds to 2 seconds load time just by doing this.

        Your bounce rate will thank you. Your users will thank you. Your revenue will thank you.

        Try it today and watch your analytics change overnight.
        """,
        "video_url": "https://www.youtube.com/watch?v=example-tech-tutorial",
        "expected_elements": ["hook", "educational value", "actionable tips", "hashtags"]
    },
    {
        "name": "Behind-the-Scenes Content",
        "script": """
        People always ask me: 'How do you come up with content ideas?'

        Here's my honest answer - I don't force it.

        I carry a notebook everywhere. When inspiration hits, I write it down immediately.

        Could be at the gym, in the shower, during a conversation with a friend.

        The best ideas come when you're not actively searching for them.

        Then once a week, I sit down and turn those random notes into actual content.

        It's not complicated. It's just about being present and paying attention.
        """,
        "video_url": "https://www.tiktok.com/@creator/video/example-bts",
        "expected_elements": ["personal story", "relatability", "practical advice"]
    }
]


def test_caption_endpoint(base_url: str = "http://localhost:8000"):
    """Test the POST /captions endpoint"""

    print("=" * 80)
    print("CAPTION GENERATION SERVICE TEST")
    print("=" * 80)
    print()

    # Health check first
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Service health check: {health_response.json()}")
        print()
    except requests.exceptions.RequestException as e:
        print(f"❌ Service is not running. Error: {e}")
        print(f"💡 Start the service with: python main.py")
        return

    # Test each case
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST CASE {i}: {test_case['name']}")
        print(f"{'=' * 80}\n")

        print(f"📝 Script Preview:")
        print(f"{test_case['script'][:200]}...\n")

        print(f"🎥 Video URL: {test_case['video_url']}\n")

        # Prepare request
        payload = {
            "script": test_case['script'],
            "video_url": test_case['video_url']
        }

        print("🚀 Sending POST request to /captions...")
        start_time = time.time()

        try:
            response = requests.post(
                f"{base_url}/captions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )

            elapsed_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()

                print(f"✅ Success! (Generated in {elapsed_time:.2f}s)\n")

                # Display results
                print("📊 RESPONSE:")
                print(f"├─ Video URL: {result.get('video', 'N/A')}")
                print(f"└─ Caption Generated: {'Yes' if result.get('caption') else 'No'}\n")

                print("📱 GENERATED CAPTION:")
                print("─" * 80)
                print(result.get('caption', 'No caption generated'))
                print("─" * 80)
                print()

                # Quality checks
                caption = result.get('caption', '')
                print("🔍 QUALITY CHECKS:")

                checks = {
                    "Has hook/opening": len(caption.split('\n')[0]) < 100 if caption else False,
                    "Includes emojis": any(char in caption for char in ['💪', '🔥', '✨', '💡', '🎯', '💬', '❤️', '👉', '📱', '⚡']),
                    "Has hashtags": '#' in caption,
                    "Multiple paragraphs": caption.count('\n\n') >= 1 if caption else False,
                    "Length appropriate": 150 < len(caption) < 2200,  # Instagram caption limits
                    "Video URL preserved": result.get('video') == test_case['video_url']
                }

                for check_name, passed in checks.items():
                    status = "✅" if passed else "⚠️"
                    print(f"  {status} {check_name}")

                print()

            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")

        except requests.exceptions.Timeout:
            print("❌ Request timed out (>60s)")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")

        print()

    print("=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    # You can customize the base URL if running on a different port
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    test_caption_endpoint(base_url)
