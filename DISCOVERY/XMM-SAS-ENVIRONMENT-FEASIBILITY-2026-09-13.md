# SAS environment feasibility: compatible OS family, storage and dependencies unresolved

2026-09-13. Read-only inventory of the existing Ubuntu WSL distribution and
primary public documentation. **No installation is ready to execute.** The OS
family is documented for SAS, but the Linux filesystem is almost full, none of
the five requested commands is on the inspected PATH, and current package
integrity/size and complete dependency compatibility were not verified.

## Exact local observations

Parent authorized starting existing Ubuntu for these checks. Two owner-context
`wsl -d Ubuntu -- bash -lc ...` calls completed with exit code 0; no container,
GUI, package manager, network command or scientific file was involved.

| Check | Observed result |
| --- | --- |
| `/etc/os-release` | Ubuntu 24.04.4 LTS, VERSION_ID 24.04, codename noble |
| `uname -m` | x86_64 |
| `python3 --version` | Python 3.12.3 |
| `getconf GNU_LIBC_VERSION` | glibc 2.39 |
| `df -Pk /`: filesystem | /dev/sdd |
| `/`: 1024-byte blocks / used / available | 1055762868 / 1001378996 / 680400 |
| `/`: reported capacity | 100% |
| `df -Pk /mnt/c`: filesystem | Windows C: |
| `/mnt/c`: 1024-byte blocks / used / available | 3515536380 / 2799007660 / 716528720 |
| `/mnt/c`: reported capacity | 80% |

Thus the Linux filesystem reported only 696,729,600 available bytes, about
664.45 MiB; the Windows-mounted filesystem reported about 683.33 GiB available.
These are instantaneous filesystem readings, not reserved capacity or a
diagnosis of why Linux space is exhausted. `df`'s used plus available need not
equal its total. No directories were enumerated and no cleanup was attempted.

The exact literal commands `command -v sas`, `command -v ecoordconv`,
`command -v evselect`, `command -v epiclccorr`, and `command -v cifbuild` all
returned the explicit fallback `NAME:NOT_ON_PATH` in Ubuntu's login-shell
context. This is a PATH check, not a broad filesystem search or proof that no
uninitialized SAS installation exists anywhere.

The first call also attempted these lookups in a shell-variable loop, but its
output lost the variable labels at the Windows/WSL quoting boundary. That
loop is **not evidence of five named command failures**. The second call used
five literal names and supplied the valid observations above. OS/runtime/disk
output from the first call was unaffected. No further repeated probes were
needed. Ubuntu was started as authorized; this task issued no shutdown command.

## What official documentation establishes

The current retrieved [HEASARC SAS OS conversion guide](https://heasarc.gsfc.nasa.gov/docs/xmm/docs/sas-convert.html)
has an in-page heading for SAS 22.1.0, despite an older 22.0.0 page title.
Its table maps Ubuntu 24 to the Ubuntu 24-based build and is marked last
modified 7 March 2025. This supports the **OS-family match**, not a test of our
Python packages, dynamic libraries or WSL filesystem behavior. It does not
establish that 22.1.0 is the newest release on this task's date.

The [ESA Docker guide](https://www.cosmos.esa.int/web/xmm-newton/sas-installation-docker4sas)
was available as primary-source indexed text. It explicitly describes building
with `sas_22.1.0-Ubuntu24.04.tgz` and names the version-specific Python package
list `sas_22.1.0_python_packages.txt`. It also includes HEASoft components and
mixed-version examples; those examples are not a complete minimal dependency
manifest for the five tasks we need. No Docker runtime or image was inspected,
loaded or installed. We did not treat its sample image sizes as this native
build's verified size.

The [ESA installation user guide](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/sas_usg/USG/installation.html)
requires selecting the correct OS build and points to the release download
and installation instructions. Direct opens of the official
[download page](https://www.cosmos.esa.int/web/xmm-newton/sas-download) and
[software-requirements page](https://www.cosmos.esa.int/web/xmm-newton/sas-requirements)
returned HTTP451 through the research tool. These access failures were respected;
no alternate transport, guessed binary URL, registration, proxy or package
request was used to circumvent them.

Consequently the Ubuntu-family binary naming is documented, but this task did
not establish a currently accessible binary download, its hash/size, exact
Python ABI/package requirements, Perl/HEASoft/library requirements, minimum
glibc compatibility or installed availability of those dependencies. An observed
Python 3.12 and glibc 2.39 are facts, not automatic compatibility passes. Search
results for download-feedback statistics were not used as installation authority.

## Smallest next setup decision

**Do not install into the nearly full Ubuntu root or start a dependency manager
with unspecified temporary storage.** Choose one explicit writable installation,
cache and temporary-data arrangement with enough verified headroom before a
download. Windows C: has space, but that does not automatically make a Linux
SAS installation on `/mnt/c` supported: execution permissions, symlinks and
filesystem semantics still need a bounded non-scientific compatibility check.
There is no authority here to delete user files, resize/move a WSL disk, create
a new distribution, or adopt Docker merely to evade the storage constraint.

The next useful setup action is a **version-specific resource manifest decision**:
an accessible official Ubuntu 24 x86_64 distribution and integrity/size evidence;
its exact runtime dependency list; and a parent-approved installation/temp path
and storage cap. If official metadata remains inaccessible, ask for that precise
missing distribution/requirements evidence rather than guessing an installer.
No executable installation recipe is supplied because those checks are not done.

In parallel, the already proposed bounded Windows CALINDEX inventory can identify
which calibration constituents the authenticated products reference. It needs
no SAS installation and no event photons. After an eventual scoped setup,
start with version and task-load checks and then the already specified fixed
geometry smoke test; do not automatically run ODF ingestion/reprocessing, a
CCF mirror, GUI setup or a downloading tutorial task.

This finding does not alter M5/M6, authorize a download, or relax calibrated
geometry, relative-exposure or fixed-negative requirements. A supported binary
loading successfully would still not demonstrate source recovery or a discovery.

## Parent follow-up: officially linked binary listing found

Root read the complete note and independently opened the NASA conversion guide
and ESA installation user guide. Following the conversion guide's explicit
Ubuntu24 link reaches an accessible [official HEASARC distribution listing](https://heasarc.gsfc.nasa.gov/FTP/xmm/software/sas/latest/Linux/Ubuntu24.04/).
It lists `sas_22.1.0-Ubuntu24.04.tgz` and the version-qualified
`sas_22.1.0-a8f2c2afa-20250304-ubuntu24.04-gcc13.3.0-x86_64.tgz`, each shown as
1.4G and last modified2025-03-04 11:18. This is new primary-source evidence of
an officially linked binary location, not a guessed URL or a binary download.
The directory's rounded size is not an exact byte count or an integrity hash.
Its parent-directory open failed; no package or archive header was requested.

The ESA guide explicitly permits choosing an installation directory and says
the installer checks Perl/SAS_PERL and the appropriate Python version. Exact
release-specific requirements, dependencies, verified distribution integrity,
expanded storage and filesystem compatibility remain unresolved. The Linux
root-space constraint is unchanged. No installer, download or cleanup follows
this metadata discovery; it narrows the future resource-manifest work.
