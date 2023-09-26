cmake_minimum_required(VERSION 3.12)

project(LLVM_IR_Project)

# Find LLVM package
find_package(LLVM REQUIRED CONFIG)

# Set the path to LLVM IR file
set(LLVM_IR_FILE "main.ll")

# Create a custom target to run LLVM IR
add_custom_target(run_llvm_ir
    COMMAND ${LLVM_TOOLS_BINARY_DIR}/lli ${CMAKE_CURRENT_SOURCE_DIR}/${LLVM_IR_FILE}
    DEPENDS ${LLVM_IR_FILE}
    COMMENT "Running LLVM IR file: ${LLVM_IR_FILE}"
)