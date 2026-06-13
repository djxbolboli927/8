#!/usr/bin/env python3
"""
Pool Extractor v2 — On-chain Verification + Pair Filter + Extended DEXes

خط ۱۶:  LIMIT = تعداد تراکنش‌ها
خط ۲۱:  PAIR_FILTERS = فیلتر جفت‌ها (خالی = همه)
"""

import json, time, sys, http.client, ssl, urllib.parse

# ═══════════════════ CONFIG ═══════════════════
RPC    = "https://rpc.fra.shyft.to?api_key=farYqEW-7r1vxqok"
WALLET = "8oKVwqA5S2B7g2Li6yqZ4KKghpER8G1vj3bbeg8dFkSw"

# ─── خط ۱۶: تعداد تراکنش‌ها ───
LIMIT  = 10

# ─── خط ۲۱-۵۶: فیلتر جفت‌ها ───
# هر جفت = set از دو mint address
# خالی = همه استخرها نمایش داده میشن
WSOL     = "So11111111111111111111111111111111111111112"
USDC     = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
JITOSOL  = "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn"
MSOL     = "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So"

PAIR_FILTERS = [
    # جفت ۱: wSOL / USDC
    { WSOL, USDC },
    # جفت ۲: wSOL / JitoSOL
    { WSOL, JITOSOL },
    # جفت ۳: wSOL / mSOL
    { WSOL, MSOL },
    # جفت ۴: USDC / JitoSOL
    { USDC, JITOSOL },
    # جفت ۵: USDC / mSOL
    { USDC, MSOL },
    # جفت ۶: JitoSOL / mSOL
    { JITOSOL, MSOL },
    # برای اضافه کردن جفت جدید:
    # { "MINT_ADDRESS_1", "MINT_ADDRESS_2" },
]

OUTPUT_JSON      = "pools-from-wallet.json"
OUTPUT_ANNOTATED = "pools-from-wallet-annotated.txt"

# ═══════════════════ DEX PROGRAMS ═══════════════════

DEX_NAMES = {
    # ── Raydium ──
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium_AMM",
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": "Raydium_CLMM",
    "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C": "Raydium_CPMM",
    # ── Orca ──
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc":  "Orca_Whirlpool",
    # ── Meteora ──
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": "Meteora_DLMM",
    "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB": "Meteora_DAMM",
    "24Uqj9JCLxUeoC3hGfh5W3s9FM9uCHDS2SG3LYwBpyTi": "Meteora_Vault",
    # ── GoonFi ──
    "goonuddtQRrWqqn5nFyczVKaie28f3kDkHWkHtURSLE":  "GoonFi_V2",
    # ── PumpFun ──
    "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA":  "PumpFun_AMM",
    # ── Phoenix ──
    "PhoeNiXZ8ByJGLkxNfZRnkUfjvmuYqLR89jjFHGqdXY":  "Phoenix",
    # ── Saber ──
    "SSwpkEEcbUqx4vtoEByFjSkhKdCT862DNVb52nZg1UZ":  "Saber",
    # ── Aquifer ──
    "AQU1FRd7papthgdrwPTTq5JacJh8YtwEXaBfKU3bTz45": "Aquifer",
    # ── Tessera V ──
    "TessVdML9pBGgG9yGks7o4HewRaXVAMuoVj4x83GLQH":  "Tessera_V",
    # ── 1Dex ──
    "DEXYosS6oEGvk8uCDayvwEZz4qEyDJRf9nFgYCaqPMTm": "1Dex",
    # ── AlphaQ ──
    "ALPHAQmeA7bjrVuccPsYPiCvsi428SNwte66Srvs4pHA":  "AlphaQ",
    # ── Manifest (order book → pubkey = market address) ──
    "MNFSTqtC93rEfYHB6hF82sKdZpUDFWkViLByLd1k1Ms":  "Manifest",
    # ── Byreal CLMM ──
    "REALQqNEomY6cQGZJUGwywTBD2UmDT32rZcNnfxQ5N2":  "Byreal_CLMM",
    # ── Sanctum Router ──
    "stkitrT1Uoy18Dk1fTrgPw8W6MVzoCfYoAFT4MLsmhq":  "Sanctum_Router",
    # ── Stake Pool ──
    "SPoo1Ku8WFXoNDMHPsrGSTSG1Y47rzgn41SLUNakuHy":  "Stake_Pool",
    # ── PancakeSwap ──
    "HpNfyc2Saw7RKkQd8nEL4khUcuPhQ7WwY1B2qjx8jxFq": "PancakeSwap",
    # ── stabble ──
    "swapFpHZwjELNnjvThjajtiVmkz3yPQEHjLtka2fwHW":  "stabble_Weighted",
    "swapNyd8XiQwJ6ianp9snpu4brUqFxadzvHebnAXjJZ":  "stabble_Stable",
    # ── SolFi V2 ──
    "SV2EYYJyRz2YhfXwXnhNAevDEui5Q6yrfyo13WtupPF":  "SolFi_V2",
}

