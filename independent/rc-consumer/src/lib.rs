// SPDX-License-Identifier: Apache-2.0
//! Independent, offline semantic consumer for the release-candidate golden corpus.

use serde::Serialize;
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};
use time::{OffsetDateTime, format_description::well_known::Rfc3339};

#[derive(Clone, Debug, Serialize)]
pub struct Outcome {
    pub category: String,
    pub issue_codes: BTreeSet<String>,
}

impl Outcome {
    fn new(category: &str) -> Self {
        Self {
            category: category.to_owned(),
            issue_codes: BTreeSet::new(),
        }
    }

    fn issue(mut self, code: &str) -> Self {
        self.issue_codes.insert(code.to_owned());
        self
    }
}

fn rfc3339(value: &str) -> Option<OffsetDateTime> {
    OffsetDateTime::parse(value, &Rfc3339).ok()
}

#[derive(Debug, Serialize)]
pub struct CaseResult {
    pub id: String,
    pub kind: String,
    pub expected: String,
    pub actual: String,
    pub classification: String,
    pub issue_codes: BTreeSet<String>,
}

#[derive(Debug, Serialize)]
pub struct Summary {
    pub total: usize,
    pub agreement: usize,
    pub disagreement: usize,
    pub unsupported: usize,
    pub implementation_errors: usize,
    pub categories: BTreeMap<String, usize>,
}

#[derive(Debug, Serialize)]
pub struct RunResult {
    pub implementation: &'static str,
    pub implementation_language: &'static str,
    pub implementation_independence: &'static str,
    pub operator_independence: &'static str,
    pub organizational_independence: &'static str,
    pub summary: Summary,
    pub results: Vec<CaseResult>,
}

fn status(value: Option<&Value>) -> &'static str {
    match value.and_then(Value::as_str) {
        Some("PASS") => "PASS",
        Some("FAIL") => "FAIL",
        _ => "UNKNOWN",
    }
}

fn aggregate<'a>(values: impl IntoIterator<Item = &'a str>) -> &'static str {
    let mut result = "PASS";
    let mut seen = false;
    for value in values {
        seen = true;
        if value == "FAIL" {
            return "FAIL";
        }
        if value != "PASS" {
            result = "UNKNOWN";
        }
    }
    if seen { result } else { "UNKNOWN" }
}

fn freshness_status(value: Option<&Value>, at: &str) -> &'static str {
    let declared = status(value.and_then(|item| item.get("status")));
    let valid_until = value
        .and_then(|item| item.get("valid_until"))
        .and_then(Value::as_str);
    match (rfc3339(at), valid_until.map(rfc3339)) {
        (Some(moment), Some(Some(limit))) if moment > limit => aggregate([declared, "UNKNOWN"]),
        (Some(_), Some(Some(_)) | None) => declared,
        _ => "UNKNOWN",
    }
}

fn array(value: Option<&Value>) -> &[Value] {
    value.and_then(Value::as_array).map_or(&[], Vec::as_slice)
}

fn object_id<'a>(value: &'a Value, key: &str) -> Option<&'a str> {
    value.get(key).and_then(Value::as_str)
}

fn valid_id(value: Option<&Value>) -> bool {
    let Some(value) = value.and_then(Value::as_str) else {
        return false;
    };
    let mut bytes = value.bytes();
    value.len() <= 128
        && bytes
            .next()
            .is_some_and(|byte| byte.is_ascii_alphanumeric())
        && bytes.all(|byte| byte.is_ascii_alphanumeric() || b"._:-".contains(&byte))
}

fn valid_sha256(value: Option<&Value>) -> bool {
    value.and_then(Value::as_str).is_some_and(|value| {
        value.len() == 71
            && value.starts_with("sha256:")
            && value[7..]
                .bytes()
                .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    })
}

