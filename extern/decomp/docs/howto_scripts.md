# Howto / Tools Overview – Super Mario Strikers Decomp Project

This document explains two helpful tools used in the decompilation workflow: `class_gen` for generating source files and `clang-format` for consistent code formatting.

---

## 1. `class_gen`

The `class_gen` script is used to generate `.h` and `.cpp` files from translation unit (TU) disassembly files. This significantly accelerates the process of creating new files, which would otherwise require tedious and repetitive copy-pasting.

### Features

* Parses TU `.s` files and generates corresponding `.h` and `.cpp` files.
* Automatically translates metadata such as demangled method names.
* Adds symbol data (address, size, offset) as structured comments.

### Usage

To generate files for a single object file:

```bash
./tools/scripts/class_gen.py --obj-file ./build/G4QE01/asm/Goalie.s
```

This will produce `.h` and `.cpp` files in:

**⚠️ Make sure to review the generated files before moving them into their proper locations in the codebase.**


For more detailed information about the script's features and advanced usage, see [class_gen.md](../../tools/scripts/class_gen.md).

---

## 2. Code Formatting with `clang-format`

Consistent code formatting improves readability for both yourself and contributors. We use [`clang-format`](https://clang.llvm.org/docs/ClangFormat.html) with a shared style configuration to enforce consistency across the project.

### Usage

To format a file:

```bash
./format.sh src/Game/PhysicsObject.cpp
```

### ⚠️ Inline Assembly Warning

Be careful when formatting files with inline `asm` blocks. `clang-format` will likely break the formatting or logic of assembly code. To prevent this, you **must** wrap inline assembly with `clang-format` guards:

#### Example:

```cpp
asm static void __init_registers(void) {
  // clang-format off
  nofralloc
  lis r1,  _stack_addr@h
  ori r1, r1,  _stack_addr@l
  lis r2, _SDA2_BASE_@h
  ori r2, r2, _SDA2_BASE_@l
  lis r13, _SDA_BASE_@h
  ori r13, r13, _SDA_BASE_@l
  blr
  // clang-format on
}
```
