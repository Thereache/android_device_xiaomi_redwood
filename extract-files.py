#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import os
import subprocess

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

namespace_imports = [
    'device/xiaomi/redwood',
    'hardware/qcom-caf/common/libqti-perfd-client',
    'hardware/qcom-caf/sm8350',
    'hardware/qcom-caf/wlan',
    'hardware/xiaomi',
    'vendor/qcom/opensource/commonsys/display',
    'vendor/qcom/opensource/commonsys-intf/display',
    'vendor/qcom/opensource/dataservices',
    'vendor/qcom/opensource/display',
    'vendor/xiaomi/redwood',
]

def lib_fixup_vendor_suffix(lib: str, partition: str, *args, **kwargs):
    return f'{lib}_{partition}' if partition == 'vendor' else None

def split_zip(ctx, file, file_path, *args, **kwargs):
    subprocess.run(['split', '--bytes=20M', '-d', file_path, f'{file_path}.part'], check=True)

def add_to_gitignore(ctx, file, file_path, *args, **kwargs):
    # Navigate to Android root from script location, then target the vendor directory
    script_dir = os.path.dirname(__file__)
    gitignore_path = os.path.abspath(os.path.join(script_dir, '../../..', 'vendor/xiaomi/redwood', '.gitignore'))
    
    # Ensure the parent directories exist
    os.makedirs(os.path.dirname(gitignore_path), exist_ok=True)
    
    entry = 'proprietary/vendor/etc/faceunlock/resources.zip\n'
    
    # Check if the entry already exists before appending
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            if entry in f.readlines():
                return
                
    with open(gitignore_path, 'a') as f:
        f.write(entry)


lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
    (
        'com.qualcomm.qti.dpm.api@1.0',
        'libmmosal',
        'vendor.qti.diaghal@1.0',
        'vendor.qti.imsrtpservice@3.0',
    ): lib_fixup_vendor_suffix,
}

