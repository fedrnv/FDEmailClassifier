// Copyright 2026 FDEmailClassifier contributors
// SPDX-License-Identifier: Apache-2.0
//! Version 1 advisory output. No type in this module executes suggested actions.
use serde::{Deserialize, Deserializer, Serialize, Serializer};

pub mod calibration;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SchemaVersion {
    #[serde(rename = "1")]
    V1,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Topic {
    Work,
    Personal,
    Finance,
    Shopping,
    Travel,
    Social,
    Newsletters,
    Marketing,
    Education,
    Health,
    Legal,
    Other,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Status {
    Classified,
    Unknown,
    Abstained,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Priority {
    Unknown,
    Low,
    Normal,
    High,
    Urgent,
}

/// Unknown means not assessed; clear is an assessment, never a safety guarantee.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Assessment {
    Unknown,
    Clear,
    Flagged,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Security {
    pub spam: Assessment,
    pub phishing: Assessment,
    pub malware: Assessment,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SuggestedAction {
    None,
    Review,
    Reply,
    Archive,
}

/// Both serialization and deserialization enforce cross-field validity.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Classification {
    pub schema_version: SchemaVersion,
    pub status: Status,
    pub topics: Vec<Topic>,
    pub priority: Priority,
    pub security: Security,
    pub suggested_action: SuggestedAction,
}

#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Wire {
    schema_version: SchemaVersion,
    status: Status,
    topics: Vec<Topic>,
    priority: Priority,
    security: Security,
    suggested_action: SuggestedAction,
}

impl Classification {
    /// Static error messages deliberately exclude payload values.
    pub fn validate(&self) -> Result<(), &'static str> {
        if self.topics.len() > 12 {
            return Err("too many topics");
        }
        for (index, topic) in self.topics.iter().enumerate() {
            if self.topics[..index].contains(topic) {
                return Err("duplicate topic");
            }
        }
        match self.status {
            Status::Classified if self.topics.is_empty() => Err("classified requires topics"),
            Status::Unknown | Status::Abstained
                if !self.topics.is_empty()
                    || self.priority != Priority::Unknown
                    || self.suggested_action != SuggestedAction::Review =>
            {
                Err("unknown or abstained requires empty topics, unknown priority and review")
            }
            _ => Ok(()),
        }
    }
}

impl Serialize for Classification {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        self.validate().map_err(serde::ser::Error::custom)?;
        Wire {
            schema_version: self.schema_version,
            status: self.status,
            topics: self.topics.clone(),
            priority: self.priority,
            security: self.security.clone(),
            suggested_action: self.suggested_action,
        }
        .serialize(serializer)
    }
}

impl<'de> Deserialize<'de> for Classification {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let wire = Wire::deserialize(deserializer)?;
        let value = Self {
            schema_version: wire.schema_version,
            status: wire.status,
            topics: wire.topics,
            priority: wire.priority,
            security: wire.security,
            suggested_action: wire.suggested_action,
        };
        value.validate().map_err(serde::de::Error::custom)?;
        Ok(value)
    }
}

#[cfg(test)]
mod tests;
