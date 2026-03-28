"""
Test suite for Caption Agent with sample Pydantic input models
Run with: python test_caption_agent.py
"""

import asyncio
import os
from caption_models import CaptionInput
from caption_agent import CaptionAgent, generate_instagram_caption


# Sample Test Data using Pydantic Models
class TestCaptionSamples:
    """Collection of sample inputs for testing the caption agent"""

    @staticmethod
    def fitness_motivation_script() -> CaptionInput:
        """Sample: Fitness motivation content"""
        return CaptionInput(
            script="""
            Hey everyone! Today I want to talk about consistency.
            You know, people always ask me what's the secret to getting fit.
            And I always tell them - it's not about being perfect, it's about showing up.
            Even on days when you don't feel like it, even when you're tired, even when you're busy.
            That's what separates those who achieve their goals from those who don't.
            So if you're watching this and you've been putting off your workout - this is your sign.
            Get up, move your body, and thank yourself later.
            Remember, every small step counts. Let's get it!
            """,
            video_url="https://storage.googleapis.com/example-bucket/fitness-video-001.mp4",
            target_audience="fitness enthusiasts, beginners",
            tone="motivational"
        )

    @staticmethod
    def cooking_tutorial_script() -> CaptionInput:
        """Sample: Cooking tutorial content"""
        return CaptionInput(
            script="""
            Welcome to my kitchen! Today we're making the easiest pasta dish you'll ever make.
            I'm talking 15 minutes, 5 ingredients, and it tastes like you spent hours on it.
            First, we're going to boil our pasta - just regular spaghetti works great.
            While that's cooking, grab some garlic, olive oil, red pepper flakes, and parmesan.
            The secret is to save some pasta water - trust me on this one.
            Once your pasta is al dente, drain it but save a cup of that starchy water.
            Heat up your olive oil with the garlic and red pepper flakes until fragrant.
            Toss in your pasta, add a splash of that pasta water, and finish with parmesan.
            That's it! Restaurant quality pasta at home. You've got this!
            """,
            video_url="https://storage.googleapis.com/example-bucket/pasta-recipe-042.mp4",
            target_audience="home cooks, busy professionals",
            tone="friendly"
        )

    @staticmethod
    def tech_tutorial_script() -> CaptionInput:
        """Sample: Tech tutorial content"""
        return CaptionInput(
            script="""
            Alright, let me show you a productivity hack that changed my life.
            If you're using multiple monitors and constantly losing your windows, this is for you.
            I'm going to teach you three keyboard shortcuts that will make you 10x faster.
            First up: Command + Tab on Mac or Alt + Tab on Windows - switch between apps instantly.
            Second: Command + ~ to cycle through windows of the same app.
            And third: Mission Control or Task View to see everything at once.
            Once you master these, you'll wonder how you ever lived without them.
            Try it right now and let me know which one blows your mind the most!
            """,
            video_url="https://storage.googleapis.com/example-bucket/productivity-tips-007.mp4",
            target_audience="professionals, students, remote workers",
            tone="educational"
        )

    @staticmethod
    def travel_vlog_script() -> CaptionInput:
        """Sample: Travel vlog content"""
        return CaptionInput(
            script="""
            I can't believe I'm finally here in Bali!
            This place has been on my bucket list for years and it's even more beautiful than I imagined.
            Today I'm taking you to this hidden waterfall that barely anyone knows about.
            The hike is a bit challenging - about 45 minutes through the jungle - but so worth it.
            Look at this view! The water is crystal clear and there's literally no one else here.
            This is what I love about traveling - finding these secret spots off the beaten path.
            If you're planning a trip to Bali, save this location because you need to add it to your itinerary.
            Trust me, you won't regret it. Where should I explore next?
            """,
            video_url="https://storage.googleapis.com/example-bucket/bali-waterfall-023.mp4",
            target_audience="travelers, adventure seekers",
            tone="enthusiastic"
        )

    @staticmethod
    def business_tips_script() -> CaptionInput:
        """Sample: Business advice content"""
        return CaptionInput(
            script="""
            Let's talk about something nobody tells you when you start a business.
            You will fail. Multiple times. And that's completely okay.
            I've been an entrepreneur for 8 years now, and I've failed more times than I can count.
            But here's what I learned: every failure taught me something invaluable.
            The key is to fail fast, learn quickly, and pivot when necessary.
            Don't be afraid to test new ideas, even if they seem crazy.
            Some of my biggest successes came from ideas people said would never work.
            So if you're sitting on a business idea right now, scared to take the leap - do it.
            The worst that can happen is you learn something valuable. The best? You change your life.
            """,
            video_url="https://storage.googleapis.com/example-bucket/business-advice-019.mp4",
            target_audience="entrepreneurs, business owners, aspiring founders",
            tone="inspiring"
        )

    @staticmethod
    def minimal_script() -> CaptionInput:
        """Sample: Very short script for testing"""
        return CaptionInput(
            script="Quick tip: Start your day with water before coffee. Your body will thank you!",
            video_url=None,
            tone="casual"
        )


