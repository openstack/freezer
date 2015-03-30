Freezer Scenario Functional Testing
====================================

The most straight forward way to set up the Freezer functional testing
environment is by utilizing VAGRANT. There is initial Vagrant file that
by default is setup to work with Virtualbox and Ubuntu 14.04 as virtual
machine OS.

In order to prepare your Vagrant + VirtualBox/KVM environment there is:

  $ ./prepare-vagrant.sh

The script is tested to work on Ubuntu and will automatically download
and deploy Vagrant, VirtualBox, KVM and libvrt as well as mutate Vagrant
plugins. It will also download a base Ubuntu 14.04 64bit Vagrant box and
use mutate plugin to deoplu a libvrt version for KVM use.

Before running 'vagrant up' for the first time make sure you have replaced
the 'P-R-O-X-Y' string (Vagrant file) with the correct HTTP proxy URL and
port if behind one e.g. P-R-O-X-Y => http://proxy.test.company.com:3344

To start the process of MV deployment run:

  $ vagrant destroy -f #This will delete any previosly deployed instances
  $ vagrant up #This kick starts the Devstack Swift VM that tests use

When process is done normalyy it take 10 - 20 min depends on your network.
You should have a fully configured Swift object storage VM that is
accessible on a host only IP e.g 10.199.199.199

Copy file swiftrc.sample to swiftrc and edited properly should you need to.

Next you need to decide weather you want to perform the integration tests
locally on your station or into the Vagrant VM. There are two scripts to
do just that:

   $ ./run-local.py
   $ ./run-remote.sh

The first of them will setup loopback LVM disk that your Freezer scenario
tests will need and mount it in /mnt.
The second will create the LVM disk in the Vagrant virtual machine and will
synchronize all Freezer files to the VM as well where it is going to trigger
the integration test.

Successful test run should look something similar to this:

............
test_lvm_level0 (backup_scenario.BackupScenarioFS) ... ok
test_no_lvm_level0 (backup_scenario.BackupScenarioFS) ... ok
test_utils_methods (backup_scenario.BackupScenarioFS) ... ok

----------------------------------------------------------------------
Ran 3 tests in 2.696s

OK
