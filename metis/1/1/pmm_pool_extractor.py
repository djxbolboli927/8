#!/usr/bin/env python3
"""
universal_extractor.py  —  همه صرافی‌ها در یک اسکریپت

صرافی‌ها (16 عدد):
  Meteora_Pools   | GoonFi_V2      | Raydium_CLMM
  AlphaQ          | Meteora_DLMM   | PancakeSwap
  Orca_Whirlpool  | SolFi_V2       | Orca_V2
  Manifest        | Tessera_V      | 1Dex
  Raydium_CPMM    | Raydium_AMM_V4 | Invariant       | BisonFi

اجرا:
    python3 universal_extractor.py
"""

import json, time, sys, http.client, ssl, urllib.parse, base64

# ═══════════════════════════════════════════
#                   CONFIG
# ═══════════════════════════════════════════

RPC    = "https://rpc.fra.shyft.to?api_key=OzrZu1GKwkebvxIg"
WALLET = "7nwPXZNhBj88jcC22VNBQUYLohTsQWh5VGxWqnAAcvMf"
LIMIT  = 10000   # تعداد کل تراکنش (pagination خودکار)

OUTPUT_JSON      = "all-pools.json"
OUTPUT_ANNOTATED = "all-pools-annotated.txt"
CHUNK_SIZE       = 1000

# ═══════════════════════════════════════════
#   DEX CONFIGS
#   name, pool_idx, min_accounts
# ═══════════════════════════════════════════

# ── گروه 1 ──────────────────────────────────
# Meteora Pools (DAMM)
# [0]=Pool  [5]=VaultTokenA  [6]=VaultTokenB  [7]=VaultLpMintA  [8]=VaultLpMintB
METEORA_POOLS = "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"

# GoonFi V2
# [0]=User  [1]=Market(pool)  [4]=PoolTokenA  [5]=PoolTokenB  [6]=MintA  [7]=MintB
GOONFI_V2 = "goonuddtQRrWqqn5nFyczVKaie28f3kDkHWkHtURSLE"

# Raydium CLMM
# [0]=Payer  [1]=AmmConfig  [2]=PoolState(pool)  [5]=InputVault  [6]=OutputVault
RAYDIUM_CLMM = "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"

# ── گروه 2 ──────────────────────────────────
# AlphaQ
# [0]=User  [1]=Market(pool)  [5]=VaultA  [6]=VaultB
ALPHAQ = "ALPHAQmeA7bjrVuccPsYPiCvsi428SNwte66Srvs4pHA"

# Meteora DLMM
# [0]=LbPair(pool)  [2]=ReserveX  [3]=ReserveY
METEORA_DLMM = "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"

# PancakeSwap
# [0]=Payer  [1]=AmmConfig  [2]=PoolState(pool)  [5]=InputVault  [6]=OutputVault
PANCAKE = "HpNfyc2Saw7RKkQd8nEL4khUcuPhQ7WwY1B2qjx8jxFq"

# ── گروه 3 ────────────────────────────────
# Orca Whirlpool (Swap_v2)
# [0]=TokenProgramA  [1]=TokenProgramB  [2]=Whirlpool(pool)
# [4]=TokenVaultA  [6]=TokenVaultB  [10]=Oracle
WHIRLPOOL = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"

# SolFi V2
# [0]=User  [1]=Pair(pool)  [4]=PoolTokenA  [5]=PoolTokenB
SOLFI = "SV2EYYJyRz2YhfXwXnhNAevDEui5Q6yrfyo13WtupPF"

# Orca Token Swap V2
# [0]=Market(pool)  [4]=PoolSource  [5]=PoolDest  [7]=PoolMint
ORCA_V2 = "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP"

# ── گروه 4 ────────────────────────────────
# Manifest (SwapV2)
# [1]=Payer  [2]=Market(pool)  [6]=BaseVault  [7]=QuoteVault  [12]=Global  [13]=GlobalVault
MANIFEST = "MNFSTqtC93rEfYHB6hF82sKdZpUDFWkViLByLd1k1Ms"

# Tessera V
# [0]=Authority  [1]=Pool(pool)  [3]=PoolTokenA  [4]=PoolTokenB
TESSERA = "TessVdML9pBGgG9yGks7o4HewRaXVAMuoVj4x83GLQH"

# 1Dex Program
# [0]=MetadataState  [1]=PoolState(pool)  [3]=TokenIn  [4]=TokenOut
ONEDEX = "DEXYosS6oEGvk8uCDayvwEZz4qEyDJRf9nFgYCaqPMTm"

# ── گروه 5 ────────────────────────────────
# Raydium CPMM
# [0]=Payer  [1]=Authority  [2]=AmmConfig  [3]=PoolState(pool)
# [6]=InputVault  [7]=OutputVault  [12]=ObservationState
RAYDIUM_CPMM = "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"

# Raydium Liquidity Pool V4
# [0]=TokenProgram  [1]=AmmId(pool)  [2]=AmmAuthority  [3]=CoinVault  [4]=PcVault
RAYDIUM_AMM_V4 = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"

# Invariant Swap
# [0]=State  [1]=Pool(pool)  [2]=Tickmap  [3]=TokenX  [4]=TokenY  [7]=ProgramAuthority
# BisonFi
# [0]=User  [1]=Pair(market)  [2]=PoolTokenA(poolA)  [3]=PoolTokenB(poolB)
# [4]=UserTokenA  [5]=UserTokenB  [6]=TokenProgramA  [7]=TokenProgramB
BISONFI = "BiSoNHVpsVZW2F7rx2eQ59yQwKxzU5NvBcmKshCSUypi"

