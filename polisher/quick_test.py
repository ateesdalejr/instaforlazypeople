#!/usr/bin/env python3
import requests
import json

url = "http://localhost:8000/captions"

payload = {
    "script": "Stop waiting for perfect conditions. The truth? They'll never come. Every successful person you admire started exactly where you are right now - uncertain, unprepared, and afraid. The only difference? They started anyway. Your dreams don't have an expiration date, but your excuses do. Take action today.",
    "video_url": "https://www.instagram.com/reel/example-motivational/"
}

print("=" * 80)
print("TESTING CAPTION GENERATION END-TO-END")
print("=" * 80)
print(f"\n📝 Script: {payload['script'][:100]}...")
print(f"🎥 Video URL: {payload['video_url']}\n")
print("🚀 Sending POST request...\n")

try:
    response = requests.post(url, json=payload, timeout=60)

    if response.status_code == 200:
        result = response.json()

        print("✅ SUCCESS!\n")
        print("📊 RESPONSE:")
        print(f"├─ Video URL: {result.get('video', 'N/A')}")
        print(f"└─ Caption Generated: {'Yes' if result.get('caption') else 'No'}\n")

        print("📱 GENERATED CAPTION:")
        print("─" * 80)
        print(result.get('caption', 'No caption'))
        print("─" * 80)

        if 'metadata' in result:
            print("\n🔍 METADATA:")
            metadata = result['metadata']
            print(f"├─ Hook: {metadata.get('hook', 'N/A')}")
            print(f"├─ CTA: {metadata.get('cta', 'N/A')}")
            print(f"├─ Total Length: {metadata.get('total_length', 'N/A')} chars")
            print(f"├─ Line Count: {metadata.get('line_count', 'N/A')}")
            print(f"└─ Hashtags: {len(metadata.get('hashtags', []))} tags")

    else:
        print(f"❌ FAILED: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "=" * 80)