fn validate_contract(value: &Value) -> Outcome {
    if value.get("schema_version").and_then(Value::as_str) != Some("0.3-rc.1") {
        return Outcome::new("UNSUPPORTED").issue("UNSUPPORTED-VERSION");
    }
    let required = [
        "profile_id",
        "contract_id",
        "contract_content_identity",
        "correctness_basis",
        "status",
        "intended_use",
        "interfaces",
        "behavior",
        "limits",
        "invariants",
        "environment_assumptions",
        "compatibility",
        "undefined_behavior",
        "reference_oracle",
        "ambiguities",
        "versioning",
        "findings",
        "evidence_ids",
        "limitations",
        "extensions",
    ];
    let allowed: BTreeSet<_> = required
        .iter()
        .copied()
        .chain(["schema_version", "mncs_version"])
        .collect();
    let Some(record) = value.as_object() else {
        return Outcome::new("INVALID").issue("SCHEMA");
    };
    if required.iter().any(|key| !record.contains_key(*key))
        || record.keys().any(|key| !allowed.contains(key.as_str()))
        || value.pointer("/behavior/malformed_inputs").is_none()
        || !valid_id(value.get("profile_id"))
        || !valid_id(value.get("contract_id"))
        || !valid_sha256(value.get("contract_content_identity"))
    {
        return Outcome::new("INVALID").issue("SCHEMA");
    }
    let mut statuses: Vec<&str> = array(value.get("findings"))
        .iter()
        .filter(|finding| finding.get("required").and_then(Value::as_bool) == Some(true))
        .map(|finding| status(finding.get("status")))
        .collect();
    let mut outcome = Outcome::new("PASS");
    if value.get("correctness_basis").and_then(Value::as_str) == Some("candidate_behavior") {
        statuses.push("FAIL");
        outcome
            .issue_codes
            .insert("MNCS-03-CONTRACT-CIRCULAR".to_owned());
    }
    for dimension in ["resource", "timing"] {
        let applicable = value
            .pointer(&format!("/limits/{dimension}_applicability/applicable"))
            .and_then(Value::as_bool)
            == Some(true);
        let missing = value
            .pointer(&format!("/limits/{dimension}"))
            .and_then(Value::as_array)
            .is_none_or(Vec::is_empty);
        if applicable && missing {
            statuses.push("FAIL");
            outcome.issue_codes.insert(format!(
                "MNCS-03-CONTRACT-{}-MISSING",
                dimension.to_uppercase()
            ));
        }
    }
    for ambiguity in array(value.get("ambiguities")) {
        if ambiguity.get("material").and_then(Value::as_bool) == Some(true) {
            statuses.push(
                if ambiguity
                    .get("demonstrated_violation")
                    .and_then(Value::as_bool)
                    == Some(true)
                {
                    "FAIL"
                } else {
                    "UNKNOWN"
                },
            );
        }
    }
    let computed = aggregate(statuses);
    if status(value.get("status")) != computed {
        return outcome
            .issue("MNCS-03-CONTRACT-RESULT-MISMATCH")
            .with_category("INVALID");
    }
    outcome.with_category(computed)
}

impl Outcome {
    fn with_category(mut self, category: &str) -> Self {
        category.clone_into(&mut self.category);
        self
    }
}

fn claim_map(value: &Value) -> BTreeMap<&str, &Value> {
    array(value.get("claims"))
        .iter()
        .filter_map(|claim| object_id(claim, "claim_id").map(|id| (id, claim)))
        .collect()
}

fn visit_dependency<'a>(
    node: &'a str,
    edges: &BTreeMap<&'a str, Vec<&'a str>>,
    visiting: &mut BTreeSet<&'a str>,
    visited: &mut BTreeSet<&'a str>,
) -> bool {
    if visiting.contains(node) {
        return true;
    }
    if visited.contains(node) {
        return false;
    }
    visiting.insert(node);
    if edges.get(node).is_some_and(|targets| {
        targets
            .iter()
            .any(|target| visit_dependency(target, edges, visiting, visited))
    }) {
        return true;
    }
    visiting.remove(node);
    visited.insert(node);
    false
}

fn dependency_cycle(value: &Value, claim_ids: &BTreeSet<&str>) -> bool {
    let mut edges: BTreeMap<&str, Vec<&str>> =
        claim_ids.iter().map(|id| (*id, Vec::new())).collect();
    for dependency in array(value.get("dependencies")) {
        if let (Some(source), Some(target)) = (
            object_id(dependency, "source_claim_id"),
            object_id(dependency, "target_claim_id"),
        ) && let Some(targets) = edges.get_mut(source)
        {
            targets.push(target);
        }
    }
    let mut visiting = BTreeSet::new();
    let mut visited = BTreeSet::new();
    claim_ids
        .iter()
        .any(|node| visit_dependency(node, &edges, &mut visiting, &mut visited))
}

fn string_set(value: Option<&Value>) -> BTreeSet<String> {
    array(value)
        .iter()
        .filter_map(Value::as_str)
        .map(str::to_owned)
        .collect()
}

fn graph_impact_closure(value: &Value, direct: &BTreeSet<String>) -> BTreeSet<String> {
    let mut upstream: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    for dependency in array(value.get("dependencies")) {
        if dependency.get("required").and_then(Value::as_bool) != Some(true) {
            continue;
        }
        if let (Some(source), Some(target)) = (
            object_id(dependency, "source_claim_id"),
            object_id(dependency, "target_claim_id"),
        ) {
            upstream
                .entry(target.to_owned())
                .or_default()
                .insert(source.to_owned());
        }
    }
    let mut affected = direct.clone();
    let mut frontier: Vec<String> = direct.iter().cloned().collect();
    while let Some(target) = frontier.pop() {
        for source in upstream.get(&target).into_iter().flatten() {
            if affected.insert(source.clone()) {
                frontier.push(source.clone());
            }
        }
    }
    affected
}