INVARIANT = "HyaB3W9q6XdA5xwpU4XnSZV94htfmbmqJXZcEbRaJutt"

# ── DEX dict ────────────────────────────────
DEX = {
    METEORA_POOLS:  {"name": "Meteora_Pools",   "pool_idx": 0, "min": 14},
    GOONFI_V2:      {"name": "GoonFi_V2",       "pool_idx": 1, "min": 8},
    RAYDIUM_CLMM:   {"name": "Raydium_CLMM",    "pool_idx": 2, "min": 13},
    ALPHAQ:         {"name": "AlphaQ",          "pool_idx": 1, "min": 11},
    METEORA_DLMM:   {"name": "Meteora_DLMM",    "pool_idx": 0, "min": 4},
    PANCAKE:        {"name": "PancakeSwap",     "pool_idx": 2, "min": 9},
    WHIRLPOOL:      {"name": "Orca_Whirlpool",  "pool_idx": 2, "min": 11},
    SOLFI:          {"name": "SolFi_V2",        "pool_idx": 1, "min": 6},
    ORCA_V2:        {"name": "Orca_V2",         "pool_idx": 0, "min": 9},
    MANIFEST:       {"name": "Manifest",        "pool_idx": 2, "min": 14},
    TESSERA:        {"name": "Tessera_V",       "pool_idx": 1, "min": 5},
    ONEDEX:         {"name": "1Dex",            "pool_idx": 1, "min": 5},
    RAYDIUM_CPMM:   {"name": "Raydium_CPMM",   "pool_idx": 3, "min": 13},
    RAYDIUM_AMM_V4: {"name": "Raydium_AMM_V4", "pool_idx": 1, "min": 8},
    BISONFI:        {"name": "BisonFi",         "pool_idx": 1, "min": 4},
    INVARIANT:      {"name": "Invariant",       "pool_idx": 1, "min": 8},
}

