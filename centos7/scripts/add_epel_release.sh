#!/bin/sh -eux

tput bold
echo "Adding the epel-release repository"
tput sgr0

yum -y install epel-release
