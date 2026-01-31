#!/usr/bin/env python3
"""Test deduplication hash standardization"""


import state_store
from bot.constants import TRIP_OW, TRIP_RT

# Test make_offer_hash function exists and works
try:
    # Test RT hash
    h_rt = state_store.make_offer_hash("RT", "GIG", "ORL", "2026-02-01", "2026-02-08", 150)
    print(f"✓ RT hash: {h_rt[:16]}...")
    assert len(h_rt) == 64, "SHA-256 should produce 64-char hex"
    
    # Test OW hash
    h_ow = state_store.make_offer_hash("OW", "GIG", "MIA", "2026-02-01", None, 200)
    print(f"✓ OW hash: {h_ow[:16]}...")
    assert len(h_ow) == 64, "SHA-256 should produce 64-char hex"
    
    # Test same input produces same hash (stability)
    h_rt_2 = state_store.make_offer_hash("RT", "GIG", "ORL", "2026-02-01", "2026-02-08", 150)
    assert h_rt == h_rt_2, "Hash should be stable across calls"
    print("✓ Hash is stable across executions")
    
    # Test different inputs produce different hashes
    h_rt_diff = state_store.make_offer_hash("RT", "GIG", "ORL", "2026-02-01", "2026-02-08", 151)
    assert h_rt != h_rt_diff, "Different inputs should produce different hashes"
    print("✓ Different inputs produce different hashes")
    

    # Verifica se as constantes estão corretas
    assert TRIP_OW == "OW", "TRIP_OW should be 'OW'"
    assert TRIP_RT == "RT", "TRIP_RT should be 'RT'"
    print("✓ Constants available in bot.constants")
    
    print("\n✓✓✓ Deduplication standardization verified ✓✓✓")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