KNOWN_TOKENS = {
    "So11111111111111111111111111111111111111112": "WSOL",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT",
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN": "JUP",
    "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So": "mSOL",
    "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn": "JitoSOL",
    "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj": "stSOL",
    "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R": "RAY",
    "2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk": "ETH",
    "poLisWXnNRwC6oBu1vHiuKQzFjGL4XDSu4g9qjz9qVk": "POLIS",
    "8x5VqbHA8D7NkD52uNuS5nnt3PwA8pLD34ymskeSo2Wn": "ZEREBRO",
    "3qq54YqAKG3TcrwNHXFSpMCWoL8gmMuPceJ4FG9npump": "CLANKER",
    "J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr": "SPX",
    "63LfDmNb3MQ8mw9MtZ2To9bEA2M71kZUUGq5tiJxcqj9": "GIGA",
    "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU": "SAMO",
    "Fch1oixTPri8zxBnmdCEADoJW2toyFHxqDZacQkwdvSP": "HARAMBE",
    "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs": "WETH",
    "USDH1SM1ojwWUga67PGrgFWUHibbjqMvuMaDkRJTgkX": "USDH",
    "Cy1GS2FqefgaMbi45UunrUzin1rfEmTUYnomddzBpump": "MOBY",
    "GJtJuWD9qYcCkrwMBmtY1tpapV1sKfB2zUv9Q4aqpump": "$RIF",
    "18FU95xFJhUUkyyCLU13HSzDLs7oC4QZdXQHL6SCeab36": "UNI",
    "6ogzHhzdrQr9Pgv6hZ2MNze7UrzBMAFyBBWUYp1Fhitx": "RETARDIO",
    "4y9E3tJpGNzRr1592oWTPECgyp2VDSc1Bf3DqAm5FZsK": "FATGF",
    "SHDWyBxihqiCj6YekG2GUr7wqKLeLAMK1gHZck9pL6y": "SHDW",
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": "BONK",
    "9LzCMqDgTKYz9Drzqnpgee3SGa89up3a247ypMj2xrqM": "AUDIO",
    "FeR8VBqNRSUD5NtXAj2n3j1dAHkZHfyDktKuLXD4pump": "jellyjelly",
    "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr": "POPCAT",
    "A8C3xuqscfmyLrte3VmTqrAq8kgMASius9AFNANwpump": "FWOG",
    "SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt": "SRM",
    "GEJpt3Wjmr628FqXxTgxMce1pLntcPV4uFi8ksxMyPQh": "daoSOL",
    "3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh": "WBTC",
    "2eTJqpK4QqWofGLSoirWNdC3Goyxp81KC3JDMqcupump": "mindshare",
    "HgBRWfYxEfvPhtqkaeymCQtHCrKE46qQ43pKe8HCpump": "Bert",
    "bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1": "bSOL",
    "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3": "PYTH",
    "5UUH9RTDiSpq6HKS6bp4NdU9PNJpXRXuiw6ShBTBhgH2": "TROLL",
    "5oVNBeEEQvYi1cX3ir8Dx5n1P7pdxydbGF2X4TxVusJm": "INF",
    "BLZEEuZUBVqFhj8adcCFPJvPVCiCyVmh3hkJMrU8KuJA": "BLZE",
    "27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4": "JLP",
    "E1kvzJNxShvvWTrudokpzuc789vRiDXfXG3duCuY6ooE": "DITH",
    "oreoU2P8bN6jkk3jbaiVxYnG1dCXcYxwhwyK9jSybcp": "ORE",
    "SoLiDMWBct5TurG1LNcocemBK7QmTn4P33GSrRrcd2n": "SOLID",
    "G7iK3prSzAA4vzcJWvsLUEsdCqzR7PnMzJV61vSdFSNW": "NST",
    "CKaKtYvz6dKPyMvYq9Rh3UBrnNqYZAyd7iF4hJtjUvks": "GARI",
    "J9BcrQfX4p9D1bvLzRNCbMDv8f44a9LFdeqNE4Yk2WMD": "ISC",
    "madHpjRn6bd8t78Rsy7NuSuNwWa2HU8ByPobZprHbHv": "MAD",
    "2oGLxYuNBJRcepT1mEV6KnETaLD7Bf6qq3CM6skasBfe": "PUPS",
    "LSTxxxnJzKDFSLr4dUkPcmCf5VyryEqzPLz5j4bpxFp": "LST",
    "vSoLxydx6akxyMD9XEcPvGYNGq6Nn66oqVb3UkGkei7": "vSOL",
    "BorGY4ub2Fz4RLboGxnuxWdZts7EKhUTB624AFmfCgX": "BORGY",
    "ED5nyyWEzpPPiWimP8vYm7sD7TD3LAt3Q3gRTWHzPJBY": "MOODENG",
    "3iQL8BFS2vE7mww4ehAqQHAsbmRNCrPxizWAT2Zfyr9y": "VIRTUAL",
    "74SBV4zDXxTRgv1pEMoECskKBkZHc2yGPnc7GYVepump": "swarms",
    "61V8vBaqAGMpgDQi4JcAwo1dmBGHsyhzodcPqnEVpump": "arc",
    "FaxYQ3LVXP51rDP2yWGLWVrFAAHeSdFF8SGZxwj2dvor": "SWAG",
    "KENJSUYLASHUMfHyy5o4Hp2FdNqZg1AsUPhfH2kYvEP": "GRIFFAIN",
    "kinXdEcpDQeHPEuQnqmUgtYykqKGVFq6CeVX5iAHJq6": "KIN",
    "USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB": "USD1",
    "ATLASXmbPQxBUYbxPsV97usA3fPQYEqzQBUHgiFCUsXx": "ATLAS",
    "CzLSujWBLFsSjncfkh59rUFqvafWcY5tzedWJSuypump": "GOAT",
    "nosXBVoaCTtYdLvKY6Csb4AC8JCdQKKAaWYtx2ZMoo7": "NOS",
    "9gP2kCy3wA1ctvYWQk75guqXuHfrEomqydHLtcTCqiLa": "WBNB",
    "Hax9LTgsQkze1YFychnBLtFH8gYbQKtKfWKKg2SP6gdD": "TAI",
    "Dfh5DzRgSvvCFDoYc2ciTkMrbDfRKybA4SoFbPmApump": "pippin",
    "eL5fUxj2J4CiQsmW85k5FG9DvuQjjUoBHoQBi2Kpump": "UFD",
    "Df6yfrKC8kZE3KNkrHERKzAetSxbrWeniQfyJY4Jpump": "CHILLGUY",
    "6yjNqPzTSanBWSa6dxVEgTjePXBrZ2FoHLDQwYwEsyM6": "Chud",
    "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm": "$WIF",
    "9nEqaUcb16sQ3Tn1psbkWqyhPdLmfHWjKGymREjsAgTE": "WOOF",
    "GMzuntWYJLpNuCizrSR7ZXggiMdDzTNiEmSNHHunpump": "dreams",
    "MangoCzJ36AjZyKwVj3VnYU4GTonjfVEnJmvvWaxLac": "MNGO",
    "DtR4D9FtVoTX2569gaL837ZgrB6wNjj6tkmnX9Rdk9B2": "aura",
    "CreiuhfwdWCN5mJbMJtA9bBpYQrQF2tCBuZwSPWfpump": "PYTHIA",
    "F594veMrVJbwyHbUKWWkKLq3xomg4SFb8YukXGBwmgvg": "CHATOSHI",
    "8wXtPeU6557ETkp9WHFY1n1EcU6NxDvbAggHGsMYiHsB": "GME",
    "Apgp3SzNB5VpVWbK5q2ucBvCJEsf1gqXL4iUAqvD9pgB": "HARAMBE",
    "DKu9kykSfbN5LBfFXtNNDPaX35o4Fv6vJ9FKk7pZpump": "AVA",
    "CPcf58MNikQw2G23kTVWQevRDeFDpdxMH7KkR7Lhpump": "DOBBY",
    "8Ki8DpuWNxu9VsS3kQbarsCWMcFGWkzzA8pUPto9zBd5": "LOCKIN",
    "7i5KKsX2weiTkry7jA4ZwSuXGhs5eJBEjY8vVxR4pfRx": "GMT",
    "hntyVP6YFm1Hg25TN9WGLqM12b8TQmcknKrdu1oxWux": "HNT",
    "KMNo3nJsBXfcpJTVhZcXLW7RmTwTt4GVFE7suUBo9sS": "KMNO",
    "HzwqbKZw8HxMN6bF2yFZNrht3c2iXXzpKcFu7uBEDKtr": "EURC",
    "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE": "ORCA",
    "cbbtcf3aa214zXHbiAZQwf4122FBYbraNdFqgw4iMij": "cbBTC",
    "EchesyfXePKdLtoiZSL8pBe8Myagyy8ZRqsACNCFGnvp": "FIDA",
    "METAewgxyPbgwsseH8T16a39CQ5VyVxZi9zXiDPY18m": "MPLX",
    "zBTCug3er3tLyffELcvDNrKkCymbPWysGcWihESYfLg": "zBTC",
    "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL": "JTO",
    "DEkqHyPN7GMRJ5cArtQFAWefqbZb33Hyf6s5iCwjEonT": "USDe",
    "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN": "TRUMP",
    "jupSoLaHXQiZZTSfEWMTRRgpnyFm8f6sZdosWBjx93v": "JupSOL",
    "MNDEFzGvMt87ueuHvVU9VcTqsAP5b3fTGPsHuuPA5ey": "MNDE",
    "METAwkXcqyXKy1AtsSgJ8JiUHwGCafnZL38n3vYmeta": "META",
    "WENWENvqqNya429ubCdR81ZmD69brwQaaBYY6p3LCpk": "WEN",
    "jUpa2aDCzvdR9EF4fqDXmuyMUkonPTohphABLmRkRFj": "RIFT",
    "7JA5eZdCzztSfQbJvS8aVVxMFfd81Rs9VvwnocV1mKHu": "GEOD",
    "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump": "Fartcoin",
    "dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj": "stSOL",
    "8FU95xFJhUUkyyCLU13HSzDLs7oC4QZdXQHL6SCeab36": "UNI",
}
KNOWN_TOKENS = {k.strip(): v.strip() for k, v in KNOWN_TOKENS.items()}

