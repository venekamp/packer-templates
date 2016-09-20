#!/bin/bash -eux

tput bold
echo Installing additional packages
tput sgr0

yum -y install vim-enhanced wget
