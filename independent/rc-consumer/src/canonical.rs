//! RFC 8785 canonical JSON and bounded SHA-256 identities.

use std::fs::File;
use std::io::Read;
use std::path::Path;

use serde_json::Value;
use sha2::{Digest, Sha256};

use crate::json;

pub const MAX_JSON_BYTES: u64 = 10 * 1024 * 1024;

/// Read a bounded regular file without following symbolic links.
///
/// # Errors
///
/// Returns an error when the path is not a stable regular file, exceeds the
/// configured bound, or cannot be read.
pub fn read_regular(path: &Path, maximum: u64) -> Result<Vec<u8>, String> {
    let link_metadata = std::fs::symlink_metadata(path).map_err(|error| error.to_string())?;
    if link_metadata.file_type().is_symlink() || !link_metadata.is_file() {
        return Err(format!(
            "not a regular non-symlink file: {}",
            path.display()
        ));
    }
    if link_metadata.len() > maximum {
        return Err(format!("file exceeds {maximum} bytes: {}", path.display()));
    }
    let mut file = File::open(path).map_err(|error| error.to_string())?;
    let before = file.metadata().map_err(|error| error.to_string())?;
    if !before.is_file() || before.len() > maximum {
        return Err(format!("unsafe file type or size: {}", path.display()));
    }
    let mut content =
        Vec::with_capacity(usize::try_from(before.len()).map_err(|error| error.to_string())?);
    (&mut file)
        .take(maximum + 1)
        .read_to_end(&mut content)
        .map_err(|error| error.to_string())?;
    if u64::try_from(content.len()).unwrap_or(u64::MAX) > maximum {
        return Err(format!(
            "file grew beyond {maximum} bytes: {}",
            path.display()
        ));
    }
    let after = file.metadata().map_err(|error| error.to_string())?;
    if before.len() != after.len()
        || before.modified().map_err(|error| error.to_string())?
            != after.modified().map_err(|error| error.to_string())?
    {
        return Err(format!("file changed while reading: {}", path.display()));
    }
    Ok(content)
}

/// Serialize a JSON value according to RFC 8785.
///
/// # Errors
///
/// Returns an error when the value cannot be represented as canonical JSON.
pub fn canonicalize(value: &Value) -> Result<Vec<u8>, String> {
    serde_jcs::to_vec(value).map_err(|error| error.to_string())
}

#[must_use]
pub fn mncs_sha256(content: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(content)))
}

/// Parse canonical JSON while rejecting duplicate keys and unsafe integers.
///
/// # Errors
///
/// Returns an error for invalid or non-canonical JSON.
pub fn canonical_value(content: &[u8]) -> Result<Value, String> {
    let value = json::parse_slice(content)?;
    if canonicalize(&value)? != content {
        return Err("JSON is not RFC 8785 canonical".to_owned());
    }
    Ok(value)
}

/// Read and strictly parse a bounded JSON file.
///
/// # Errors
///
/// Returns an error when the file cannot be safely read or contains invalid
/// JSON.
pub fn read_json(path: &Path, maximum: u64) -> Result<Value, String> {
    json::parse_slice(&read_regular(path, maximum)?)
}

#[cfg(test)]
mod tests {
    use super::{canonical_value, canonicalize};
    use serde_json::json;

    #[test]
    fn canonicalizes_numbers_and_order() {
        assert_eq!(
            canonicalize(&json!({"z": -0.0, "a": "€", "n": 1e30})).unwrap(),
            r#"{"a":"€","n":1e+30,"z":0}"#.as_bytes()
        );
        assert!(canonical_value(br#"{"z":0,"a":1}"#).is_err());
    }
}
