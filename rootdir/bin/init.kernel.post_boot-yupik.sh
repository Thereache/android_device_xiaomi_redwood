#=============================================================================
# Copyright (c) 2020-2021 Qualcomm Technologies, Inc.
# All Rights Reserved.
#=============================================================================

function configure_zram_parameters() {
	MemTotalStr=`cat /proc/meminfo | grep MemTotal`
	MemTotal=${MemTotalStr:16:8}

	let RamSizeGB="( $MemTotal / 1048576 ) + 1"
	diskSizeUnit=M
	if [ $RamSizeGB -le 2 ]; then
		let zRamSizeMB="( $RamSizeGB * 1024 ) * 3 / 4"
	else
		let zRamSizeMB="( $RamSizeGB * 1024 ) / 2"
	fi

	if [ $zRamSizeMB -gt 4096 ]; then
		let zRamSizeMB=4096
	fi

	echo lz4 > /sys/block/zram0/comp_algorithm

	if [ -f /sys/block/zram0/disksize ]; then
		if [ -f /sys/block/zram0/use_dedup ]; then
			echo 1 > /sys/block/zram0/use_dedup
		fi
		echo "$zRamSizeMB""$diskSizeUnit" > /sys/block/zram0/disksize

		if [ -e /sys/kernel/slab/zs_handle ]; then
			echo 0 > /sys/kernel/slab/zs_handle/store_user
		fi
		if [ -e /sys/kernel/slab/zspage ]; then
			echo 0 > /sys/kernel/slab/zspage/store_user
		fi

		mkswap /dev/block/zram0
		swapon /dev/block/zram0 -p 32758
	fi
}

function configure_read_ahead_kb_values() {
	dmpts=$(ls /sys/block/*/queue/read_ahead_kb | grep -e dm -e mmc)
	ra_kb=128

	if [ -f /sys/block/mmcblk0/bdi/read_ahead_kb ]; then
		echo $ra_kb > /sys/block/mmcblk0/bdi/read_ahead_kb
	fi
	if [ -f /sys/block/mmcblk0rpmb/bdi/read_ahead_kb ]; then
		echo $ra_kb > /sys/block/mmcblk0rpmb/bdi/read_ahead_kb
	fi
	for dm in $dmpts; do
		echo $ra_kb > $dm
	done
}

function configure_memory_parameters() {
	configure_zram_parameters
	configure_read_ahead_kb_values
	echo 100 > /proc/sys/vm/swappiness

	# GKI has no extra_free_kbytes; wake kswapd earlier.
	echo 200 > /proc/sys/vm/watermark_scale_factor

	MemTotalStr=`cat /proc/meminfo | grep MemTotal`
	MemTotal=${MemTotalStr:16:8}
	if [ $MemTotal -le 8388608 ]; then
		echo 0 > /proc/sys/vm/watermark_boost_factor
	fi
}

# 6.18 uses PELT, schedutil and CASS. Legacy WALT, core control,
# input boost and 5.4 memlat/bw_hwmon nodes are not present.
echo 0-1 > /dev/cpuset/background/cpus
echo 0-3 > /dev/cpuset/restricted/cpus
echo 0-2 > /dev/cpuset/system-background/cpus
echo 0-6 > /dev/cpuset/foreground/cpus

for policy in /sys/devices/system/cpu/cpufreq/policy*; do
	echo "schedutil" > $policy/scaling_governor
done

echo 691200 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq
echo 691200 > /sys/devices/system/cpu/cpufreq/policy4/scaling_min_freq
echo 806400 > /sys/devices/system/cpu/cpufreq/policy7/scaling_min_freq

# deep uses PSCI SYSTEM_SUSPEND and does not reach the SoC sleep states.
echo s2idle > /sys/power/mem_sleep

configure_memory_parameters

setprop vendor.post_boot.parsed 1
