usage() {
    echo "Usage: $0 {-e encrypted device} {-r raw device}"
    exit 1
}

[[ $USER != "root" ]] && echo "Needs to run as root" && exit 1

enc=""
raw=""
while getopts e:r: option
do
    case "${option}"
    in
        e) enc=${OPTARG};;
        r) raw=${OPTARG};;
        [?]) usage
        exit 1;;
    esac
done

[[ -z "$enc" ]] && usage
[[ -z "$raw" ]] && usage

# run all as root
# disable for now since I haven't quite figured out how to pass env variables to su
#sudo su <<-'.'

# install rpmforge if not already
rpmforge=rpmforge-release-0.3.6-1.el5.rf.i386
rpm -qa | grep $1>/dev/null $rpmforge && echo "RPM Forge already installed" || rpm -Uhv http://apt.sw.be/redhat/el5/en/i386/rpmforge/RPMS/$rpmforge.rpm

# install fio if not already
yum list installed | grep $1>/dev/null "^fio" && echo "fio is already installed" || yum install --assumeyes fio

# create a key file
keyfile=$HOME/.lukskey
echo "Generating key file $keyfile"
touch $keyfile && echo "$keyfile created"
# silly password
echo "apccore" > $keyfile

# set up encrypted device
echo "Running cryptsetup -q -d $keyfile luksFormat $enc"
cryptsetup -q -d $keyfile luksFormat $enc
file -s $enc
cryptsetup -d $keyfile luksOpen $enc encrypted

# create filesystem
echo "Creating ext3 fs on /dev/mapper/encrypted"
mkfs.ext3 -q -m 0 /dev/mapper/encrypted
echo "Creating ext3 fs on $raw"
mkfs.ext3 -q -m 0 $raw

# create mounting points
mkdir -p /plain
mkdir -p /encrypted
echo "Mounting /dev/mapper/encrypted on /encrypted"
mount $1 > /dev/null 2>&1 /dev/mapper/encrypted /encrypted
echo "Mounting $raw on /plain"
mount $1 > /dev/null 2>&1 $raw /plain

# download the fio input file
# grabbing from my github account for now, need to figure out better way to do this
fiofile=https://raw.github.com/terryma/ebs-benchmarking/master/public/bench.fio
echo "Downloading fio job file at $fiofile"
curl -O -s $fiofile 


# finally run the test
echo "Running fio test..."
fio bench.fio

#.