blob_fixups: blob_fixups_user_type = {
    'vendor/etc/faceunlock/resources.zip': blob_fixup()
        .call(split_zip)
        .call(add_to_gitignore),
    ('vendor/etc/media_lahaina/video_system_specs.json', 'vendor/etc/media_yupik_v1/video_system_specs.json'): blob_fixup()
        .regex_replace('"max_retry_alloc_output_timeout": 10000,', '"max_retry_alloc_output_timeout": 0,'),
    'vendor/etc/vintf/manifest/c2_manifest_vendor.xml': blob_fixup()
        .regex_replace('.*ozoaudio.*\n?', ''),
    ('vendor/etc/camera/pureShot_parameter.xml', 'vendor/etc/camera/pureView_parameter.xml'): blob_fixup()
        .regex_replace(r'=(\d+)>', r'="\1">'),
    ('vendor/etc/media_codecs.xml', 'vendor/etc/media_codecs_lahaina.xml', 'vendor/etc/media_codecs_system_default.xml', 'vendor/etc/media_codecs_system_default_lahaina.xml', 'vendor/etc/media_codecs_system_default_yupik.xml'): blob_fixup()
        .regex_replace('.+media_codecs_(c2_audio|google_audio|google_c2|google_telephony|vendor_audio).+\n', '')
        .regex_replace(r'(?s)(<Settings.*?>)',r'\1\n        <Domain name="telephony" enabled="true" />'),
    ('vendor/etc/media_codecs_yupik_v1.xml', 'vendor/etc/media_codecs_lahaina_vendor.xml'): blob_fixup()
        .regex_replace('.+media_codecs_with_dolby.+\n', ''),
    'vendor/etc/init/netmgrd.rc': blob_fixup()
        .regex_replace(r'    #Load rmnet_core driver\n(?:    exec [^\n]*modprobe[^\n]*\n)+',
                       '    # RMNET drivers are built into the kernel.\n')
        .regex_replace(r'\non property:persist\.vendor\.data\.(?:shs|perf|offload)_ko_load=[0-3]\n(?:    exec [^\n]*modprobe[^\n]*\n)+', ''),
    ('vendor/etc/init/android.hardware.drm@1.3-service.widevine.rc', 'vendor/etc/init/vendor.qti.media.c2@1.0-service.rc'): blob_fixup()
        .regex_replace('writepid /dev/cpuset/foreground/tasks', 'task_profiles ProcessCapacityHigh'),
    'vendor/etc/public.libraries.txt': blob_fixup()
        .regex_replace('.*libqti-perfd-client.so.*\n?', '')
        .regex_replace(r'(?s)^(.*)\Z',r'\1libmialgoengine.so'),
    'vendor/etc/msm_irqbalance.conf': blob_fixup()
        .regex_replace('#arch_timer, arm-pmu, arch_mem_timer', '#arch_timer, arm-pmu, arch_mem_timer, msm_drm, kgsl_3d0_irq')
        .regex_replace('IGNORED_IRQ=27,23,38', 'IGNORED_IRQ=27,23,38,115,332'),
    'vendor/lib64/android.hardware.secure_element@1.0-impl.so': blob_fixup()
        .remove_needed('android.hidl.base@1.0.so'),
    ('vendor/lib64/mediadrm/libwvdrmengine.so', 'vendor/lib64/libwvhidl.so'): blob_fixup()
         .add_needed('libcrypto_shim.so'),
    ('vendor/lib/hw/audio.primary.lahaina.so', 'vendor/lib/libaudioroute_ext.so'): blob_fixup()
        .replace_needed('libaudioroute.so', 'libaudioroute-v34.so'),
    'vendor/lib64/hw/camera.qcom.so': blob_fixup()
        .sig_replace('73 74 5F 6C 69 63 65 6E 73 65 2E 6C 69 63', '63 61 6D 65 72 61 5F 63 6E 66 2E 74 78 74')
        .add_needed('libprocessgroup_shim.so'),
    'vendor/lib64/hw/camera.xiaomi.so': blob_fixup()
        .sig_replace('29 07 00 94', '1F 20 03 D5'),
    'vendor/lib64/hw/com.qti.chi.override.so' : blob_fixup()
        .add_needed('libprocessgroup_shim.so'),
    'vendor/lib64/libmialgo_rfs.so': blob_fixup()
        .clear_symbol_version('remote_handle64_close')
        .clear_symbol_version('remote_handle64_invoke')
        .clear_symbol_version('remote_handle64_open')
        .clear_symbol_version('remote_register_buf_attr')
        .clear_symbol_version('remote_session_control'),
    ('vendor/lib64/libalAILDC.so', 'vendor/lib64/libalLDC.so', 'vendor/lib64/libalhLDC.so'): blob_fixup()
        .clear_symbol_version('AHardwareBuffer_allocate')
        .clear_symbol_version('AHardwareBuffer_describe')
        .clear_symbol_version('AHardwareBuffer_lock')
        .clear_symbol_version('AHardwareBuffer_release')
        .clear_symbol_version('AHardwareBuffer_unlock'),
    'vendor/lib64/libarcsoft_hdrplus_hvx_stub.so': blob_fixup()
        .clear_symbol_version('remote_handle_close')
        .clear_symbol_version('remote_handle_invoke')
        .clear_symbol_version('remote_handle_open'),
    ('vendor/lib/libaudiocloudctrl.so', 'vendor/lib64/libdpps.so', 'vendor/lib64/libsnapdragoncolor-manager.so'): blob_fixup()
        .replace_needed('libtinyxml2.so', 'libtinyxml2-v34.so'),
    'vendor/etc/libnfc-nci.conf': blob_fixup()
        .regex_replace('NFC_DEBUG_ENABLED=1', 'NFC_DEBUG_ENABLED=0'),
    'vendor/etc/libnfc-nxp.conf': blob_fixup()
        .regex_replace('(NXPLOG_.*_LOGLEVEL)=0x03', '\\1=0x02')
        .regex_replace('NFC_DEBUG_ENABLED=1', 'NFC_DEBUG_ENABLED=0'),
}  # fmt: skip


module = ExtractUtilsModule(
    'redwood',
    'xiaomi',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