SKIP_ACCOUNTS = {
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
    "JUP2jxvXaqu7NQY1GmNf4m1vodw12LVXYxbFL2uB9Ne",
    "ComputeBudget111111111111111111111111111111",
    "11111111111111111111111111111111",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJe1bz",
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
    "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",
    "Memo1UhkJBfCR6MNLc2aTHqszREt9aGdCrEBN6HNsA9M",
    "SysvarRent111111111111111111111111111111111",
    "SysvarC1ock11111111111111111111111111111111",
    "So11111111111111111111111111111111111111112",
    # ── آدرس‌های اشتباه شناسایی‌شده (نه pool، بلکه position/vault/wallet) ──
    # Raydium_CLMM (personal positions, not pool state)
    "E64NGkDLLCdQ2yFNPcavaKptrEgmiQaNykUuLC1Qgwyp",
    "9EeWRCL8CJnikDFCDzG8rtmBs5KQR1jEYKCR5rRZ2NEi",
    # PancakeSwap
    "GcJVsj5MxokA4eRMUkB4cJHuZ6o9Y8MooXBViN5F1mYW",
    "HZzqEWHEvSiqYt6PxxLs7zXETmqGuryqfmvggjAkqisp",
    # 1Dex
    "5nmAbnjJfW1skrPvYjLTBNdhoKzJfznnbvDcM8G2U7Ki",
    # Aquifer
    "5AVyF6qJBi8GxVjh6nh4Ew1DiJZugPxz9m58a8v2osk2",
    # Byreal_CLMM
    "4E6xP73xzTs4aCvY92hbXRwWkYptNwvViPZmLcZEBUk4",
    # Orca_Whirlpool
    "Esvfxt3jMDdtTZqLF1fqRhDjzM8Bpr7fZxJMrK69PB7e",
    # GoonFi_V2
    "BNrK9LpEn65QA4TyBLVSMdngW3XHj3xLfFPwGdCBv8wV",
}

TOKEN_PROGRAMS = {
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
}

KNOWN_TOKENS = {
    "So11111111111111111111111111111111111111112":    "SOL",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB":  "USDT",
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN":   "JUP",
    "27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4":  "JLP",
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263":  "BONK",
    "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So":   "mSOL",
    "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs":   "ETH",
    "bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1":   "bSOL",
    "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn":  "JitoSOL",
}

SWAP_ACCOUNT_SIZE = {
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": {"account_compressed_count":6,  "account_len":9,  "account_metas_count":9},
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": {"account_compressed_count":13, "account_len":13, "account_metas_count":13},
    "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C": {"account_compressed_count":9,  "account_len":9,  "account_metas_count":9},
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc":  {"account_compressed_count":7,  "account_len":9,  "account_metas_count":9},
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": {"account_compressed_count":16, "account_len":16, "account_metas_count":16},
    "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB": {"account_compressed_count":9,  "account_len":11, "account_metas_count":11},
    "goonuddtQRrWqqn5nFyczVKaie28f3kDkHWkHtURSLE":  {"account_compressed_count":7,  "account_len":9,  "account_metas_count":9},
    "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA":  {"account_compressed_count":6,  "account_len":8,  "account_metas_count":8},
}
DEFAULT_SAS = {"account_compressed_count":9, "account_len":9, "account_metas_count":9}


# ═══════════════════ RPC ═══════════════════

def rpc_call(method, params):
    parsed = urllib.parse.urlparse(RPC)
    host   = parsed.netloc
    path   = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query

    body = json.dumps({"jsonrpc":"2.0", "id":1, "method":method, "params":params})
    ctx  = ssl.create_default_context()
    conn = http.client.HTTPSConnection(host, timeout=30, context=ctx)
    try:
        conn.request("POST", path, body, {
            "Content-Type": "application/json",
            "Accept":       "application/json",
            "User-Agent":   "pool-extractor/2.0",
        })
        resp = conn.getresponse()
        raw  = resp.read().decode()
        if resp.status != 200:
            print(f"    ❌ HTTP {resp.status}: {raw[:200]}")
            return {}
        return json.loads(raw)
    finally:
        conn.close()


# ═══════════════════ ACCOUNT CACHE ═══════════════════