fn derive_revalidation(
    value: &Value,
    claim_ids: &BTreeSet<&str>,
) -> (&'static str, BTreeSet<String>, BTreeSet<String>) {
    let material: Vec<&Value> = array(value.get("material_changes"))
        .iter()
        .filter(|change| change.get("material").and_then(Value::as_bool) == Some(true))
        .collect();
    let direct: BTreeSet<String> = material
        .iter()
        .flat_map(|change| array(change.get("affected_claim_ids")))
        .filter_map(Value::as_str)
        .map(str::to_owned)
        .collect();
    let affected = graph_impact_closure(value, &direct);
    let Some(revalidation) = value.get("revalidation").and_then(Value::as_object) else {
        return ("UNKNOWN", direct, affected);
    };
    let Some(impact) = value.get("evidence_impact").and_then(Value::as_object) else {
        return ("UNKNOWN", direct, affected);
    };
    let impact_status = status(impact.get("status"));
    if material.is_empty() {
        return (
            aggregate([impact_status, status(revalidation.get("status"))]),
            direct,
            affected,
        );
    }
    let mode = revalidation.get("mode").and_then(Value::as_str);
    if mode == Some("none") {
        return (aggregate([impact_status, "UNKNOWN"]), direct, affected);
    }
    let scope = string_set(revalidation.get("scope_claim_ids"));
    let covered = string_set(revalidation.get("covered_change_ids"));
    let material_ids: BTreeSet<String> = material
        .iter()
        .filter_map(|change| object_id(change, "change_id"))
        .map(str::to_owned)
        .collect();
    let invalidated = string_set(impact.get("invalidated_evidence_ids"));
    let retained = string_set(revalidation.get("retained_evidence_ids"));
    let required_new = string_set(impact.get("required_new_evidence_ids"));
    let new = string_set(revalidation.get("new_evidence_ids"));
    let known_claims: BTreeSet<String> = claim_ids.iter().map(|id| (*id).to_owned()).collect();
    let mut sufficient = affected.is_subset(&scope)
        && material_ids.is_subset(&covered)
        && invalidated.is_disjoint(&retained)
        && required_new.is_subset(&new)
        && affected.is_subset(&known_claims);
    if mode == Some("full") {
        sufficient = sufficient && known_claims.is_subset(&scope);
    }
    let result = if impact_status == "FAIL" {
        "FAIL"
    } else if sufficient && impact_status == "PASS" {
        "PASS"
    } else {
        "UNKNOWN"
    };
    (result, direct, affected)
}

fn derive_claim<'a>(
    id: &'a str,
    claims: &BTreeMap<&'a str, &'a Value>,
    value: &'a Value,
    at: &str,
    derived: &mut BTreeMap<&'a str, &'static str>,
    visiting: &mut BTreeSet<&'a str>,
) -> &'static str {
    if let Some(result) = derived.get(id) {
        return result;
    }
    if !visiting.insert(id) {
        return "UNKNOWN";
    }
    let Some(claim) = claims.get(id) else {
        return "UNKNOWN";
    };
    let mut statuses = vec![
        status(claim.get("base_status")),
        freshness_status(claim.get("freshness"), at),
    ];
    if claim.get("retired").and_then(Value::as_bool) == Some(true) {
        statuses.push("FAIL");
    }
    for dependency in array(value.get("dependencies")) {
        if object_id(dependency, "source_claim_id") != Some(id)
            || dependency.get("required").and_then(Value::as_bool) != Some(true)
        {
            continue;
        }
        let target = object_id(dependency, "target_claim_id");
        statuses.push(target.map_or("UNKNOWN", |target_id| {
            derive_claim(target_id, claims, value, at, derived, visiting)
        }));
        statuses.push(status(dependency.get("interface_compatibility")));
        statuses.push(status(dependency.get("environment_compatibility")));
        for group_id in array(dependency.get("correlated_failure_group_ids"))
            .iter()
            .filter_map(Value::as_str)
        {
            let group_status = array(value.get("correlated_failure_groups"))
                .iter()
                .find(|group| object_id(group, "group_id") == Some(group_id))
                .map_or("UNKNOWN", |group| status(group.get("status")));
            statuses.push(group_status);
        }
    }
    visiting.remove(id);
    let result = aggregate(statuses);
    derived.insert(id, result);
    result
}

