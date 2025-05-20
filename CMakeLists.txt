cmake_minimum_required(VERSION 3.15...3.26)

project(${SKBUILD_PROJECT_NAME} VERSION ${SKBUILD_PROJECT_VERSION} LANGUAGES CXX)

# cmake_policy(SET CMP0054 NEW)

# Visual Studio C++ does not support keywords such
# as "and", "not", etc. Settting the /permissive-
# flag for the compiler makes it suppor them.
if(MSVC)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /permissive-")
endif()

set(PYBIND11_FINDPYTHON ON)

find_package(pybind11 CONFIG REQUIRED)

# With the settings above pybind11 finds Python
# find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)

# USER_PROJECT_PATH is set in pyproject.toml
include_directories(${CMAKE_SOURCE_DIR}/${USER_PROJECT_PATH}/include)
# include_directories(${CMAKE_SOURCE_DIR}/src/DSGRN/_dsgrn/include)

pybind11_add_module(_dsgrn MODULE ${USER_PROJECT_PATH}/DSGRN.cpp)
# pybind11_add_module(_dsgrn MODULE src/DSGRN/_dsgrn/DSGRN.cpp)

message("USER PROJECT PATH IS ${USER_PROJECT_PATH}")
message("CMAKE SOURCE DIR IS ${CMAKE_SOURCE_DIR}")
message("CMAKE MODULE PATH IS ${CMAKE_MODULE_PATH}")
message("SKBUILD PROJECT NAME IS ${SKBUILD_PROJECT_NAME}")

install(TARGETS _dsgrn DESTINATION ${SKBUILD_PROJECT_NAME})
