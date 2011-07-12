#!/bin/bash

BASEDIR=$(dirname $(readlink -f $0))
PARENTDIR=$(dirname $BASEDIR)

instance_types=( m1.small m1.large m1.xlarge c1.xlarge )
file_systems=( ext3 ext4 xfs )
tenancies=( dedicated default )

for i in "${instance_types[@]}"
do
    for f in "${file_systems[@]}"
    do
        for t in "${tenancies[@]}"
        do
            python $BASEDIR/create-instance.py -i $i -f $f -t $t > $PARENTDIR/logs/$i-$f-$t.out
        done
    done
done

