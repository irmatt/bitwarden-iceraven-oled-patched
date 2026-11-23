#!/usr/bin/env python3
"""Print SHA-256 fingerprints of certificates in an APK's v2/v3/v3.1 signing block.

Pure Python, no Android SDK or Java required. Also works on split-base APKs.
"""
import hashlib
import struct
import sys
from zipfile import ZipFile


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def u64(b, o):
    return struct.unpack_from("<Q", b, o)[0]


def certs_from_signed_data(sd):
    off = 4 + u32(sd, 0)
    certs_len = u32(sd, off)
    off += 4
    end = off + certs_len
    certs = []
    while off < end:
        n = u32(sd, off)
        off += 4
        certs.append(sd[off:off + n])
        off += n
    return certs


def signers_from_value(value):
    off, end = 4, 4 + u32(value, 0)
    out = []
    while off < end:
        n = u32(value, off)
        off += 4
        signer = value[off:off + n]
        off += n
        out.append(signer[4:4 + u32(signer, 0)])
    return out


def fingerprints(path):
    with ZipFile(path) as z:
        # The local-file header offsets are not enough: read the raw file for the signing block.
        data = open(path, "rb").read()
    eocd = data.rfind(b"PK\x05\x06")
    if eocd < 0:
        raise ValueError("no EOCD")
    cd_off = u32(data, eocd + 16)
    size = u64(data, cd_off - 24)
    start = cd_off - 8 - size
    if data[cd_off - 16:cd_off] != b"APK Sig Block 42":
        raise ValueError("no APK signing block")
    found = {}
    p, end = start + 8, cd_off - 24
    while p < end:
        plen = u64(data, p)
        block_id = u32(data, p + 8)
        value = data[p + 12:p + 8 + plen]
        label = {0x7109871A: "v2", 0xF05368C0: "v3", 0x1B93AD61: "v3.1"}.get(block_id)
        if label:
            found[label] = []
            for sd in signers_from_value(value):
                for der in certs_from_signed_data(sd):
                    found[label].append(":".join(f"{x:02X}" for x in hashlib.sha256(der).digest()))
        p += 8 + plen
    return found


for path in sys.argv[1:]:
    print("==", path)
    try:
        for scheme, certs in fingerprints(path).items():
            for cert in certs:
                print(f"{scheme}  {cert}")
    except Exception as e:
        print("ERROR", e)
