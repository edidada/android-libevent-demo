# android-libevent-demo

在 Android 平台上使用 [libevent](https://github.com/libevent/libevent) 的最小演示工程。

- `src/main.cpp`：用 libevent 的 `event_base` 创建一个 0.5s 周期定时器，触发 3 次后退出（可移植：Android 用 `__android_log_print`，Linux 用 `printf`）。
- `build_libevent.sh`：用 Android NDK 的 cmake toolchain 把 libevent 2.1.12 交叉编译为 **arm64-v8a** 静态库（关闭 OpenSSL/测试/样例以减小体积）；传入空 NDK 路径则做原生(host)构建。
- `CMakeLists.txt`：把预编译好的 libevent 静态库链接进一个 native 可执行文件 `libevent_demo`，同时兼容 Android（NDK）与 Linux（原生，用于冒烟测试）。

## 本地交叉编译（需自备 NDK）

```bash
# 1) 交叉编译 libevent -> ./prebuilt
bash build_libevent.sh $ANDROID_NDK_HOME arm64-v8a 24 $PWD/prebuilt

# 2) 用 NDK toolchain 构建 demo
cmake -S . -B build-android \
  -DCMAKE_TOOLCHAIN_FILE=$ANDROID_NDK_HOME/build/cmake/android.toolchain.cmake \
  -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-24 \
  -DLIBEVENT_ROOT=$PWD/prebuilt
cmake --build build-android

# 产物：build-android/libevent_demo （可 adb push 到设备运行）
```

## CI

GitHub Actions（`.github/workflows/build.yml`）做两件事：

1. **android** job：下载 NDK r27c → 交叉编译 libevent → 交叉编译 demo（arm64-v8a），验证 Android 平台可链接 libevent。
2. **linux-smoke** job：在 runner 上从源码构建 libevent（host）→ 编译并**运行**同一份代码，证明 libevent 逻辑可用（无需 Android 设备即可冒烟测试）。

> libevent 是纯 C 事件通知库，官方支持 Android NDK 交叉编译，因此“第三方库可交叉编译进 Android”在本工程中得到了实际验证。
