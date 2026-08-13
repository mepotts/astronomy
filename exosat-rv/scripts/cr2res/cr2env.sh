#!/bin/bash
# Environment for the locally built cr2res 1.6.10 stack.
export CR2RES_PREFIX=$HOME/cr2res/install
export PATH="$CR2RES_PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$CR2RES_PREFIX/lib:$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="$CR2RES_PREFIX/lib/pkgconfig"
export CPL_RECIPE_DIR="$CR2RES_PREFIX/lib/esopipes-plugins/cr2re-1.6.10"
export CR2RES_CALIB=$HOME/cr2res/calib
