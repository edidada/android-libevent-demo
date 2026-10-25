"""Build catalog entries outside vcpkg, using the same Android toolchain."""
import argparse
import json
import os
from pathlib import Path
import shutil
import re
import subprocess
import sys


def run(*args, cwd=None):
    print('+', *map(str, args), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ndk', required=True)
    parser.add_argument('--abi', required=True)
    args = parser.parse_args()
    root = Path('out/extra').resolve()
    root.mkdir(parents=True, exist_ok=True)
    results = {}
    sources = {
        'libkev': ('Jamol/libkev', '1e0d103eecb2a6b97a698ff4f1effd15ec069da1'),
        'gear-lib': ('gozfree/gear-lib', 'bffbfd25af4ff7b04ebfafdab391b55270b0273e'),
        'box2d': ('erincatto/box2d', 'v2.4.1'),
        'tbox': ('tboox/tbox', 'c8fb971e2bf43c3402aa32e1a8ae70de11163f63'),
        'tensorflow-lite': ('tensorflow/tensorflow', 'v2.18.0'),
    }
    for name, (repo, ref) in sources.items():
        try:
            src = root / (name + '-src')
            prefix = root / name
            run('git', 'init', src)
            run('git', 'remote', 'add', 'origin', 'https://github.com/' + repo + '.git', cwd=src)
            run('git', 'fetch', '--depth', '1', 'origin', ref, cwd=src)
            run('git', 'checkout', 'FETCH_HEAD', cwd=src)
            if name == 'tbox':
                arch = {'arm64-v8a': 'arm64-v8a', 'armeabi-v7a': 'armeabi-v7a',
                        'x86': 'x86', 'x86_64': 'x86_64'}[args.abi]
                run('xmake', 'f', '-y', '-p', 'android', '-a', arch, '-m', 'release',
                    '--ndk=' + args.ndk, '--ndk_sdkver=24', '--demo=n', cwd=src)
                run('xmake', '-y', '-j', '3', 'tbox', cwd=src)
                run('xmake', 'install', '-o', prefix, 'tbox', cwd=src)
            else:
                if name == 'libkev':
                    cm = src / 'CMakeLists.txt'
                    cm.write_text(cm.read_text().replace('-Werror', ''), encoding='utf-8')
                if name == 'gear-lib':
                    log = src / 'gear-lib/liblog/liblog.c'
                    log.write_text(re.sub(r'\bgettid\b', 'gear_gettid', log.read_text()), encoding='utf-8')
                    thread = src / 'gear-lib/libthread/libthread.c'
                    text = thread.read_text()
                    # Bionic does not expose inheritance attributes. Thread names are
                    # already saved by thread_set_name; getname_np requires API 26.
                    text = text.replace('    if (0 == pthread_attr_getinheritsched',
                                        '#ifndef __ANDROID__\n    if (0 == pthread_attr_getinheritsched')
                    text = text.replace('    if (0 == pthread_attr_getschedpolicy',
                                        '#endif\n    if (0 == pthread_attr_getschedpolicy')
                    text = text.replace('if (0 == pthread_getname_np(t->tid, t->name, sizeof(t->name)))',
                                        "if (t->name[0] != '\\0')")
                    thread.write_text(text, encoding='utf-8')
                    # Portable networking subset. Exclude Windows poller and optional AV dependencies.
                    modules = ['libposix', 'libdarray', 'libthread', 'liblog', 'libgevent', 'libsock']
                    cmake = ['cmake_minimum_required(VERSION 3.16)', 'project(gear C)',
                             'set(OS_LINUX TRUE)', 'set(BUILD_SHARED_LIBS OFF)']
                    for mod in modules:
                        cmake += [f'set({mod[3:].upper()}_INCLUDE_DIR "${{CMAKE_CURRENT_SOURCE_DIR}}/gear-lib/{mod}")']
                    for mod in modules:
                        cmake += [f'add_subdirectory(gear-lib/{mod})']
                    cmake += ['install(TARGETS posix darray thread log gevent sock ARCHIVE DESTINATION lib)',
                              'install(DIRECTORY gear-lib/ DESTINATION include FILES_MATCHING PATTERN "*.h")']
                    (src / 'CMakeLists.txt').write_text('\n'.join(cmake), encoding='utf-8')
                build = root / (name + '-build')
                cmake_src = src / 'tensorflow/lite' if name == 'tensorflow-lite' else src
                run('cmake', '-S', cmake_src, '-B', build, '-G', 'Ninja',
                    '-DCMAKE_TOOLCHAIN_FILE=' + args.ndk + '/build/cmake/android.toolchain.cmake',
                    '-DANDROID_ABI=' + args.abi, '-DANDROID_PLATFORM=android-24',
                    '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_POLICY_VERSION_MINIMUM=3.5',
                    '-DBUILD_SHARED_LIBS=OFF', '-DBOX2D_BUILD_UNIT_TESTS=OFF',
                    '-DBOX2D_BUILD_TESTBED=OFF', '-DTFLITE_ENABLE_XNNPACK=OFF',
                    '-DTFLITE_ENABLE_GPU=OFF', '-DTFLITE_ENABLE_INSTALL=ON',
                    '-DCMAKE_INSTALL_PREFIX=' + str(prefix))
                run('cmake', '--build', build, '--parallel', '3')
                if name == 'libkev':
                    (prefix / 'lib').mkdir(parents=True, exist_ok=True)
                    for lib in src.rglob('libkev.a'):
                        shutil.copy2(lib, prefix / 'lib' / lib.name)
                    shutil.copytree(src / 'include', prefix / 'include', dirs_exist_ok=True)
                else:
                    run('cmake', '--install', build)
            libraries = list(prefix.rglob('*.a'))
            if not libraries:
                raise RuntimeError('No Android static archive installed for ' + name)
            results[name] = {'status': 'success', 'libraries': [str(p.relative_to(prefix)) for p in libraries]}
        except (subprocess.CalledProcessError, OSError, RuntimeError) as exc:
            results[name] = {'status': 'failure', 'error': str(exc)}
    (root / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))
    return int(any(item['status'] != 'success' for item in results.values()))


if __name__ == '__main__':
    sys.exit(main())
