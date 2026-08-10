# NEYROLOC — legacy remote-access notes

This directory is retained only for the local `frpc` binary and historical
context. The current, multi-tenant deployment is documented in
`deploy/README.md`; the desktop application provisions and starts its tunnel
through `NEYROLOCK_5/core/tunnel.py`.

Do not commit `frpc.toml`, tunnel tokens, server addresses, private keys, or
other machine-specific infrastructure data here. Both `frpc.toml` and the
local `frpc` binary are excluded by `remote/.gitignore`.

For local Wi-Fi access, start the desktop application's remote server and use
the address/QR code shown in “Файл → Удалённый доступ с телефона”. For public
access, use the tunnel controls in the same dialog.