#[allow(clippy::too_many_lines)]
fn validate_assurance(value: &Value, at: &str) -> Outcome {
    if value.get("schema_version").and_then(Value::as_str) != Some("0.3-rc.1") {
        return Outcome::new("UNSUPPORTED").issue("UNSUPPORTED-VERSION");
    }
    let claims = claim_map(value);
    if claims.len() != array(value.get("claims")).len() {
        return Outcome::new("INVALID").issue("MNCS-03-DUPLICATE-CLAIM");
    }
    let ids: BTreeSet<_> = claims.keys().copied().collect();
    for dependency in array(value.get("dependencies")) {
        for key in ["source_claim_id", "target_claim_id"] {
            if object_id(dependency, key).is_none_or(|id| !ids.contains(id)) {
                return Outcome::new("INVALID").issue("MNCS-03-REFERENCE-MISSING");
            }
        }
        if dependency.get("required").and_then(Value::as_bool) == Some(false) {
            let target = object_id(dependency, "target_claim_id").and_then(|id| claims.get(id));
            let uncertain = target.is_none_or(|claim| status(claim.get("status")) != "PASS");
            let source = object_id(dependency, "source_claim_id").and_then(|id| claims.get(id));
            if uncertain
                && source
                    .and_then(|claim| claim.get("limitations"))
                    .and_then(Value::as_array)
                    .is_none_or(Vec::is_empty)
            {
                return Outcome::new("INVALID").issue("MNCS-03-OPTIONAL-DEPENDENCY-UNDISCLOSED");
            }
        }
    }
    if dependency_cycle(value, &ids) {
        return Outcome::new("INVALID").issue("MNCS-03-DEPENDENCY-CYCLE");
    }
    let mut derived = BTreeMap::new();
    let mut visiting = BTreeSet::new();
    for (id, claim) in &claims {
        let computed = derive_claim(id, &claims, value, at, &mut derived, &mut visiting);
        if status(claim.get("status")) != computed {
            return Outcome::new("INVALID").issue("MNCS-03-CLAIM-RESULT-MISMATCH");
        }
    }
    let Some(root_id) = object_id(value, "root_claim_id") else {
        return Outcome::new("INVALID").issue("MNCS-03-ROOT-CLAIM-MISSING");
    };
    let Some(root) = claims.get(root_id) else {
        return Outcome::new("INVALID").issue("MNCS-03-ROOT-CLAIM-MISSING");
    };
    let mut root_status = aggregate([
        *derived.get(root_id).unwrap_or(&"UNKNOWN"),
        status(value.get("contract_profile_status")),
        freshness_status(value.get("freshness"), at),
    ]);
    if array(value.get("material_changes")).iter().any(|change| {
        change.get("material").and_then(Value::as_bool) == Some(true)
            && change.get("old_identity") == change.get("new_identity")
    }) {
        return Outcome::new("INVALID").issue("MNCS-03-MATERIAL-IDENTITY-UNCHANGED");
    }
    let (revalidation_status, direct_impact, affected) = derive_revalidation(value, &ids);
    let declared_revalidation = status(value.pointer("/revalidation/status"));
    let declared_impact = string_set(value.pointer("/evidence_impact/affected_claim_ids"));
    let known_claims: BTreeSet<String> = ids.iter().map(|id| (*id).to_owned()).collect();
    let mut revalidation_issues = Outcome::new("INVALID");
    if declared_revalidation != revalidation_status {
        revalidation_issues
            .issue_codes
            .insert("MNCS-03-REVALIDATION-RESULT-MISMATCH".to_owned());
    }
    if !affected.is_subset(&declared_impact) {
        revalidation_issues
            .issue_codes
            .insert("MNCS-03-IMPACT-SCOPE-INCOMPLETE".to_owned());
    }
    if !direct_impact.is_subset(&known_claims) {
        revalidation_issues
            .issue_codes
            .insert("MNCS-03-CHANGE-CLAIM-MISSING".to_owned());
    }
    if !affected.is_empty() {
        root_status = aggregate([root_status, revalidation_status]);
    }
    if !revalidation_issues.issue_codes.is_empty() {
        if status(value.pointer("/mncs/status")) != root_status {
            revalidation_issues
                .issue_codes
                .insert("MNCS-03-ASSURANCE-RESULT-MISMATCH".to_owned());
        }
        return revalidation_issues;
    }
    if value
        .pointer("/migration/downgrade_detected")
        .and_then(Value::as_bool)
        == Some(true)
    {
        return Outcome::new("INVALID").issue("MNCS-03-DOWNGRADE");
    }
    let mut outcome = Outcome::new(root_status);
    if let Some(rollback) = value
        .pointer("/lifecycle/rollback")
        .filter(|item| !item.is_null())
    {
        let mut rollback_status = status(rollback.get("test_status"));
        if rollback.get("active_release_id") != value.get("release_id") {
            rollback_status = "FAIL";
            outcome
                .issue_codes
                .insert("MNCS-03-ROLLBACK-BINDING".to_owned());
        }
        if rollback.get("environment_id") != root.get("environment_id") {
            rollback_status = "FAIL";
            outcome
                .issue_codes
                .insert("MNCS-03-ROLLBACK-ENVIRONMENT".to_owned());
        }
        root_status = aggregate([root_status, rollback_status]);
    }
    if let Some(retirement) = value
        .pointer("/lifecycle/retirement")
        .filter(|item| !item.is_null())
        && object_id(retirement, "claim_id") == Some(root_id)
    {
        root_status = "FAIL";
    }
    if let Some(replacement) = value
        .pointer("/lifecycle/replacement")
        .filter(|item| !item.is_null())
    {
        for key in ["old_claim_id", "new_claim_id"] {
            if object_id(replacement, key).is_none_or(|id| !ids.contains(id)) {
                return Outcome::new("INVALID").issue("MNCS-03-REPLACEMENT-CLAIM-MISSING");
            }
        }
        root_status = aggregate([root_status, status(replacement.get("status"))]);
    }
    let top_mncds = value.get("mncds");
    if top_mncds != root.get("mncds") {
        return Outcome::new("INVALID").issue("MNCS-03-MNCDS-ROOT-MISMATCH");
    }
    if let Some(label) = value.get("display_label").and_then(Value::as_str) {
        let expected = top_mncds.and_then(|item| {
            Some(format!(
                "{} / {}",
                item.get("profile")?.as_str()?,
                value.pointer("/mncs/level")?.as_str()?
            ))
        });
        if expected.as_deref() != Some(label) {
            return Outcome::new("INVALID").issue("MNCS-03-DISPLAY-LABEL-MISMATCH");
        }
    }
    if status(value.pointer("/mncs/status")) != root_status {
        return Outcome::new("INVALID").issue("MNCS-03-ASSURANCE-RESULT-MISMATCH");
    }
    root_status.clone_into(&mut outcome.category);
    outcome
}

