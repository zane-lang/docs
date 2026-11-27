# Install Zane

This page shows how to install `zane`, the command that builds and runs Zane programs, and a compiler for `zane` to use.

## Install `zane`

On **Linux x86_64** or **macOS on Apple Silicon**:

```sh
curl -fsSL https://github.com/zane-lang/zane/releases/latest/download/install.sh | sh
```

The script checks the download's SHA-256 and writes `~/.local/bin/zane`. To
install into another directory, set `ZANE_INSTALL_DIR`; to install a particular
version, pass its tag: `sh -s -- v0.18`.

On **Windows x86_64**, in PowerShell:

```powershell
& ([scriptblock]::Create((Invoke-RestMethod https://github.com/zane-lang/zane/releases/latest/download/install.ps1)))
```

The PowerShell script installs into `%LOCALAPPDATA%\Programs\Zane\bin` and
adds that folder to your user `Path`. To install a particular version or into
another folder, add `-Version v0.18` or `-InstallDir <folder>` after the
command above.

Neither installer needs administrator access. You can also download the
binaries from the [releases page](https://github.com/zane-lang/zane/releases)
and read the scripts before running them.

## Put it on your `PATH`

On Linux and macOS, `~/.local/bin` is often on the `PATH` already. If the
shell reports that `zane` is not found when you run `zane --version`, add this
line to `~/.bashrc` or `~/.zshrc` and open a new terminal:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

## Install a compiler

`zane` runs the Zane compiler, `zanec`, which comes as a separate download.
Install the newest release:

```sh
zane toolchain install
zane --version
```

Compilers are installed side by side under `~/.zane/toolchains/`, one
directory per version, so projects pinned to different versions build next to
each other. Each compiler release includes everything needed to build programs
for Linux, macOS and Windows, including the C compiler that builds a
package's C code ([Calling C](guides/c-interop.md)), so you don't need to
install a C compiler or LLVM yourself.
To keep `zane`'s files in a directory other than `~/.zane`, set `ZANE_HOME`.

A new project is pinned to the newest compiler installed. Installing a newer
compiler later doesn't change any existing project until you run
`zane toolchain update` in that project; see [Projects](guides/projects.md#the-compiler-a-project-uses).

## Keep `zane` up to date

```sh
zane self update
```

`zane self update` replaces the running `zane` with the latest release, after
checking the release's SHA-256. A `zane` installed through Nix or Homebrew is
updated by that package manager instead.

## Editor support

[`zane-nvim`](https://github.com/zane-lang/zane-nvim) gives Neovim (0.12 or
newer) syntax highlighting for `.zn` files through Tree-sitter. With
[lazy.nvim](https://github.com/folke/lazy.nvim):

```lua
{ "zane-lang/zane-nvim", lazy = false }
```

`zane-nvim` needs nvim-treesitter (`main` branch), the Tree-sitter CLI, a C
compiler, `curl` and `tar`; the parser installs itself the first time you open
a Zane file. The `zane-nvim` README lists the other ways to install it and its
options.

For C code in a package, `zane check` writes `compile_commands.json`, which
clangd reads.

## Next

[Your first project](first-project.md) creates, runs and tests a project.
