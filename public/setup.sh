#!/bin/sh
# This script is ran on the instance to execute the fio tests

usage() {
    echo "Usage: $0 {-d device} {-f filesystem}"
    exit 1
}

# setup
#INSTANCE_TYPE=`curl -s http://169.254.169.254/latest/meta-data/instance-type`
#INSTANCE_ID=`curl -s http://169.254.169.254/latest/meta-data/instance-id`

[ $USER != "root" ] && echo "Needs to run as root" && exit 1

enc=""
raw=""
device=""
filesystem=""
while getopts d:f: option
do
    case "${option}"
    in
        d) device=${OPTARG};;
        f) filesystem=${OPTARG};;
        [?]) usage
        exit 1;;
    esac
done

[ -z "$device" ] && usage
[ -z "$filesystem" ] && usage

# run all as root
# disable for now since I haven't quite figured out how to pass env variables to su
#sudo su <<-'.'

# install rpmforge if not already, since this is needed to install fio
rpmforge=rpmforge-release-0.3.6-1.el5.rf.i386
echo "Checking RPMforge..."
rpm -qa | grep $rpmforge > /dev/null && echo "RPMforge is already installed" || rpm -Uhv http://apt.sw.be/redhat/el5/en/i386/rpmforge/RPMS/$rpmforge.rpm

# install fio if not already
echo "Checking fio..."
yum list installed | grep "^fio" > /dev/null && echo "fio is already installed" || yum install --assumeyes fio

# install xfs
echo "Installing xfsprogs..."
yum install --assumeyes xfsprogs

# create a key file and populate it if not already exists
echo "Checking encryption key..."
keyfile=$HOME/.lukskey
if [ -e $keyfile ] 
then
    echo "Encryption key ($keyfile) already exists, going to use it"
else
    echo "Generating key file $keyfile"
    touch $keyfile && echo "$keyfile created"
    # silly password
    echo "apccore" > $keyfile
fi

# unmount our stuff
echo "Unmounting /plain and /encrypted..."
umount -l /plain
umount -l /encrypted

# close our encrypted luks device
echo "Closing existing LUKS device 'encrypted'"
cryptsetup luksClose encrypted

# set up two partitions, one encrypted and one raw
echo "Setting up two 130 cylinder partitions on $device, WIPING everything on there"
{
    echo 0,130
    echo ,130
} | sfdisk  $device
raw=${device}1
enc=${device}2

# sleep for 5 seconds before the next step as i've encountered race conditions previously
echo "Sleeping for 5 seconds before calling cryptsetup..."
sleep 5

# set up encrypted device
echo "Running cryptsetup -q -d $keyfile luksFormat $enc"
cryptsetup -q -d $keyfile luksFormat $enc
if [ $? -eq 0 ]
then
    echo "luksFormat successfully called on device $enc"
else
    echo "Something is wrong, aborting..."
    exit 1
fi

file -s $enc
cryptsetup -d $keyfile luksOpen $enc encrypted

# create filesystem
echo "Creating $filesystem fs on /dev/mapper/encrypted"
mkfs -t $filesystem -q /dev/mapper/encrypted
echo "Creating $filesystem fs on $raw"
mkfs -t $filesystem -q $raw

# create mounting points
mkdir -p /plain
mkdir -p /encrypted
echo "Mounting /dev/mapper/encrypted on /encrypted"
mount /dev/mapper/encrypted /encrypted > /dev/null 2>&1
echo "Mounting $raw on /plain"
mount $raw /plain > /dev/null 2>&1

# download the fio input file
# grabbing from my github account for now, need to figure out better way to do this
fiofilename=bench.fio
echo "Checking for fio job file" 
if [ -e $fiofilename ] 
then
    echo "$fiofilename already exists, going to use it" 
else
    fiofile=https://raw.github.com/terryma/ebs-benchmarking/master/public/$fiofilename
    echo "Downloading fio job file at $fiofile"
    curl -O -s $fiofile 
fi

# finally run the test and save the result
echo "Running fio test..."
# fio bench.fio | tee test-result.txt
#TEST_OUTPUT=${INSTANCE_TYPE}-${INSTANCE_ID}-`date +%m-%d-%y-%H:%M:%S`.out
TEST_OUTPUT="test-result.out"
echo "Outputting to $TEST_OUTPUT"

fio --output=$TEST_OUTPUT bench.fio

# Clean up
# unmount our stuff
echo "Unmounting /plain and /encrypted..."
umount -l /plain
umount -l /encrypted

# close our encrypted luks device
echo "Closing existing LUKS device 'encrypted'"
cryptsetup luksClose encrypted

#.