fn validate_threat(value: &Value) -> Outcome {
    if value.get("schema_version").and_then(Value::as_str) != Some("0.3-rc.1") {
        return Outcome::new("UNSUPPORTED").issue("UNSUPPORTED-VERSION");
    }
    if !valid_id(value.get("threat_id")) {
        return Outcome::new("INVALID").issue("SCHEMA");
    }
    let computed = aggregate(
        array(value.get("mitigations"))
            .iter()
            .map(|item| status(item.get("status"))),
    );
    if status(value.get("status")) == computed {
        Outcome::new(computed)
    } else {
        Outcome::new("INVALID").issue("MNCS-03-THREAT-RESULT-MISMATCH")
    }
}

fn validate_measurement(value: &Value, at: &str) -> Outcome {
    if value.get("schema_version").and_then(Value::as_str) != Some("0.3-rc.1") {
        return Outcome::new("UNSUPPORTED").issue("UNSUPPORTED-VERSION");
    }
    if !valid_id(value.get("profile_id"))
        || value
            .get("sample_count")
            .and_then(Value::as_u64)
            .is_none_or(|count| count < 2)
        || value
            .get("repetitions")
            .and_then(Value::as_u64)
            .is_none_or(|count| count < 2)
    {
        return Outcome::new("INVALID").issue("SCHEMA");
    }
    let mut statuses = vec![freshness_status(value.get("freshness"), at)];
    let mut outcome = Outcome::new("PASS");
    if value.get("reporting_mode").and_then(Value::as_str) == Some("best_run_only") {
        statuses.push("FAIL");
        outcome
            .issue_codes
            .insert("MNCS-03-MEASUREMENT-BEST-RUN".to_owned());
    }
    let computed = aggregate(statuses);
    if status(value.get("status")) == computed {
        outcome.with_category(computed)
    } else {
        Outcome::new("INVALID").issue("MNCS-03-MEASUREMENT-RESULT-MISMATCH")
    }
}

fn candidate_ids(value: &Value) -> BTreeSet<&str> {
    array(value.get("candidates"))
        .iter()
        .filter_map(|candidate| object_id(candidate, "candidate_id"))
        .collect()
}