KNOWN_TOKEN_ALIASES = {
    # Frequent malformed forms seen in raw extraction/user inputs
    "1111So11111111111111111111111111111111111111112": "So11111111111111111111111111111111111111112",
    "dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj": "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj",
    "8FU95xFJhUUkyyCLU13HSzDLs7oC4QZdXQHL6SCeab36": "18FU95xFJhUUkyyCLU13HSzDLs7oC4QZdXQHL6SCeab36",
}

# ═══════════════════════════════════════════
#   RPC
# ═══════════════════════════════════════════

def rpc_call(method, params):
    parsed = urllib.parse.urlparse(RPC)
    host   = parsed.netloc
    path   = (parsed.path or "/") + ("?" + parsed.query if parsed.query else "")
    body   = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    ctx    = ssl.create_default_context()
    conn   = http.client.HTTPSConnection(host, timeout=30, context=ctx)
    try:
        conn.request("POST", path, body, {
            "Content-Type": "application/json",
            "Accept":       "application/json",
        })
        resp = conn.getresponse()
        raw  = resp.read().decode()
        return json.loads(raw) if resp.status == 200 else {}
    finally:
        conn.close()

_acct_cache = {}

def fetch_account(pubkey):
    if pubkey not in _acct_cache:
        r = rpc_call("getAccountInfo", [pubkey, {"encoding": "base64", "commitment": "confirmed"}])
        _acct_cache[pubkey] = r.get("result", {}).get("value")
    return _acct_cache[pubkey]

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def to_b58(data: bytes) -> str:
    leading = 0
    for b in data:
        if b == 0:
            leading += 1
        else:
            break
    n = int.from_bytes(data, "big")
    chars = []
    while n:
        n, r = divmod(n, 58)
        chars.append(_B58[r])
    return "1" * leading + "".join(reversed(chars))

def read_pubkey_at(data: bytes, offset: int):
    if not data or len(data) < offset + 32:
        return None
    raw = data[offset:offset + 32]
    return None if not any(raw) else to_b58(raw)

def get_token_account_mint(token_account_pubkey: str):
    """Decode SPL token-account mint (first 32 bytes of account data)."""
    # If this field is already a mint address (not a token-account), resolve directly.
    direct = normalize_mint_pubkey(token_account_pubkey)
    if direct and direct in KNOWN_TOKENS:
        return direct

    info = fetch_account(token_account_pubkey)
    if not info:
        return None
    owner = info.get("owner")
    if owner not in (
        "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # SPL Token
        "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",  # Token-2022
    ):
        return None
    data_field = info.get("data")
    if not (isinstance(data_field, list) and data_field):
        return None
    try:
        raw = base64.b64decode(data_field[0])
        if len(raw) < 32:
            return None
        mint = read_pubkey_at(raw, 0)
        return normalize_mint_pubkey(mint)
    except Exception:
        return None

def normalize_mint_pubkey(mint_pubkey: str):
    if not mint_pubkey:
        return None
    p = str(mint_pubkey).strip().strip('"').strip("'")
    p = "".join(p.split())

    if p in KNOWN_TOKEN_ALIASES:
        p = KNOWN_TOKEN_ALIASES[p]
    if p in KNOWN_TOKENS:
        return p

    # If one leading character was accidentally dropped, recover it when unique.
    if 42 <= len(p) <= 43:
        matches = [ch + p for ch in _B58 if (ch + p) in KNOWN_TOKENS]
        if len(matches) == 1:
            return matches[0]

    # If one extra leading char was accidentally added, recover by removing one.
    if len(p) >= 43 and p[1:] in KNOWN_TOKENS:
        return p[1:]

    # Fix occasional malformed output like 1111So111... by trimming leading '1'
    # only when the trimmed value becomes a known mint.
    if p.startswith("1"):
        max_trim = min(12, len(p) - 1)
        for i in range(1, max_trim + 1):
            cand = p[i:]
            if cand in KNOWN_TOKENS:
                return cand
    # WSOL canonical fallback
    wsol = "So11111111111111111111111111111111111111112"
    if p.endswith(wsol):
        return wsol
    return p

