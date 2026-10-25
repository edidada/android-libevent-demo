cmake_minimum_required(VERSION 3.18)
project(libevent_demo CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# LIBEVENT_ROOT points at a prebuilt libevent prefix (lib/ + include/)
if(NOT LIBEVENT_ROOT)
  set(LIBEVENT_ROOT "/usr")
endif()

find_library(LOG_LIB log)

add_executable(libevent_demo src/main.cpp)
target_include_directories(libevent_demo PRIVATE ${LIBEVENT_ROOT}/include)
target_link_libraries(libevent_demo ${LIBEVENT_ROOT}/lib/libevent.a)

if(ANDROID)
  # Android: libevent may reference dlopen; bionic integrates pthread into libc
  if(LOG_LIB)
    target_link_libraries(libevent_demo ${LOG_LIB})
  endif()
  target_link_libraries(libevent_demo dl)
else()
  # Linux native smoke-test build
  target_link_libraries(libevent_demo pthread dl)
endif()