#[allow(clippy::too_many_lines)]
fn validate_mncds(value: &Value) -> Outcome {
    if value.get("mncds_version").and_then(Value::as_str) != Some("0.1-rc.1") {
        return Outcome::new("UNSUPPORTED").issue("unsupported-version");
    }
    let candidates = array(value.get("candidates"));
    let ids = candidate_ids(value);
    if ids.len() != candidates.len() {
        return Outcome::new("INVALID").issue("duplicate-id");
    }
    for candidate in candidates {
        for parent in array(candidate.get("parent_ids"))
            .iter()
            .filter_map(Value::as_str)
        {
            if !ids.contains(parent) {
                return Outcome::new("INVALID").issue("unknown-parent");
            }
        }
    }
    let parent_map: BTreeMap<_, _> = candidates
        .iter()
        .filter_map(|candidate| {
            Some((
                object_id(candidate, "candidate_id")?,
                array(candidate.get("parent_ids"))
                    .iter()
                    .filter_map(Value::as_str)
                    .collect::<Vec<_>>(),
            ))
        })
        .collect();
    for start in &ids {
        let mut stack = vec![*start];
        let mut seen = BTreeSet::new();
        while let Some(current) = stack.pop() {
            if !seen.insert(current) {
                return Outcome::new("INVALID").issue("lineage-cycle");
            }
            stack.extend(parent_map.get(current).into_iter().flatten().copied());
        }
    }
    if let Some(permissions) = value
        .pointer("/generator/permissions")
        .and_then(Value::as_object)
    {
        for key in [
            "modify_contract",
            "modify_baseline",
            "modify_evaluators",
            "modify_selection_policy",
            "modify_thresholds",
            "access_protected_holdout",
        ] {
            if permissions.get(key).and_then(Value::as_bool) == Some(true) {
                return Outcome::new("FAIL").issue("generator-authority-violation");
            }
        }
    }
    if value
        .pointer("/reproducibility/class")
        .and_then(Value::as_str)
        == Some("NONE")
    {
        return Outcome::new("FAIL").issue("d2-reproducibility-missing");
    }
    let mut outcome = Outcome::new("PASS");
    let mut computed = "PASS";
    let roles = array(value.get("roles"));
    let mut authorities: BTreeMap<&str, usize> = BTreeMap::new();
    for role in roles {
        if let Some(authority) = object_id(role, "authority_id") {
            *authorities.entry(authority).or_default() += 1;
        }
    }
    let disclosures: BTreeSet<_> = array(value.get("authority_overlaps"))
        .iter()
        .filter_map(|item| object_id(item, "authority_id"))
        .collect();
    if authorities
        .iter()
        .any(|(authority, count)| *count > 1 && !disclosures.contains(authority))
    {
        computed = "FAIL";
        outcome
            .issue_codes
            .insert("authority-overlap-undisclosed".to_owned());
    }
    if value
        .pointer("/partitions/holdout_contaminated")
        .and_then(Value::as_bool)
        == Some(true)
    {
        computed = "FAIL";
        outcome
            .issue_codes
            .insert("holdout-contaminated".to_owned());
    }
    if value
        .pointer("/selection/rule_recorded_before_final_evaluation")
        .and_then(Value::as_bool)
        == Some(false)
    {
        computed = "FAIL";
        outcome
            .issue_codes
            .insert("selection-rule-post-hoc".to_owned());
    }
    let selected_id = value
        .pointer("/selection/selected_candidate_id")
        .and_then(Value::as_str);
    let selected = selected_id.and_then(|id| {
        candidates
            .iter()
            .find(|candidate| object_id(candidate, "candidate_id") == Some(id))
    });
    if selected.is_none() {
        computed = "FAIL";
        outcome
            .issue_codes
            .insert("selected-candidate-missing".to_owned());
    } else if selected.is_some_and(|candidate| {
        candidate.get("disposition").and_then(Value::as_str) != Some("selected")
            || candidate.get("retained").and_then(Value::as_bool) != Some(true)
    }) {
        computed = "FAIL";
        outcome
            .issue_codes
            .insert("selection-disposition-mismatch".to_owned());
    }
    if candidates.iter().any(|candidate| {
        candidate
            .get("materially_evaluated")
            .and_then(Value::as_bool)
            == Some(true)
            && candidate.get("retained").and_then(Value::as_bool) != Some(true)
    }) {
        computed = "FAIL";
        outcome
            .issue_codes
            .insert("material-candidate-not-retained".to_owned());
    }
    if let Some(selected) = selected {
        let required: Vec<_> = array(selected.get("evaluator_results"))
            .iter()
            .filter(|result| result.get("required").and_then(Value::as_bool) == Some(true))
            .map(|result| status(result.get("status")))
            .collect();
        if required.contains(&"FAIL") {
            computed = "FAIL";
            outcome
                .issue_codes
                .insert("selected-required-fail".to_owned());
        } else if required.contains(&"UNKNOWN")
            && value
                .pointer("/selection/unknown_policy")
                .and_then(Value::as_str)
                == Some("reject")
        {
            computed = "FAIL";
            outcome.issue_codes.insert("unknown-promoted".to_owned());
        }
    }
    if value.pointer("/mncs_binding/contract_id") != value.pointer("/charter/contract_id") {
        computed = "FAIL";
        outcome
            .issue_codes
            .insert("mncs-binding-mismatch".to_owned());
    }
    let epochs = array(value.get("epochs"));
    let parents: BTreeMap<_, _> = epochs
        .iter()
        .filter_map(|epoch| {
            Some((
                object_id(epoch, "epoch_id")?,
                epoch.get("parent_epoch_id").and_then(Value::as_str),
            ))
        })
        .collect();
    for start in parents.keys() {
        let mut current = Some(*start);
        let mut seen = BTreeSet::new();
        while let Some(id) = current {
            if !seen.insert(id) {
                computed = "FAIL";
                outcome.issue_codes.insert("epoch-cycle".to_owned());
                break;
            }
            current = parents.get(id).copied().flatten();
        }
    }
    let profile = value
        .get("profile")
        .and_then(Value::as_str)
        .unwrap_or("MNCDS-D1");
    if matches!(profile, "MNCDS-D3" | "MNCDS-D4") {
        for evidence in array(value.get("protected_evidence")) {
            let evidence_status = status(evidence.get("status"));
            if evidence_status == "FAIL" {
                computed = "FAIL";
                outcome
                    .issue_codes
                    .insert("protected-evidence-failed".to_owned());
            } else if evidence_status == "UNKNOWN" && computed == "PASS" {
                computed = "UNKNOWN";
                outcome
                    .issue_codes
                    .insert("protected-evidence-unknown".to_owned());
            }
        }
    }
    if profile == "MNCDS-D4" {
        for (pointer, code) in [
            (
                "/release_controls/monitoring/status",
                "monitoring-not-established",
            ),
            (
                "/release_controls/rollback/test_status",
                "rollback-not-tested",
            ),
            (
                "/release_controls/regeneration_or_replacement/status",
                "regeneration-drill-failed",
            ),
        ] {
            let control = status(value.pointer(pointer));
            if control == "FAIL" {
                computed = "FAIL";
                outcome.issue_codes.insert(code.to_owned());
            } else if control == "UNKNOWN" && computed == "PASS" {
                computed = "UNKNOWN";
                outcome.issue_codes.insert(code.to_owned());
            }
        }
        if value
            .pointer("/release_controls/retirement/retired")
            .and_then(Value::as_bool)
            == Some(true)
        {
            computed = "FAIL";
            outcome
                .issue_codes
                .insert("selected-candidate-retired".to_owned());
        }
    }
    computed.clone_into(&mut outcome.category);
    outcome
}

