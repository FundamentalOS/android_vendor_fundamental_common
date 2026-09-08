# Allow vendor/extra to override any property by setting it first
$(call inherit-product-if-exists, vendor/extra/product.mk)

# Exclude repos from bp scanning
PRODUCT_SOURCE_ROOT_DIRS += -kernel/platform
PRODUCT_SOURCE_ROOT_DIRS += -prebuilts/misc/protobuf_vendorcompat

# Allow vendor prebuilt repos to exclude themselves from bp scanning
-include $(sort $(wildcard vendor/*/*/exclude-bp.mk))

PRODUCT_BRAND ?= FundamentalOS

ifeq ($(PRODUCT_GMS_CLIENTID_BASE),)
PRODUCT_PRODUCT_PROPERTIES += \
    ro.com.google.clientidbase=android-google
else
PRODUCT_PRODUCT_PROPERTIES += \
    ro.com.google.clientidbase=$(PRODUCT_GMS_CLIENTID_BASE)
endif

ifeq ($(PRODUCT_IS_ATV),true)
ifeq ($(PRODUCT_ATV_CLIENTID_BASE),)
PRODUCT_PRODUCT_PROPERTIES += \
    ro.oem.key1=ATV00100020
else
PRODUCT_PRODUCT_PROPERTIES += \
    ro.oem.key1=$(PRODUCT_ATV_CLIENTID_BASE)
endif
endif

ifeq ($(TARGET_BUILD_VARIANT),eng)
# Disable ADB authentication
PRODUCT_SYSTEM_EXT_PROPERTIES += ro.adb.secure=0
else
ifdef WITH_ADB_INSECURE
# Forcebly disable ADB authentication
PRODUCT_SYSTEM_EXT_PROPERTIES += ro.adb.secure=0
else
# Enable ADB authentication
PRODUCT_SYSTEM_EXT_PROPERTIES += ro.adb.secure=1

# Set ro.debuggable=0 for userdebug
PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG := true
endif

# Disable extra StrictMode features on all non-engineering builds
PRODUCT_PRODUCT_PROPERTIES += persist.sys.strictmode.disable=true
endif

# A/B: allow downgrades on non-user builds
ifneq ($(strip $(AB_OTA_PARTITIONS) $(AB_OTA_POSTINSTALL_CONFIG)),)
ifneq ($(TARGET_BUILD_VARIANT),user)
PRODUCT_PRODUCT_PROPERTIES += \
    ro.ota.allow_downgrade=true
endif
endif

# FundamentalOS broadcast actions whitelist
PRODUCT_COPY_FILES += \
    vendor/fundamental/common/config/permissions/fundamental-sysconfig.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/sysconfig/fundamental-sysconfig.xml

# FundamentalOS init rc file
PRODUCT_COPY_FILES += \
    vendor/fundamental/common/prebuilt/common/etc/init/init.fundamental-system_ext.rc:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/init/init.fundamental-system_ext.rc

# Enable SIP+VoIP on all targets
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.software.sip.voip.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/permissions/android.software.sip.voip.xml

# Credential storage
PRODUCT_PACKAGES += \
    android.software.credentials.prebuilt.xml

# Enable wireless Xbox 360 controller support
PRODUCT_COPY_FILES += \
    frameworks/base/data/keyboards/Vendor_045e_Product_028e.kl:$(TARGET_COPY_OUT_PRODUCT)/usr/keylayout/Vendor_045e_Product_0719.kl

# Component overrides
PRODUCT_PACKAGES += \
    fundamental-component-overrides.xml

# FundamentalOS: Pixel lockscreen clock-face plugins (SystemUIClocks-*) imported from
# stock BP4A (payload in packages/apps/SystemUIClocks). Generic SystemUI ClockProviderPlugins,
# so ROM-wide rather than device-bound; user-build loading is enabled via
# config_pluginAllowlist in vendor/fundamental/common/overlay/common. if-exists so a device
# without the prebuilt repo still builds.
$(call inherit-product-if-exists, packages/apps/SystemUIClocks/clocks.mk)

# Enforce privapp-permissions whitelist
PRODUCT_PRODUCT_PROPERTIES += \
    ro.control_privapp_permissions=enforce

# Do not include art debug targets
PRODUCT_ART_TARGET_INCLUDE_DEBUG_BUILD := false

# Strip the local variable table and the local variable type table to reduce
# the size of the system image. This has no bearing on stack traces, but will
# leave less information available via JDWP.
PRODUCT_MINIMIZE_JAVA_DEBUG_INFO := true

# Enable whole-program R8 Java optimizations for SystemUI and system_server,
# but also allow explicit overriding for testing and development.
SYSTEM_OPTIMIZE_JAVA ?= true
SYSTEMUI_OPTIMIZE_JAVA ?= true