async def test_single_caption(sample_input: CaptionInput, test_name: str):
    """Test caption generation with a single sample input"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    print(f"\nInput Script:\n{sample_input.script[:200]}...")
    print(f"\nTarget Audience: {sample_input.target_audience}")
    print(f"Tone: {sample_input.tone}")
    print("\n" + "-"*80)
    print("Generating caption...")
    print("-"*80 + "\n")

    try:
        # Generate caption
        result = await generate_instagram_caption(
            script=sample_input.script,
            video_url=sample_input.video_url
        )

        if result.success:
            print("✅ SUCCESS!\n")
            print("GENERATED CAPTION:")
            print("="*80)
            print(result.caption)
            print("="*80)
            print(f"\nMetadata:")
            print(f"  - Total Length: {result.metadata.get('total_length')} characters")
            print(f"  - Line Count: {result.metadata.get('line_count')} lines")
            print(f"  - Hook: {result.metadata.get('hook')}")
            print(f"  - CTA: {result.metadata.get('cta')}")
            print(f"  - Hashtags: {len(result.metadata.get('hashtags', []))} tags")

            if result.metadata.get('processing_errors'):
                print(f"\n⚠️  Processing Warnings: {result.metadata['processing_errors']}")
        else:
            print(f"❌ FAILED: {result.error_message}")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

    print("\n")


async def run_all_tests():
    """Run all test samples"""
    print("\n" + "🚀 " + "="*76 + " 🚀")
    print("  CAPTION AGENT TEST SUITE")
    print("🚀 " + "="*76 + " 🚀\n")

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'\n")
        return

    samples = TestCaptionSamples()

    test_cases = [
        (samples.fitness_motivation_script(), "Fitness Motivation Video"),
        (samples.cooking_tutorial_script(), "Cooking Tutorial Video"),
        (samples.tech_tutorial_script(), "Tech Tutorial Video"),
        (samples.travel_vlog_script(), "Travel Vlog Video"),
        (samples.business_tips_script(), "Business Advice Video"),
        (samples.minimal_script(), "Minimal Script Test"),
    ]

    for sample_input, test_name in test_cases:
        await test_single_caption(sample_input, test_name)
        await asyncio.sleep(1)  # Brief pause between tests

    print("\n" + "🎉 " + "="*76 + " 🎉")
    print("  ALL TESTS COMPLETED!")
    print("🎉 " + "="*76 + " 🎉\n")


async def run_single_test(test_name: str = "fitness"):
    """Run a single test by name"""
    samples = TestCaptionSamples()

    test_map = {
        "fitness": (samples.fitness_motivation_script(), "Fitness Motivation Video"),
        "cooking": (samples.cooking_tutorial_script(), "Cooking Tutorial Video"),
        "tech": (samples.tech_tutorial_script(), "Tech Tutorial Video"),
        "travel": (samples.travel_vlog_script(), "Travel Vlog Video"),
        "business": (samples.business_tips_script(), "Business Advice Video"),
        "minimal": (samples.minimal_script(), "Minimal Script Test"),
    }

    if test_name not in test_map:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_map.keys())}")
        return

    sample_input, display_name = test_map[test_name]
    await test_single_caption(sample_input, display_name)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Run single test
        test_name = sys.argv[1].lower()
        asyncio.run(run_single_test(test_name))
    else:
        # Run all tests
        asyncio.run(run_all_tests())
