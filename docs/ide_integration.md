# BBC-AOS IDE Integration

## VS Code

Install the `ide/vscode-bbc-aos` extension folder during local development.

Commands:
- `BBC-AOS: Ask`
- `BBC-AOS: Index`
- `BBC-AOS: Vault Status`
- `BBC-AOS: Doctor`

## Cursor

Use the integrated terminal:

```bash
bbc ask "review auth module"
```

## JetBrains

Add an External Tool that runs `bbc` with arguments such as `ask "$Prompt$"`.

## Zed

Create a task that runs `bbc doctor`, `bbc index .`, or `bbc ask "<goal>"`.

## Neovim

Use `vim-dispatch` or a terminal split to run the BBC CLI.
