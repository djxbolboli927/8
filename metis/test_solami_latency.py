#!/usr/bin/env python3
import requests
import time
import json
import statistics

URL = "https://solana-rpc.publicnode.com"
HEADERS = {"Content-Type": "application/json"}

# 🔸 جایگزین با base64 واقعی از یک تراکنش سولانا
DUMMY_TX = "AgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAEDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyAhIiMkJSYnKCkqKywtLi8wMTIzNDU2Nzg5Ojs8PT4/QEFCQ0RFRkdISUpLTE1OT1BRUlNUVVZXWFlaW1xdXl9gYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXp7fH1+f4ABAgMEBQYHCAkKCwwNDg8QERITFBUWFxgZGhscHR4fICEiIyQlJicoKSorLC0uLzAxMjM0NTY3ODk6Ozw9Pj9AQUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVpbXF1eX2BhYmNkZWZnaGlqa2xtbm9wcXJzdHV2d3h5ent8fX5/gA=="

PAYLOAD = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "simulateBundle",
    "params": [{"version": 1, "transactions": [DUMMY_TX]}]
}

def test_bundle_simulation(iterations=10):
    print(f"🧪 تست شبیه‌سازی باندل ({iterations} بار)...")
    latencies = []
    server_times = []
    
    # گرم‌کردن کش DNS/TLS
    requests.post(URL, json=PAYLOAD, headers=HEADERS, timeout=10)
    
    for i in range(iterations):
        start = time.perf_counter()
        resp = requests.post(URL, json=PAYLOAD, headers=HEADERS, timeout=15)
        end = time.perf_counter()
        
        total_ms = (end - start) * 1000
        latencies.append(total_ms)
        
        if resp.status_code == 200:
            data = resp.json()
            result = data.get("result", {})
            # استخراج زمان شبیه‌سازی اگر RPC آن را برگرداند
            sim_time = result.get("simulationTimeMs", 0)
            server_times.append(sim_time)
            status = "✅ Success" if result.get("err") is None else f"❌ Revert: {result.get('err')}"
            print(f"[{i+1}] RTT: {total_ms:6.1f}ms | Status: {status}")
        else:
            print(f"[{i+1}] ❌ HTTP {resp.status_code} | RTT: {total_ms:6.1f}ms")
            
    print("\n📊 خلاصه آماری:")
    print(f"   میانگین RTT کل: {statistics.mean(latencies):.1f} ms")
    print(f"   میانه RTT کل:  {statistics.median(latencies):.1f} ms")
    print(f"   کمترین RTT:    {min(latencies):.1f} ms")
    print(f"   بیشترین RTT:   {max(latencies):.1f} ms")
    if server_times:
        print(f"   میانگین زمان شبیه‌سازی سرور: {statistics.mean(server_times):.1f} ms")

if __name__ == "__main__":
    test_bundle_simulation()