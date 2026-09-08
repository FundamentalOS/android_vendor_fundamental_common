# Inherit common FundamentalOS stuff
$(call inherit-product, vendor/fundamental/common/config/common_mobile.mk)

PRODUCT_SIZE := full

# Include GoogleSansFlex font
$(call inherit-product-if-exists, external/google-fonts/google-sans-flex/fonts.mk)

# Fonts
PRODUCT_PACKAGES += \
    fonts_customization.xml \
    FontGoogleSansFlexOverlay

# Include the LatinIME dictionaries
PRODUCT_PACKAGE_OVERLAYS += vendor/fundamental/common/overlay/dictionaries
PRODUCT_ENFORCE_RRO_EXCLUDED_OVERLAYS += vendor/fundamental/common/overlay/dictionaries
