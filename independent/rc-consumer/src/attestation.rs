//! Offline Ed25519 verification for the MNCS DSSE-compatible envelope subset.

use std::collections::{BTreeMap, BTreeSet};

use base64::Engine;
use base64::engine::general_purpose::STANDARD;
use ed25519_dalek::{Signature, VerifyingKey};
use serde::Serialize;
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};
use time::{OffsetDateTime, format_description::well_known::Rfc3339};

use crate::{canonical, json};

pub const PAYLOAD_TYPE: &str = "application/vnd.mncs.attestation-statement.v0.2+json";

#[derive(Debug, Clone, Serialize)]
pub struct SignatureResult {
    pub keyid: String,
    pub cryptographically_valid: bool,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct Verification {
    pub payload_valid: bool,
    pub expired: bool,
    pub cryptographically_valid: bool,
    pub signatures: Vec<SignatureResult>,
    pub statement: Option<Value>,
    pub issues: Vec<String>,
}

fn pae(payload_type: &str, payload: &[u8]) -> Vec<u8> {
    format!(
        "DSSEv1 {} {} {} ",
        payload_type.len(),
        payload_type,
        payload.len()
    )
    .into_bytes()
    .into_iter()
    .chain(payload.iter().copied())
    .collect()
}

fn key_id(raw: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(raw)))
}

fn parse_time(value: Option<&Value>) -> Option<OffsetDateTime> {
    value
        .and_then(Value::as_str)
        .and_then(|text| OffsetDateTime::parse(text, &Rfc3339).ok())
}

fn public_keys(records: &[Value]) -> Result<BTreeMap<String, VerifyingKey>, String> {
    let mut keys = BTreeMap::new();
    for record in records {
        let object = record
            .as_object()
            .ok_or_else(|| "key record must be an object".to_owned())?;
        if object.get("schema_version").and_then(Value::as_str) != Some("0.2")
            || object.get("algorithm").and_then(Value::as_str) != Some("ed25519")
            || !object.get("extensions").is_some_and(Value::is_object)
        {
            return Err("unsupported or malformed public-key record".to_owned());
        }
        let keyid = object
            .get("keyid")
            .and_then(Value::as_str)
            .ok_or_else(|| "key record has no keyid".to_owned())?;
        let raw = STANDARD
            .decode(
                object
                    .get("public_key")
                    .and_then(Value::as_str)
                    .ok_or_else(|| "key record has no public_key".to_owned())?,
            )
            .map_err(|error| error.to_string())?;
        let bytes: [u8; 32] = raw
            .try_into()
            .map_err(|_| "invalid Ed25519 public-key length".to_owned())?;
        if key_id(&bytes) != keyid {
            return Err("key ID does not match public-key bytes".to_owned());
        }
        let key = VerifyingKey::from_bytes(&bytes).map_err(|error| error.to_string())?;
        if keys.insert(keyid.to_owned(), key).is_some() {
            return Err("duplicate public key ID".to_owned());
        }
    }
    Ok(keys)
}

fn subject_hashes(statement: &Map<String, Value>) -> BTreeSet<&str> {
    statement
        .get("subject")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_object)
        .filter_map(|item| item.get("digest"))
        .filter_map(Value::as_object)
        .filter_map(|digest| digest.get("sha256"))
        .filter_map(Value::as_str)
        .collect()
}

fn valid_sha256(value: Option<&Value>) -> bool {
    value.and_then(Value::as_str).is_some_and(|text| {
        text.len() == 71
            && text.starts_with("sha256:")
            && text[7..]
                .bytes()
                .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    })
}

fn validate_statement(statement: &Map<String, Value>, issues: &mut Vec<String>) {
    let allowed_predicates = [
        "https://mncs.dev/predicate/conformance-result/v0.2",
        "https://mncs.dev/predicate/gate-result/v0.2",
        "https://mncs.dev/predicate/evidence-index/v0.2",
        "https://mncs.dev/predicate/reproducible-package/v0.2",
        "https://mncs.dev/predicate/provider-result/v0.2",
        "https://mncs.dev/predicate/release-artifact/v0.2",
    ];
    let component = statement.get("component").and_then(Value::as_object);
    let valid = statement.get("_type").and_then(Value::as_str)
        == Some("https://mncs.dev/attestation/v0.2/statement")
        && statement.get("mncs_version").and_then(Value::as_str) == Some("0.2")
        && statement.get("schema_version").and_then(Value::as_str) == Some("0.2")
        && statement
            .get("subject")
            .and_then(Value::as_array)
            .is_some_and(|values| !values.is_empty())
        && statement
            .get("contract_id")
            .and_then(Value::as_str)
            .is_some_and(|value| !value.is_empty())
        && component.is_some_and(|value| {
            value
                .get("name")
                .and_then(Value::as_str)
                .is_some_and(|item| !item.is_empty())
                && value
                    .get("version")
                    .and_then(Value::as_str)
                    .is_some_and(|item| !item.is_empty())
                && valid_sha256(value.get("identity"))
        })
        && statement
            .get("environment")
            .and_then(Value::as_str)
            .is_some_and(|value| !value.is_empty())
        && statement
            .get("predicate_type")
            .and_then(Value::as_str)
            .is_some_and(|value| allowed_predicates.contains(&value))
        && statement.get("predicate").is_some_and(Value::is_object)
        && parse_time(statement.get("created_at")).is_some()
        && statement.get("extensions").is_some_and(Value::is_object);
    if !valid {
        issues.push("attestation statement schema violation".to_owned());
    }
    if statement.contains_key("expires_at") && parse_time(statement.get("expires_at")).is_none() {
        issues.push("invalid attestation expiration".to_owned());
    }
    for subject in statement
        .get("subject")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
    {
        let valid = subject
            .get("name")
            .and_then(Value::as_str)
            .is_some_and(|value| !value.is_empty())
            && valid_sha256(
                subject
                    .pointer("/digest/sha256")
                    .map(|value| {
                        if let Some(text) = value.as_str() {
                            Value::String(format!("sha256:{text}"))
                        } else {
                            Value::Null
                        }
                    })
                    .as_ref(),
            );
        if !valid {
            issues.push("invalid attestation subject identity".to_owned());
        }
    }
}

