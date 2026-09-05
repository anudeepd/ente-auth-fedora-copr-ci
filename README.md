# ente-auth-fedora-copr-ci

[Ente Auth](https://github.com/ente/ente) is a free, open-source, end-to-end encrypted 2FA authenticator.

This repo packages Ente Auth for Fedora by rewrapping the upstream prebuilt Linux RPM (`ente-auth-vX.Y.Z-x86_64.rpm`) with a Fedora spec. Currently x86_64 only, matching upstream's prebuilt release artifacts. A GitHub Actions workflow runs daily at 12AM UTC to check the latest `auth-v*` release from https://github.com/ente/ente (a monorepo, so tags are filtered by the `auth-v` prefix) and rebuilds COPR only when a new version is published. The downloaded RPM is verified against the SHA256SUMS file published with each upstream release before submission.

The COPR project repository is available from: https://copr.fedorainfracloud.org/coprs/anudeepd/enteauth

## Packaging compliance

This package is distributed via COPR only. It rewraps the upstream prebuilt
binary RPM, so it is **not eligible for the official Fedora repositories**:
the Fedora Packaging Guidelines require all binaries to be built from source
in the Fedora build system, and this repo intentionally ships the upstream
blob as-is (see `specs/enteauth.spec`).

Everything else follows the guidelines:

- `ExclusiveArch: x86_64` — matches upstream's prebuilt artifacts.
- `%build` present (empty — nothing to compile) so rpm's build hooks run.
- `%check` runs `desktop-file-validate` and `appstreamcli validate` on the
  packaged files inside the build.
- `rpmlint` runs in CI on the built RPM with **0 errors, 0 warnings**:
  every flagged pattern is inherent to rewrapping the Flutter blob
  (private libs without SONAME under `/usr/share`, required `$ORIGIN`
  runpaths, `arch-dependent-file-in-usr-share`, unstripped prebuilt
  binaries, dictionary misses, GUI app without man page, docs not bundled
  by design, desktop file pointing at a symlinked binary) and is filtered
  in `rpmlintrc` with per-filter rationales.
- `%{_bindir}`, `%{_datadir}`, `%{_metainfodir}` macros used in `%files`.
- License provenance: the `LICENSE` text is fetched from the upstream
  release tag by `spectool` (the prebuilt RPM ships none); a fetch failure
  fails the build, so the packaged license always matches the packaged
  version. `License: AGPL-3.0-or-later` (SPDX) matches the upstream
  `LICENSE`/RPM (`AGPLv3`). Nothing else is bundled: upstream payload plus
  license and curated metainfo.
- `%global debug_package %{nil}` with an explicit rationale: the prebuilt
  foreign binary cannot produce debuginfo, and disabling the debug package
  also skips `brp-strip`, which would otherwise rewrite the upstream blob.
  The foreign `.build-id` carried by the upstream RPM is dropped, and the
  `add-det` brp hook is disabled, for the same reason: the blob must ship
  byte-identical.
- One minimal, documented transformation: upstream's Flutter plugin libs
  bake in a `RUNPATH` pointing at the GitHub Actions build workspace
  (`/home/runner/work/...`), which cannot exist on user machines and fails
  Fedora's `check-rpaths`. `%prep` deletes exactly that entry with
  `chrpath` (a no-op if upstream ever stops emitting it); code and the
  working `$ORIGIN` runpaths are untouched.
- Upstream ships an AppStream file with a non-reverse-DNS id (`enteauth`)
  that fails validation, so this repo ships a curated
  `io.ente.auth.metainfo.xml` (same content, RDNS id matching
  `Icon`/`StartupWMClass`); the upstream desktop file and icon are kept
  as-is. The stale upstream AppStream file is removed at `%prep`.
- Only one explicit runtime dep: `polkit` (for the shipped policy file,
  which no ELF links, so it can't be auto-detected). Library deps
  (tray ayatana libs, `libsecret`, `libgtk-3`, `libc`, …) are auto-detected
  from `DT_NEEDED`. Deliberately not mirrored from upstream: the legacy
  `libappindicator` compat package (the tray plugin links ayatana),
  `libsecret` (auto-detected) and `sqlite-libs` (bundled, unlinked).
  One auto-detected dep is excluded: `libjvm.so` (via the unused
  `libdartjni.so` JNI bridge) would drag in a full JVM that upstream
  itself doesn't require. The versioned
  `libcurl.so.4(CURL_OPENSSL_4)` requirement is excluded too (nothing in
  Fedora provides it; the unversioned `libcurl.so.4` dep stays and every
  needed symbol resolves). No network access inside the buildroot.
- The downloaded RPM is verified against the SHA256SUMS published with the
  upstream release before submission to COPR.

# Instructions

Enable the COPR repository then install the package.

<pre>
sudo dnf copr enable anudeepd/enteauth
sudo dnf install enteauth
</pre>

## Credits

Pattern and workflow structure adapted from
[anudeepd/iloader-fedora-copr-ci](https://github.com/anudeepd/iloader-fedora-copr-ci)
(which itself was adapted from
[DeltaCopy/waterfox-fedora-copr-ci](https://github.com/DeltaCopy/waterfox-fedora-copr-ci))
— thanks for the clean reference implementation.

<h3> COPR build status </h3>

[![Copr build status](https://copr.fedorainfracloud.org/coprs/anudeepd/enteauth/package/enteauth/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/anudeepd/enteauth/package/enteauth/)

<h3> GitHub action workflow status </h3>

[![enteauth Fedora COPR CI](https://github.com/anudeepd/ente-auth-fedora-copr-ci/actions/workflows/enteauth-ci.yml/badge.svg)](https://github.com/anudeepd/ente-auth-fedora-copr-ci/actions/workflows/enteauth-ci.yml)

## Latest version
<a href="https://github.com/ente/ente/releases?q=auth-v&expanded=true">
  <img src="https://img.shields.io/github/v/release/ente/ente?filter=auth-v*&label=ente-auth" alt="ente-auth latest release">
</a>
