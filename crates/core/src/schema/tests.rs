use super::*;
use serde_json::{Value, json};

const FIXTURES: [&str; 3] = [
    include_str!("../../../../schemas/examples/classified.json"),
    include_str!("../../../../schemas/examples/unknown.json"),
    include_str!("../../../../schemas/examples/abstained.json"),
];

#[test]
fn schema_round_trip_all_states() {
    for fixture in FIXTURES {
        let value: Classification = serde_json::from_str(fixture).unwrap();
        let encoded = serde_json::to_string(&value).unwrap();
        assert_eq!(
            serde_json::from_str::<Classification>(&encoded).unwrap(),
            value
        );
        assert_eq!(
            serde_json::from_str::<Value>(&encoded).unwrap(),
            serde_json::from_str::<Value>(fixture).unwrap()
        );
    }
}

#[test]
fn schema_invalid_payloads_fail_without_mutation() {
    let base: Value = serde_json::from_str(FIXTURES[0]).unwrap();
    for (field, invalid) in [
        ("schema_version", json!("2")),
        ("schema_version", json!(1)),
        ("topics", json!(["work", "work"])),
        ("topics", json!([])),
        ("topics", json!(["not_a_topic"])),
        ("topics", json!(null)),
        ("priority", json!("now")),
        ("status", json!("success")),
        ("suggested_action", json!("delete")),
        ("extra", json!(true)),
        (
            "security",
            json!({"spam":"clear","phishing":"clear","malware":"clear","extra":true}),
        ),
        ("security", json!({"spam":"clear","phishing":"clear"})),
    ] {
        let mut bad = base.clone();
        bad[field] = invalid;
        let before = bad.clone();
        assert!(
            serde_json::from_value::<Classification>(bad.clone()).is_err(),
            "{field}"
        );
        assert_eq!(bad, before);
    }
    for field in base.as_object().unwrap().keys() {
        let mut bad = base.clone();
        bad.as_object_mut().unwrap().remove(field);
        assert!(
            serde_json::from_value::<Classification>(bad).is_err(),
            "missing {field}"
        );
    }
    assert!(serde_json::from_str::<Classification>("{").is_err());
    let duplicate = FIXTURES[0].replace(
        "\"schema_version\":\"1\"",
        "\"schema_version\":\"1\",\"schema_version\":\"1\"",
    );
    assert!(serde_json::from_str::<Classification>(&duplicate).is_err());
}

#[test]
fn schema_abstention_and_serialization_fail_closed() {
    for fixture in &FIXTURES[1..] {
        for (field, bad) in [
            ("topics", json!(["other"])),
            ("priority", json!("high")),
            ("suggested_action", json!("archive")),
        ] {
            let mut value: Value = serde_json::from_str(fixture).unwrap();
            value[field] = bad;
            assert!(serde_json::from_value::<Classification>(value).is_err());
        }
    }
    let mut typed: Classification = serde_json::from_str(FIXTURES[0]).unwrap();
    typed.topics.clear();
    assert!(serde_json::to_string(&typed).is_err());
}

#[test]
fn schema_all_twelve_topics_match_json_schema() {
    let schema: Value = serde_json::from_str(include_str!(
        "../../../../schemas/classification-v1.schema.json"
    ))
    .unwrap();
    let topics = schema["properties"]["topics"]["items"]["enum"]
        .as_array()
        .unwrap();
    assert_eq!(topics.len(), 12);
    let mut payload: Value = serde_json::from_str(FIXTURES[0]).unwrap();
    payload["topics"] = json!(topics);
    let typed: Classification = serde_json::from_value(payload).unwrap();
    assert_eq!(typed.topics.len(), 12);
    let encoded = serde_json::to_value(typed).unwrap();
    assert_eq!(encoded["topics"], json!(topics));
}
