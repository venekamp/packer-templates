#!/bin/bash -eux

SSH_USER_HOME=/home/$SSH_USER
VBOX_VERSION=$(cat $SSH_USER_HOME/.vbox_version)

echo "Installing VirtualBox Guest Additions ($VBOX_VERSION)."

yum install -y bzip2 gcc make perl kernel-devel-`uname -r` kernel-headers-`uname -r`

mount -o loop,ro $SSH_USER_HOME/VBoxGuestAdditions.iso /mnt
sh /mnt/VBoxLinuxAdditions.run --nox11
umount /mnt

rm -rf $SSH_USER_HOME/VBoxGuestAdditions.iso
rm -f $SSH_USER_HOME/.vbox_version

echo "Removing packages needed for building guest tools."
yum -y autoremove gcc make kernel-devel kernel-headers perl
