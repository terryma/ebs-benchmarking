#!/bin/zsh

# Source my .zshrc for cron to work correctly
. ~/.zshrc
BASEDIR=$(dirname $(readlink -f $0))
PARENTDIR=$(dirname $BASEDIR)

instance_types=( m1.small m1.large m1.xlarge c1.xlarge )
file_systems=( ext3 ext4 xfs )
#tenancies=( dedicated default )
tenancies=( dedicated )

for i in "${instance_types[@]}"
do
    for f in "${file_systems[@]}"
    do
        for t in "${tenancies[@]}"
        do
            echo "#########################################################################################"
            echo "Running test with instance type = $i, file system = $f, tenancy = $t"
            echo "#########################################################################################"
            #. $BASEDIR/create-instance.py -i $i -f $f -t $t > $PARENTDIR/logs/$i-$f-$t.out
            /usr/bin/env python $BASEDIR/create-instance.py -i $i -f $f -t $t
        done
    done
done

