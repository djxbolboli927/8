#!/usr/bin/env python3
"""
metis_dex_probe.py

کار این اسکریپت:
  - به متیس محلی (127.0.0.1:8080) وصل می‌شود
  - برای هر DEX یک quote WSOL→USDC می‌گیرد که فقط از آن DEX عبور کند
  - تعداد accounts در swap instruction را می‌شمارد
  - نتیجه: swapAccountSize دقیق برای هر DEX

پیش‌نیاز: متیس در حال اجرا باشد روی 127.0.0.1:8080

اجرا:
    python3 metis_dex_probe.py
"""

import json, time, http.client, urllib.parse, sys, base64

METIS = "http://127.0.0.1:8080"

# جفت تست — همه DEX ها این را دارند
WSOL  = "So11111111111111111111111111111111111111112"
USDC  = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
AMOUNT = 100_000_000   # 0.1 SOL

# یک wallet معتبر (فقط برای ساخت instruction — sign نمی‌کنیم)
WALLET = "8oKVwqA5S2B7g2Li6yqZ4KKghpER8G1vj3bbeg8dFkSw"

# DEX هایی که می‌خواهیم بررسی کنیم
# (program_id, نام برای نمایش)
DEXES = [
    ("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc", "Orca Whirlpool"),
    ("Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB", "Meteora Pools"),
    ("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8", "Raydium AMM v4"),
    ("CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK", "Raydium CLMM"),
    ("CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C", "Raydium CPMM"),
    ("LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",  "Meteora DLMM"),
    ("MERLuDFBMmsHnsBPZw2sDQZHvXFMwp8EdjudcU2HKky",  "Mercurial"),
    ("9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP", "Orca v2"),
]

# ═══════════════════════════════════════════
#   HTTP helpers — http (نه https) برای localhost
# ═══════════════════════════════════════════

def get(path_and_query: str) -> dict:
    conn = http.client.HTTPConnection("127.0.0.1", 8080, timeout=15)
    try:
        conn.request("GET", path_and_query, headers={"Accept": "application/json"})
        resp = conn.getresponse()
        raw  = resp.read().decode()
        if resp.status != 200:
            print(f"  HTTP {resp.status}: {raw[:200]}")
            return {}
        return json.loads(raw)
    finally:
        conn.close()

def post(path: str, body: dict) -> dict:
    data = json.dumps(body)
    conn = http.client.HTTPConnection("127.0.0.1", 8080, timeout=15)
    try:
        conn.request("POST", path, data, {
            "Content-Type": "application/json",
            "Accept":       "application/json",
        })
        resp = conn.getresponse()
        raw  = resp.read().decode()
        if resp.status != 200:
            print(f"  HTTP {resp.status}: {raw[:300]}")
            return {}
        return json.loads(raw)
    finally:
        conn.close()

# ═══════════════════════════════════════════
#   Step 1: program-id-to-label
# ═══════════════════════════════════════════

def load_labels() -> dict:
    """برگشت: {program_id: label_string}"""
    print("📡 /program-id-to-label ...", end=" ", flush=True)
    data = get("/program-id-to-label")
    if not data:
        print("❌ متیس پاسخ نداد — آیا روی 127.0.0.1:8080 اجرا است؟")
        sys.exit(1)
    print(f"✅ ({len(data)} DEX)")
    return data

# ═══════════════════════════════════════════
#   Step 2: quote → force یک DEX
# ═══════════════════════════════════════════

def quote_via(label: str) -> dict | None:
    qs = urllib.parse.urlencode({
        "inputMint":        WSOL,
        "outputMint":       USDC,
        "amount":           AMOUNT,
        "slippageBps":      100,
        "dexes":            label,         # ← force این DEX
        "onlyDirectRoutes": "true",        # ← فقط یک hop
    })
    data = get(f"/quote?{qs}")
    if not data or "error" in data:
        return None
    return data

# ═══════════════════════════════════════════
#   Step 3: swap-instructions → شمارش accounts
# ═══════════════════════════════════════════

def get_accounts(quote: dict) -> dict:
    resp = post("/swap-instructions", {
        "quoteResponse": quote,
        "userPublicKey": WALLET,
    })
    if not resp:
        return {}

    # swapInstruction.accounts = لیست accounts
    swap_ix = resp.get("swapInstruction", {})
    accounts = swap_ix.get("accounts", [])
    alts     = resp.get("addressLookupTableAddresses", [])

    return {
        "account_len":          len(accounts),
        "account_metas_count":  len(accounts),
        "alts":                 alts,
        "program_id":           swap_ix.get("programId"),
        "accounts":             accounts,  # لیست کامل برای بررسی
    }

