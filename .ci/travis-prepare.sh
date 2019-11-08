#!/usr/bin/env sh
set -e -x

# Build Base for use with https://travis-ci.org
#
# Set environment variables
# BASE= 3.14 3.15 3.16 7.0  (VCS branch)
# STATIC=  YES / default (shared)

die() {
  echo "$1" >&2
  exit 1
}

[ "$BASE" ] || exit 0

if [ "$STATIC" = "YES" ]
then
  BASEDIR=base-$BASE-static
else
  BASEDIR=base-$BASE-shared
fi

CDIR="$HOME/.cache/$BASEDIR"
EPICS_BASE="$CDIR/base"

if [ ! -e "$CDIR/built" ]
then
  install -d "$CDIR"
  ( cd "$CDIR" && git clone --depth 10 --branch $BASE https://github.com/epics-base/epics-base.git base )

  EPICS_HOST_ARCH=`sh $EPICS_BASE/startup/EpicsHostArch`

  case "$STATIC" in
  YES)
    cat << EOF >> "$EPICS_BASE/configure/CONFIG_SITE"
STATIC_BUILD=YES
EOF
    ;;
  *) ;;
  esac

  case "$CMPLR" in
  clang)
    echo "Host compiler is clang"
    cat << EOF >> "$EPICS_BASE/configure/os/CONFIG_SITE.Common.$EPICS_HOST_ARCH"
GNU         = NO
CMPLR_CLASS = clang
CC          = clang
CCC         = clang++
EOF

    # hack
    sed -i -e 's/CMPLR_CLASS = gcc/CMPLR_CLASS = clang/' "$EPICS_BASE/configure/CONFIG.gnuCommon"

    clang --version
    ;;
  *)
    echo "Host compiler is default"
    gcc --version
    ;;
  esac

  make -C "$EPICS_BASE" -j2

  cat << EOF > configure/RELEASE.local
EPICS_BASE=$EPICS_BASE
EOF

  case "$BASE" in
  *3.14*)
    ( cd "$CDIR" && wget https://www.aps.anl.gov/epics/download/extensions/extensionsTop_20120904.tar.gz && tar -xzf extensionsTop_*.tar.gz)

    ( cd "$CDIR" && wget https://www.aps.anl.gov/epics/download/extensions/msi1-7.tar.gz && tar -xzf msi1-7.tar.gz && mv msi1-7 extensions/src/msi)

    cat << EOF > "$CDIR/extensions/configure/RELEASE"
EPICS_BASE=$EPICS_BASE
EPICS_EXTENSIONS=\$(TOP)
EOF

    ( cd "$CDIR/extensions" && make )

    cp "$CDIR/extensions/bin/$EPICS_HOST_ARCH/msi" "$EPICS_BASE/bin/$EPICS_HOST_ARCH/"

    echo 'MSI:=$(EPICS_BASE)/bin/$(EPICS_HOST_ARCH)/msi' >> "$EPICS_BASE/configure/CONFIG_SITE"
    ;;

  *7.*)
    ( cd "$CDIR" && git clone --depth 10 https://github.com/epics-modules/pcas.git pcas )
    cat << EOF > "$CDIR/pcas/configure/RELEASE.local"
EPICS_BASE=$EPICS_BASE
EOF

    make -C "$CDIR/pcas" -j2

    cat << EOF >> configure/RELEASE.local
PCAS=$CDIR/pcas
EOF
    ;;

  *) ;;
  esac

  touch "$CDIR/built"
fi

EPICS_HOST_ARCH=`sh $EPICS_BASE/startup/EpicsHostArch`
