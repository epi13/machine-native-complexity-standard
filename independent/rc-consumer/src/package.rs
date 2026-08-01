//! Bounded verification of deterministic `mncs-zip-0.1` archives.

use std::collections::BTreeSet;
use std::fs::File;
use std::io::Read;
use std::path::Path;

use serde::Serialize;
use serde_json::Value;
use zip::{CompressionMethod, ZipArchive};

use crate::canonical;

const INDEX_PATH: &str = "mncs-package-index.json";
const MAX_FILES: usize = 4_001;
const MAX_DEPTH: usize = 24;
const MAX_MEMBER: u64 = 64 * 1024 * 1024;
const MAX_TOTAL: u64 = 512 * 1024 * 1024;
const MAX_ARCHIVE: u64 = MAX_TOTAL + 16 * 1024 * 1024;

#[derive(Debug, Clone, Serialize)]
pub struct PackageReport {
    pub valid: bool,
    pub package_sha256: String,
    pub file_count: usize,
    pub total_bytes: u64,
    pub evidence_index_sha256: Option<String>,
    pub issues: Vec<String>,
    pub index: Option<Value>,
}

fn safe_name(name: &str) -> bool {
    if name.is_empty()
        || name.starts_with('/')
        || name.contains('\\')
        || name.contains('\0')
        || name.ends_with('/')
    {
        return false;
    }
    let parts = name.split('/').collect::<Vec<_>>();
    parts.len() <= MAX_DEPTH
        && parts
            .iter()
            .all(|part| !part.is_empty() && *part != "." && *part != "..")
}

fn unsafe_mode(mode: Option<u32>) -> bool {
    mode.is_some_and(|value| {
        let file_type = value & 0o170_000;
        file_type != 0 && file_type != 0o100_000
    })
}

fn read_member(
    archive: &mut ZipArchive<File>,
    name: &str,
    maximum: u64,
) -> Result<Vec<u8>, String> {
    let mut file = archive.by_name(name).map_err(|error| error.to_string())?;
    if file.size() > maximum {
        return Err(format!("member size limit exceeded: {name}"));
    }
    let mut content =
        Vec::with_capacity(usize::try_from(file.size()).map_err(|error| error.to_string())?);
    (&mut file)
        .take(maximum + 1)
        .read_to_end(&mut content)
        .map_err(|error| error.to_string())?;
    if u64::try_from(content.len()).unwrap_or(u64::MAX) > maximum {
        return Err(format!("member grew beyond size limit: {name}"));
    }
    Ok(content)
}

fn valid_hash(value: Option<&Value>) -> bool {
    value.and_then(Value::as_str).is_some_and(|text| {
        text.len() == 71
            && text.starts_with("sha256:")
            && text[7..]
                .bytes()
                .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    })
}

fn validate_index(index: &Value, issues: &mut Vec<String>) -> Vec<Value> {
    let Some(object) = index.as_object() else {
        issues.push("package index must be an object".to_owned());
        return Vec::new();
    };
    if object.get("schema_version").and_then(Value::as_str) != Some("0.2")
        || object.get("mncs_version").and_then(Value::as_str) != Some("0.2")
        || object.get("format").and_then(Value::as_str) != Some("mncs-zip-0.1")
        || !object.get("extensions").is_some_and(Value::is_object)
    {
        issues.push("invalid package-index header".to_owned());
    }
    let Some(records) = object.get("files").and_then(Value::as_array) else {
        issues.push("package index files must be an array".to_owned());
        return Vec::new();
    };
    if records.len() >= MAX_FILES {
        issues.push("package index file-count limit exceeded".to_owned());
    }
    records.clone()
}