def token_mint_name(mint_pubkey: str):
    if not mint_pubkey:
        return "?"
    return KNOWN_TOKENS.get(normalize_mint_pubkey(mint_pubkey), "?")

def get_meteora_pool_mints(pool_pubkey: str):
    """Read Meteora DAMM v1 pool token mint A/B from pool state."""
    info = fetch_account(pool_pubkey)
    if not info:
        return None, None
    data_field = info.get("data")
    if not (isinstance(data_field, list) and data_field):
        return None, None
    try:
        raw = base64.b64decode(data_field[0])
        ma = normalize_mint_pubkey(read_pubkey_at(raw, 40))
        mb = normalize_mint_pubkey(read_pubkey_at(raw, 72))
        return ma, mb
    except Exception:
        return None, None

# ═══════════════════════════════════════════
#   ALT
# ═══════════════════════════════════════════

_alt_cache = {}

def fetch_alt_set(alt_pubkey: str) -> set:
    if alt_pubkey in _alt_cache:
        return _alt_cache[alt_pubkey]
    info = fetch_account(alt_pubkey)
    result = set()
    if not info:
        _alt_cache[alt_pubkey] = result
        return result
    data_field = info.get("data")
    if not (isinstance(data_field, list) and data_field):
        _alt_cache[alt_pubkey] = result
        return result
    try:
        raw = base64.b64decode(data_field[0])
        pos = 22
        has_auth = raw[pos] if len(raw) > pos else 0
        pos += 1
        if has_auth:
            pos += 32
        pos += 1
        while pos + 32 <= len(raw):
            addr = raw[pos:pos + 32]
            if any(addr):
                result.add(to_b58(addr))
            pos += 32
    except Exception:
        pass
    _alt_cache[alt_pubkey] = result
    return result

def find_pool_alt(pool_pubkey: str, alt_keys: list) -> str:
    for alt in alt_keys:
        if pool_pubkey in fetch_alt_set(alt):
            return alt
    return alt_keys[0] if alt_keys else ""

# ═══════════════════════════════════════════
#   token labels (فقط Meteora_Pools، فقط نمایش)
# ═══════════════════════════════════════════

def get_pool_token_labels(pool_pubkey: str) -> tuple:
    info = fetch_account(pool_pubkey)
    if not info:
        return "?", "?"
    data_field = info.get("data")
    if not (isinstance(data_field, list) and data_field):
        return "?", "?"
    try:
        raw = base64.b64decode(data_field[0])
        ma  = read_pubkey_at(raw, 40)
        mb  = read_pubkey_at(raw, 72)
        la  = KNOWN_TOKENS.get(ma, (ma[:10] + "…") if ma else "?")
        lb  = KNOWN_TOKENS.get(mb, (mb[:10] + "…") if mb else "?")
        return la, lb
    except Exception:
        return "?", "?"

# Override with normalized mint parsing (kept here to preserve legacy block above).
def get_pool_token_labels(pool_pubkey: str) -> tuple:
    ma, mb = get_meteora_pool_mints(pool_pubkey)
    la = token_mint_name(ma)
    lb = token_mint_name(mb)
    if la == "?" and ma:
        la = ma[:10] + "â€¦"
    if lb == "?" and mb:
        lb = mb[:10] + "â€¦"
    return la, lb

# ═══════════════════════════════════════════
#   instructions
# ═══════════════════════════════════════════

def extract_instructions(msg: dict, meta: dict) -> list:
    results = []
    seen    = set()

    def _add(prog: str, accs: list):
        cfg = DEX.get(prog)
        if not cfg or len(accs) < cfg["min"]:
            return
        pool_pk = accs[cfg["pool_idx"]]
        if pool_pk in seen:
            return
        seen.add(pool_pk)
        results.append({"program": prog, "accounts": accs})

    for ix in msg.get("instructions", []):
        _add(ix.get("programId", ""), ix.get("accounts", []))
    for group in meta.get("innerInstructions", []):
        for ix in group.get("instructions", []):
            _add(ix.get("programId", ""), ix.get("accounts", []))

    return results

# ═══════════════════════════════════════════
#   build_entry  —  هر صرافی قالب مخصوص خودش
# ═══════════════════════════════════════════

