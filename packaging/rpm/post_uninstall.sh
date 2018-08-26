rm -rf %{_sysconfdir}/sudoers.d/afsutil
getent group afsutil >/dev/null && groupdel afsutil
