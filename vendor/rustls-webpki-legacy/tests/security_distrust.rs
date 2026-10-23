//! Deterministic incident-chain regression: no network and no disabled verification.
//! Deliberately legacy roots include AAA to exercise alternate cross-signs.
use pki_types::{CertificateDer, ServerName, UnixTime};
use std::{fs, path::PathBuf, time::Duration};
fn verify(host: &str) -> Result<(), webpki::Error> {
    let folder = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/security-fixtures");
    let mut paths = fs::read_dir(folder.join(host))
        .unwrap()
        .map(|p| p.unwrap().path())
        .collect::<Vec<_>>();
    paths.sort();
    let certs = paths
        .iter()
        .map(|p| CertificateDer::from(fs::read(p).unwrap()))
        .collect::<Vec<_>>();
    let ee = webpki::EndEntityCert::try_from(&certs[0])?;
    let legacy = ["AAA-Certificate-Services.der", "emSign-ECC-Root-CA-G3.der"]
        .iter()
        .map(|name| CertificateDer::from(fs::read(folder.join(name)).unwrap()))
        .collect::<Vec<_>>();
    let mut anchors = webpki_roots::TLS_SERVER_ROOTS.to_vec();
    for root in &legacy {
        anchors.push(webpki::anchor_from_trusted_cert(root)?);
    }
    let seconds = fs::read_to_string(folder.join("verification-time.txt"))
        .unwrap()
        .trim()
        .parse()
        .unwrap();
    ee.verify_for_usage(
        webpki::ALL_VERIFICATION_ALGS,
        &anchors,
        &certs[1..],
        UnixTime::since_unix_epoch(Duration::from_secs(seconds)),
        webpki::KeyUsage::server_auth(),
        None,
        None,
    )?;
    ee.verify_is_valid_for_subject_name(&ServerName::try_from(host).unwrap())
}
#[test]
fn legitimate_certificate_remains_valid() {
    assert_eq!(verify("example.com"), Ok(()));
}
#[test]
fn compromised_keys_rejected_in_direct_and_alternate_chains() {
    for cross in ["", "-aaa"] {
        for purpose in ["dv", "ov", "ev"] {
            for series in ["g3b", "g3c"] {
                let host = format!("{purpose}-{series}{cross}-emudhra.we-have-a-problem.com");
                assert_eq!(verify(&host), Err(webpki::Error::UnknownIssuer), "{host}");
            }
        }
    }
}
