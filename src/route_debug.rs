//! Optional route / signer debug log.
//!
//! When `performance.route_debug_path` is non-empty, the bot appends one JSON
//! object per line to that file recording, for every circular route that reaches
//! the candidate stage:
//!   * the signing wallet pubkey (the keypair that signs every Jito bundle), and
//!   * the exact route Metis returned, broken down per hop into
//!     `{dex, inputMint, outputMint}`.
//!
//! This lets the operator confirm two things independently of the running
//! pipeline: (1) transactions are signed by the expected wallet, and (2) Metis
//! only ever returns DIRECT routes — a correct circular direct route looks like
//! `WSOL->USDC` then `USDC->WSOL` (hop_count == 2, one hop per leg).
//!
//! Writing is best-effort: any IO error is reported to stderr and otherwise
//! ignored so debug logging can never disrupt trading.

use std::fs::OpenOptions;
use std::io::Write;
use std::path::Path;

use serde_json::{json, Value};

/// Break a Metis `route_plan` down into `[{dex, inputMint, outputMint}]`.
pub fn route_hops(route_plan: &Value) -> Vec<Value> {
    route_plan
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|hop| hop.get("swapInfo"))
        .map(|swap_info| {
            json!({
                "dex": swap_info.get("label").cloned().unwrap_or(Value::Null),
                "inputMint": swap_info.get("inputMint").cloned().unwrap_or(Value::Null),
                "outputMint": swap_info.get("outputMint").cloned().unwrap_or(Value::Null),
            })
        })
        .collect()
}

/// Append one route record: signing wallet + the per-hop route Metis returned.
pub fn log_route(
    path: &str,
    signer_wallet: &str,
    route_sig: u128,
    only_direct: bool,
    hop_count: usize,
    route_plan: &Value,
) {
    if path.is_empty() {
        return;
    }
    let record = json!({
        "ts_ms": now_ms(),
        "kind": "route",
        "signer_wallet": signer_wallet,
        "route_sig": format!("{route_sig:032x}"),
        "only_direct": only_direct,
        "hop_count": hop_count,
        "hops": route_hops(route_plan),
    });
    if let Err(e) = append_line(path, &record.to_string()) {
        eprintln!("[route_debug_write_failed] path={path} error={e}");
    }
}

/// Append a one-off startup record so the signing wallet is recorded even
/// before (or without) any route being found.
pub fn log_startup(path: &str, signer_wallet: &str, only_direct_routes: bool) {
    if path.is_empty() {
        return;
    }
    let record = json!({
        "ts_ms": now_ms(),
        "kind": "startup",
        "signer_wallet": signer_wallet,
        "only_direct_routes": only_direct_routes,
    });
    if let Err(e) = append_line(path, &record.to_string()) {
        eprintln!("[route_debug_write_failed] path={path} error={e}");
    }
}

fn append_line(path: &str, line: &str) -> std::io::Result<()> {
    if let Some(parent) = Path::new(path).parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)?;
        }
    }
    let mut file = OpenOptions::new().create(true).append(true).open(path)?;
    writeln!(file, "{line}")
}

fn now_ms() -> u128 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0)
}
