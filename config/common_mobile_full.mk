# Inherit common FundamentalOS stuff
$(call inherit-product, vendor/fundamental/common/config/common_mobile.mk)

PRODUCT_SIZE := full

# Apps carried over from LineageOS (FundamentalOS forks)
PRODUCT_PACKAGES += \
    Camelot \
    Etar \
    Recorder

# Include GoogleSansFlex font
$(call inherit-product-if-exists, external/google-fonts/google-sans-flex/fonts.mk)

# Fonts
PRODUCT_PACKAGES += \
    fonts_customization.xml \
    FontGoogleSansFlexOverlay

# Include the LatinIME dictionaries
PRODUCT_PACKAGE_OVERLAYS += vendor/fundamental/common/overlay/dictionaries
PRODUCT_ENFORCE_RRO_EXCLUDED_OVERLAYS += vendor/fundamental/common/overlay/dictionaries

# Chrome, Photos and YouTube Music come from GApps; keep the AOSP stand-ins out.
TARGET_EXCLUDES_AOSP_MEDIA_APPS := true
