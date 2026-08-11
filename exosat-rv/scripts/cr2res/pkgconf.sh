#!/bin/bash
# cr2re's configure hard-errors without pkg-config, and this box has no passwordless sudo,
# so build pkgconf into the same prefix and expose it as `pkg-config`.
P=$HOME/cr2res/install
cd $HOME/cr2res/build || exit 1
rm -rf pkgconf-2.3.0 && tar xJf pkgconf.tar.xz
cd pkgconf-2.3.0 || exit 1
./configure --prefix="$P" > cfg.log 2>&1 || { echo CONFIG_FAIL; tail -10 cfg.log; exit 1; }
make -j2 > make.log 2>&1 && make install >> make.log 2>&1 || { echo MAKE_FAIL; tail -15 make.log; exit 1; }
ln -sf "$P/bin/pkgconf" "$P/bin/pkg-config"
"$P/bin/pkg-config" --version && echo PKGCONF_OK
