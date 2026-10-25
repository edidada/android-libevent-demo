#!/usr/bin/env bash
# Cross-compile (or native-build) libevent for Android/Linux using CMake.
# Usage: build_libevent.sh <NDK_PATH|""> <ABI> <API_LEVEL> <INSTALL_PREFIX>
#   - pass an empty NDK_PATH ("") to do a native host build (Linux smoke test)
set -euo pipefail

NDK="${1:-}"
ABI="${2:-arm64-v8a}"
API="${3:-24}"
PREFIX="${4:?install prefix required}"
VER="2.1.12-stable"

WORK="$(mktemp -d)"
echo "== building libevent ${VER} (NDK='${NDK:-host}') =="
cd "$WORK"
curl -fSL "https://github.com/libevent/libevent/archive/refs/tags/release-${VER}.tar.gz" -o le.tgz
tar xzf le.tgz
cd "libevent-release-${VER}"

mkdir -p build && cd build

# On Android, pthread is integrated into libc (no -lpthread lib), so force
# FindThreads to detect it via the -pthread flag instead of -lpthread.
if [ -n "${NDK}" ]; then
  cmake -DCMAKE_TOOLCHAIN_FILE="${NDK}/build/cmake/android.toolchain.cmake"         -DANDROID_ABI="${ABI}" -DANDROID_PLATFORM="android-${API}"         -DTHREADS_PREFER_PTHREAD_FLAG=ON -DCMAKE_THREAD_PREFER_PTHREAD=ON         -DCMAKE_INSTALL_PREFIX="${PREFIX}"         -DEVENT__DISABLE_OPENSSL=ON -DEVENT__DISABLE_BENCHMARK=ON         -DEVENT__DISABLE_TESTS=ON -DEVENT__DISABLE_SAMPLES=ON         -DBUILD_SHARED_LIBS=OFF -DCMAKE_BUILD_TYPE=Release ..
else
  cmake -DCMAKE_INSTALL_PREFIX="${PREFIX}"         -DEVENT__DISABLE_OPENSSL=ON -DEVENT__DISABLE_BENCHMARK=ON         -DEVENT__DISABLE_TESTS=ON -DEVENT__DISABLE_SAMPLES=ON         -DBUILD_SHARED_LIBS=OFF -DCMAKE_BUILD_TYPE=Release ..
fi

cmake --build . -j"$(nproc)"
cmake --install .
echo "== libevent installed to ${PREFIX} =="
ls -R "${PREFIX}" | head -40
