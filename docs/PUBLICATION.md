# Public source boundary

This repository begins with a fresh sanitized root commit. Private bench history is deliberately not a parent. Public content includes engineering sources, measured records, CAD, derived review artifacts, selected regression fixtures and ten hardware photos. EXIF/XMP/ICC and comment metadata were removed from published JPEG copies without recompressing image data; CAD photo/source hashes were updated without changing BRep geometry. Private originals remain separate.

Never add flash dumps, compiled firmware, NVS, credentials, SSH keys, private network details, personal paths, raw runtime inventories, internal coordination files, host-administration scripts or unsanitized logs. Keep local configuration under ignored `local/`, use environment variables for device discovery, and review staged content before every push. Ignore rules are convenience, not a security boundary. Run `python tools/check_public_content.py` and an independent secret scanner before publication. CI checks common mistakes; human review remains necessary.

If a secret is exposed, notify the owner privately, revoke/rotate it, and coordinate history cleanup. Never paste secrets into a public issue.
