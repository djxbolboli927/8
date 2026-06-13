import requests
import time

RPC = "https://rpc.fra.shyft.to?api_key=farYqEW-7r1vxqok"
COMPETITOR = "8oKVwqA5S2B7g2Li6yqZ4KKghpER8G1vj3bbeg8dFkSw"
WSOL = "So11111111111111111111111111111111111111112"

DEX_PROGRAMS = {
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter",
    "cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG": "Meteora_DAMM",
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": "Raydium_CLMM",
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Whirlpool",
    "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C": "Raydium_CPMM",
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": "Meteora_DLMM",
    "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP": "Meteora_Pools",
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium_V4",
    "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA": "PumpSwap",
    "TessVdML9pBGgG9yGks7o4HewRaXVAMuoVj4x83GLQH": "Tessera_V_PMM",
    "SoLFiHG9TfgtdUXUjWAxi3LtvYuFyDLVhBWxdMZxyCe": "SolFi_PMM",
    "ZERor4xhbUycZ6gb9ntrhqscUcZmAbQDjEAtCf4hbZY": "ZeroFi_PMM",
}

COMMON_ACCOUNTS = {
    "11111111111111111111111111111111",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",
    "ComputeBudget111111111111111111111111111111",
    "So11111111111111111111111111111111111111112",
    "SysvarRent111111111111111111111111111111111",
    "SysvarC1ock11111111111111111111111111111111",
    "Sysvar1nstructions1111111111111111111111111",
    "SysvarS1otHashes111111111111111111111111111",
}

def rpc(method, params):
    try:
        r = requests.post(RPC, json={
            "jsonrpc": "2.0", "id": 1, "method": method, "params": params
        }, timeout=30)
        r.raise_for_status()
        j = r.json()
        if "error" in j:
            return None
        return j.get("result")
    except Exception as e:
        print(f"  rpc error: {e}")
        return None

def tx_keys(tx):
    keys = []
    msg = tx.get("transaction", {}).get("message", {})
    for k in msg.get("accountKeys", []) or []:
        keys.append(k.get("pubkey") if isinstance(k, dict) else k)
    meta = tx.get("meta") or {}
    la = meta.get("loadedAddresses") or {}
    for k in (la.get("writable") or []):
        keys.append(k)
    for k in (la.get("readonly") or []):
        keys.append(k)
    return [k for k in keys if k]

def pool_accounts(keys_list):
    return set(k for k in keys_list if k not in COMMON_ACCOUNTS and k not in DEX_PROGRAMS)

def get_dex_programs(keys_list):
    return set(keys_list) & set(DEX_PROGRAMS.keys())

def get_signer(tx):
    msg = tx.get("transaction", {}).get("message", {})
    keys = msg.get("accountKeys", []) or []
    if not keys:
        return None
    k = keys[0]
    return k.get("pubkey") if isinstance(k, dict) else k

def token_changes(tx, owner):
    """All non-zero token balance deltas for given owner."""
    if not owner:
        return {}
    meta = tx.get("meta") or {}
    pre = meta.get("preTokenBalances") or []
    post = meta.get("postTokenBalances") or []
    ch = {}
    for b in pre:
        if b.get("owner") == owner:
            m = b.get("mint")
            a = int(b.get("uiTokenAmount", {}).get("amount", "0"))
            ch[m] = ch.get(m, 0) - a
    for b in post:
        if b.get("owner") == owner:
            m = b.get("mint")
            a = int(b.get("uiTokenAmount", {}).get("amount", "0"))
            ch[m] = ch.get(m, 0) + a
    return {m: c for m, c in ch.items() if c != 0}

def fmt_change(mint, delta):
    if mint == WSOL:
        return f"{delta:+d} lamports ({delta/1e9:+.9f} SOL)  [WSOL]"
    short = mint[:8] + ".." + mint[-4:]
    return f"{delta:+d} raw  [{short}]"

def find_competitor_index(block, sig):
    for idx, t in enumerate(block.get("transactions", []) or []):
        sl = t.get("transaction", {}).get("signatures", [])
        if sl and sl[0] == sig:
            return idx
    return None

