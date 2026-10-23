# Legacy TLS verifier backport

`rustls-webpki-legacy` is the ISC-licensed0.102.8 crate, verified against its Cargo.lock SHA256. `SECURITY-BACKPORT.json` records provenance and all eight exact upstream0.103.16 SPKI byte-file hashes. Original license/copyright notices are retained.

The two upstream path/anchor-SPKI checks are applied before path verification. They return the existing `UnknownIssuer` error to preserve this old branch API. Signature, hostname, expiry, trust-anchor and revocation checks remain enabled. This compatiblepatch changes only known compromised-key acceptance.

The path patch is needed by libsql0.9.30/Rustls0.22.4. The modern branch stays on upstreamwebpki0.103.16. This backport does not fix every historical0.102.x nameconstraint/CRL advisory; qualify a supportedlibsql upgrade separately. Remove this patch when that supported migration no longerresolves0.102.x.

Rollback: revert the pathpatch and its lockfile changes; restoringvulnerable verification is a securityregression, so retain isolation and patchedsystemroots.

The upstream README setext headings and trailing spaces in documentation/OpenSSL PEM annotations are normalized for repository whitespace checks. Every encoded PEM block is verified unchanged; per-file before/after hashes are in SECURITY-BACKPORT.json.

Remaining legacy advisories: https://github.com/advisories/GHSA-xgp8-3hg3-c2mh ; https://github.com/advisories/GHSA-965h-392x-2mh5 ; https://github.com/advisories/GHSA-82j2-j2ch-gfr8 ; https://github.com/advisories/GHSA-pwjx-qhcg-rvj4 . This fork disables issue tracking, so retain these explicit open findings until separately qualified.
