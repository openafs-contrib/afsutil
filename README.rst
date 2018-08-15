=======
afsutil
=======

**afsutil** is a command-line tool to build, install, and setup OpenAFS for
developers and testers.

Command line interface
----------------------

::

    usage: afsutil <command> [options]
    
    commands:
      version      Print version
      help         Print usage
      getdeps      Install build dependencies
      check        Check hostname
      build        Build binaries
      reload       Reload the kernel module from the build tree
      package      Build packages
      install      Install binaries
      remove       Remove binaries
      start        Start AFS services
      stop         Stop AFS services
      ktcreate     Create a fake keytab
      ktdestroy    Destroy a keytab
      ktsetkey     Add a service key from a keytab file
      ktlogin      Obtain a token with a keytab
      newcell      Setup a new cell
      mtroot       Mount root volumes in a new cell
      addfs        Add a new fileserver to a cell

Examples
--------

To build OpenAFS from sources::

    $ git clone git://git.openafs.org/openafs.git
    $ cd openafs
    $ afsutil build

To install legacy "Transarc-style" binaries::

    $ sudo afsutil install \
      --force \
      --dist transarc \
      --components server client \
      --dir /usr/local/src/openafs-test/amd64_linux26/dest \
      --cell example.com \
      --realm EXAMPLE.COM \
      --hosts myhost1 myhost2 myhost3 \
      --csdb /root/CellServDB.dist \
      -o "afsd=-dynroot -fakestat -afsdb" \
      -o "bosserver=-pidfiles"

To setup the OpenAFS service key from a Kerberos 5 keytab file::

    $ sudo afsutil setkey
      --cell example.com \
      --realm EXAMPLE.COM \
      --keytab /root/fake.keytab

To start the OpenAFS servers::

    $ sudo afsutil start server

To setup a new OpenAFS cell on 3 servers, after 'afsutil install' has been run
on each::

    $ sudo afsutil newcell \
      --cell example.com \
      --realm EXAMPLE.COM \
      --admin example.admin \
      --top test \
      --akimpersonate \
      --keytab /root/fake.keytab \
      --fs myhost1 myhost2 myhost3 \
      --db myhost1 myhost2 myhost3 \
      --aklog /usr/local/bin/aklog-1.6 \
      -o "dafs=yes" \
      -o "afsd=-dynroot -fakestat -afsdb" \
      -o "bosserver=-pidfiles" \
      -o "dafileserver=L"

To start the client::

    $ sudo -n afsutil start client

To mount the top-level volumes after the client is running::

    $ afsutil mtroot \
     --cell example.com \
     --admin example.admin \
     --top test \
     --realm EXAMPLE.COM \
     --akimpersonate \
     --keytab /root/fake.keytab \
     --fs myhost1 \
     -o "afsd=-dynroot -fakestat -afsdb"
