#!/usr/bin/env python3
"""
step1_find_pools.py

آدرس استخرهای Meteora را از تراکنش‌های wallet پیدا می‌کند
و در فایل pool_pubkeys.py ذخیره می‌کند (آماده برای paste در step2)

اجرا:
    python3 step1_find_pools.py
"""

import json, time, sys, http.client, ssl, urllib.parse

RPC    = "https://rpc.fra.shyft.to?api_key=farYqEW-7r1vxqok"
WALLET = "8oKVwqA5S2B7g2Li6yqZ4KKghpER8G1vj3bbeg8dFkSw"
LIMIT  = 1000
OUTPUT = "pool_pubkeys.py"

TARGET_PROGRAMS = {
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": "Raydium_Concentrated_Liquidity",
}
MIN_ACCOUNTS = 1   # فقط pool pubkey لازم است، index 0

def rpc_call(method, params):
    parsed = urllib.parse.urlparse(RPC)
    host   = parsed.netloc
    path   = (parsed.path or "/") + ("?" + parsed.query if parsed.query else "")
    body   = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    ctx    = ssl.create_default_context()
    conn   = http.client.HTTPSConnection(host, timeout=30, context=ctx)
    try:
        conn.request("POST", path, body, {"Content-Type": "application/json"})
        resp = conn.getresponse()
        raw  = resp.read().decode()
        return json.loads(raw) if resp.status == 200 else {}
    finally:
        conn.close()

def main():
    print(f"📡 Fetching {LIMIT} signatures for {WALLET[:20]}...")
    resp = rpc_call("getSignaturesForAddress",
                    [WALLET, {"limit": LIMIT, "commitment": "confirmed"}])
    sigs = [s["signature"] for s in resp.get("result", []) if not s.get("err")]
    print(f"   ✅ {len(sigs)} transactions\n")

    found  = {}   # {pool_pubkey: dex_name}
    seen   = set()

    for i, sig in enumerate(sigs, 1):
        print(f"[{i}/{len(sigs)}] {sig[:40]}...", end=" ", flush=True)

        try:
            resp = rpc_call("getTransaction", [sig, {
                "encoding": "jsonParsed",
                "maxSupportedTransactionVersion": 0,
                "commitment": "confirmed",
            }])
            tx = resp.get("result")
        except Exception as e:
            print(f"❌ {e}")
            time.sleep(0.3)
            continue

        if not tx:
            print("null")
            time.sleep(0.1)
            continue

        msg  = tx["transaction"]["message"]
        meta = tx["meta"]
        hit  = []

        def _check(prog, accs):
            if prog not in TARGET_PROGRAMS or len(accs) < 1:
                return
            pool_pk = accs[0]
            if pool_pk in seen:
                return
            seen.add(pool_pk)
            found[pool_pk] = TARGET_PROGRAMS[prog]
            hit.append(pool_pk[:16] + "...")

        for ix in msg.get("instructions", []):
            _check(ix.get("programId", ""), ix.get("accounts", []))
        for group in meta.get("innerInstructions", []):
            for ix in group.get("instructions", []):
                _check(ix.get("programId", ""), ix.get("accounts", []))

        print("✅ " + ", ".join(hit) if hit else "—")
        time.sleep(0.12)

    # ── ذخیره با فرمت آماده برای step2 ──
    with open(OUTPUT, "w") as f:
        f.write("# آدرس استخرها — خروجی step1\n")
        f.write("# این فایل را در step2_fetch_from_cache.py paste کنید\n\n")
        f.write("POOL_PUBKEYS = [\n")
        for pk, dex in found.items():
            f.write(f'    "{pk}",  # {dex}\n')
        f.write("]\n")

    print(f"\n✅ {len(found)} pool → {OUTPUT}")
    for pk, dex in found.items():
        print(f"   {dex}  {pk}")

if __name__ == "__main__":
    main()