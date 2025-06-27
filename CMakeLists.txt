cmake_minimum_required(VERSION 3.12)

project(DSGRN)

cmake_policy(SET CMP0054 NEW)

# Visual Studio C++ does not support keywords such
# as "and", "not", etc. Settting the /permissive-
# flag for the compiler makes it suppor them.
if(MSVC)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /permissive-")
endif()

add_subdirectory(pybind11)

include_directories (
  ${CMAKE_SOURCE_DIR}/include
  /usr/local/include
  ${USER_INCLUDE_PATH} )

link_directories (
  ${USER_LIBRARY_PATH}
  /usr/local/lib )

message("USER INCLUDE PATH IS ${USER_INCLUDE_PATH}")

pybind11_add_module(_dsgrn src/DSGRN/_dsgrn/DSGRN.cpp)