/// Validate an MNCS DSSE envelope and its Ed25519 signatures.
///
/// # Errors
///
/// Returns an error when an input key record cannot be decoded safely.
#[allow(clippy::too_many_lines)]
pub fn verify(
    envelope: &Value,
    key_records: &[Value],
    expected_subject: Option<&str>,
    expected_contract: Option<&str>,
    expected_environment: Option<&str>,
    now: OffsetDateTime,
) -> Result<Verification, String> {
    let object = envelope
        .as_object()
        .ok_or_else(|| "envelope must be an object".to_owned())?;
    let mut issues = Vec::new();
    if object.len() != 3
        || !object.contains_key("payloadType")
        || !object.contains_key("payload")
        || !object.contains_key("signatures")
    {
        issues.push("attestation envelope schema violation".to_owned());
    }
    let payload_type = object
        .get("payloadType")
        .and_then(Value::as_str)
        .unwrap_or_default();
    if payload_type != PAYLOAD_TYPE {
        issues.push("unsupported attestation payload type".to_owned());
    }
    let payload = object
        .get("payload")
        .and_then(Value::as_str)
        .and_then(|value| STANDARD.decode(value).ok())
        .unwrap_or_default();
    let statement = json::parse_slice(&payload).ok();
    let statement_object = statement.as_ref().and_then(Value::as_object);
    if statement_object.is_none()
        || canonical::canonicalize(statement.as_ref().unwrap_or(&Value::Null))
            .ok()
            .as_deref()
            != Some(payload.as_slice())
    {
        issues.push("attestation payload is not canonical JSON".to_owned());
    }
    if let Some(statement) = statement_object {
        validate_statement(statement, &mut issues);
        if let Some(expected) =
            expected_subject.map(|value| value.strip_prefix("sha256:").unwrap_or(value))
            && !subject_hashes(statement).contains(expected)
        {
            issues.push("attestation subject binding mismatch".to_owned());
        }
        if let Some(expected) = expected_contract
            && statement.get("contract_id").and_then(Value::as_str) != Some(expected)
        {
            issues.push("attestation contract binding mismatch".to_owned());
        }
        if let Some(expected) = expected_environment
            && statement.get("environment").and_then(Value::as_str) != Some(expected)
        {
            issues.push("attestation environment binding mismatch".to_owned());
        }
    }
    let expired = statement_object
        .and_then(|value| parse_time(value.get("expires_at")))
        .is_some_and(|expiration| now >= expiration);
    let keys = public_keys(key_records)?;
    let signatures = object
        .get("signatures")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    if signatures.is_empty() {
        issues.push("attestation signatures must be a non-empty array".to_owned());
    }
    let mut seen = BTreeSet::new();
    let mut results = Vec::new();
    for item in signatures {
        let Some(signature_object) = item.as_object() else {
            results.push(SignatureResult {
                keyid: String::new(),
                cryptographically_valid: false,
                reason: "malformed signature".to_owned(),
            });
            issues.push("malformed signature".to_owned());
            continue;
        };
        let keyid = signature_object
            .get("keyid")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_owned();
        if signature_object.len() != 3 || !seen.insert(keyid.clone()) {
            results.push(SignatureResult {
                keyid,
                cryptographically_valid: false,
                reason: "duplicate or malformed signature".to_owned(),
            });
            issues.push("duplicate or malformed signature".to_owned());
            continue;
        }
        let valid = (|| -> Result<(), String> {
            if signature_object.get("algorithm").and_then(Value::as_str) != Some("ed25519") {
                return Err("algorithm confusion".to_owned());
            }
            let key = keys
                .get(&keyid)
                .ok_or_else(|| "public key unavailable".to_owned())?;
            let raw = STANDARD
                .decode(
                    signature_object
                        .get("sig")
                        .and_then(Value::as_str)
                        .ok_or_else(|| "signature missing".to_owned())?,
                )
                .map_err(|error| error.to_string())?;
            let signature = Signature::from_slice(&raw).map_err(|error| error.to_string())?;
            key.verify_strict(&pae(payload_type, &payload), &signature)
                .map_err(|error| error.to_string())
        })()
        .is_ok();
        results.push(SignatureResult {
            keyid,
            cryptographically_valid: valid,
            reason: if valid {
                "valid signature".to_owned()
            } else {
                "invalid signature".to_owned()
            },
        });
    }
    if !results.iter().any(|item| item.cryptographically_valid) {
        issues.push("no cryptographically valid signature".to_owned());
    }
    issues.sort();
    issues.dedup();
    let payload_valid = issues
        .iter()
        .all(|issue| issue == "no cryptographically valid signature");
    let cryptographically_valid =
        payload_valid && results.iter().any(|item| item.cryptographically_valid);
    Ok(Verification {
        payload_valid,
        expired,
        cryptographically_valid,
        signatures: results,
        statement,
        issues,
    })
}