# Disable vendor restrictions
PRODUCT_RESTRICT_VENDOR_FILES := false

ifneq ($(TARGET_DISABLE_EPPE),true)
# Require all requested packages to exist
# AOSP 17 product makefiles list two Google-internal modules that have no
# open-source definition (base_system.mk: com.android.ranging behind
# RELEASE_RANGING_STACK, base_vendor.mk: vendor_tracing_descriptors); AOSP
# itself only warns about them.
$(call enforce-product-packages-exist-internal,$(lastword $(_include_stack)),product_manifest.xml rild Calendar android.hidl.memory@1.0-impl.vendor vndk_apex_snapshot_package com.android.ranging vendor_tracing_descriptors)
endif

# Bootanimation
TARGET_SCREEN_WIDTH ?= 1080
TARGET_SCREEN_HEIGHT ?= 1920
PRODUCT_PACKAGES += \
    bootanimation.zip \
    bootanimation-dark.zip

# FundamentalOS apps
ifeq ($(PRODUCT_IS_ATV),)
PRODUCT_PACKAGES += \
    ExactCalculator
endif

# Setup wizard (FundamentalOS fork of the LineageOS one; overrides Provision)
PRODUCT_PACKAGES += \
    FundamentalSetupWizard

# Config
PRODUCT_PACKAGES += \
    SimpleDeviceConfig

# Extra tools
PRODUCT_PACKAGES += \
    bash \
    curl \
    getcap \
    htop \
    nano \
    setcap \
    vim

PRODUCT_PACKAGES += \
    nano_recovery

PRODUCT_ARTIFACT_PATH_REQUIREMENT_ALLOWED_LIST += \
    system/bin/curl \
    system/bin/getcap \
    system/bin/setcap \
    system/%/libzstd.so

# fastbootd
ifneq ($(TARGET_DISABLE_FASTBOOTD),true)
PRODUCT_PACKAGES += \
    fastbootd
endif

# Openssh
PRODUCT_PACKAGES += \
    scp \
    sftp \
    ssh \
    sshd \
    sshd_config \
    ssh-keygen \
    start-ssh

PRODUCT_COPY_FILES += \
    vendor/fundamental/common/prebuilt/common/etc/init/init.openssh.rc:$(TARGET_COPY_OUT_PRODUCT)/etc/init/init.openssh.rc

# OverlayFS
PRODUCT_PACKAGES_DEBUG += \
    disable-overlays

# Storage manager
PRODUCT_PRODUCT_PROPERTIES += \
    ro.storage_manager.enabled=true

# SystemUI
PRODUCT_DEXPREOPT_SPEED_APPS += \
    CarSystemUI \
    SystemUI \
    SystemUIFundamental

PRODUCT_PRODUCT_PROPERTIES += \
    dalvik.vm.systemuicompilerfilter=speed

# FundamentalOS: SystemUIFundamental overrides SystemUI (adds the Pixel
# SystemUI feature ports); ColumbusService provides Quick Tap.
PRODUCT_PACKAGES += \
    SystemUIFundamental \
    ColumbusService

ifeq ($(TARGET_BUILD_VARIANT),userdebug)
PRODUCT_PRODUCT_PROPERTIES += \
    debug.sf.enable_transaction_tracing=false
endif

# Audio files
$(call inherit-product, vendor/fundamental/common/audio/audio.mk)

# SetupWizard
PRODUCT_PRODUCT_PROPERTIES += \
    setupwizard.theme=glif_v4 \
    setupwizard.feature.day_night_mode_enabled=true

PRODUCT_ENFORCE_RRO_EXCLUDED_OVERLAYS += vendor/fundamental/common/overlay/no-rro
PRODUCT_PACKAGE_OVERLAYS += \
    vendor/fundamental/common/overlay/common \
    vendor/fundamental/common/overlay/no-rro

PRODUCT_PACKAGES += \
    DocumentsUIOverlay \
    NetworkStackOverlay \
    PermissionControllerOverlay

# Translations
CUSTOM_LOCALES += \
    ast_ES \
    ckb_IQ \
    ckb_IR \
    gd_GB \
    cy_GB \
    fur_IT \
    nn_NO

include vendor/fundamental/common/config/version.mk

-include vendor/lineage-priv/keys/keys.mk

-include $(WORKSPACE)/build_env/image-auto-bits.mk

# FundamentalOS: create the Play Integrity forge config dir (/data/misc/fundamental) at boot
PRODUCT_COPY_FILES += \
    vendor/fundamental/common/prebuilt/common/etc/init/fundamental_integrity.rc:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/init/fundamental_integrity.rc

# FundamentalOS keybox fetch service
PRODUCT_PACKAGES += FundamentalForge