_account_cache = {}

def fetch_accounts(pubkeys):
    to_fetch = [p for p in pubkeys if p not in _account_cache]
    if to_fetch:
        for i in range(0, len(to_fetch), 100):
            batch = to_fetch[i:i+100]
            resp = rpc_call("getMultipleAccounts", [
                batch,
                {"encoding": "jsonParsed", "commitment": "confirmed"}
            ])
            values = resp.get("result", {}).get("value", [None] * len(batch))
            for pk, info in zip(batch, values):
                _account_cache[pk] = info
            time.sleep(0.15)
    return {p: _account_cache.get(p) for p in pubkeys}


def token_label(mint):
    return KNOWN_TOKENS.get(mint, mint[:12] + "…")


# ═══════════════════ PAIR FILTER ═══════════════════

def matches_pair_filter(mints_set):
    if not PAIR_FILTERS:
        return True
    for pair in PAIR_FILTERS:
        if pair.issubset(mints_set):
            return True
    return False


def pair_filter_label():
    if not PAIR_FILTERS:
        return "ALL (no filter)"
    parts = []
    for pair in PAIR_FILTERS:
        labels = [token_label(m) for m in sorted(pair)]
        parts.append(" / ".join(labels))
    return ", ".join(parts)


# ═══════════════════ CORE LOGIC ═══════════════════

def identify_pool_and_mints(dex_program, instruction_accounts):
    candidates = []
    seen = set()
    for a in instruction_accounts:
        if a in seen:
            continue
        seen.add(a)
        if a in SKIP_ACCOUNTS or a == WALLET or a in DEX_NAMES or len(a) < 32:
            continue
        candidates.append(a)

    if not candidates:
        return None, []

    infos = fetch_accounts(candidates)

    pool_pubkey = None
    mints = set()

    for pubkey in candidates:
        info = infos.get(pubkey)
        if info is None:
            continue

        owner = info.get("owner", "")

        if owner == dex_program:
            if pool_pubkey is None:
                pool_pubkey = pubkey
            continue

        if owner in TOKEN_PROGRAMS:
            data = info.get("data", {})
            if isinstance(data, dict) and "parsed" in data:
                parsed_info = data["parsed"].get("info", {})
                mint = parsed_info.get("mint", "")
                if mint:
                    mints.add(mint)

    sorted_mints = sorted(mints, key=lambda m: (m not in KNOWN_TOKENS, m))
    return pool_pubkey, sorted_mints


def extract_dex_instructions(meta):
    dex_ixs = []
    seen_keys = set()

    for group in meta.get("innerInstructions", []):
        for ix in group.get("instructions", []):
            prog = ix.get("programId", "")
            if prog not in DEX_NAMES:
                continue
            accs = ix.get("accounts", [])
            if len(accs) < 3:
                continue
            key = prog + "|" + ",".join(accs[:5])
            if key in seen_keys:
                continue
            seen_keys.add(key)
            dex_ixs.append({
                "dex_program": prog,
                "dex_name":    DEX_NAMES[prog],
                "accounts":    accs,
            })

    return dex_ixs


# ═══════════════════ MAIN ═══════════════════

