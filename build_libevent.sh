#!/usr/bin/env bash
# Cross-compile libevent for Android using the NDK cmake toolchain.
# Usage: build_libevent.sh <NDK_PATH> <ABI> <API_LEVEL> <INSTALL_PREFIX>
set -euo pipefail

NDK="${1:?NDK path required}"
ABI="${2:-arm64-v8a}"
API="${3:-24}"
PREFIX="${4:?install prefix required}"
VER="2.1.12-stable"

WORK="$(mktemp -d)"
echo "== building libevent ${VER} for ${ABI}/android-${API} =="
cd "$WORK"
curl -fSL "https://github.com/libevent/libevent/archive/refs/tags/release-${VER}.tar.gz" -o le.tgz
tar xzf le.tgz
cd "libevent-release-${VER}"

mkdir -p build && cd build
cmake -DCMAKE_TOOLCHAIN_FILE="${NDK}/build/cmake/android.toolchain.cmake" -DANDROID_ABI="${ABI}" -DANDROID_PLATFORM="android-${API}" -DCMAKE_INSTALL_PREFIX="${PREFIX}" -DEVENT__DISABLE_OPENSSL=ON -DEVENT__DISABLE_BENCHMARK=ON -DEVENT__DISABLE_TESTS=ON -DEVENT__DISABLE_SAMPLES=ON -DBUILD_SHARED_LIBS=OFF -DCMAKE_BUILD_TYPE=Release .
cmake --build . -j"$(nproc)"
cmake --install .
echo "== libevent installed to ${PREFIX} =="
ls -R "${PREFIX}" | head -40
