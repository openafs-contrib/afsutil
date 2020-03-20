# Copyright (c) 2014-2018 Sine Nomine Associates
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

"""Install build dependencies for OpenAFS."""

import logging
import os
import platform
import urllib2
import tempfile

from afsutil.system import sh, CommandFailed

logger = logging.getLogger(__name__)

class Unsupported(Exception):
    pass

def apt_get_install(packages, dryrun=False):
    sh('apt-get', '-y', 'install', *packages, dryrun=dryrun, output=False)

def yum_install(packages, dryrun=False):
    sh('yum', 'install', '-y', *packages, dryrun=dryrun, output=False)

def dnf_install(packages, dryrun=False):
    sh('dnf', 'install', '-y', *packages, dryrun=dryrun, output=False)

def zypper_install(packages, dryrun=False):
    sh('zypper', 'install', '-y', *packages, dryrun=dryrun, output=False)

def pkg_install(packages, dryrun=False, update_all=True):
    # Recent versions of solarisstudio fail to install due to dependency
    # conflicts unless the system is updated first.
    if update_all:
        sh('pkg', 'update', '-v', 'entire@latest', dryrun=dryrun, output=False)
    # Ignore package already installed errors.
    ERROR_ALREADY_INSTALLED = 4
    try:
        sh('pkg', 'install', '--accept', *packages, dryrun=dryrun, output=False)
    except CommandFailed as e:
        if e.code != ERROR_ALREADY_INSTALLED:
            logger.error("pkg install failed: %s" % e)
            raise e

def lookup_solarisstudio(creds='/root/creds',
                         key='pkg.oracle.com.key.pem',
                         cert='pkg.oracle.com.certificate.pem',
                         **kwargs):
    """
    Lookup the Solaris Studio package.

    Before running this function, create an account on the Oracle Technology Network
    and follow the instructions to create and download the key and certificate files.
    Place the key and cert file in a local directory or at a private url.  The
    default location of the key and cert files is /root/creds. Set the 'creds'
    keyword argurment to specify a different path or a url.
    """
    path = None
    tmpdir = None
    quiet = True

    def download(baseurl, filename, path):
        url = os.path.join(baseurl, filename)
        dst = os.path.join(path, filename)
        rsp = urllib2.urlopen(url)
        logger.info("Downloading '%s' to '%s'.", url, dst)
        with open(dst, 'wb') as f:
            f.write(rsp.read())

    def normalize(s):
        return [int(x) for x in s.split('.')]

    def compare_versions(a, b):
        return cmp(normalize(a), normalize(b))

    if creds.startswith('http://') or creds.startswith('https://'):
        try:
            path = tmpdir = tempfile.mkdtemp()
            download(creds, key, tmpdir)
            download(creds, cert, tmpdir)
        except urllib2.HTTPError as e:
            logger.error("Unable to download files from url '%s', %s'." % (creds, e))
            return None
        finally:
            logger.info("Cleaning up temporary files in '%s'.", tmpdir)
            if os.path.exists(os.path.join(tmpdir, key)):
                os.remove(os.path.join(tmpdir, key))
            if os.path.exists(os.path.join(tmpdir, cert)):
                os.remove(os.path.join(tmpdir, cert))
            if os.path.exists(tmpdir) and tmpdir != "/":
                os.rmdir(tmpdir)
    elif os.path.exists(creds):
        logger.info("Using credentials in path '%s'.", creds)
        path = creds
    else:
        logger.error("creds path '%s' not found.", creds)
        return None

    logger.info("Setting publisher for solarisstudio.")
    sh('pkg', 'set-publisher',   # Will refresh if already set.
       '-k', os.path.join(path, key),
       '-c', os.path.join(path, cert),
       '-G', '*',
       '-g', 'https://pkg.oracle.com/solarisstudio/release', 'solarisstudio',
       output=False, quiet=quiet)

    logger.info("Getting available solaris studio packages.")
    packages = {}
    output = sh('pkg', 'list', '-H', '-a', '-v', '--no-refresh',
                'pkg://solarisstudio/*', quiet=quiet)
    for line in output:
        # Extract the root package name, version, and install state.
        fmri,ifo = line.split()
        pkg,vt = fmri.split('@')
        v,t = vt.split(':')
        version = v.split(',')[0]
        name = pkg.replace('pkg://solarisstudio/developer/','')
        istate = ifo[0] == 'i'
        if '/' in name:
            pass # Skip non-root ones, e.g. 'developerstudio-125/cc'.
        else:
            logger.info("Found package %s, version %s, installed %s.",
                        name, version, istate)
            packages[name] = {'version':version, 'installed':istate}

    # Find the most recent version.
    solarisstudio = None
    vers = '0.0'
    for name in packages.keys():
        if compare_versions(packages[name]['version'], vers) > 0:
            vers = packages[name]['version']
            solarisstudio = 'pkg://solarisstudio/developer/{0}'.format(name)
    if solarisstudio:
        logger.info("Most recent version found is '%s'.", solarisstudio)
    else:
        logger.info("Could not find solaris studio package.")
    return solarisstudio

