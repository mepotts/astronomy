#!/bin/sh
# Shim standing in for gnuplot. viper instantiates a gnuplot subprocess at import time
# and writes plot commands to its stdin; it only truly needs gnuplot for interactive
# -look* plots, which a headless RV extraction never uses. Answer -V, then sink stdin so
# the pipe stays open instead of breaking.
case "$1" in
  -V|--version) echo "gnuplot 5.4 patchlevel 0"; exit 0 ;;
esac
cat > /dev/null 2>&1
exit 0
