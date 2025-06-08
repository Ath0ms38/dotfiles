# Starship Configuration

This directory contains the Starship prompt configuration.

## Files

- `.config/starship.toml` - Starship configuration file

## Features

- Custom prompt format with box-drawing characters
- Git branch and status indicators
- Language-specific icons for various programming languages
- Directory path with repository-aware truncation
- Colored output for better visibility

## Installation

To install just the starship configuration:

```bash
make starship
```

This will symlink the `starship.toml` file to `~/.config/starship.toml` using GNU Stow.

## Requirements

Make sure you have Starship installed on your system. You can install it from:
- https://starship.rs/

Also ensure your shell is configured to use Starship. For Zsh, add this to your `.zshrc`:

```bash
eval "$(starship init zsh)"