def build_entry(prog: str, accs: list, alt: str) -> dict:

    # ── گروه 1 ──────────────────────────────
    if prog == METEORA_POOLS:
        mint_a, mint_b = get_meteora_pool_mints(accs[0])
        mint_a_name = token_mint_name(mint_a)
        mint_b_name = token_mint_name(mint_b)
        return {
            "pubkey": accs[0],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "vaultLpMint": {"a": accs[7], "b": accs[8]},
                "vaultToken":  {"a": accs[5], "b": accs[6]},
                # Extra static accounts often present in Meteora DAMM swap ix.
                # Keeping them here helps downstream builders that need full metas.
                "vaultAuthority": {"a": accs[3], "b": accs[4]},
                "vaultLp": {"a": accs[9], "b": accs[10]},
                "protocolTokenFee": accs[11],
                "vaultProgram": accs[13] if len(accs) > 13 else "",
                "tokenProgram": accs[14] if len(accs) > 14 else "",
                "tokenAccountA": accs[5],
                "tokenAccountB": accs[6],
                "tokenmentA": mint_a if mint_a else "",
                "tokenmentB": mint_b if mint_b else "",
                "tokenmentA_name": mint_a_name,
                "tokenmentB_name": mint_b_name,
            },
        }

    elif prog == GOONFI_V2:
        return {
            "pubkey": accs[1],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "tokenAccountA": accs[4],
                "tokenAccountB": accs[5],
                "accountA":      accs[6],
                "accountB":      accs[7],
            },
        }

    elif prog == RAYDIUM_CLMM:
        mint_a = get_token_account_mint(accs[5])
        mint_b = get_token_account_mint(accs[6])
        mint_a_name = token_mint_name(mint_a)
        mint_b_name = token_mint_name(mint_b)
        return {
            "pubkey": accs[2],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "tokenAccountA": accs[5],
                "tokenAccountB": accs[6],
                "tokenmentA": mint_a if mint_a else "",
                "tokenmentB": mint_b if mint_b else "",
                "tokenmentA_name": mint_a_name,
                "tokenmentB_name": mint_b_name,
            },
        }

    # ── گروه 2 ──────────────────────────────
    elif prog == ALPHAQ:
        return {
            "pubkey": accs[1],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "tokenAccountA": accs[5],
                "tokenAccountB": accs[6],
            },
        }

    elif prog == METEORA_DLMM:
        # DLMM reserve vaults are token accounts; decode their mint addresses.
        mint_a = get_token_account_mint(accs[2])
        mint_b = get_token_account_mint(accs[3])
        mint_a_name = token_mint_name(mint_a)
        mint_b_name = token_mint_name(mint_b)
        return {
            "pubkey": accs[0],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "tokenAccountA": accs[2],
                "tokenAccountB": accs[3],
                "tokenmentA": mint_a if mint_a else "",
                "tokenmentB": mint_b if mint_b else "",
                "tokenmentA_name": mint_a_name,
                "tokenmentB_name": mint_b_name,
            },
        }

    elif prog == PANCAKE:
        return {
            "pubkey": accs[2],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "tokenAccountA": accs[5],
                "tokenAccountB": accs[6],
            },
        }

    # ── گروه 3 ──────────────────────────────
    elif prog == WHIRLPOOL:
        mint_a = get_token_account_mint(accs[4])
        mint_b = get_token_account_mint(accs[6])
        mint_a_name = token_mint_name(mint_a)
        mint_b_name = token_mint_name(mint_b)
        return {
            "pubkey": accs[2],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "tokenAccountA": accs[4],
                "tokenAccountB": accs[6],
                "tokenmentA": mint_a if mint_a else "",
                "tokenmentB": mint_b if mint_b else "",
                "tokenmentA_name": mint_a_name,
                "tokenmentB_name": mint_b_name,
                "oracle":        accs[10],
            },
        }

    elif prog == SOLFI:
        return {
            "pubkey": accs[1],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "tokenAccountA": accs[4],
                "tokenAccountB": accs[5],
            },
        }

    elif prog == ORCA_V2:
        return {
            "pubkey": accs[0],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "tokenAccountA": accs[4],
                "tokenAccountB": accs[5],
                "poolMint":      accs[7],
            },
        }

    # ── گروه 4 ──────────────────────────────
    elif prog == MANIFEST:
        return {
            "pubkey": accs[2],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "tokenAccountA": accs[6],
                "tokenAccountB": accs[7],
                "global":        accs[12],
                "globalVault":   accs[13],
            },
        }

    elif prog == TESSERA:
        return {
            "pubkey": accs[1],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "authority":     accs[0],
                "tokenAccountA": accs[3],
                "tokenAccountB": accs[4],
            },
        }

    elif prog == ONEDEX:
        return {
            "pubkey": accs[1],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "metadataState": accs[0],
                "tokenAccountA": accs[3],
                "tokenAccountB": accs[4],
            },
        }

    # ── گروه 5 ──────────────────────────────
    elif prog == RAYDIUM_CPMM:
        mint_a = get_token_account_mint(accs[6])
        mint_b = get_token_account_mint(accs[7])
        mint_a_name = token_mint_name(mint_a)
        mint_b_name = token_mint_name(mint_b)
        return {
            "pubkey": accs[3],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "authority":        accs[1],
                "tokenAccountA":    accs[6],
                "tokenAccountB":    accs[7],
                "tokenmentA": mint_a if mint_a else "",
                "tokenmentB": mint_b if mint_b else "",
                "tokenmentA_name": mint_a_name,
                "tokenmentB_name": mint_b_name,
                "observationState": accs[12],
            },
        }

    elif prog == RAYDIUM_AMM_V4:
        # Raydium AMM V4 swap account order:
        # [3] AmmCoinVault (Pool 1), [4] AmmPcVault (Pool 2)
        # NOTE: previously [4]/[5] was used, which can capture the wrong account.
        vault_a = accs[3]
        vault_b = accs[4]
        mint_a = get_token_account_mint(vault_a)
        mint_b = get_token_account_mint(vault_b)
        mint_a_name = token_mint_name(mint_a)
        mint_b_name = token_mint_name(mint_b)
        return {
            "pubkey": accs[1],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "authority":     accs[2],
                "tokenAccountA": vault_a,
                "tokenAccountB": vault_b,
                "tokenmentA": mint_a if mint_a else "",
                "tokenmentB": mint_b if mint_b else "",
                "tokenmentA_name": mint_a_name,
                "tokenmentB_name": mint_b_name,
            },
        }

    elif prog == BISONFI:
        # BisonFi swap account order from Solscan:
        # [1] Pair/market, [2] Pool A, [3] Pool B.
        mint_a = get_token_account_mint(accs[2])
        mint_b = get_token_account_mint(accs[3])
        mint_a_name = token_mint_name(mint_a)
        mint_b_name = token_mint_name(mint_b)
        return {
            "pubkey": accs[1],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "market": accs[1],
                "poolA": accs[2],
                "poolB": accs[3],
                "tokenAccountA": accs[2],
                "tokenAccountB": accs[3],
                "tokenmentA": mint_a if mint_a else "",
                "tokenmentB": mint_b if mint_b else "",
                "tokenmentA_name": mint_a_name,
                "tokenmentB_name": mint_b_name,
                "tokenProgramA": accs[6] if len(accs) > 6 else "",
                "tokenProgramB": accs[7] if len(accs) > 7 else "",
                "sysvarInstructions": accs[8] if len(accs) > 8 else "",
            },
        }
    else:  # INVARIANT
        return {
            "pubkey": accs[1],
            "owner":  prog,
            "params": {
                "addressLookupTableAddress": alt,
                "routingGroup": 2,
                "state":            accs[0],
                "tickmap":          accs[2],
                "tokenAccountA":    accs[3],
                "tokenAccountB":    accs[4],
                "programAuthority": accs[7],
            },
        }