fn apply_mutation(value: &mut Value, mutation: &Value) -> Result<(), String> {
    let path = mutation
        .get("path")
        .and_then(Value::as_str)
        .ok_or("mutation path is missing")?;
    let (parent_path, final_token) = path
        .rsplit_once('/')
        .ok_or_else(|| format!("invalid mutation path: {path}"))?;
    let parent = value
        .pointer_mut(parent_path)
        .ok_or_else(|| format!("mutation parent does not resolve: {parent_path}"))?;
    let operation = mutation
        .get("op")
        .and_then(Value::as_str)
        .ok_or("mutation operation is missing")?;
    match (operation, parent) {
        ("set", Value::Object(object)) => {
            object.insert(final_token.to_owned(), mutation["value"].clone());
        }
        ("set", Value::Array(items)) => {
            let index = final_token
                .parse::<usize>()
                .map_err(|error| error.to_string())?;
            items[index] = mutation["value"].clone();
        }
        ("delete", Value::Object(object)) => {
            object.remove(final_token);
        }
        ("delete", Value::Array(items)) => {
            let index = final_token
                .parse::<usize>()
                .map_err(|error| error.to_string())?;
            items.remove(index);
        }
        ("append", Value::Object(object)) => object
            .get_mut(final_token)
            .and_then(Value::as_array_mut)
            .ok_or_else(|| format!("append target is not an array: {path}"))?
            .push(mutation["value"].clone()),
        ("append", Value::Array(items)) => {
            let index = final_token
                .parse::<usize>()
                .map_err(|error| error.to_string())?;
            items[index]
                .as_array_mut()
                .ok_or_else(|| format!("append target is not an array: {path}"))?
                .push(mutation["value"].clone());
        }
        _ => return Err(format!("unsupported mutation: {operation} {path}")),
    }
    Ok(())
}

fn load_json(path: &Path) -> Result<Value, String> {
    serde_json::from_str(&fs::read_to_string(path).map_err(|error| error.to_string())?)
        .map_err(|error| error.to_string())
}