def getdeps(dryrun=False, skip_headers=False, skip_solarisstudio=False, **kwargs):
    """Determine platform and install build dependencies."""
    system = platform.system().lower()
    if system == 'linux':
        dist = platform.dist()[0].lower()
        release = platform.dist()[1].lower()
        if dist == 'debian' or dist == 'ubuntu':
            packages = [
                'autoconf',
                'automake',
                'bison',
                'comerr-dev',
                'dblatex',
                'dkms',
                'docbook-xsl',
                'doxygen',
                'flex',
                'libelf-dev',
                'libfuse-dev',
                'libkrb5-dev',
                'libncurses5-dev',
                'libpam0g-dev',
                'libtool',
                'libxml2-utils',
                'make',
                'perl',
                'pkg-config',
                'xsltproc',
            ]
            if not skip_headers:
                packages.append('linux-headers-{0}'.format(platform.release()))
            apt_get_install(packages, dryrun)
        elif dist == 'centos':
            packages = [
                'autoconf',
                'automake',
                'bison',
                'elfutils-devel',
                'flex',
                'fuse-devel',
                'gcc',
                'glibc-devel',
                'krb5-devel',
                'libtool',
                'make',
                'ncurses-devel',
                'pam-devel',
                'perl-devel',
                'perl-ExtUtils-Embed',
                'perl-Test-Simple',
                'redhat-rpm-config',
                'rpm-build',
                'swig',
                'wget',
            ]
            if not skip_headers:
                packages.append('kernel-devel-uname-r == {0}'.format(platform.release()))
            yum_install(packages, dryrun)
        elif dist == 'suse':
            packages = [
                'autoconf',
                'automake',
                'bison',
                'flex',
                'fuse-devel',
                'gcc',
                'glibc-devel',
                'krb5-devel',
                'libtool',
                'make',
                'ncurses-devel',
                'pam-devel',
                'rpm-build',
                'wget',
            ]
            if not skip_headers:
                packages.append('kernel-devel')
            zypper_install(packages, dryrun)
        elif dist == 'fedora' and release < 22:
            packages = [
                'autoconf',
                'automake',
                'bison',
                'elfutils-devel',
                'flex',
                'fuse-devel',
                'gcc',
                'glibc-devel',
                'krb5-devel',
                'libtool',
                'make',
                'ncurses-devel',
                'pam-devel',
                'perl-devel',
                'perl-ExtUtils-Embed',
                'perl-Test-Simple',
                'redhat-rpm-config',
                'rpm-build',
                'swig',
                'wget',
            ]
            if not skip_headers:
                packages.append('kernel-devel-uname-r == {0}'.format(platform.release()))
            yum_install(packages, dryrun)
        elif dist == 'fedora':
            packages = [
                'autoconf',
                'automake',
                'bison',
                'elfutils-devel',
                'flex',
                'fuse-devel',
                'gcc',
                'glibc-devel',
                'krb5-devel',
                'libtool',
                'make',
                'ncurses-devel',
                'pam-devel',
                'perl-devel',
                'perl-ExtUtils-Embed',
                'perl-Test-Simple',
                'redhat-rpm-config',
                'rpm-build',
                'swig',
                'wget',
            ]
            if not skip_headers:
                packages.append('kernel-devel-uname-r == {0}'.format(platform.release()))
            dnf_install(packages, dryrun)
        else:
            raise Unsupported("Linux dist '{0}'.".format(dist))
    elif system == 'sunos':
        release = platform.release()
        if release == '5.11':
            packages = [
                'autoconf',
                'automake',
                'bison',
                'flex',
                'git',
                'gnu-binutils',
                'gnu-coreutils',
                'gnu-sed',
                'libtool',
                'make',
                'onbld',
                'text/locale',
            ]
            if not skip_solarisstudio:
                solarisstudio = lookup_solarisstudio(**kwargs)
                if solarisstudio:
                    packages.append(solarisstudio)
            pkg_install(packages, dryrun)
        else:
            raise Unsupported("Solaris release '{0}'".format(release))
    else:
        raise Unsupported("Operating system '{0}'.".format(system))