def main():
    print(f"\n=== Forensic v3: {COMPETITOR} ===\n")
    sigs_data = rpc("getSignaturesForAddress", [COMPETITOR, {"limit": 20}])
    if not sigs_data:
        print("ERROR")
        return
    sigs = [s["signature"] for s in sigs_data if s.get("err") is None]
    print(f"got {len(sigs)} successful txs\n")

    rows = []
    for i, sig in enumerate(sigs):
        time.sleep(0.3)
        print(f"\n{'='*92}")
        print(f"[{i+1}/{len(sigs)}] COMPETITOR TX")
        print(f"  sig:    {sig}")

        tx = rpc("getTransaction", [sig, {
            "encoding": "jsonParsed",
            "maxSupportedTransactionVersion": 0,
        }])
        if not tx:
            print("  → could not fetch")
            continue

        slot = tx["slot"]
        keys_list = tx_keys(tx)
        their_pools = pool_accounts(keys_list)
        their_programs = get_dex_programs(keys_list)
        their_wsol = sum(v for m, v in token_changes(tx, COMPETITOR).items() if m == WSOL)

        print(f"  slot:   {slot}")
        print(f"  dexes:  {sorted(DEX_PROGRAMS[p] for p in their_programs)}")
        print(f"  WSOL:   {their_wsol:+d} lamports ({their_wsol/1e9:+.9f} SOL)")

        same_slot = []
        prior_slot = []
        comp_idx = None

        for back in range(0, 4):
            target = slot - back
            block = rpc("getBlock", [target, {
                "encoding": "jsonParsed",
                "maxSupportedTransactionVersion": 0,
                "transactionDetails": "full",
                "rewards": False,
            }])
            if not block:
                continue
            if back == 0:
                comp_idx = find_competitor_index(block, sig)
                if comp_idx is not None:
                    print(f"  COMP block index: {comp_idx}")

            for tx_idx, other in enumerate(block.get("transactions", []) or []):
                sl = other.get("transaction", {}).get("signatures", [])
                if not sl: continue
                osig = sl[0]
                if osig == sig: continue
                if (other.get("meta") or {}).get("err"): continue
                okeys = tx_keys(other)
                opools = pool_accounts(okeys)
                oprogs = get_dex_programs(okeys)
                if not oprogs: continue
                overlap = their_pools & opools
                if len(overlap) < 3: continue
                if len(oprogs) >= 3: continue
                osigner = get_signer(other)
                if osigner == COMPETITOR: continue
                info = {
                    "sig": osig, "signer": osigner,
                    "programs": sorted(DEX_PROGRAMS[p] for p in oprogs),
                    "overlap": sorted(overlap), "overlap_n": len(overlap),
                    "vchanges": token_changes(other, osigner),
                    "back": back, "slot": target, "idx": tx_idx,
                }
                if back == 0:
                    same_slot.append(info)
                else:
                    prior_slot.append(info)

        before_comp = [v for v in same_slot if comp_idx is not None and v["idx"] < comp_idx]
        after_comp  = [v for v in same_slot if comp_idx is not None and v["idx"] > comp_idx]
        before_comp.sort(key=lambda v: -v["overlap_n"])
        after_comp.sort(key=lambda v: -v["overlap_n"])
        prior_slot.sort(key=lambda v: (v["back"], -v["overlap_n"]))

        if before_comp:
            category = "SAME_SLOT_AFTER_VICTIM"
            verdict = "✓ REAL same-slot backrun (comp AFTER victim) — ShredStream-like signal"
            best = before_comp[0]
        elif prior_slot:
            category = "PRIOR_SLOT"
            verdict = f"✓ Prior-slot backrun ({prior_slot[0]['back']} slot behind) — typical Geyser latency"
            best = prior_slot[0]
        elif after_comp and not before_comp:
            category = "ONLY_BEFORE_COMP"
            verdict = "✗ Only same-slot candidates landed AFTER comp — NOT backrun; likely state-polling"
            best = after_comp[0]
        else:
            category = "TRIANGULAR"
            verdict = "✗ No plausible victim — state-based / triangular"
            best = None

        print(f"  → {verdict}")
        print(f"    same-slot before-comp: {len(before_comp)}, after-comp: {len(after_comp)}, prior-slot: {len(prior_slot)}")

        show = (before_comp + prior_slot)[:3]
        if not show and after_comp:
            print(f"  (showing same-slot-AFTER-comp candidates only — these can't be the true source)")
            show = after_comp[:3]

        for j, v in enumerate(show):
            if v["back"] == 0:
                gap = comp_idx - v["idx"]
                where = f"SAME-SLOT, idx_gap=+{gap}  (victim@{v['idx']}, comp@{comp_idx})"
            else:
                where = f"PRIOR-SLOT-{v['back']}  (slot {v['slot']}, block_idx={v['idx']})"
            print(f"\n    --- victim #{j+1}  [{where}] ---")
            print(f"      tx:        {v['sig']}")
            print(f"      signer:    {v['signer']}")
            print(f"      dexes:     {v['programs']}")
            print(f"      shared pools ({v['overlap_n']}):")
            for a in v["overlap"]:
                print(f"        {a}")
            print(f"      victim token changes:")
            if not v["vchanges"]:
                print(f"        (none detected — signer may not be trade owner)")
            else:
                for m, d in v["vchanges"].items():
                    print(f"        {fmt_change(m, d)}")

        rows.append({"i": i+1, "category": category, "comp_wsol": their_wsol,
                     "comp_idx": comp_idx, "best": best})

    print(f"\n\n{'='*92}\n=== خلاصه‌ی نهایی ===\n{'='*92}")
    counts = {}
    print(f"{'#':<3} {'category':<25} {'comp_idx':<10} {'victim_idx':<11} {'gap':<10} {'comp WSOL'}")
    print("-"*92)
    for r in rows:
        counts[r["category"]] = counts.get(r["category"], 0) + 1
        if r["best"]:
            vi = r["best"]["idx"]
            if r["best"]["back"] == 0:
                gap_str = f"+{r['comp_idx'] - vi}"
            else:
                gap_str = f"slot-{r['best']['back']}"
        else:
            vi, gap_str = "-", "-"
        ci = str(r["comp_idx"]) if r["comp_idx"] is not None else "?"
        print(f"{r['i']:<3} {r['category']:<25} {ci:<10} {str(vi):<11} {gap_str:<10} {r['comp_wsol']:+d}")
    print()
    print(f"Total: {len(rows)}")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print()
    print("Interpretation key:")
    print("  SAME_SLOT_AFTER_VICTIM dominant → ShredStream or very low-latency local Geyser")
    print("  PRIOR_SLOT dominant             → Standard Yellowstone Geyser stream")
    print("  ONLY_BEFORE_COMP dominant       → State-based / polling, NOT real backrun")
    print("  Mixed                           → Hybrid signals")

if __name__ == "__main__":
    main()