# ═══════════════════════════════════════════
#   fetch signatures  با pagination
# ═══════════════════════════════════════════

def fetch_signature_page(page_limit: int, before: str = None):
    """
    Fetch one page from getSignaturesForAddress.
    Returns:
      raw_items: all signatures (including failed tx)
      ok_items : only signatures with err == None
      next_before: signature cursor for next page
    """
    params = [WALLET, {"limit": page_limit, "commitment": "confirmed"}]
    if before:
        params[1]["before"] = before

    resp = rpc_call("getSignaturesForAddress", params)
    raw_items = resp.get("result", []) or []
    ok_items = [s for s in raw_items if not s.get("err")]
    next_before = raw_items[-1]["signature"] if raw_items else None
    return raw_items, ok_items, next_before

    """تا limit تراکنش با pagination (هر بار max 1000)."""
    sigs   = []
    before = None
    batch  = min(limit, 1000)

    while len(sigs) < limit:
        params = [WALLET, {"limit": batch, "commitment": "confirmed"}]
        if before:
            params[1]["before"] = before

        resp = rpc_call("getSignaturesForAddress", params)
        items = [s for s in resp.get("result", []) if not s.get("err")]
        if not items:
            break

        sigs.extend(items)
        if len(items) < batch:
            break   # آخرین صفحه

        before = items[-1]["signature"]
        remaining = limit - len(sigs)
        batch = min(remaining, 1000)
        time.sleep(0.2)

    return sigs[:limit]

# ═══════════════════════════════════════════
#                   MAIN
# ═══════════════════════════════════════════

