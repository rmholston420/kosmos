# Kosmos systemd deployment (Colossus)

Two units cooperate:

1. **DozerDB** — already running as a Docker container from `ops/compose/memory.yml`
   with `restart: unless-stopped`, so it survives host reboot on its own.
2. **kosmos-kernel.service** — this directory. Runs the FastAPI kernel with the
   DozerDB backend wired in via `/etc/kosmos/kernel.env`.

## Install (one-time)

```bash
sudo mkdir -p /etc/kosmos
sudo cp ops/systemd/kosmos-kernel.env /etc/kosmos/kernel.env
sudo chmod 600 /etc/kosmos/kernel.env
sudo chown root:root /etc/kosmos/kernel.env

sudo cp ops/systemd/kosmos-kernel.service /etc/systemd/system/kosmos-kernel.service
sudo systemctl daemon-reload
sudo systemctl enable --now kosmos-kernel.service
```

## Verify

```bash
systemctl status kosmos-kernel
journalctl -u kosmos-kernel -f
curl -sS http://127.0.0.1:8000/api/kernel/routes | python3 -m json.tool | head
```

## Change env

```bash
sudo editor /etc/kosmos/kernel.env
sudo systemctl restart kosmos-kernel
```

## Uninstall

```bash
sudo systemctl disable --now kosmos-kernel.service
sudo rm /etc/systemd/system/kosmos-kernel.service /etc/kosmos/kernel.env
sudo systemctl daemon-reload
```