# ═══════════════════════════════════════════
#   Step 4: /swap → compressed count از tx header
# ═══════════════════════════════════════════

def get_compressed_count(quote: dict) -> int | None:
    """
    serialized tx را می‌گیریم و static account count را
    از header v0 Transaction می‌خوانیم.
    compressed = total_in_ix - static_in_tx
    """
    resp = post("/swap", {
        "quoteResponse": quote,
        "userPublicKey": WALLET,
    })
    if not resp:
        return None

    tx_b64 = resp.get("swapTransaction")
    if not tx_b64:
        return None

    try:
        raw = base64.b64decode(tx_b64)
    except Exception:
        return None

    # compact-u16 reader
    def cu16(data, pos):
        val, shift = 0, 0
        while True:
            b = data[pos]; pos += 1
            val |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7
        return val, pos

    try:
        pos = 1          # skip prefix byte (0x80 = v0)
        pos += 3         # skip message header (3 bytes)
        num_static, pos = cu16(raw, pos)
        return num_static
    except Exception:
        return None

# ═══════════════════════════════════════════
#                   MAIN
# ═══════════════════════════════════════════

def main():
    print("═" * 55)
    print("  Metis DEX Account Size Probe")
    print(f"  Metis  : {METIS}")
    print(f"  Pair   : WSOL → USDC  ({AMOUNT/1e9} SOL)")
    print("═" * 55 + "\n")

    # load label map
    label_map = load_labels()
    print()

    results = []

    for pid, name in DEXES:
        print(f"── {name} ──────────────────────")

        label = label_map.get(pid)
        if not label:
            print(f"  ⚠️  label نامشخص برای این program_id")
            print(f"     {pid}")
            results.append({"name": name, "pid": pid, "status": "no_label"})
            print()
            continue

        print(f"  label : {label}")

        # quote
        print(f"  quote ...", end=" ", flush=True)
        q = quote_via(label)
        if not q:
            print("❌ (جفت یا نقدینگی نیست)")
            results.append({"name": name, "pid": pid, "label": label, "status": "no_quote"})
            print()
            continue
        print("✅")

        # route را نمایش می‌دهیم
        for step in q.get("routePlan", []):
            si = step.get("swapInfo", {})
            print(f"  route : {si.get('label','?')}  pool={si.get('ammKey','?')[:20]}...")

        # swap-instructions
        print(f"  swap-instructions ...", end=" ", flush=True)
        acc = get_accounts(q)
        if not acc:
            print("❌")
            results.append({"name": name, "pid": pid, "label": label, "status": "no_instructions"})
            print()
            continue
        print("✅")

        account_len = acc["account_len"]
        alts        = acc["alts"]
        print(f"  account_len         = {account_len}")
        print(f"  ALTs                = {len(alts)}  {alts}")

        # compressed count از tx
        print(f"  /swap (compressed) ...", end=" ", flush=True)
        static = get_compressed_count(q)
        if static is not None:
            compressed = account_len - static
            print(f"✅  static={static}  compressed={compressed}")
        else:
            compressed = "?"
            print("⚠️  skip")

        entry = {
            "name":    name,
            "pid":     pid,
            "label":   label,
            "status":  "ok",
            "swapAccountSize": {
                "account_compressed_count": compressed,
                "account_len":              account_len,
                "account_metas_count":      account_len,
            },
            "alts": alts,
        }
        results.append(entry)

        print(f"\n  ✅ swapAccountSize:")
        print(f"     account_compressed_count : {compressed}")
        print(f"     account_len              : {account_len}")
        print(f"     account_metas_count      : {account_len}")
        print()

        time.sleep(0.2)

    # ── ذخیره ──
    out = "dex_account_sizes.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # ── خلاصه نهایی ──
    print("═" * 55)
    print("  خلاصه")
    print("═" * 55)
    ok = [r for r in results if r.get("status") == "ok"]
    for r in ok:
        s = r["swapAccountSize"]
        print(f"  {r['name']:<22} len={s['account_len']:>3}  "
              f"compressed={str(s['account_compressed_count']):>4}  "
              f"label={r['label']}")
    fail = [r for r in results if r.get("status") != "ok"]
    if fail:
        print()
        for r in fail:
            print(f"  {r['name']:<22} ← {r.get('status','?')}")

    print(f"\n📄 {out}\n")


if __name__ == "__main__":
    main()