/// Validate one user-supplied RC record inside the declared Rust subset.
#[must_use]
pub fn validate_record_value(kind: &str, value: &Value, at: &str) -> Outcome {
    match kind {
        "contract" => validate_contract(value),
        "assurance" => validate_assurance(value, at),
        "threat" => validate_threat(value),
        "measurement" => validate_measurement(value, at),
        _ => Outcome::new("UNSUPPORTED").issue("unsupported-kind"),
    }
}

/// Validate one user-supplied MNCDS aggregate inside the declared Rust subset.
#[must_use]
pub fn validate_mncds_value(value: &Value) -> Outcome {
    validate_mncds(value)
}

/// Run a corpus directly from its JSON manifest.
///
/// # Errors
///
/// Returns an error for unreadable JSON, malformed corpus structure, unresolved
/// base paths, or invalid mutation operations. No candidate or evidence is run.
pub fn run_corpus(path: &Path) -> Result<RunResult, String> {
    let corpus = load_json(path)?;
    let bases = corpus
        .get("bases")
        .and_then(Value::as_object)
        .ok_or("corpus bases are missing")?;
    let mut base_values: BTreeMap<String, Value> = BTreeMap::new();
    let directory = path.parent().unwrap_or_else(|| Path::new("."));
    for (kind, relative) in bases {
        let relative = relative.as_str().ok_or("base path is not a string")?;
        base_values.insert(kind.clone(), load_json(&directory.join(relative))?);
    }
    let mut results = Vec::new();
    let mut categories = BTreeMap::new();
    let mut agreement = 0;
    let mut disagreement = 0;
    let mut unsupported = 0;
    let default_at = corpus
        .get("evaluation_time")
        .and_then(Value::as_str)
        .ok_or("corpus evaluation_time is missing")?;
    for case in array(corpus.get("cases")) {
        let id = object_id(case, "id").ok_or("case id is missing")?;
        let kind = object_id(case, "kind").ok_or("case kind is missing")?;
        let expected = object_id(case, "expected").ok_or("case expected is missing")?;
        let mut value = base_values
            .get(kind)
            .cloned()
            .ok_or_else(|| format!("base is missing for {kind}"))?;
        for mutation in array(case.get("mutations")) {
            apply_mutation(&mut value, mutation)?;
        }
        let at = case.get("at").and_then(Value::as_str).unwrap_or(default_at);
        let outcome = if kind == "mncds" {
            validate_mncds_value(&value)
        } else {
            validate_record_value(kind, &value, at)
        };
        *categories.entry(outcome.category.clone()).or_insert(0) += 1;
        let classification = if outcome.category == "UNSUPPORTED" && expected != "UNSUPPORTED" {
            unsupported += 1;
            "UNSUPPORTED_RULE"
        } else if outcome.category == expected {
            agreement += 1;
            "AGREEMENT"
        } else {
            disagreement += 1;
            "DISAGREEMENT"
        };
        results.push(CaseResult {
            id: id.to_owned(),
            kind: kind.to_owned(),
            expected: expected.to_owned(),
            actual: outcome.category,
            classification: classification.to_owned(),
            issue_codes: outcome.issue_codes,
        });
    }
    Ok(RunResult {
        implementation: "mncs-rc-consumer",
        implementation_language: "Rust",
        implementation_independence: "independent source and executable",
        operator_independence: "UNKNOWN",
        organizational_independence: "UNKNOWN",
        summary: Summary {
            total: results.len(),
            agreement,
            disagreement,
            unsupported,
            implementation_errors: 0,
            categories,
        },
        results,
    })
}

#[must_use]
pub fn default_corpus_from_manifest() -> PathBuf {
    PathBuf::from("conformance/release-candidate/corpus.json")
}

#[cfg(test)]
mod tests {
    use super::{aggregate, apply_mutation};
    use serde_json::json;

    #[test]
    fn status_precedence_is_fail_unknown_pass() {
        assert_eq!(aggregate(["PASS"]), "PASS");
        assert_eq!(aggregate(["PASS", "UNKNOWN"]), "UNKNOWN");
        assert_eq!(aggregate(["UNKNOWN", "FAIL"]), "FAIL");
        assert_eq!(aggregate([]), "UNKNOWN");
    }

    #[test]
    fn mutation_language_is_independent_and_bounded() {
        let mut value = json!({"items": [{"status": "PASS"}]});
        apply_mutation(
            &mut value,
            &json!({"op": "set", "path": "/items/0/status", "value": "FAIL"}),
        )
        .unwrap();
        assert_eq!(value["items"][0]["status"], "FAIL");
    }
}
