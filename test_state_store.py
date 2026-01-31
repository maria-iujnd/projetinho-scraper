#!/usr/bin/env python3
"""Test state_store imports and basic functionality"""
import sys

# Test import
try:
    import state_store
    print("✓ state_store imports successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test setup_database
try:
    state_store.setup_database()
    print("✓ setup_database() works")
except Exception as e:
    print(f"✗ setup_database() failed: {e}")
    sys.exit(1)

# Test mark_good
try:
    state_store.mark_good("GIG", "ORL", "RT", "2026-02-01", "2026-02-08", 150)
    print("✓ mark_good() works for RT")
except Exception as e:
    print(f"✗ mark_good() failed: {e}")
    sys.exit(1)

# Test mark_good with OW (None return_date)
try:
    state_store.mark_good("GIG", "MIA", "OW", "2026-02-01", None, 200)
    print("✓ mark_good() works for OW")
except Exception as e:
    print(f"✗ mark_good() OW failed: {e}")
    sys.exit(1)

# Test mark_bad
try:
    state_store.mark_bad("GIG", "ORL", "RT", "2026-02-01", "2026-02-08", 500)
    print("✓ mark_bad() works for RT")
except Exception as e:
    print(f"✗ mark_bad() failed: {e}")
    sys.exit(1)

# Test mark_no_data
try:
    state_store.mark_no_data("GIG", "BOG", "OW", "2026-02-05", None)
    print("✓ mark_no_data() works for OW")
except Exception as e:
    print(f"✗ mark_no_data() failed: {e}")
    sys.exit(1)

# Test should_check
try:
    result = state_store.should_check("GIG", "ORL", "RT", "2026-02-01", "2026-02-08")
    print(f"✓ should_check() works (result: {result})")
except Exception as e:
    print(f"✗ should_check() failed: {e}")
    sys.exit(1)

# Test should_check with OW
try:
    result = state_store.should_check("GIG", "MIA", "OW", "2026-02-01", None)
    print(f"✓ should_check() works for OW (result: {result})")
except Exception as e:
    print(f"✗ should_check() OW failed: {e}")
    sys.exit(1)

# Test get_rt_avg_price
try:
    result = state_store.get_rt_avg_price("GIG", "ORL", min_samples=1)
    print(f"✓ get_rt_avg_price() works (result: {result})")
except Exception as e:
    print(f"✗ get_rt_avg_price() failed: {e}")
    sys.exit(1)

# Test is_announced / mark_announced
try:
    state_store.mark_announced("test_hash_123")
    is_ann = state_store.is_announced("test_hash_123")
    print(f"✓ mark_announced() and is_announced() work (found: {is_ann})")
except Exception as e:
    print(f"✗ announcements functions failed: {e}")
    sys.exit(1)

# Test stubs
try:
    state_store.cleanup_expired_monitors()
    state_store.get_monitor_dates("GIG", "ORL", "OW")
    state_store.pick_dates_spread_with_cooldown("GIG", "ORL", "RT", None, 10, 3)
    state_store.touch_monitor_checked("GIG", "ORL", "2026-02-01", "OW")
    state_store.add_to_monitor("GIG", "ORL", "2026-02-01")
    state_store.get_historical_avg_price("GIG", "ORL")
    state_store.get_historical_avg_price_rt("GIG", "ORL", None, 150)
    print("✓ All stub functions work")
except Exception as e:
    print(f"✗ Stub functions failed: {e}")
    sys.exit(1)

print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