def main():
    print(f"═══════════════════════════════════════════")
    print(f"  Pool Extractor v2 + Pair Filter")
    print(f"  Wallet: {WALLET[:20]}...")
    print(f"  Limit:  {LIMIT} transactions")
    print(f"  DEXes:  {len(DEX_NAMES)} programs")
    print(f"  Filter: {pair_filter_label()}")
    print(f"═══════════════════════════════════════════\n")

    print(f"📡 Fetching {LIMIT} signatures...")
    resp = rpc_call("getSignaturesForAddress", [WALLET, {"limit": LIMIT, "commitment": "confirmed"}])
    sigs = [s["signature"] for s in resp.get("result", []) if not s.get("err")]
    print(f"   ✅ {len(sigs)} successful transactions\n")

    if not sigs:
        print("❌ No transactions found")
        sys.exit(1)

    results = []
    skipped_by_filter = 0
    seen_pools = set()

    for i, sig in enumerate(sigs, 1):
        print(f"─── [{i}/{len(sigs)}] {sig[:32]}... ───")

        try:
            resp = rpc_call("getTransaction", [sig, {
                "encoding": "jsonParsed",
                "maxSupportedTransactionVersion": 0,
                "commitment": "confirmed",
            }])
            tx = resp.get("result")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            time.sleep(0.3)
            continue

        if not tx:
            print(f"   ❌ null transaction")
            time.sleep(0.15)
            continue

        msg  = tx["transaction"]["message"]
        meta = tx["meta"]

        alts = msg.get("addressTableLookups", [])
        alt_keys = [a["accountKey"] for a in alts] if alts else []

        if not alt_keys:
            print(f"   ➖ no ALT — skipping")
            time.sleep(0.1)
            continue

        dex_ixs = extract_dex_instructions(meta)

        if not dex_ixs:
            print(f"   ➖ no DEX instructions found")
            time.sleep(0.1)
            continue

        print(f"   📊 Found {len(dex_ixs)} DEX instruction(s), ALTs: {len(alt_keys)}")

        for dix in dex_ixs:
            prog  = dix["dex_program"]
            dname = dix["dex_name"]
            accs  = dix["accounts"]

            print(f"   🔍 {dname:18} ({len(accs)} accounts) → ", end="", flush=True)

            pool_pubkey, mints = identify_pool_and_mints(prog, accs)

            if not pool_pubkey:
                print("❌ pool not found")
                continue

            if pool_pubkey in seen_pools:
                print(f"♻️  duplicate: {pool_pubkey[:20]}...")
                continue

            # ── فیلتر جفت ──
            mints_set = set(mints)
            if not matches_pair_filter(mints_set):
                labels = [token_label(m) for m in mints]
                pair_str = " / ".join(labels)
                print(f"⏭️  filtered out: {pair_str}")
                skipped_by_filter += 1
                continue

            seen_pools.add(pool_pubkey)

            labels = [token_label(m) for m in mints]
            pair_str = " / ".join(labels) if labels else "⚠️ no mints"
            print(f"✅ {pair_str}")
            print(f"      Pool:  {pool_pubkey}")
            print(f"      Mints: {mints}")
            print(f"      ALT:   {alt_keys[0][:20]}...")

            results.append({
                "pool_pubkey":  pool_pubkey,
                "dex_program":  prog,
                "dex_name":     dname,
                "mints":        mints,
                "mint_labels":  labels,
                "alt_addresses": alt_keys,
                "signature":    sig,
            })

        time.sleep(0.15)

    # ── خروجی ──
    print(f"\n═══════════════════════════════════════════")
    print(f"  Results: {len(results)} pools matched filter")
    print(f"  Skipped by filter: {skipped_by_filter}")
    print(f"  Account cache: {len(_account_cache)} accounts")
    print(f"═══════════════════════════════════════════\n")

    if not results:
        print("❌ No pools matched the filter")
        sys.exit(0)

    cache_entries = []
    for r in results:
        entry = {
            "pubkey": r["pool_pubkey"],
            "owner":  r["dex_program"],
            "params": {
                "addressLookupTableAddress": r["alt_addresses"][0],
                "routingGroup": 3,
                "swapAccountSize": SWAP_ACCOUNT_SIZE.get(r["dex_program"], DEFAULT_SAS),
            }
        }
        cache_entries.append(entry)

    with open(OUTPUT_JSON, "w") as f:
        json.dump(cache_entries, f, indent=2)

    with open(OUTPUT_ANNOTATED, "w") as f:
        f.write(f"// Pool Extractor v2 + Pair Filter\n")
        f.write(f"// Wallet: {WALLET}\n")
        f.write(f"// Filter: {pair_filter_label()}\n")
        f.write(f"// Total: {len(results)} pools\n\n[\n")
        for idx, (r, e) in enumerate(zip(results, cache_entries)):
            comma = "," if idx < len(results) - 1 else ""
            pair = " / ".join(r["mint_labels"])
            f.write(f"  // [{idx+1}] DEX: {r['dex_name']} | Pair: {pair}\n")
            f.write(f"  // Mints: {', '.join(r['mints'])}\n")
            f.write(f"  // TX: {r['signature'][:48]}...\n")
            f.write("  " + json.dumps(e, indent=2).replace("\n", "\n  ") + comma + "\n\n")
        f.write("]\n")

    print(f"📄 {OUTPUT_JSON}")
    print(f"📝 {OUTPUT_ANNOTATED}\n")

    for idx, (r, e) in enumerate(zip(results, cache_entries)):
        pair = " / ".join(r["mint_labels"])
        print(f"┌─ [{idx+1}] {r['dex_name']} | {pair}")
        print(f"│  Mints: {', '.join(r['mints'])}")
        print(f"│  Pool:  {r['pool_pubkey']}")
        print(f"│  ALT:   {r['alt_addresses'][0]}")
        print(f"└─ Cache:")
        for line in json.dumps(e, indent=2).split("\n"):
            print(f"   {line}")
        print()


if __name__ == "__main__":
    main()