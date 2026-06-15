//! Missing-account learning system — neutralized (simplified to the reference
//! design).
//!
//! The previous implementation ran a background RPC fetcher and continuously
//! wrote several artifacts (`missing_sim_accounts_pending.json`,
//! `missing_sim_account_cache.json`, `missing_sim_account_errors.json`,
//! `missing_sim_account_live.json`, `missing_accounts_8000.json`). That loop
//! added a lot of noise and complexity but did not change whether a route can
//! be simulated: a genuinely-missing required account is already handled inline
//! by the simulator (the route is dropped fail-closed), and pool/vault/mint
//! state is kept fresh by the Yellowstone subscription + startup RPC prefetch.
//!
//! The whole subsystem is reduced to no-ops here. The public surface
//! (`MissingAccountEvent`, `AutoMissingAccountsHandle::record`, `start`,
//! `load_cache_into_account_cache`) is preserved so the call sites in
//! `litesvm_sim` / `main` compile unchanged.

use solana_client::rpc_client::RpcClient;
use solana_sdk::pubkey::Pubkey;
use std::path::Path;
use std::sync::Arc;

use crate::account_cache::AccountCache;

/// Event the hot simulation path used to enqueue for background fetching.
/// Kept as a type so call sites are unchanged; constructing one is now inert.
#[derive(Clone, Debug)]
pub struct MissingAccountEvent {
    pub pubkey: Pubkey,
    pub route_sig: u128,
    pub route_labels: String,
    pub programs: String,
    pub source: String,
    pub is_signer: bool,
    pub is_writable: bool,
    pub created_by_setup: bool,
}

/// Cheap handle passed to the hot simulation path. `record()` is now a no-op.
#[derive(Clone, Default)]
pub struct AutoMissingAccountsHandle;

impl AutoMissingAccountsHandle {
    #[inline]
    pub fn record(&self, _event: MissingAccountEvent) {}
}

/// No-op: the background learning task is no longer started.
pub fn start(
    _manual_accounts_root: &Path,
    _rpc: Arc<RpcClient>,
    _fallback_rpcs: Arc<Vec<Arc<RpcClient>>>,
    _account_cache: AccountCache,
) -> AutoMissingAccountsHandle {
    AutoMissingAccountsHandle
}

/// No-op: previously-learned accounts are no longer reloaded from disk. Pool
/// and mint state is restored by the mix.json prefetch + Yellowstone stream.
pub fn load_cache_into_account_cache(_manual_accounts_root: &Path, _cache: &AccountCache) -> usize {
    0
}
