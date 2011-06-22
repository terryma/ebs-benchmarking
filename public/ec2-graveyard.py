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

