# Copyright (c) 2014-2017 Sine Nomine Associates
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""Linux specific utilities."""

import logging
import os
import re

from afsutil.system import common as _mod
CommandMissing = _mod.CommandMissing
CommandFailed = _mod.CommandFailed
cat = _mod.cat
directory_should_exist = _mod.directory_should_exist
directory_should_not_exist = _mod.directory_should_not_exist
file_should_exist = _mod.file_should_exist
mkdirp = _mod.mkdirp
nproc = _mod.nproc
path_join = _mod.path_join
symlink = _mod.symlink
touch = _mod.touch
which = _mod.which

logger = logging.getLogger(__name__)

def get_running():
    """Get a set of running processes."""
    ps = sh.Command('ps')
    procs = set()
    column = None
    for line in ps(, '-e', '-f', _iter=True):
        line = line.rstrip()
        if column is None:
            # The first line of the `ps' output is a header line which
            # used to find the command field column.
            column = line.index('CMD')
            continue
        cmd_line = line[column:]
        if cmd_line.startswith('['):  # skip linux threads
            continue
        command = cmd_line.split()[0]
        procs.add(os.path.basename(command))
    return procs

def is_running(program):
    """Returns true if program is running."""
    return program in get_running()

def afs_mountpoint():
    mountpoint = None
    pattern = r'^AFS on (/.\S+)'
    paths = os.environ.get('PATH', '').split(':')
    paths.extend(['/bin', '/sbin', '/usr/sbin'])
    mount = sh.Command('mount', search_paths=paths)
    for line in mount(_iter=True):
        found = re.search(pattern, line)
        if found:
            mountpoint = found.group(1)
    return mountpoint

def is_afs_mounted():
    """Returns true if afs is mounted."""
    return afs_mountpoint() is not None

def afs_umount():
    """Attempt to unmount afs, if mounted."""
    afs = afs_mountpoint()
    if afs:
        umount = which('umount', extra_paths=['/bin', '/sbin', '/usr/sbin'])
        xsh(umount, afs)

def network_interfaces():
    """Return list of non-loopback network interfaces."""
    addrs = []
    output = xsh('/sbin/ip', '-oneline', '-family', 'inet', 'addr', 'show', quiet=True)
    for line in output:
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
        if match:
            addr = match.group(1)
            if not addr.startswith("127."):
                addrs.append(addr)
    logger.debug("Found network interfaces: %s", ",".join(addrs))
    return addrs

def is_loaded(kmod):
    with open("/proc/modules", "r") as f:
        for line in f.readlines():
            if kmod == line.split()[0]:
                return True
    return False

def configure_dynamic_linker(path):
    """Configure the dynamic linker with ldconfig.

    Add a path to the ld configuration file for the OpenAFS shared
    libraries and run ldconfig to update the dynamic linker."""
    conf = '/etc/ld.so.conf.d/openafs.conf'
    paths = set()
    paths.add(path)
    if os.path.exists(conf):
        with open(conf, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue
                paths.add(line)
    with open(conf, 'w') as f:
        logger.debug("Writing %s", conf)
        for path in paths:
            f.write("%s\n" % path)
    xsh('/sbin/ldconfig')

def unload_module():
    output = xsh('/sbin/lsmod')
    for line in output:
        kmods = re.findall(r'^(libafs|openafs)\s', line)
        for kmod in kmods:
            xsh('rmmod', kmod)

def detect_gfind():
    return which('find')

def tar(tarball, source_path, tar=None):
    if tar is None:
        tar = 'tar'
    xsh(tar, 'czf', tarball, source_path, quiet=True)

def untar(tarball, chdir=None, tar=None):
    if tar is None:
        tar = 'tar'
    savedir = None
    if chdir:
        savedir = os.getcwd()
        os.chdir(chdir)
    try:
        xsh(tar, 'xzf', tarball, quiet=True)
    finally:
        if savedir:
            os.chdir(savedir)