/// Verify the structure and identities of a bounded MNCS package archive.
///
/// # Errors
///
/// Returns an error when the package cannot be opened or read safely.
#[allow(clippy::too_many_lines)]
pub fn verify(path: &Path) -> Result<PackageReport, String> {
    let package_content = canonical::read_regular(path, MAX_ARCHIVE)?;
    let package_sha256 = canonical::mncs_sha256(&package_content);
    let mut archive = ZipArchive::new(File::open(path).map_err(|error| error.to_string())?)
        .map_err(|error| error.to_string())?;
    let file_count = archive.len();
    let mut issues = Vec::new();
    if file_count > MAX_FILES {
        issues.push("file-count limit exceeded".to_owned());
    }
    let mut names = Vec::new();
    let mut seen = BTreeSet::new();
    let mut total_bytes = 0_u64;
    for index in 0..file_count {
        let file = archive
            .by_index_raw(index)
            .map_err(|error| error.to_string())?;
        let name = file.name().to_owned();
        if !seen.insert(name.clone()) {
            issues.push("duplicate archive member".to_owned());
        }
        if !safe_name(&name) {
            issues.push(format!("unsafe package path: {name}"));
        }
        if file.is_dir() || unsafe_mode(file.unix_mode()) {
            issues.push(format!("unsafe archive member type: {name}"));
        }
        if file.compression() != CompressionMethod::Stored {
            issues.push(format!("non-deterministic compression: {name}"));
        }
        if file.size() > MAX_MEMBER {
            issues.push(format!("member size limit exceeded: {name}"));
        }
        total_bytes = total_bytes.saturating_add(file.size());
        if total_bytes > MAX_TOTAL {
            issues.push("total uncompressed size limit exceeded".to_owned());
        }
        names.push(name);
    }
    let mut sorted_names = names.clone();
    sorted_names.sort_by(|left, right| left.as_bytes().cmp(right.as_bytes()));
    if names != sorted_names {
        issues.push("members are not bytewise path sorted".to_owned());
    }

    let mut parsed_index = None;
    let mut evidence_index_sha256 = None;
    if names.iter().any(|name| name == INDEX_PATH) {
        match read_member(&mut archive, INDEX_PATH, MAX_MEMBER)
            .and_then(|content| canonical::canonical_value(&content))
        {
            Ok(value) => {
                evidence_index_sha256 = value
                    .get("evidence_index_sha256")
                    .and_then(Value::as_str)
                    .map(str::to_owned);
                parsed_index = Some(value);
            }
            Err(error) => issues.push(format!("invalid package index: {error}")),
        }
    } else {
        issues.push("package index is missing".to_owned());
    }

    if let Some(index) = &parsed_index {
        let records = validate_index(index, &mut issues);
        let mut expected_names = Vec::new();
        let mut indexed_names = BTreeSet::new();
        for record in records {
            let Some(record) = record.as_object() else {
                issues.push("malformed package index record".to_owned());
                continue;
            };
            let name = record
                .get("path")
                .and_then(Value::as_str)
                .unwrap_or_default();
            expected_names.push(name.to_owned());
            if !safe_name(name) || name == INDEX_PATH || !indexed_names.insert(name.to_owned()) {
                issues.push(format!("invalid indexed path: {name}"));
                continue;
            }
            if !valid_hash(record.get("sha256"))
                || record.get("size").and_then(Value::as_u64).is_none()
            {
                issues.push(format!("invalid package index identity record: {name}"));
                continue;
            }
            match read_member(&mut archive, name, MAX_MEMBER) {
                Ok(content) => {
                    if record.get("size").and_then(Value::as_u64)
                        != Some(u64::try_from(content.len()).unwrap_or(u64::MAX))
                    {
                        issues.push(format!("size mismatch: {name}"));
                    }
                    if record.get("sha256").and_then(Value::as_str)
                        != Some(canonical::mncs_sha256(&content).as_str())
                    {
                        issues.push(format!("hash mismatch: {name}"));
                    }
                }
                Err(_) => issues.push(format!("indexed member is missing: {name}")),
            }
        }
        let actual_names = names
            .iter()
            .filter(|name| name.as_str() != INDEX_PATH)
            .cloned()
            .collect::<Vec<_>>();
        if expected_names != actual_names {
            issues.push("package index/member ordering mismatch".to_owned());
        }
        if names.iter().any(|name| name == "evidence/index.json") {
            if let Ok(content) = read_member(&mut archive, "evidence/index.json", MAX_MEMBER)
                && evidence_index_sha256.as_deref()
                    != Some(canonical::mncs_sha256(&content).as_str())
            {
                issues.push("embedded evidence-index identity mismatch".to_owned());
            }
        } else if evidence_index_sha256.is_some() {
            issues.push("declared evidence index is missing".to_owned());
        }
    }

    issues.sort();
    issues.dedup();
    Ok(PackageReport {
        valid: issues.is_empty(),
        package_sha256,
        file_count,
        total_bytes,
        evidence_index_sha256,
        issues,
        index: parsed_index,
    })
}

#[cfg(test)]
mod tests {
    use super::{safe_name, unsafe_mode};

    #[test]
    fn rejects_unsafe_names_and_member_types() {
        assert!(safe_name("evidence/result.json"));
        assert!(!safe_name("../escape"));
        assert!(!safe_name("/absolute"));
        assert!(!safe_name("nested//empty"));
        assert!(unsafe_mode(Some(0o120_777)));
        assert!(!unsafe_mode(Some(0o100_644)));
    }
}
