getent group afsutil >/dev/null || groupadd -r afsutil
echo '%afsutil ALL=(root) NOPASSWD: %{_bindir}/afsutil' > %{_sysconfdir}/sudoers.d/afsutil
chmod 440 %{_sysconfdir}/sudoers.d/afsutil