def main():
    print("=" * 62)
    print("  Universal Pool Extractor  - 16 DEX")
    print(f"  Wallet : {WALLET[:28]}...")
    print(f"  Limit  : {LIMIT:,} transactions")
    print("=" * 62 + "\n")

    print("Fetching signatures (pagination in staged chunks)...")

    results    = []
    seen_pools = set()
    cnt        = {p: 0 for p in DEX}

    before = None
    fetched_raw = 0
    fetched_ok = 0
    processed_ok = 0
    stage = 0

    while fetched_raw < LIMIT:
        need = min(CHUNK_SIZE, LIMIT - fetched_raw)
        raw_items, ok_items, next_before = fetch_signature_page(need, before)
        if not raw_items:
            break

        stage += 1
        fetched_raw += len(raw_items)
        fetched_ok += len(ok_items)
        print(
            f"  stage {stage:02d}: fetched={len(raw_items):4d}  ok={len(ok_items):4d}  total={fetched_raw:5d}/{LIMIT}"
        )

        for sig_item in ok_items:
            sig = sig_item["signature"]
            processed_ok += 1
            if processed_ok % 500 == 0:
                print(f"  ... processed_ok={processed_ok} pools={len(results)}")

            try:
                resp = rpc_call("getTransaction", [sig, {
                    "encoding":                      "jsonParsed",
                    "maxSupportedTransactionVersion": 0,
                    "commitment":                    "confirmed",
                }])
                tx = resp.get("result")
            except Exception as e:
                print(f"   X {sig[:20]}... {e}")
                time.sleep(0.25)
                continue

            if not tx:
                time.sleep(0.05)
                continue

            msg  = tx["transaction"]["message"]
            meta = tx["meta"]
            alts = [a["accountKey"] for a in msg.get("addressTableLookups", [])]

            ixs = extract_instructions(msg, meta)
            if not ixs:
                time.sleep(0.03)
                continue

            for ix in ixs:
                prog    = ix["program"]
                accs    = ix["accounts"]
                cfg     = DEX[prog]
                pool_pk = accs[cfg["pool_idx"]]

                if pool_pk in seen_pools:
                    continue

                alt   = find_pool_alt(pool_pk, alts)
                entry = build_entry(prog, accs, alt)
                seen_pools.add(pool_pk)
                cnt[prog] += 1
                results.append(entry)

                if prog == METEORA_POOLS:
                    la, lb = get_pool_token_labels(pool_pk)
                    print(f"   OK {cfg['name']:<18} {la}/{lb}  {pool_pk[:20]}...")
                else:
                    print(f"   OK {cfg['name']:<18} {pool_pk[:20]}...")

            time.sleep(0.03)

        if len(raw_items) < need:
            break
        before = next_before
        time.sleep(0.2)

    print(f"\n   OK fetched_raw={fetched_raw:,}  usable_ok={fetched_ok:,}  processed_ok={processed_ok:,}\n")

    if processed_ok == 0:
        print("No processable transactions found")
        sys.exit(1)

    results.sort(key=lambda e: e["owner"])

    print("\n" + "=" * 62)
    total_found = 0
    for prog, c in cnt.items():
        if c > 0:
            print(f"  {DEX[prog]['name']:<20} {c:>6} pool")
            total_found += c
    print(f"  {'-'*30}")
    print(f"  {'TOTAL':<20} {total_found:>6} -> {OUTPUT_JSON}")
    print(f"  RPC cache  : {len(_acct_cache):,} accounts")
    print(f"  ALT cache  : {len(_alt_cache):,} ALTs")
    print("=" * 62 + "\n")

    if not results:
        print("No pool found")
        sys.exit(0)

    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    with open(OUTPUT_ANNOTATED, "w") as f:
        f.write("// Universal Pool Extractor - 16 DEX\n")
        f.write(f"// Wallet: {WALLET}\n")
        f.write(f"// Total: {len(results)} pools\n\n[\n")
        for idx, e in enumerate(results):
            comma = "," if idx < len(results) - 1 else ""
            name  = DEX[e["owner"]]["name"]
            f.write(f"  // [{idx+1}] {name}  {e['pubkey'][:20]}...\n")
            block = json.dumps(e, indent=2).replace("\n", "\n  ")
            f.write(f"  {block}{comma}\n\n")
        f.write("]\n")

    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {OUTPUT_ANNOTATED}\n")
    return
    print("═" * 62)
    print("  Universal Pool Extractor  —  16 DEX")
    print(f"  Wallet : {WALLET[:28]}...")
    print(f"  Limit  : {LIMIT:,} transactions")
    print("═" * 62 + "\n")

    print("📡 Fetching signatures (pagination)...")
    sig_items = fetch_all_signatures(LIMIT)
    sigs = [s["signature"] for s in sig_items]
    print(f"   ✅ {len(sigs):,} transactions\n")

    if not sigs:
        print("❌ هیچ تراکنشی پیدا نشد")
        sys.exit(1)

    results    = []
    seen_pools = set()
    cnt        = {p: 0 for p in DEX}

    for i, sig in enumerate(sigs, 1):
        if i % 500 == 0:
            print(f"  ... [{i}/{len(sigs)}] pools={len(results)}")

        try:
            resp = rpc_call("getTransaction", [sig, {
                "encoding":                      "jsonParsed",
                "maxSupportedTransactionVersion": 0,
                "commitment":                    "confirmed",
            }])
            tx = resp.get("result")
        except Exception as e:
            print(f"   ❌ {sig[:20]}... {e}")
            time.sleep(0.3)
            continue

        if not tx:
            time.sleep(0.1)
            continue

        msg  = tx["transaction"]["message"]
        meta = tx["meta"]
        alts = [a["accountKey"] for a in msg.get("addressTableLookups", [])]

        ixs = extract_instructions(msg, meta)
        if not ixs:
            time.sleep(0.1)
            continue

        for ix in ixs:
            prog    = ix["program"]
            accs    = ix["accounts"]
            cfg     = DEX[prog]
            pool_pk = accs[cfg["pool_idx"]]

            if pool_pk in seen_pools:
                continue

            alt   = find_pool_alt(pool_pk, alts)
            entry = build_entry(prog, accs, alt)
            seen_pools.add(pool_pk)
            cnt[prog] += 1
            results.append(entry)

            if prog == METEORA_POOLS:
                la, lb = get_pool_token_labels(pool_pk)
                print(f"   ✅ {cfg['name']:<18} {la}/{lb}  {pool_pk[:20]}...")
            else:
                print(f"   ✅ {cfg['name']:<18} {pool_pk[:20]}...")

        time.sleep(0.12)

    # ── ذخیره ──
    results.sort(key=lambda e: e["owner"])

    print("\n" + "═" * 62)
    total_found = 0
    for prog, c in cnt.items():
        if c > 0:
            print(f"  {DEX[prog]['name']:<20} {c:>6} pool")
            total_found += c
    print(f"  {'─'*30}")
    print(f"  {'کل':<20} {total_found:>6} → {OUTPUT_JSON}")
    print(f"  RPC cache  : {len(_acct_cache):,} accounts")
    print(f"  ALT cache  : {len(_alt_cache):,} ALTs")
    print("═" * 62 + "\n")

    if not results:
        print("❌ هیچ pool پیدا نشد")
        sys.exit(0)

    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    with open(OUTPUT_ANNOTATED, "w") as f:
        f.write("// Universal Pool Extractor — 16 DEX\n")
        f.write(f"// Wallet: {WALLET}\n")
        f.write(f"// Total: {len(results)} pools\n\n[\n")
        for idx, e in enumerate(results):
            comma = "," if idx < len(results) - 1 else ""
            name  = DEX[e["owner"]]["name"]
            f.write(f"  // [{idx+1}] {name}  {e['pubkey'][:20]}...\n")
            block = json.dumps(e, indent=2).replace("\n", "\n  ")
            f.write(f"  {block}{comma}\n\n")
        f.write("]\n")

    print(f"📄 {OUTPUT_JSON}")
    print(f"📝 {OUTPUT_ANNOTATED}\n")


if __name__ == "__main__":
    main()
