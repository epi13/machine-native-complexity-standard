//! Deterministic offline trust-policy evaluation.

use std::collections::BTreeSet;

use serde::Serialize;
use serde_json::Value;
use time::{OffsetDateTime, format_description::well_known::Rfc3339};

use crate::attestation::{self, Verification};

#[derive(Debug, Clone, Serialize)]
pub struct Evaluation {
    pub cryptographically_valid: bool,
    pub trusted: bool,
    pub certified: bool,
    pub trusted_signers: Vec<String>,
    pub satisfied_roles: Vec<String>,
    pub reasons: Vec<String>,
    pub verification: Verification,
}

fn parse_time(value: Option<&Value>) -> Option<OffsetDateTime> {
    value
        .and_then(Value::as_str)
        .and_then(|text| OffsetDateTime::parse(text, &Rfc3339).ok())
}

fn scope_matches(value: &str, scopes: Option<&Value>) -> bool {
    scopes.and_then(Value::as_array).is_none_or(|values| {
        values
            .iter()
            .filter_map(Value::as_str)
            .any(|item| item == "*" || item == value)
    })
}

fn positive_integer(policy: &serde_json::Map<String, Value>, name: &str) -> Result<usize, String> {
    let value = policy
        .get(name)
        .and_then(Value::as_u64)
        .ok_or_else(|| format!("{name} must be an integer"))?;
    if value == 0 {
        return Err(format!("{name} must be positive"));
    }
    usize::try_from(value).map_err(|error| error.to_string())
}

fn nonnegative_integer(
    policy: &serde_json::Map<String, Value>,
    name: &str,
) -> Result<usize, String> {
    usize::try_from(policy.get(name).and_then(Value::as_u64).unwrap_or(0))
        .map_err(|error| error.to_string())
}

fn string_array(
    value: Option<&Value>,
    name: &str,
    allow_empty: bool,
) -> Result<Vec<String>, String> {
    let values = value
        .and_then(Value::as_array)
        .ok_or_else(|| format!("{name} must be an array"))?;
    if !allow_empty && values.is_empty() {
        return Err(format!("{name} must be non-empty"));
    }
    let mut result = Vec::new();
    let mut seen = BTreeSet::new();
    for value in values {
        let text = value
            .as_str()
            .filter(|text| !text.is_empty())
            .ok_or_else(|| format!("{name} must contain non-empty strings"))?;
        if !seen.insert(text) {
            return Err(format!("{name} must not contain duplicates"));
        }
        result.push(text.to_owned());
    }
    Ok(result)
}

fn validate_policy(policy: &serde_json::Map<String, Value>) -> Result<(), String> {
    if policy.get("schema_version").and_then(Value::as_str) != Some("0.2")
        || policy
            .get("trust_domain")
            .and_then(Value::as_str)
            .is_none_or(str::is_empty)
        || policy.get("offline").and_then(Value::as_bool) != Some(true)
        || !policy.get("extensions").is_some_and(Value::is_object)
    {
        return Err("invalid trust-policy header".to_owned());
    }
    let keys = policy
        .get("keys")
        .and_then(Value::as_array)
        .filter(|keys| !keys.is_empty())
        .ok_or_else(|| "policy keys must be a non-empty array".to_owned())?;
    let mut keyids = BTreeSet::new();
    for record in keys {
        let object = record
            .as_object()
            .ok_or_else(|| "key record must be an object".to_owned())?;
        let keyid = object
            .get("keyid")
            .and_then(Value::as_str)
            .filter(|value| !value.is_empty())
            .ok_or_else(|| "key record has no keyid".to_owned())?;
        if !keyids.insert(keyid) {
            return Err("duplicate key record".to_owned());
        }
        string_array(object.get("roles"), "key roles", false)?;
        for field in ["predicate_types", "components", "contracts", "environments"] {
            if object.contains_key(field) {
                string_array(object.get(field), field, true)?;
            }
        }
        if object.contains_key("valid_from") && parse_time(object.get("valid_from")).is_none() {
            return Err("invalid key valid_from".to_owned());
        }
        if object.contains_key("valid_until") && parse_time(object.get("valid_until")).is_none() {
            return Err("invalid key valid_until".to_owned());
        }
    }
    string_array(
        policy.get("allowed_predicate_types"),
        "allowed_predicate_types",
        false,
    )?;
    string_array(policy.get("required_roles"), "required_roles", true)?;
    positive_integer(policy, "minimum_signatures")?;
    positive_integer(policy, "distinct_signers")?;
    nonnegative_integer(policy, "minimum_independent_evaluators")?;
    if !matches!(
        policy.get("unknown_handling").and_then(Value::as_str),
        Some("reject" | "manual_review")
    ) {
        return Err("invalid unknown_handling".to_owned());
    }
    let revocations = policy
        .get("revocations")
        .and_then(Value::as_array)
        .ok_or_else(|| "revocations must be an array".to_owned())?;
    for record in revocations {
        let object = record
            .as_object()
            .ok_or_else(|| "revocation record must be an object".to_owned())?;
        if object
            .get("keyid")
            .and_then(Value::as_str)
            .is_none_or(str::is_empty)
            || parse_time(object.get("revoked_at")).is_none()
            || object
                .get("reason")
                .and_then(Value::as_str)
                .is_none_or(str::is_empty)
            || !object.get("extensions").is_some_and(Value::is_object)
        {
            return Err("invalid revocation record".to_owned());
        }
    }
    Ok(())
}

