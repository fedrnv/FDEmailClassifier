"""Versioned, offline email text normalization for training ingestion only."""

import hashlib
import json
import unicodedata
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser

VERSION = "fdec-email-normalization/v1"
MAX_MESSAGE_BYTES = 2_000_000
MAX_BODY_CHARS = 200_000
MAX_ROWS = 100_000
MAX_TOTAL_TEXT_BYTES = 50_000_000


class IngestionError(Exception):
    """Only static error codes, never source content or third-party exceptions."""


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def text(value, limit):
    if not isinstance(value, str) or len(value) > limit:
        raise IngestionError("invalid_text")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError:
        raise IngestionError("invalid_text_encoding") from None
    if any(ord(char) < 32 and char not in "\r\n\t" for char in value):
        raise IngestionError("invalid_text_control")
    return " ".join(unicodedata.normalize("NFC", value).split())


class VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "head", "iframe", "object", "template"}:
            self.hidden.append(tag)
        elif not self.hidden and tag in {"p", "div", "br", "li", "tr", "hr", "h1", "h2", "h3"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if self.hidden and self.hidden[-1] == tag:
            self.hidden.pop()
        elif not self.hidden:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def html_text(value):
    parser = VisibleHTML()
    parser.feed(value)
    parser.close()
    return "".join(parser.parts)


def mime_text(raw):
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_MESSAGE_BYTES:
        raise IngestionError("invalid_mime_size")
    try:
        message = BytesParser(policy=policy.default).parsebytes(raw)
        parts = list(message.walk())
        if len(parts) > 100 or any(part.defects for part in parts):
            raise IngestionError("invalid_mime")
        subjects = message.get_all("Subject", [])
        if len(subjects) > 1 or any(getattr(header, "defects", ()) for header in subjects):
            raise IngestionError("ambiguous_mime_subject")

        def extract(part, depth=0):
            if depth > 20:
                raise IngestionError("mime_depth_limit")
            if part.get_content_disposition() == "attachment" or part.get_filename() or part.get_content_type() == "message/rfc822":
                return []
            if part.is_multipart():
                children = [extract(child, depth + 1) for child in part.iter_parts()]
                if part.get_content_subtype() == "alternative":
                    for kind in ("text/plain", "text/html"):
                        for child in children:
                            preferred = [item for item in child if item[0] == kind]
                            if preferred:
                                return preferred
                    return []
                return [item for child in children for item in child]
            kind = part.get_content_type()
            if kind not in {"text/plain", "text/html"}:
                return []
            encodings = part.get_all("Content-Transfer-Encoding", [])
            if len(encodings) > 1 or str(encodings[0] if encodings else "7bit").lower() not in {"7bit", "8bit", "binary", "base64", "quoted-printable"}:
                raise IngestionError("invalid_mime_encoding")
            payload = part.get_payload(decode=True)
            if part.defects or not isinstance(payload, bytes):
                raise IngestionError("invalid_mime_encoding")
            decoded = payload.decode(part.get_content_charset() or "ascii", errors="strict")
            return [(kind, html_text(decoded) if kind == "text/html" else decoded)]

        body = " ".join(item[1] for item in extract(message))
        return str(subjects[0]) if subjects else "", body
    except IngestionError:
        raise
    except Exception:
        raise IngestionError("invalid_mime") from None


def normalize_row(row):
    allowed = {"subject", "body", "body_format", "raw", "raw_mime", "labels", "category", "priority", "action", "source_round"}
    if not isinstance(row, dict) or not row or set(row) - allowed:
        raise IngestionError("unsupported_record")
    raw_keys = set(row) & {"raw", "raw_mime"}
    if raw_keys:
        if len(raw_keys) != 1 or set(row) & {"subject", "body", "body_format"}:
            raise IngestionError("ambiguous_record_content")
        raw = row[next(iter(raw_keys))]
        if "raw_mime" in row:
            if not isinstance(raw, str):
                raise IngestionError("invalid_mime")
            raw = raw.encode("utf-8", errors="strict")
        subject, body = mime_text(raw)
    else:
        if "subject" not in row or "body" not in row or row.get("body_format", "plain") not in {"plain", "html"}:
            raise IngestionError("missing_record_content")
        subject, body = row["subject"], row["body"]
        # Validate size/type before feeding the HTML parser.
        text(body, MAX_BODY_CHARS)
        if row.get("body_format") == "html":
            body = html_text(body)
    subject, body = text(subject, 4096), text(body, MAX_BODY_CHARS)
    if not body:
        raise IngestionError("empty_message")
    labels = {}
    for key in ("category", "priority", "action"):
        if key in row:
            labels[key] = text(row[key], 256)
    if "labels" in row:
        if not isinstance(row["labels"], list) or len(row["labels"]) > 32:
            raise IngestionError("invalid_source_labels")
        labels["labels"] = sorted({text(value, 256) for value in row["labels"]})
    annotation = {"labels": labels}
    if "source_round" in row:
        annotation["source_round"] = text(row["source_round"], 256)
    identity = hashlib.sha256((VERSION + "\0" + canonical_json([subject, body])).encode("utf-8")).hexdigest()
    return identity, subject, body, annotation


def deduplicate(rows, source):
    records = {}
    count = 0
    text_bytes = 0
    for index, row in enumerate(rows):
        count += 1
        if count > MAX_ROWS:
            raise IngestionError("row_limit")
        identity, subject, body, annotation = normalize_row(row)
        text_bytes += len(subject.encode("utf-8")) + len(body.encode("utf-8"))
        if text_bytes > MAX_TOTAL_TEXT_BYTES:
            raise IngestionError("dataset_text_limit")
        if identity not in records:
            records[identity] = {"schema": "fdec-normalized-email/v1", "content_id": identity, "subject": subject, "body": body, "source": source, "annotations": [], "annotation_conflict": False}
        record = records[identity]
        if (record["subject"], record["body"]) != (subject, body):
            raise IngestionError("content_hash_collision")
        record["annotations"].append({"source_row": index, **annotation})
    if not count:
        raise IngestionError("empty_dataset")
    for record in records.values():
        record["annotation_conflict"] = len({canonical_json(item["labels"]) for item in record["annotations"]}) > 1
    return [records[key] for key in sorted(records)], count
