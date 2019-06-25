#!/bin/sh
#
# afsutil-teardown - teardown a test cell
#

# Stopping clients
/usr/bin/sudo -n afsutil stop client

# Stopping servers
/usr/bin/sudo -n afsutil stop server

# Uninstalling
/usr/bin/sudo -n afsutil remove --dist transarc --purge

# Removing service key
/usr/bin/sudo -n afsutil ktdestroy --keytab /tmp/afsrobot/fake.keytab --force
