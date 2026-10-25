#!/usr/bin/env bash
# Build libevent for Android (autotools cross-compile) or host (CMake).
# Usage: build_libevent.sh <NDK_PATH|""> <ABI> <API_LEVEL> <INSTALL_PREFIX>
#   - pass an empty NDK_PATH ("") to do a native host build (Linux smoke test)
set -euo pipefail

NDK="${1:-}"
ABI="${2:-arm64-v8a}"
API="${3:-24}"
PREFIX="${4:?install prefix required}"
VER="2.1.12-stable"
# Use the official release tarball (it ships a generated ./configure).
# The auto-generated git tag archive does NOT contain configure.
SRC="libevent-${VER}"

WORK="$(mktemp -d)"
echo "== building libevent ${VER} (NDK='${NDK:-host}') =="
cd "$WORK"
curl -fSL "https://github.com/libevent/libevent/releases/download/release-${VER}/${SRC}.tar.gz" -o le.tgz
tar xzf le.tgz
cd "${SRC}"

if [ -n "${NDK}" ]; then
  # Android: cross-compile with the NDK clang wrapper. We disable thread
  # support because our demo only uses timers (no pthread needed), which
  # avoids libevent's CMake find_package(Threads) failing on Android NDK.
  TC="${NDK}/toolchains/llvm/prebuilt/linux-x86_64"
  export CC="${TC}/bin/aarch64-linux-android${API}-clang"
  export CXX="${TC}/bin/aarch64-linux-android${API}-clang++"
  export AR="${TC}/bin/llvm-ar"
  export RANLIB="${TC}/bin/llvm-ranlib"
  export STRIP="${TC}/bin/llvm-strip"
  ./configure --host=aarch64-linux-android \
    --prefix="${PREFIX}" --enable-static --disable-shared \
    --disable-openssl --disable-samples --disable-libevent-regress \
    --disable-thread-support
  make -j"$(nproc)"
  make install
else
  mkdir -p build && cd build
  cmake -DCMAKE_INSTALL_PREFIX="${PREFIX}" \
    -DEVENT__DISABLE_OPENSSL=ON -DEVENT__DISABLE_BENCHMARK=ON \
    -DEVENT__DISABLE_TESTS=ON -DEVENT__DISABLE_SAMPLES=ON \
    -DBUILD_SHARED_LIBS=OFF -DCMAKE_BUILD_TYPE=Release ..
  cmake --build . -j"$(nproc)"
  cmake --install .
fi

echo "== libevent installed to ${PREFIX} =="
ls -R "${PREFIX}" | head -40
