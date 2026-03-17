"""
Quick test script — run this to validate your agent works
before connecting the frontend UI.

Usage:
    python test_agent.py
"""

import asyncio
import json
import httpx

BASE_URL = "http://localhost:8000"

TEST_PROFILE = {
    "org_type": "Enterprise (1000+ employees)",
    "regulatory": "SOC 2 / ISO 27001",
    "maturity": "defined",
    "objectives": [
        "Cloud-first migration (on-prem to cloud)",
        "Modernization of existing on-prem / hybrid infrastructure"
    ],
    "context": "Migrating 40 legacy Java apps to AWS. Currently on VMware. No formal security architecture practice yet."
}

async def test_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/health")
        print("Health check:", r.json())

async def test_analyze():
    print("\nSending org profile to agent...\n")
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{BASE_URL}/analyze", json=TEST_PROFILE)
        if r.status_code != 200:
            print("ERROR:", r.status_code, r.text)
            return
        
        data = r.json()
        
        print("=" * 60)
        print("AGENT ANALYSIS")
        print("=" * 60)
        print(data["analysis_text"])
        
        print("\n" + "=" * 60)
        print("FRAMEWORK BLEND")
        print("=" * 60)
        blend = data["mapping"].get("framework_blend", {})
        print("  Primary:   ", blend.get("primary", []))
        print("  Supporting:", blend.get("supporting", []))
        print("  Excluded:  ", blend.get("excluded", []))
        
        print("\n" + "=" * 60)
        print("MAPPING TABLE")
        print("=" * 60)
        rows = data["mapping"].get("rows", [])
        for row in rows:
            print(f"\n[{row.get('priority','?')}] {row['requirement']} ({row['domain']})")
            for fw, detail in row["frameworks"].items():
                if detail["fit"] != "none":
                    print(f"      {fw:12} → {detail['fit']:10} {detail['artifact']}")
        
        print(f"\n Total requirements mapped: {len(rows)}")
        print("\nSave full JSON? (raw output below)")
        print(json.dumps(data["mapping"], indent=2)[:500] + "...")

async def main():
    try:
        await test_health()
        await test_analyze()
    except httpx.ConnectError:
        print("Cannot connect to agent. Make sure agent.py is running:")
        print("  python agent.py")

if __name__ == "__main__":
    asyncio.run(main())
