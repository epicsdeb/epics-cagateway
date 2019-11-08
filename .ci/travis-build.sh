#!/usr/bin/env sh
set -e -x

[ "$BASE" ] || exit 0

make -j2 $EXTRA

[ "$TEST" = "NO" ] && exit 0

# Configure pyepics and IOC wrapper
eval `grep -m 1 "EPICS_BASE[[:space:]]*=" configure/RELEASE.local`
EPICS_HOST_ARCH=`sh $EPICS_BASE/startup/EpicsHostArch`
export PYEPICS_LIBCA=$EPICS_BASE/lib/$EPICS_HOST_ARCH/libca.so
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$EPICS_BASE/lib/$EPICS_HOST_ARCH
export PATH=$PATH:$EPICS_BASE/bin/$EPICS_HOST_ARCH

ls -al $EPICS_BASE/lib/$EPICS_HOST_ARCH

echo Check pyepics install
python -c "import epics; print(epics.__version__)"
python -c "import epics.ca; print(epics.ca.find_libca())"

make tapfiles
find . -name '*.tap' -print0 | xargs -0 -n1 prove -e cat -f
