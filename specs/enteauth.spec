# Prebuilt foreign binary: no build-id or debuginfo can be produced, and
# disabling the debug package also skips brp-strip, which would otherwise
# rewrite the upstream blob. The binary ships as-is from the release RPM.
%global debug_package %{nil}

# add-determinism's brp hook (add-det) would regenerate /usr/lib/.build-id
# links from the blob's ELF build-id notes and otherwise normalize the
# payload. The blob must ship byte-identical, so unset the hook (consistent
# with %%global debug_package %%{nil} above).
%undefine __brp_add_determinism

Name:           enteauth
Version:        4.4.25
Release:        %autorelease
Summary:        2FA app with free end-to-end encrypted backup and sync
License:        AGPL-3.0-or-later
URL:            https://github.com/ente/ente
ExclusiveArch:  x86_64

Source0:        https://github.com/ente/ente/releases/download/auth-v%{version}/ente-auth-v%{version}-x86_64.rpm
# Upstream prebuilt RPM ships no license file. spectool fetches LICENSE for
# the exact version being packaged from the release tag; a failed fetch fails
# the build, so the packaged license always matches the packaged version.
Source1:        https://raw.githubusercontent.com/ente/ente/auth-v%{version}/LICENSE
# Curated AppStream metadata: upstream ships enteauth.appdata.xml with a
# non-reverse-DNS id ("enteauth") which fails `appstreamcli validate`.
# This file keeps upstream's content but uses the RDNS id io.ente.auth
# (matching Icon/StartupWMClass) so the packaged metadata validates.
Source2:        io.ente.auth.metainfo.xml

BuildRequires:  desktop-file-utils
BuildRequires:  appstream
BuildRequires:  cpio
BuildRequires:  chrpath
BuildRequires:  binutils

# Only one explicit runtime dep: the polkit policy file
# (com.ente.auth.policy) is not linked by any ELF, so the dependency
# generator cannot see it. Everything else is auto-detected from DT_NEEDED:
# the tray icon's ayatana libs, libsecret, gtk3, etc.
# Deliberately NOT mirrored from the upstream RPM's declared requirements:
# libappindicator (legacy compat package; the tray plugin actually links
# the auto-detected libayatana-appindicator3), libsecret (auto-detected via
# libsecret-1.so.0), sqlite-libs (no ELF links system sqlite; bundled).
Requires:       polkit

# NOTE: library deps (libgtk-3, libglib, libc, etc.) are added automatically
# by rpmbuild's dependency generator from DT_NEEDED entries.
#
# One auto-detected dep is excluded: libdartjni.so (an Android JNI bridge
# that Flutter bundles into every Linux build, and which the main binary
# does not link) would otherwise pull a libjvm.so requirement, dragging in
# a full JVM. Upstream's own RPM declares no such requirement and runs fine
# without it, so exclude it to keep the install footprint at parity.
%global __requires_exclude ^libjvm\\.so

%description
Ente Auth is a free, open-source, end-to-end encrypted 2FA authenticator.
It backs up your one-time codes so you never lose your tokens, with apps
for mobile, desktop and web that stay in sync. This package rewraps the
upstream prebuilt Linux RPM for Fedora (COPR only).

%prep
rpm2cpio %{SOURCE0} | cpio -idmu
# Drop the foreign .build-id carried by the upstream RPM; the debug package
# is disabled, so we ship no debuginfo of our own.
rm -rf usr/lib/.build-id
# Upstream's Flutter plugin libs carry a RUNPATH pointing at the GitHub
# Actions build workspace (/home/runner/work/.../flutter/ephemeral), which
# cannot exist on end-user machines and trips Fedora's check-rpaths
# (ERROR 0002, failing %%install). Delete exactly that entry with chrpath;
# it is the sole RUNPATH on the affected files, so nothing else changes and
# runtime behavior is identical (the loader already falls back to the main
# binary's $ORIGIN/lib RUNPATH plus the system paths). This loop is a no-op
# if a future upstream release stops baking the path in.
for lib in usr/share/enteauth/lib/*.so; do
  if readelf -d "$lib" 2>/dev/null | grep -q '/home/runner/work/'; then
    chrpath -d "$lib"
  fi
done
# Drop the upstream AppStream file (non-RDNS id); %install ships the
# curated Source2 instead. The upstream desktop file and icon are kept.
rm -f usr/share/metainfo/enteauth.appdata.xml
cp %{SOURCE1} LICENSE

%build
# Nothing to compile: the prebuilt upstream binary is unpacked in %%prep.
# The section exists so rpm's build hooks (e.g. macro-injected steps) run.

%install
cp -a usr %{buildroot}/
install -Dm0644 %{SOURCE2} %{buildroot}%{_metainfodir}/io.ente.auth.metainfo.xml

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/enteauth.desktop
appstreamcli validate --no-net %{buildroot}%{_metainfodir}/io.ente.auth.metainfo.xml

%files
%license LICENSE
%{_bindir}/enteauth
%{_datadir}/enteauth/
%{_datadir}/applications/enteauth.desktop
%{_datadir}/pixmaps/io.ente.auth.png
%{_datadir}/polkit-1/actions/com.ente.auth.policy
%{_metainfodir}/io.ente.auth.metainfo.xml
# Release is %%autorelease: COPR's rpmautospec sets it to the changelog entry
# count. To rebuild the same upstream version with a spec change, append a new
# %%changelog entry — Release bumps automatically and the NVR stays unique.

%changelog
* Sat Sep 05 2026 Anudeep D <anudeepd2@gmail.com> - 4.4.25-1
- Initial Fedora repackaging of upstream prebuilt RPM
