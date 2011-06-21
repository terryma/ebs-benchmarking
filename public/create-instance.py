# This script will create the EC2 instance and bootstrap it to kick off the setup script to execute the fio tests

import sys
import boto
import time
import logging
from boto.ec2.blockdevicemapping import *

logging.basicConfig(filename="boto.log", level=logging.DEBUG)

ec2 = boto.connect_ec2()

SIZE = 2
ZONE = 'us-east-1d'
MAX_RETRIES = 10
AMI_ID_32 = 'ami-8c1fece5' # Basic 32-bit Amazon Linux
AMI_ID_64 = 'ami-8e1fece7' # Basic 64-bit Amazon Linux
INSTANCE_TYPE = 'm1.large'

#Create a 2GB volume
#print "Creating {0}GB volume in {1}".format(SIZE, ZONE)
#res = ec2.create_volume(SIZE, ZONE)
#volumeId = res.id
#print "Volume {0} created".format(volumeId)

# Query for the volume
#counter = 0
#while (1):
    #if (counter == MAX_RETRIES):
        #sys.exit("Reached max retries for querying volume creation, exiting...")
    #print "Checking to see if volume {0} is available...".format(volumeId)
    #res = ec2.get_all_volumes([volumeId])
    #if (res[0].status == 'available'):
        #print "{0} is available".format(volumeId)
        #break;
    ## sleep a second and do it again
    #time.sleep(1)
    #counter += 1

# Delete the volume
#print "Deleting volume {0}".format(volumeId)
#res = ec2.delete_volume(volumeId);
#if (res):
    #print "Volume {0} deleted".format(volumeId)
#else:
    #print "Deleting volume {0} failed"

# Launch the instance
deviceMap = BlockDeviceMapping()
ephemeralDevice = BlockDeviceType()
ephemeralDevice.ephemeral_name = 'ephemeral0'
ebsDevice = BlockDeviceType()
ebsDevice.size = 2
ebsDevice.delete_on_termination= True
deviceMap['/dev/sdb'] = ephemeralDevice
deviceMap['/dev/sdc'] = ebsDevice
print "Launching instance..."
reservation = ec2.run_instances(
        image_id=AMI_ID_64,
        placement=ZONE,
        key_name='terry-key',
        instance_type=INSTANCE_TYPE,
        subnet_id='subnet-92167cfb',
        security_group_ids=['sg-d71507bb'],
        block_device_map=deviceMap
        )
reservationId = reservation.id

# Query for the instance
counter = 0
MAX_RETRY_DESC_INSTANCES = 100
while (1):
    if (counter == MAX_RETRY_DESC_INSTANCES):
        sys.exit("Reached max retries for querying instance state, exiting...")
    print "Checking to see if reservation %s is running..." % reservationId
    res = ec2.get_all_instances(filters={'reservation-id':reservationId})
    if res:
        instance = res[0].instances[0]
        print "Found instance with reservation-id %s. Instance ID = %s" % (reservationId, instance.id)
        print "Instance state = %s" % instance.state
        if instance.state == 'terminated':
            print "Instance is terminated, something bad happened"
            sys.exit("Exiting...")
        if instance.state == 'running':
            break
    # sleep a second and do it again
    time.sleep(1)
    counter += 1

# Terminate the instance
#print "Terminating instance %s" % instance.id
#res = ec2.terminate_instances(instance_ids=[instance.id])
#print res
#print res[0]
#print res[0].__dict__

print "Done!"
