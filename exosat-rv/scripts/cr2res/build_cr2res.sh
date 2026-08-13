#!/bin/bash
# Build the cr2res stack straight from the kit's tarballs instead of via ESO's
# install_pipeline. Reasons:
#   - install_pipeline needs a tty, refuses to rerun, and restarts from zero every time
#   - the WSL *service* on this box crashes intermittently under sustained build load
#     (Wsl/Service/E_UNEXPECTED), so a non-resumable build never finishes
# Each component drops a .stamp; rerunning skips what is already installed.
K=$HOME/cr2res/cr2re-kit-1.6.10-5
P=$HOME/cr2res/install
S=$HOME/cr2res/stamps
B=$HOME/cr2res/build
mkdir -p "$P" "$S" "$B"
export PATH="$P/bin:$PATH" LD_LIBRARY_PATH="$P/lib:$LD_LIBRARY_PATH" PKG_CONFIG_PATH="$P/lib/pkgconfig"
JOBS=2   # keep load low; this box's WSL service falls over under heavier builds

log () { echo "[$(date +%H:%M:%S)] $*"; }

build () {                     # build <name> <tarball> <configure args...>
  name="$1"; tar="$2"; shift 2
  [ -f "$S/$name" ] && { log "skip $name (already installed)"; return 0; }
  log "=== $name ==="
  cd "$B" || return 1
  rm -rf "$name"; mkdir -p "$name"
  case "$tar" in
    *.tar.bz2) tar xjf "$K/$tar" -C "$name" --strip-components=1 ;;
    *)         tar xzf "$K/$tar" -C "$name" --strip-components=1 ;;
  esac
  cd "$name" || return 1
  ./configure --prefix="$P" "$@" > cfg.log 2>&1 || { log "CONFIGURE FAILED $name"; tail -15 cfg.log; return 1; }
  make -j$JOBS  > make.log 2>&1 || { log "MAKE FAILED $name"; tail -25 make.log; return 1; }
  make install >> make.log 2>&1 || { log "INSTALL FAILED $name"; tail -25 make.log; return 1; }
  touch "$S/$name"; log "$name OK"
}

build cfitsio cfitsio-4.6.2.tar.gz --enable-reentrant || exit 1
build wcslib  wcslib-8.4.tar.bz2 --with-cfitsiolib="$P/lib" --with-cfitsioinc="$P/include" --without-pgplot || exit 1
build fftw    fftw-3.3.10.tar.gz --enable-shared --enable-threads --enable-float || exit 1
build fftwd   fftw-3.3.10.tar.gz --enable-shared --enable-threads          || exit 1
build gsl     gsl-2.8.tar.gz                                              || exit 1
build erfa    erfa-2.0.1.tar.gz                                           || exit 1
# CPL bundles libcext under cpl/libcext but its own configure check for it still fails,
# so build and install libcext first and point CPL at it.
if [ ! -f "$S/cext" ]; then
  log "=== libcext (bundled in cpl) ==="
  cd "$B" && rm -rf cextsrc && mkdir -p cextsrc && tar xzf "$K/cpl-7.4.tar.gz" -C cextsrc --strip-components=1
  cd "$B/cextsrc/libcext" || exit 1
  ./configure --prefix="$P" > cfg.log 2>&1 || { log "CONFIGURE FAILED cext"; tail -15 cfg.log; exit 1; }
  make -j$JOBS > make.log 2>&1 && make install >> make.log 2>&1 || { log "MAKE FAILED cext"; tail -20 make.log; exit 1; }
  touch "$S/cext"; log "cext OK"
fi

build cpl     cpl-7.4.tar.gz --with-cfitsio="$P" --with-wcslib="$P" --with-fftw="$P" --with-cext="$P" || exit 1
build esorex  esorex-3.13.11.tar.gz --with-cpl="$P" --with-cext="$P" || exit 1
build cr2re   cr2re-1.6.10.tar.gz --with-cpl="$P" --with-cext="$P" --with-gsl="$P" --with-erfa="$P" || exit 1

# pipeline calibration files
if [ ! -f "$S/calib" ]; then
  mkdir -p "$HOME/cr2res/calib" && tar xzf "$K/cr2re-calib-1.6.10.tar.gz" -C "$HOME/cr2res/calib" && touch "$S/calib"
  log "calib OK"
fi
log "ALL COMPONENTS BUILT"
"$P/bin/esorex" --version 2>&1 | head -3
"$P/bin/esorex" --recipes 2>&1 | grep -i nodding | head -5
touch "$HOME/cr2res/DONE"
