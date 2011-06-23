# This script will create the EC2 instance and bootstrap it to kick off the setup script to execute the fio tests

import sys
import getopt
import boto
import time
import logging
from subprocess import call # Used to invoke an external command.
from boto.ec2.blockdevicemapping import *
from eip import *

#logging.basicConfig(filename="boto.log", level=logging.DEBUG)

ec2 = boto.connect_ec2()

EBS_VOLUME_SIZE = 2 # The EBS volume to create in GB
MAX_RETRIES = 10
AMI_ID_32 = 'ami-8c1fece5' # Basic 32-bit Amazon Linux
AMI_ID_64 = 'ami-8e1fece7' # Basic 64-bit Amazon Linux

zone = 'us-east-1d' # AZ for the instance and the EBS volume

keyName = 'terry-key'
subnetId = 'subnet-92167cfb'
securityGroupId = 'sg-d71507bb'

def usage():
    print "Usage place holder"
    sys.exit(1)

# Supported instance types
instanceTypes = {
    'm1.small' : {'name':'m1.small' , 'condensed':'m1small' , 'ami':AMI_ID_32},
    'm1.large' : {'name':'m1.large' , 'condensed':'m1large' , 'ami':AMI_ID_64},
    'm1.xlarge': {'name':'m1.xlarge', 'condensed':'m1xlarge', 'ami':AMI_ID_64}
}

# Supported filesystems
fileSystems = ['ext3', 'ext4']

instanceType = None
fileSystem = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "i:f:", ["instance-type=", "file-system="])
except getopt.GetoptError, err:
    print str(err)
    usage()
for o, a in opts:
    if o in ("-i", "--instance-type"):
        if a in instanceTypes:
            instanceType = instanceTypes[a]
        else:
            print "Instance type %s is not a valid value. Valid values %s" % (a, instanceTypes.keys())
            usage()
    if o in ("-f", "--file-system"):
        if a in fileSystems:
            fileSystem = a
        else:
            print "Filesystem %s is not a valid value. Valid values %s" % (a, fileSystems)
            usage()

if not instanceType:
    print "Instance type is required"
    usage()
if not fileSystem:
    print "Filesystem is required"
    usage()








# Return the block device map for the instance
def getDeviceMap():
    deviceMap = BlockDeviceMapping()
    ephemeralDevice = BlockDeviceType()
    ephemeralDevice.ephemeral_name = 'ephemeral0'
    ebsDevice = BlockDeviceType()
    ebsDevice.size = EBS_VOLUME_SIZE
    ebsDevice.delete_on_termination= True
    deviceMap['/dev/sdb'] = ephemeralDevice
    deviceMap['/dev/sdc'] = ebsDevice
    return deviceMap


# Launch the instance
deviceMap = getDeviceMap()
print "Launching %s instance in %s with AMI %s..." % (instanceType['name'], zone, instanceType['ami'])
reservation = ec2.run_instances(image_id=instanceType['ami'],
                                placement=zone,
                                key_name=keyName,
                                instance_type=instanceType['name'],
                                subnet_id=subnetId,
                                security_group_ids=[securityGroupId],
                                block_device_map=deviceMap
                               )
reservationId = reservation.id
print "Instance reservation id: %s" % reservationId

# Query for the instance
counter = 0
MAX_RETRY_DESC_INSTANCES = 100
print "Checking to see if reservation %s is running..." % reservationId
res = ec2.get_all_instances(filters={'reservation-id':reservationId})
instance = res[0].instances[0]
print "Found instance %s with reservation id %s" % (instance.id, reservationId)
while True:
    if (counter == MAX_RETRY_DESC_INSTANCES):
        sys.exit("Reached max retries for querying instance state, exiting...")
    print "Instance state = %s" % instance.state
    if instance.state == 'terminated':
        print "Instance is terminated, something bad happened"
        sys.exit("Exiting...")
    if instance.state == 'running':
        print "Instance is running!"
        break
    # sleep a second and do it again
    time.sleep(1)
    counter += 1
    instance.update()

eipManager = EipManager(ec2)

# If the instance is already associated with a eip, disassociate it first
eipManager.disassociate_instance(instance.id)

# Get a new vpc eip
vpcAddress = eipManager.get_vpc_address()

# Assoicate the instance with the eip
associationId = eipManager.associate_instance(instance.id, vpcAddress.allocationId)


keyfile = "/home/zhenchma/EC2/keys/terry-key.pem"
script = "./setup.sh"
# Try to connect 10 times
MAX_CONNECT_ATTEMPTS = 10
connectAttempts = 0

print "Trying to scp %s to instance at %s..." % (script, vpcAddress.ip)
while True:
    retcode = call(["scp", "-q", "-o", "ConnectTimeout=5", "-i", keyfile, script, "ec2-user@%s:/home/ec2-user" % vpcAddress.ip])
    if retcode == 0:
        print "Successfully copied script to remote host"
        break
    time.sleep(10)
    sys.stdout.write(".")
    connectAttempts += 1
    if connectAttempts > MAX_CONNECT_ATTEMPTS:
        sys.exit("Reached max connect attempts. Aborting...")

print "Trying to execute %s on instance at %s..." % (script, vpcAddress.ip)
command = 'sudo %s -d /dev/xvdc -f %s' % (script, fileSystem)
retcode = call(["ssh", "-t", "-i", keyfile, "ec2-user@%s" % vpcAddress.ip, command])
print retcode

_mountOption='none'
_storageType='ebs'
_tenancy='dedicated'
_encryptionLayer='domU'

fileName='-'.join([instanceType['condensed'], fileSystem, _mountOption, _storageType, _tenancy, _encryptionLayer,instance.id, str(int(time.time()))])
fileName+='.txt'
print fileName

print "Trying to retrieve test result file from instance..."
retcode = call(["scp", "-q", "-o", "ConnectTimeout=5", "-i", keyfile, "ec2-user@%s:/home/ec2-user/test-result.out" % vpcAddress.ip, "./results/%s" % fileName])
if retcode == 0:
    print "Successfully retrieved test result from instance"


# Clean up...
# Get rid of the eip
print "Disassociating eip with associateId %s" % associationId
eipManager.disassociate_address(associationId)
print "Releasing eip with allocationId %s" % vpcAddress.allocationId
eipManager.release_address(vpcAddress.allocationId)

# Terminate the instance
print "Terminating instance %s" % instance.id
res = ec2.terminate_instances(instance_ids=[instance.id])

print "Done!"


