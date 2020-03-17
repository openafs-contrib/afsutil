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
      package      Build RPM packages
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


Installation
------------

Install with `yum`::

    $ sudo yum install https://download.sinenomine.net/openafs/repo/sna-openafs-release-latest.noarch.rpm
    $ sudo yum install afsutil

Install with `pip`::

    $ sudo pip install afsutil
 
Install with `virtualenv`::

    $ python -m virtualenv ~/.virtualenv/afsutil
    $ . ~/.virtualenv/afsutil/bin/activate
    (afsutil) $ pip install afsutil
    (afsutil) $ deactivate
    $ sudo ln -s /home/$USER/.virtualenv/afsutil/bin/afsutil /usr/bin/afsutil
    
    $ afsutil version
    $ sudo afsutil version

Install from source::

    $ git clone https://github.com/openafs-contrib/afsutil
    $ cd afsutil
    $ <python-interpreter> configure.py  # i.e. python, python2
    $ sudo make install    # or make install-user for local install

Examples
--------

To build OpenAFS from sources::

    $ git clone git://git.openafs.org/openafs.git
    $ cd openafs
    $ sudo afstuil getdeps
    $ afsutil build

To build RPM packages from an arbitrary git checkout (on an rpm-based system)::

    $ sudo afsutil getdeps
    $ git clone git://git.openafs.org/openafs.git
    $ cd openafs
    $ git checkout <branch-or-tag>
    $ afsutil package
    $ ls ./package/rpmbuild/RPMS

The `afsutil package` command will build packages for the userspace and kernel
modules by default. See the `--build` option to build these separately.

The `afsutil package` command also supports the Fedora `mock` build system, which
is useful to build kernel modules for a large variety of kernel versions.

To build RPM packages from a git checkout with `mock`, including kernel
modules (kmods) for each kernel version found in the yum repositories::

   # Install mock.
   $ sudo yum install mock
   $ sudo usermod -a -G mock $USER
   $ newgrp - mock

   # Install packages needed to build the OpenAFS SRPM.
   $ sudo yum install git libtool bzip2

   # Checkout and then build packages.
   $ git clone git://git.openafs.org/openafs.git
   $ git checkout <branch-or-tag>
   $ afsutil package --mock   # This will take some time.


To install legacy "Transarc-style" binaries::

    $ sudo afsutil install \
      --force \
      --components server client \
      --dist transarc \
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

    $ sudo afsutil start client

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

Configuration files
-------------------

All of the command line values may be set in a configuration file.  Place
global configuration in `/etc/afsutil.cfg`, per user options in
`~/.afsutil.cfg`, and per project options in `.git/afsutil.cfg`. Use command
line options to override configuration options.

The **afsutil** configuration files are ini-style format.  The sections of the
configuration file correspond to the subcommand names, e.g., `build`,
`install`, `newcell`. Options within each section correspond to the command
line option names.

Some subcommands, such as `install` and `newcell` have options like `--options`
and `--paths`, which consist of multiple name/values pairs. These are
represented in the configuration file as subsection in the form
`[<subcommand>.<option>]`.

For example, the `install` command example given above has set of startup
options for `afsd` and `bosserver`. This would be specified in the
configuration file as::

    [install]
    force = yes
    components = server client
    dist = transarc
    dir = /usr/local/src/openafs-test/amd64_linux26/dest
    cell = example.com
    realm = EXAMPLE.COM
    hosts = myhost1 myhost2 myhost3
    csdb = /root/CellServDB.dist

    [install.options]
    afsd = -dynroot -fakestat -afsdb
    bosserver = -pidfiles

Here is an example configuration file::

    $ cat /etc/afsutil.cfg
    [install]
    cell = example.com
    realm = EXAMPLE.COM
    force = True
    components = server client
    dist = transarc
    hosts = debian9

    [install.options]
    afsd = -dynroot -fakestat -afsdb
    bosserver =

    [ktcreate]
    cell = example.com
    realm = EXAMPLE.COM
    keytab = /home/mtycobb/afsrobot/fake.keytab

    [ktsetkey]
    cell = example.com
    realm = EXAMPLE.COM
    keytab = /home/mtycobb/afsrobot/fake.keytab
    format = detect
    [ktsetkey.paths]
    asetkey = /usr/afs/bin/asetkey

    [newcell]
    cell = example.com
    realm = EXAMPLE.COM
    admin = afsrobot.admin
    fs = debian9
    db = debian9

    [newcell.options]
    bosserver =
    dafileserver =
    davolserver =
    debian9.dafileserver = -d 1 -L
    debian9.davolserver = -d 1

    [newcell.paths]
    aklog=/home/mtycobb/.local/bin/aklog-1.6
    asetkey=/usr/afs/bin/asetkey
    bos=/usr/afs/bin/bos
    fs=/usr/afs/bin/fs
    gfind=/usr/bin/find
    pagsh=/usr/afsws/bin/pagsh
    pts=/usr/afs/bin/pts
    rxdebug=/usr/afsws/etc/rxdebug
    tokens=/usr/afsws/bin/tokens
    udebug=/usr/afs/bin/udebug
    unlog=/usr/afsws/bin/unlog
    vos=/usr/afs/bin/vos

    [mtroot]
    cell = example.com
    realm = EXAMPLE.COM
    admin = afsrobot.admin
    top = test
    akimpersonate = True
    keytab = /home/mtycobb/afsrobot/fake.keytab
    fs = debian9

    [mtroot.options]
    afsd = -dynroot -fakestat -afsdb

    [mtroot.paths]
    aklog = /home/mtycobb/.local/bin/aklog-1.6
    asetkey = /usr/afs/bin/asetkey
    bos = /usr/afs/bin/bos
    fs = /usr/afs/bin/fs
    gfind = /usr/bin/find
    pagsh = /usr/afsws/bin/pagsh
    pts = /usr/afs/bin/pts
    rxdebug = /usr/afsws/etc/rxdebug
    tokens = /usr/afsws/bin/tokens
    udebug = /usr/afs/bin/udebug
    unlog = /usr/afsws/bin/unlog
    vos = /usr/afs/bin/vos

And the commands to install OpenAFS and create a new cell on a single
machine::

    sudo afsutil install
    sudo afsutil ktcreate
    sudo afsutil ktsetkey
    sudo afsutil start server
    sudo afsutil newcell
    sudo afsutil start client

    afsutil mtroot
