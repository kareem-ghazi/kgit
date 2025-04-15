<div align="center">
  <br>
  <img src="kgit-logo.png" alt="Sawarly" width="40%" style="margin: 10px 0;" />
  <br><br>
</div>

<div align="center" style="line-height: 1;">
  <a href="https://github.com/kareem-ghazi/kgit" target="_blank" style="margin: 2px;">
    <img alt="Latest Release" src="https://img.shields.io/badge/Latest%20Release-1.0-brightgreen" />
  </a>
  <a href="https://opensource.org/license/mit" target="_blank" style="margin: 2px;">
    <img alt="License" src="https://img.shields.io/badge/License-MIT-red" />
  </a>
    <a href="https://python.org/" target="_blank" style="margin: 2px;">
    <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" />
  </a>
  <a href="https://www.microsoft.com/windows" target="_blank" style="margin: 2px;">
    <img alt="Platform" src="https://img.shields.io/badge/Platform-Linux-black?logo=windows" />
  </a>
</div>

## Introduction

**kgit** is a minimal Git implementation written from scratch in Python, based on the [wyag](https://wyag.thb.lt/) project. This repository reimplements the core features of the [Git version control system](https://git-scm.com/) from the ground up.

The goal is to demonstrate that, despite its reputation for complexity, the core of Git is simple and elegant.

## What is Implemented?

kgit implements the following core Git commands, compatible with real Git repositories:

- `add`
- `cat-file`
- `check-ignore`
- `checkout`
- `commit`
- `hash-object`
- `init`
- `log`
- `ls-files`
- `ls-tree`
- `rev-parse`
- `rm`
- `show-ref`
- `status`
- `tag`

Each command is a simplified version of its Git counterpart, focusing on clarity and core functionality.

## Getting Started

1. **Clone this repository:**
   ```bash
   git clone https://github.com/kareem-ghazi/kgit
   cd kgit
   ```

2. **Run kgit commands:**
   ```bash
   python3 src/kgit <command> [options]
   ```

3. **Explore the code:**  
   The main logic is in `src/kgit/libkgit.py`. Each command is implemented in a clear, readable way.

## License

This project is released under the MIT License. See [LICENSE.txt](LICENSE.txt) for details.
