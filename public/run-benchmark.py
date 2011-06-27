from subprocess import *
import time

# This script will run the benchmarking on every combination that's supported, and writes the output to ../log

# instance_types = ['m1.small', 'm1.large', 'm1.xlarge']
# file_systems = ['ext3', 'ext4', 'xfs']
instance_types = ['m1.small']
file_systems = ['ext3']
tenacies = ['dedicated', 'default']

processes = []

for i in instance_types:
    for f in file_systems:
        for t in tenacies:
            # command = "python create-instance.py -i %s -f %s -t %s > ../logs/%s-%s-%s.log" % (i, f, t, i, f, t)
            command = "python create-instance.py -i %s -f %s -t %s" % (i, f, t)
            print "Executing %s" % command
            p = Popen(command, shell=True)
            processes.append(p)
            print "Sleeping for 5 seconds..."
            time.sleep(5)

for p in processes:
    print "Waiting for process %s to finish..." % p.pid
    p.wait()


