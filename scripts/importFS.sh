#!/bin/bash
# importFS.sh - register a PRE-EXTRACTED root filesystem so the emulation
# pipeline can run even when sources/extractor/extractor.py cannot unpack the
# firmware image (common for newer uImage+SquashFS layouts, e.g. some D-Link).
#
# It reproduces exactly what the extractor is expected to leave behind:
#   * a row in the `image` table (keyed by md5 of the firmware file) -> IID
#   * ./images/<IID>.tar.gz  (a gzipped tar of the extracted root filesystem)
#
# After running this, invoke the normal pipeline:
#   sudo ./run.sh -r <brand> <firmware.bin>
# run.sh's own extractor call may still fail harmlessly; get_iid returns the IID
# from the DB and ./images/<IID>.tar.gz already exists, so it proceeds to
# getArch -> tar2db -> makeImage -> makeNetwork -> boot.
#
# Usage:
#   sudo ./scripts/importFS.sh <brand> <firmware_file> <extracted_rootfs_dir> [psql_ip]
# Example:
#   sudo ./scripts/importFS.sh dlink ./DIR_X1860_4.5.2.bin /path/to/rootfs
set -eu

BRAND="${1:?brand (e.g. dlink)}"
FW="${2:?path to firmware file (used only for its md5/IID key)}"
ROOTFS="${3:?path to already-extracted root filesystem directory}"
PSQL_IP="${4:-127.0.0.1}"

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

[ -d "$ROOTFS" ] || { echo "[-] rootfs dir not found: $ROOTFS"; exit 1; }
[ -f "$FW" ]     || { echo "[-] firmware file not found: $FW"; exit 1; }

MD5=$(md5sum "$FW" | cut -d' ' -f1)
FNAME=$(basename "$FW")
echo "[*] firmware md5 (IID key): $MD5"

psql_() { sudo -u postgres psql -d firmware -tAqc "$1"; }

# brand + image row (idempotent)
psql_ "INSERT INTO brand(name) SELECT '$BRAND' WHERE NOT EXISTS (SELECT 1 FROM brand WHERE name='$BRAND');" >/dev/null
IID=$(psql_ "INSERT INTO image(filename,brand_id,hash,rootfs_extracted) \
             VALUES ('$FNAME',(SELECT id FROM brand WHERE name='$BRAND'),'$MD5',true) \
             ON CONFLICT (hash) DO UPDATE SET filename=EXCLUDED.filename RETURNING id;" | tr -d '[:space:]')
[ -n "$IID" ] || { echo "[-] failed to register image in DB"; exit 1; }
echo "[+] IID = $IID"

mkdir -p ./images
echo "[*] building ./images/$IID.tar.gz from $ROOTFS ..."
tar --numeric-owner -czf "./images/$IID.tar.gz" -C "$ROOTFS" .
echo "[+] wrote ./images/$IID.tar.gz ($(du -h ./images/$IID.tar.gz | cut -f1))"

echo
echo "[+] Done. Now run the pipeline (the extractor step may print a harmless"
echo "    failure; the pipeline continues using the tarball above):"
echo "      sudo ./run.sh -r $BRAND $FW"
