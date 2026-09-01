# Inherit mobile full common Lineage stuff
$(call inherit-product, vendor/fundamental/config/common_mobile_full.mk)

# Enable support of one-handed mode
PRODUCT_PRODUCT_PROPERTIES += \
    ro.support_one_handed_mode?=true

$(call inherit-product, vendor/fundamental/config/telephony.mk)

# Google apps (MindTheGapps) - minimal GMS
$(call inherit-product, vendor/gapps/arm64/arm64-vendor.mk)

# FundamentalOS GMS extras (Circle to Search + Chrome)
$(call inherit-product, vendor/fundamental/config/fundamental_gms.mk)
