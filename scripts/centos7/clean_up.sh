#!/bin/bash -eux

yum clean headers
yum clean packages

echo "Save space: cleaning yum cache metadata and packages."
yum -y --enablerepo='*' clean all

echo "Save space: removing temporary file."
rm -rf /tmp/*

# work around for poor key import UI in PackageKit
rm -f /var/lib/rpm/__db*
rpm --rebuilddb

echo 'Clear out swap and disable until reboot.'

set +e

swapuuid=$(/sbin/blkid -o value -l -s UUID -t TYPE=swap)
case "$?" in
    2|0) ;;
    *) exit 1 ;;
esac

set -e

if [ "x${swapuuid}" != "x" ]; then
    # Whipeout swap partition to reduce box size
    # Swap is disabled utill reboot
    swappart=$(readlink -f /dev/disk/by-uuid/$swapuuid)

    /sbin/swapoff "${swappart}"

    set +e
    dd if=/dev/zero of="${swappart}" bs=1M >/dev/null 2>&1
    #  Ofcourse we are expecting an error. We are filling the disk
    #  and once completely filled, dd will fail...
    if [ "$?" -gt "1" ]; then
        echo "dd exit code $? is suppressed"
    fi
    set -e

    /sbin/mkswap -U "${swapuuid}" "${swappart}"
fi

echo 'Zeroing out empty area to save space in the final image'
# Zero out the free space to save space in the final image.  Contiguous
# zeroed space compresses down to nothing.
set +e
dd if=/dev/zero of=/EMPTY bs=1M >/dev/null 2>&1
#  Ofcourse we are expecting an error. We are filling the disk
#  and once completely filled, dd will fail...
if [ "$?" -gt "1" ]; then
    echo "dd exit code $? is suppressed"
fi
set -e

rm -f /EMPTY

# Block until the empty file has been removed, otherwise, Packer
# will try to kill the box while the disk is still full and that's bad
sync
