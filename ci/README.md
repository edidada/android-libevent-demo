# Android 库清单构建

来源为仓库根目录 `library.txt`。产物是 Android NDK 静态库和头文件；Linux、macOS、Windows 是编译宿主。并不把宿主原生库当作 Android 产物，也不代表在 Android 真机运行验证。

## 覆盖范围

| 清单项目 | 实际构建 |
| --- | --- |
| 网络、事件循环 | libevent、libuv、libwebsockets、libcurl、libkev |
| Gear-Lib | libposix、libdarray、libthread、liblog、libgevent、libsock 子集；不包含整个多媒体组件集 |
| nCine 依赖库 | libogg、libvorbis、libpng、libwebp、OpenAL-soft、Lua、Box2D 2.4.1、libcurl；不构建 nCine 引擎 |
| 数据、日志 | SQLite、json-c、Jansson、nlohmann/json、spdlog |
| 通用库 | POCO 默认基础组件；Boost Asio、filesystem、system、thread、regex 及其依赖；TBOX |
| 加密 | OpenSSL、mbed TLS |
| 媒体、图像 | FFmpeg avcodec/avformat/swresample/swscale 基础功能、OpenCV 基础模块、SDL3 |
| 序列化、RPC | protobuf、gRPC |
| 推理 | llama.cpp CPU 库、ONNX Runtime CPU 库、TensorFlow Lite CPU 库（关闭 GPU/XNNPACK） |

各库并非所有可选模块和编解码器均启用。详细选项见 `vcpkg.json` 和 `build_extra.py`。vcpkg baseline 和额外源码 commit/tag 固定，避免每次构建追踪浮动分支。

## 矩阵

- Ubuntu 22.04 / 24.04、macOS 14 / 15、Windows Server 2022 / 2025。
- 每个宿主版本分别构建 NDK r27c (`27.2.12479018`) 和 r28c (`28.2.13676358`)，arm64-v8a、API 24。
- Ubuntu 24.04 + r28c 额外构建 armeabi-v7a、x86、x86_64，API 24。
- 共 15 个任务；关闭 fail-fast，一个平台失败不会取消其他平台。

`libraries.yml` 在 push 到 edidada/android-libevent-demo 的 main 分支后执行，支持手动触发。保留原有 libevent 演示和 Linux 原生运行测试。

构建后用 NDK `llvm-readobj` 检查每个静态归档的 ELF 架构，另将 libevent 链接到 Android demo。Artifact 中提供头文件、静态库、版权文件、逐库结果、架构校验 JSON 和构建日志，保留 7 天。失败任务上传的部分产物不等于整个清单通过。

## 复现与查询

```bash
# 使用 workflow 指定的 vcpkg commit，bootstrap 后：
export ANDROID_NDK_HOME=/absolute/path/to/android-ndk
.ci-vcpkg/vcpkg install --triplet=arm64-android --overlay-triplets="$PWD/ci/triplets" --x-manifest-root="$PWD/ci" --x-install-root="$PWD/out/installed" --keep-going
python ci/build_extra.py --ndk "$ANDROID_NDK_HOME" --abi arm64-v8a
python ci/verify_artifacts.py --ndk "$ANDROID_NDK_HOME" --abi arm64-v8a --triplet arm64-android
gh run list --repo edidada/android-libevent-demo --workflow libraries.yml
gh run view RUN_ID --repo edidada/android-libevent-demo --log-failed
gh run download RUN_ID --repo edidada/android-libevent-demo
```

额外构建需安装 CMake、Ninja、Git、Python 3 和 xmake 3.0.5。TensorFlow Lite 先用宿主编译器构建 flatc，再交叉编译目标库；Windows 预先初始化 MSVC。标准库由 vcpkg 处理交叉编译依赖，vcpkg 需要完整 Git 历史以解析依赖版本。纯 C/C++ NDK 工程不引入 Maven/Gradle Java 包装工程；CI SDK 工具使用 JDK 17。
