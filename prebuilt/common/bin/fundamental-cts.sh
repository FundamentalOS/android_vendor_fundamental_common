#!/system/bin/sh
# FundamentalOS: enable Circle to Search (long-press nav handle) launcher flags
for kv in ENABLE_LONG_PRESS_NAV_HANDLE:true ANIMATE_LPNH:true SHRINK_NAV_HANDLE_ON_PRESS:true LPNH_TIMEOUT_MS:400 LPNH_SLOP_PERCENTAGE:71; do
    device_config put launcher "${kv%%:*}" "${kv##*:}"
done
device_config set_sync_disabled_for_tests persistent