/// Evaluate a verified attestation against an offline MNCS trust policy.
///
/// # Errors
///
/// Returns an error when the trust policy is structurally invalid or an
/// attestation key cannot be decoded.
#[allow(clippy::too_many_lines)]
pub fn evaluate(
    envelope: &Value,
    policy: &Value,
    expected_subject: Option<&str>,
    expected_contract: Option<&str>,
    expected_environment: Option<&str>,
    now: OffsetDateTime,
) -> Result<Evaluation, String> {
    let object = policy
        .as_object()
        .ok_or_else(|| "policy must be an object".to_owned())?;
    validate_policy(object)?;
    let keys = object
        .get("keys")
        .and_then(Value::as_array)
        .ok_or_else(|| "policy keys must be an array".to_owned())?;
    let verification = attestation::verify(
        envelope,
        keys,
        expected_subject,
        expected_contract,
        expected_environment,
        now,
    )?;
    let statement = verification
        .statement
        .as_ref()
        .and_then(Value::as_object)
        .cloned()
        .unwrap_or_default();
    let predicate_type = statement
        .get("predicate_type")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let contract = statement
        .get("contract_id")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let environment = statement
        .get("environment")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let component = statement
        .get("component")
        .and_then(Value::as_object)
        .and_then(|value| value.get("name"))
        .and_then(Value::as_str)
        .unwrap_or_default();
    let valid_keyids = verification
        .signatures
        .iter()
        .filter(|item| item.cryptographically_valid)
        .map(|item| item.keyid.as_str())
        .collect::<BTreeSet<_>>();
    let revoked = object
        .get("revocations")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_object)
        .filter(|record| parse_time(record.get("revoked_at")).is_some_and(|time| time <= now))
        .filter_map(|record| record.get("keyid"))
        .filter_map(Value::as_str)
        .collect::<BTreeSet<_>>();
    let mut reasons = verification.issues.clone();
    let mut trusted_signers = BTreeSet::new();
    let mut roles = BTreeSet::new();
    let mut evaluators = BTreeSet::new();
    let mut generators = BTreeSet::new();
    for record in keys.iter().filter_map(Value::as_object) {
        let Some(keyid) = record.get("keyid").and_then(Value::as_str) else {
            continue;
        };
        if !valid_keyids.contains(keyid) {
            continue;
        }
        if record.get("trusted").and_then(Value::as_bool) == Some(false) {
            reasons.push(format!(
                "cryptographically valid but untrusted key: {keyid}"
            ));
            continue;
        }
        if revoked.contains(keyid) {
            reasons.push(format!("revoked key: {keyid}"));
            continue;
        }
        if parse_time(record.get("valid_from")).is_some_and(|time| now < time)
            || parse_time(record.get("valid_until")).is_some_and(|time| now >= time)
        {
            reasons.push(format!("key outside validity window: {keyid}"));
            continue;
        }
        if !scope_matches(predicate_type, record.get("predicate_types"))
            || !scope_matches(contract, record.get("contracts"))
            || !scope_matches(component, record.get("components"))
            || !scope_matches(environment, record.get("environments"))
        {
            reasons.push(format!("key outside statement scope: {keyid}"));
            continue;
        }
        trusted_signers.insert(keyid.to_owned());
        for role in record
            .get("roles")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(Value::as_str)
        {
            roles.insert(role.to_owned());
            if role == "evaluator" {
                evaluators.insert(keyid.to_owned());
            } else if role == "generator" {
                generators.insert(keyid.to_owned());
            }
        }
    }
    let allowed = object
        .get("allowed_predicate_types")
        .and_then(Value::as_array)
        .is_some_and(|values| {
            values
                .iter()
                .filter_map(Value::as_str)
                .any(|value| value == predicate_type)
        });
    if !allowed {
        reasons.push("predicate type is not allowed".to_owned());
    }
    if verification.expired {
        reasons.push("attestation expired".to_owned());
    }
    if trusted_signers.len() < positive_integer(object, "minimum_signatures")? {
        reasons.push("insufficient trusted signatures".to_owned());
    }
    if trusted_signers.len() < positive_integer(object, "distinct_signers")? {
        reasons.push("insufficient distinct trusted signers".to_owned());
    }
    for role in object
        .get("required_roles")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_str)
    {
        if !roles.contains(role) {
            reasons.push(format!("missing required role: {role}"));
        }
    }
    if evaluators.len() < nonnegative_integer(object, "minimum_independent_evaluators")? {
        reasons.push("insufficient independent evaluators".to_owned());
    }
    if object
        .get("require_generator_evaluator_separation")
        .and_then(Value::as_bool)
        .unwrap_or(false)
        && (generators.is_empty() || evaluators.is_empty() || !generators.is_disjoint(&evaluators))
    {
        reasons.push("generator/evaluator separation failed".to_owned());
    }
    let status = statement
        .get("predicate")
        .and_then(Value::as_object)
        .and_then(|value| value.get("status"))
        .and_then(Value::as_str);
    if status == Some("UNKNOWN") {
        reasons.push(format!(
            "UNKNOWN handled as {}",
            object
                .get("unknown_handling")
                .and_then(Value::as_str)
                .unwrap_or("reject")
        ));
    }
    reasons.sort();
    reasons.dedup();
    let cryptographically_valid = verification.cryptographically_valid && !verification.expired;
    let trusted = cryptographically_valid && reasons.is_empty();
    let certified = trusted && status == Some("PASS");
    Ok(Evaluation {
        cryptographically_valid,
        trusted,
        certified,
        trusted_signers: trusted_signers.into_iter().collect(),
        satisfied_roles: roles.into_iter().collect(),
        reasons,
        verification,
    })
}

#[cfg(test)]
mod tests {
    use super::scope_matches;
    use serde_json::json;

    #[test]
    fn absent_scope_is_unbounded_and_explicit_scope_is_enforced() {
        assert!(scope_matches("x", None));
        assert!(scope_matches("x", Some(&json!(["*"]))));
        assert!(!scope_matches("x", Some(&json!(["y"]))));
    }
}
