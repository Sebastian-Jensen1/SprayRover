cmake_minimum_required(VERSION 3.22)

# Navigation & vehicle MCU firmware (STM32H7).
#
# The portable application code in app/ is built as a static library, so it can be
# compiled and unit-tested on the host (default) and cross-compiled for the MCU with
#   cmake -B build-arm -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake
# The STM32CubeMX-generated startup/HAL code and the firmware executable are added
# once the board is chosen (see documentation/design/open-questions.md #2).

project(sprayrover_nav_mcu LANGUAGES C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(sprayrover_app STATIC
    app/src/app.cpp
)
target_include_directories(sprayrover_app PUBLIC app/include)
target_compile_options(sprayrover_app PRIVATE -Wall -Wextra -Wpedantic -Werror)

if(NOT CMAKE_CROSSCOMPILING)
    enable_testing()
    add_subdirectory(tests)
endif()
