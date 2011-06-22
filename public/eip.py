from subprocess import *
import os
import re

# Boto doesn't support allocating a vpc eip as of 06/21/11, using the command line for a lot of the operations below

# Saves the public ip and allocation Id for a vpc eip
class VpcEip(object):
    def __init__(self, ip, allocationId):
        self.ip = ip
        self.allocationId = allocationId

# Main class
class EipManager(object):
    def __init__(self, ec2):
        self.addresses = ec2.get_all_addresses()

    # Return an available vpc (ip, allocationId) if there's one
    def get_available_vpc_address(self):
        print "Checking to see if there's any available vpc eip..."
        for address in self.addresses:
            if (address.domain == 'vpc' and not address.instance_id):
                ip = address.public_ip
                allocationId = address.allocationId
                print "Found available vpc eip to use. ip = %s, allocationId = %s" % (ip, allocationId)
                return VpcEip(ip, allocationId)
        print "Did not find any available vpc eip"

    # Allocate a new vpc eip and return the (ip, allocationId) tuple
    def allocate_vpc_address(self):
        print "Calling ec2-allocate-address to allocate a new eip"
        output = check_output(["ec2-allocate-address", "-d", "vpc"]).strip()
        m = re.search('ADDRESS\s(.*)\svpc\s(.*)', output)
        ip = m.group(1).strip()
        allocationId = m.group(2).strip()
        return VpcEip(ip, allocationId)

    # Disassociate the eip on the input instance
    def disassociate_instance(self, instanceId):
        for address in self.addresses:
            if (address.instance_id == instanceId):
                print "Instance %s is already associated with ip address %s" % (address.instance_id, address.public_ip)
                print "Disassociating instance..."
                print "Calling ec2-disassociate-address with associationId %s" % address.associationId
                output = check_output(["ec2-disassociate-address", "-a", address.associationId])
                print output
                break

    # Associate the instance with the input allocationId, return the associationId on success
    def associate_instance(self, instanceId, allocationId):
        print "Calling ec2-associate-address with instanceId %s and allocationId %s" % (instanceId, allocationId)
        output = check_output(["ec2-associate-address", "-i", instanceId, "-a", allocationId])
        print output
        m = re.search('(eipassoc.*)\s', output)
        associationId = m.group(1).strip()
        print "association id = %s" % associationId
        return associationId

    # Disassociate the vpc eip using the input associationId
    def disassociate_address(self, associationId):
        print "Calling ec2-disassociate-address with associationId %s" % associationId
        output = check_output(["ec2-disassociate-address", "-a", associationId])
        print output

    # Release the eip using the input allocation Id
    def release_address(self, allocationId):
        print "Calling ec2-release-address with allocationId %s" % allocationId
        output = check_output(["ec2-release-address", "-a", allocationId])
        print output

    # Return an (ip, allocation) tuple of a vpc address. This could be an existing eip that's unassociated, or a newly allocated one
    def get_vpc_address(self):
        vpcAddress = self.get_available_vpc_address()
        if not vpcAddress:
            return self.allocate_vpc_address()
        return vpcAddress
