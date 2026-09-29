# Host unit tests: plain executables that return non-zero on failure, run by CTest.
add_executable(test_app test_app.cpp)
target_link_libraries(test_app PRIVATE sprayrover_app)
add_test(NAME test_app COMMAND test_app)
