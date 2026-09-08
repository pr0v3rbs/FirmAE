# FirmAE fixes for modern distros (Kali/Debian 2025+)

These changes make FirmAE boot firmware on current distros where the original
setup breaks. Verified emulating D-Link **DIR-X1860 v4.5.2** (MIPSel/MT7621).

## 1. `tunctl` → `ip tuntap`  (the main blocker)

`uml-utilities` (which provided `tunctl`) has **no installation candidate** on
recent Kali/Debian, so TAP creation failed with `sudo: tunctl: command not found`
and no network came up. Replaced `tunctl` with the equivalent `iproute2` calls
(always present):

- `scripts/makeNetwork.py`
  - create: `sudo tunctl -t $TAP -u $USER` → `sudo ip tuntap add dev $TAP mode tap user $USER`
  - delete: `sudo tunctl -d $TAP`         → `sudo ip tuntap del dev $TAP mode tap`
- `scripts/delete.sh`
  - `sudo tunctl -d tap${IID}_${i}` → `sudo ip tuntap del dev tap${IID}_${i} mode tap`
- `install.sh` — dropped the now-unavailable `uml-utilities` package.

## 2. `scripts/importFS.sh` — run emulation with a PRE-EXTRACTED rootfs

`sources/extractor/extractor.py` fails on some newer `uImage + SquashFS(xz)`
images (e.g. recent D-Link), aborting `run.sh` with `extractor.py failed!`.
If you extracted the root filesystem yourself (e.g. `binwalk` + `unsquashfs`
/ `sasquatch`), `importFS.sh` registers it exactly as the extractor would so the
rest of the pipeline (getArch → tar2db → makeImage → makeNetwork → boot) runs:

```bash
sudo ./scripts/importFS.sh <brand> <firmware.bin> <extracted_rootfs_dir>
sudo ./run.sh -r <brand> <firmware.bin>   # extractor step fails harmlessly; pipeline continues
```

## 3. Note: multi-NIC / VLAN LAN firmware

Some firmware puts its LAN on a tagged sub-interface of a non-first NIC (the
DIR-X1860 bridges `br0` over `eth2.1`). If `makeNetwork` attaches the host TAP to
`eth0` you get no connectivity. Attach the TAP to the NIC the firmware actually
uses for LAN (here the 3rd e1000 = `net2`/`eth2`) and reach `192.168.0.1` over a
VLAN-1 host sub-interface (`tapN_0.1`). FirmAE already emits VLAN host interfaces
when `FIRMAE_NET=true`; if the wrong NIC is chosen, edit the generated
`scratch/<iid>/run.sh` qemu `-netdev tap,...ifname=` to the correct `netN`.

## Dependencies
`install.sh` already pulls `bash-static busybox-static` (needed by `makeImage.sh`).
The `vlan` package (for `ip link ... type vlan`) is also already listed.
