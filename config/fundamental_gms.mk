# FundamentalOS GMS extras: Circle to Search enablement + conditional Chrome.

# Circle to Search: seed launcher device_config flags at boot (Trebuchet/Quickstep
# has the LPNH + ContextualSearch code; these flags gate it). Routing package is set
# via config_defaultContextualSearchPackageName in the framework overlay.
PRODUCT_COPY_FILES += \
    vendor/fundamental/prebuilt/common/bin/fundamental-cts.sh:$(TARGET_COPY_OUT_PRODUCT)/etc/fundamental-cts.sh \
    vendor/fundamental/prebuilt/common/etc/init/fundamental-cts.rc:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/init/fundamental-cts.rc

# Google Chrome (Trichrome) — replaces Jelly via overrides when the tree is present.
$(call inherit-product-if-exists, vendor/chrome/config/chrome.mk)
