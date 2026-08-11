#!/bin/bash
# cr2re links libcurl; only the runtime lib is on this box, no dev headers, and no sudo.
# A minimal SSL-less build is enough -- nothing in the local reduction path fetches https.
P=$HOME/cr2res/install
cd $HOME/cr2res/build || exit 1
[ -f curl.tar.gz ] || curl -sL --max-time 300 -o curl.tar.gz https://curl.se/download/curl-8.5.0.tar.gz
rm -rf curl-8.5.0 && tar xzf curl.tar.gz
cd curl-8.5.0 || exit 1
./configure --prefix="$P" --without-ssl --disable-ldap --disable-ldaps --without-libpsl \
            --without-brotli --without-zstd --without-nghttp2 --without-libidn2 \
            --disable-docs --disable-manual > cfg.log 2>&1 || { echo CONFIG_FAIL; tail -12 cfg.log; exit 1; }
make -j4 > make.log 2>&1 && make install >> make.log 2>&1 || { echo MAKE_FAIL; tail -15 make.log; exit 1; }
PKG_CONFIG_PATH="$P/lib/pkgconfig" "$P/bin/pkg-config" --modversion libcurl && echo CURL_OK
