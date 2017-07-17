#!/bin/bash -eux

yum -y install yum-utils

package-cleanup --oldkernels --count=1 -y

yum -y remove yum-utils
