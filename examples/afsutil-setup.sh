#!/bin/sh

HOST=`hostname`

# Installing
/usr/bin/sudo -n afsutil install \
   --components server client \
   --dist transarc \
   --realm EXAMPLE.COM \
   --cell example.com \
   --hosts "$HOST" \
   --force \
   -o "afsd=-dynroot -fakestat -afsdb" \
   -o bosserver=

# Creating service key
/usr/bin/sudo -n afsutil ktcreate \
  --realm EXAMPLE.COM \
  --cell example.com \
  --keytab /tmp/afsutil/fake.keytab

# Setting service key
/usr/bin/sudo -n afsutil ktsetkey \
  --realm EXAMPLE.COM \
  --cell example.com \
  --keytab /tmp/afsutil/fake.keytab \
  --format detect \
  --paths asetkey=/usr/afs/bin/asetkey

# Starting servers
/usr/bin/sudo -n afsutil start server

# Creating new cell
/usr/bin/sudo -n afsutil newcell \
  --cell example.com \
  --admin afsadmin \
  --realm EXAMPLE.COM \
  --fs "$HOST" \
  --db "$HOST" \
  -o bosserver= \
  -o dafileserver= \
  -o davolserver=  \
  -o "$HOST.dafileserver=-d 1 -L" \
  -o "$HOST.davolserver=-d 1" \
  -p pagsh=/usr/afsws/bin/pagsh \
  -p kinit=/usr/bin/kinit \
  -p fs=/usr/afs/bin/fs \
  -p rxdebug=/usr/afsws/etc/rxdebug \
  -p bos=/usr/afs/bin/bos \
  -p udebug=/usr/afs/bin/udebug \
  -p asetkey=/usr/afs/bin/asetkey \
  -p tokens=/usr/afsws/bin/tokens \
  -p kdestroy=/usr/bin/kdestroy \
  -p unlog=/usr/afsws/bin/unlog \
  -p vos=/usr/afs/bin/vos \
  -p pts=/usr/afs/bin/pts \
  -p aklog=/usr/local/bin/aklog-1.6

# Starting clients
/usr/bin/sudo -n afsutil start client

# Mounting root volumes
afsutil mtroot \
  --realm EXAMPLE.COM \
  --cell example.com \
  --admin afsadmin \
  --top test \
  --akimpersonate \
  --keytab /tmp/afsutil/fake.keytab \
  --fs "$HOST" \
  -o "afsd=-dynroot -fakestat -afsdb" \
  -p fs=/usr/afs/bin/fs \
  -p vos=/usr/afs/bin/vos \
  -p aklog=/usr/local/bin/aklog-1.6
