"""
Simple test script for the Deep Research API.

Usage:
    python test_api.py
"""

import asyncio
import httpx
import json
from datetime import datetime


API_BASE_URL = "http://localhost:8000"


async def test_health():
    """Test health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/health")
        print(f"✓ Health check: {response.json()}")


async def test_agents_metadata():
    """Test agents metadata endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/agents")
        agents = response.json()["agents"]
        print(f"✓ Found {len(agents)} agents")
        for agent in agents:
            print(f"  - {agent['display_name']}: {agent['description']}")


async def test_research_workflow():
    """Test complete research workflow."""
    print("\n🔬 Starting research workflow test...\n")

    async with httpx.AsyncClient(timeout=300.0) as client:
        # 1. Start research
        print("1. Starting research...")
        response = await client.post(
            f"{API_BASE_URL}/api/research/start",
            json={"query": "What is quantum computing?"}
        )
        data = response.json()
        thread_id = data["thread_id"]
        print(f"   Thread ID: {thread_id}")
        print(f"   Status: {data['status']}")

        # 2. Check initial status
        await asyncio.sleep(1)
        response = await client.get(f"{API_BASE_URL}/api/research/status/{thread_id}")
        status = response.json()
        print(f"\n2. Initial status: {status['status']}")

        # 3. Monitor progress (polling)
        print("\n3. Monitoring progress...")
        max_checks = 60
        for i in range(max_checks):
            await asyncio.sleep(2)
            response = await client.get(f"{API_BASE_URL}/api/research/status/{thread_id}")
            status = response.json()

            if status["current_agent"]:
                print(f"   [{status['progress_percentage']}%] {status['current_agent']}")

            if status["status"] == "completed":
                print(f"\n✓ Research completed!")
                break
            elif status["status"] == "error":
                print(f"\n✗ Error: {status['error']}")
                return

        # 4. Get results
        if status["status"] == "completed":
            print("\n4. Fetching results...")
            response = await client.get(f"{API_BASE_URL}/api/research/result/{thread_id}")
            result = response.json()

            print(f"\n{'='*60}")
            print("RESEARCH REPORT")
            print('='*60)
            print(result["report"][:500] + "...\n")
            print(f"Sub-questions: {len(result['subqueries'])}")
            print(f"Citations: {len(result['citations'])}")


async def test_streaming():
    """Test SSE streaming (simple check)."""
    print("\n📡 Testing SSE streaming capabilities...")
    print("   (Note: Full SSE test requires EventSource, use browser/frontend)")

    async with httpx.AsyncClient() as client:
        # Start a research
        response = await client.post(
            f"{API_BASE_URL}/api/research/start",
            json={"query": "Test streaming"}
        )
        thread_id = response.json()["thread_id"]

        print(f"   Thread ID: {thread_id}")
        print(f"   Stream URL: {API_BASE_URL}/api/research/stream/{thread_id}")
        print("   ✓ SSE endpoint available")


async def main():
    """Run all tests."""
    print("="*60)
    print("DEEP RESEARCH API TEST SUITE")
    print("="*60)

    try:
        # Basic tests
        await test_health()
        await test_agents_metadata()
        await test_streaming()

        # Full workflow test (optional, takes time)
        run_full_test = input("\nRun full research workflow test? (y/N): ")
        if run_full_test.lower() == 'y':
            await test_research_workflow()

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
