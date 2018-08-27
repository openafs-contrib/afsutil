# Copyright (c) 2018 Sine Nomine Associates
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

"""Helper to install and remove OpenAFS RPM packages via yum."""

import logging

from afsutil.rpm import RpmInstaller
from afsutil.system import sh
from afsutil.install import Installer

logger = logging.getLogger(__name__)

def yum(*args):
    """Helper to run the yum command."""
    return sh('yum', *args, quiet=False)

class YumInstaller(RpmInstaller):
    """Install and remove OpenAFS packages with yum."""

    def __init__(self, dir=None, **kwargs):
        Installer.__init__(self, **kwargs)
        self.pkgdir = dir  # Defer checks until needed.
        self.packages = None
        self.installed = None

    def install(self):
        """Install RPM packages."""
        self.pre_install()
        if not (self.do_server or self.do_client):
            raise AssertionError("Expected client and/or server component.")
        packages = []
        packages.append('openafs')
        packages.append('openafs-krb5')
        packages.append('openafs-docs')
        if self.do_server:
            packages.append('openafs-server')
        if self.do_client:
            packages.append('openafs-client')
            packages.append('kmod-openafs')
        yum('-y', 'install', *packages)
        self.post_install()

    def remove(self):
        """Remove OpenAFS RPM packages."""
        # Remove all packages by default. Optionaly remove just the server or
        # client packages. If removing just one component and the other is not
        # present, then also remove the common packages.
        self.pre_remove()
        installed = self.find_installed().keys()
        packages = [] # names of packages to be removed
        if self.do_server and self.do_client:
            packages = installed # remove everything
        elif self.do_server:
            if 'openafs-client' not in installed:
                packages = installed              # remove common too
            elif 'openafs-server' in installed:
                packages = ['openafs-server']
        elif self.do_client:
            if 'openafs-server' not in installed:
                packages = installed              # remove common too
            elif 'openafs-client' in installed:
                packages = ['openafs-client', 'kmod-openafs']
        if packages:
            logger.info("removing %s" % " ".join(packages))
            yum('-y', 'remove', *packages)
        self.post_remove()
