#!/usr/bin/env python

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
VPC_SUBNET_ID = 'subnet-92167cfb' # Used for vpc instances
VPC_SECURITY_GROUP_ID = 'sg-d71507bb' # Used for vpc instances
NON_VPC_SECURITY_GROUP = 'ssh' # Used for none vpc instances

def usage():
    print "Usage place holder"
    sys.exit(1)

# Supported instance types
instanceTypes = {
    'm1.small' : {'name':'m1.small' , 'condensed':'m1small' , 'ami':AMI_ID_32},
    'm1.large' : {'name':'m1.large' , 'condensed':'m1large' , 'ami':AMI_ID_64},
    'm1.xlarge': {'name':'m1.xlarge', 'condensed':'m1xlarge', 'ami':AMI_ID_64},
    'c1.xlarge': {'name':'c1.xlarge', 'condensed':'c1xlarge', 'ami':AMI_ID_64}
}

# Supported filesystems
fileSystems = ['ext3', 'ext4', 'xfs']

# Supported tenancy
tenancies = ['dedicated', 'default']

instanceType = None
fileSystem = None
tenancy = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "i:f:t:", ["instance-type=", "file-system=", "tenancy="])
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
    if o in ("-t", "--tenancy"):
        if a in tenancies:
            tenancy = a
        else:
            print "Tenancy %s is not a valid value. Valid values %s" % (a, tenancies)
            usage()

if not instanceType:
    print "Instance type is required"
    usage()
if not fileSystem:
    print "Filesystem is required"
    usage()
if not tenancy:
    print "Tenancy is required"
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
if tenancy == 'dedicated':
    security_group_ids = [VPC_SECURITY_GROUP_ID]
    subnet_id = VPC_SUBNET_ID
    security_groups = None
else:
    security_group_ids = None
    subnet_id = None
    security_groups = [NON_VPC_SECURITY_GROUP]
print "Launching %s %s instance in %s with AMI %s..." % (tenancy, instanceType['name'], zone, instanceType['ami'])
reservation = ec2.run_instances(image_id=instanceType['ami'],
                                placement=zone,
                                key_name=keyName,
                                instance_type=instanceType['name'],
                                subnet_id=subnet_id,
                                security_group_ids=security_group_ids,
                                security_groups=security_groups,
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
#    print "Instance debug = %s" % instance.__dict__
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

public_ip = None

# Only allocate eip for dedicated instances
if (tenancy == 'dedicated'):
    eipManager = EipManager(ec2)
    # If the instance is already associated with a eip, disassociate it first
    eipManager.disassociate_instance(instance.id)
    # Get a new vpc eip
    vpcAddress = eipManager.get_vpc_address()
    # Assoicate the instance with the eip
    associationId = eipManager.associate_instance(instance.id, vpcAddress.allocationId)
    public_ip = vpcAddress.ip
else :
    public_ip = instance.ip_address
print "Instance %s is associated with public ip: %s" % (instance.id, public_ip)


BASEDIR = os.path.dirname(os.path.realpath(__file__))

keyfile = "/home/zhenchma/EC2/keys/terry-key.pem"
script = "%s/setup.sh" % (BASEDIR)
script_remotedir = "/home/ec2-user"
script_remote = "%s/setup.sh" % (script_remotedir)
# Try to connect 10 times
MAX_CONNECT_ATTEMPTS = 10
connectAttempts = 0

print "Trying to scp %s to instance at %s..." % (script, public_ip)
while True:
    retcode = call(["scp", "-q", "-o", "ConnectTimeout=5", "-i", keyfile, script, "ec2-user@%s:%s" % (public_ip, script_remotedir)])
    if retcode == 0:
        print "Successfully copied script to remote host"
        break
    time.sleep(10)
    sys.stdout.write(".")
    connectAttempts += 1
    if connectAttempts > MAX_CONNECT_ATTEMPTS:
        sys.exit("Reached max connect attempts. Aborting...")

print "Trying to execute %s on instance at %s..." % (script_remote, public_ip)
command = 'sudo %s -d /dev/xvdc -f %s' % (script_remote, fileSystem)
print "Calling ssh -t -i %s ec2-user@%s %s" % (keyfile, public_ip, command)
retcode = call(["ssh", "-t", "-t", "-i", keyfile, "ec2-user@%s" % public_ip, command])
if retcode == 0:
    print "Successfully invoked remote script"
else:
    print "Remote script execution failed with retcode %s"%retcode

# TODO These parameters need to become user input later
_mountOption='none'
_storageType='ebs'
_encryptionLayer='domU'

fileName='-'.join([instanceType['condensed'], fileSystem, _mountOption, _storageType, tenancy, _encryptionLayer,instance.id, str(int(time.time()))])
fileName+='.txt'
print fileName

print "Trying to retrieve test result file from instance..."
retcode = call(["scp", "-q", "-o", "ConnectTimeout=5", "-i", keyfile, "ec2-user@%s:/home/ec2-user/test-result.out" % public_ip, "%s/results/%s" % (BASEDIR, fileName)])
if retcode == 0:
    print "Successfully retrieved test result from instance"
else:
    print "Failed to retrieve test result from instance, retcode=%s"%retcode

# Clean up...
if (tenancy == 'dedicated'):
    # Get rid of the eip
    print "Disassociating eip with associateId %s" % associationId
    eipManager.disassociate_address(associationId)
    print "Releasing eip with allocationId %s" % vpcAddress.allocationId
    eipManager.release_address(vpcAddress.allocationId)

# Terminate the instance
print "Terminating instance %s" % instance.id
ec2 = boto.connect_ec2()
res = ec2.terminate_instances(instance_ids=[instance.id])
print res
print "###########################################"
print "########        ALL DONE!          ########"
print "###########################################"




