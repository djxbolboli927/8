#!/usr/bin/env python3
"""
step2_fetch_from_cache.py

آدرس استخرها را از pool_pubkeys.py می‌خواند
و entry کامل هر کدام را از فایل کش متیس استخراج می‌کند.

اجرا:
    python3 step2_fetch_from_cache.py --cache /path/to/metis-cache.json

خروجی:
    extracted_pools.json   ← استخرهای پیدا شده (فرمت کامل متیس)
    not_found.txt          ← استخرهایی که در کش نبودند
"""

import json, sys, argparse, os, time

OUTPUT_FOUND     = "extracted_pools.json"
OUTPUT_NOT_FOUND = "not_found.txt"

# ── آدرس‌های استخر از step1 ──
# این بخش را با خروجی step1 (pool_pubkeys.py) جایگزین کنید:
try:
    from pool_pubkeys import POOL_PUBKEYS
except ImportError:
    POOL_PUBKEYS = []
    print("⚠️  pool_pubkeys.py پیدا نشد — لیست را مستقیم در این فایل وارد کنید")

# ─────────────────────────────────────────────────────────
# یا مستقیم اینجا paste کنید:
# POOL_PUBKEYS = [
#     "Hn4qbGydHjtbMGE4cCF2DJ8odLh7gtrBPhx84FoXEHdM",
#     "5yuefgbJJpmFNK2iiYbLSpv1aZXq7F9AUKkZKErTYCvs",
#     ...
# ]
# ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", required=True,
                        help="مسیر فایل کش متیس (مثلاً /root/m/metis/cache.json)")
    args = parser.parse_args()

    if not os.path.exists(args.cache):
        print(f"❌ فایل کش پیدا نشد: {args.cache}")
        sys.exit(1)

    if not POOL_PUBKEYS:
        print("❌ POOL_PUBKEYS خالی است — ابتدا step1 را اجرا کنید")
        sys.exit(1)

    target_set = set(POOL_PUBKEYS)
    print(f"🔍 دنبال {len(target_set)} استخر در کش متیس...")

    size_mb = os.path.getsize(args.cache) / 1024 / 1024
    print(f"📂 {args.cache}  ({size_mb:.1f} MB)")

    start = time.time()
    with open(args.cache, "r") as f:
        cache_data = json.load(f)
    print(f"   ✅ {len(cache_data):,} ورودی در کش ({time.time()-start:.1f}s)\n")

    # ── جستجو ──
    found     = []
    found_set = set()

    for entry in cache_data:
        pk = entry.get("pubkey", "")
        if pk in target_set:
            found.append(entry)
            found_set.add(pk)

    not_found = [pk for pk in POOL_PUBKEYS if pk not in found_set]

    # ── ذخیره نتایج ──
    with open(OUTPUT_FOUND, "w") as f:
        json.dump(found, f, indent=2)

    with open(OUTPUT_NOT_FOUND, "w") as f:
        f.write(f"# استخرهای پیدا نشده در کش متیس ({len(not_found)} عدد)\n\n")
        for pk in not_found:
            f.write(pk + "\n")

    # ── نمایش نتیجه ──
    print("═" * 56)
    print(f"  پیدا شد    : {len(found):>5}  → {OUTPUT_FOUND}")
    print(f"  پیدا نشد   : {len(not_found):>5}  → {OUTPUT_NOT_FOUND}")
    print(f"  کل جستجو   : {len(POOL_PUBKEYS):>5}")
    print("═" * 56 + "\n")

    if found:
        print("✅ استخرهای پیدا شده:")
        for e in found:
            owner = e.get("owner", "?")[:20]
            alt   = e.get("params", {}).get("addressLookupTableAddress", "?")[:20]
            print(f"   {e['pubkey']}  owner={owner}...  alt={alt}...")
        print()

    if not_found:
        print(f"❌ {len(not_found)} استخر در کش متیس نبود:")
        for pk in not_found:
            print(f"   {pk}")
        print()
        print("   → این استخرها باید با روش دیگری (مثلاً اسکریپت استخراج) اضافه شوند")


if __name__ == "__main__":
    main()