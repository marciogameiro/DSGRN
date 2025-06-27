cmake_minimum_required(VERSION 3.15...3.26)

project(DSGRN)

cmake_policy(SET CMP0054 NEW)

# Visual Studio C++ does not support keywords such
# as "and", "not", etc. Settting the /permissive-
# flag for the compiler makes it suppor them.
if(MSVC)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /permissive-")
endif()

set(PYBIND11_FINDPYTHON ON)

find_package(pybind11 CONFIG REQUIRED)

include_directories (
  ${CMAKE_SOURCE_DIR}/include
  ${USER_INCLUDE_PATH}
  /usr/local/include )

link_directories (
  ${USER_LIBRARY_PATH}
  /usr/local/lib )

message("USER INCLUDE PATH IS ${USER_INCLUDE_PATH}")

pybind11_add_module(_dsgrn src/DSGRN/_dsgrn/DSGRN.cpp)
