"""YAML configuration validator for niche templates."""
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .yaml_loader import NicheConfig


class ValidationResult:
    """Result of a validation operation."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, message: str):
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    def print_report(self):
        if self.is_valid:
            print("✅ Validation PASSED")
        else:
            print("❌ Validation FAILED")

        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  ❌ {error}")

        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")


def validate_yaml_file(file_path: Path) -> ValidationResult:
    """Validate a YAML niche configuration file."""
    result = ValidationResult()

    # Check file exists
    if not file_path.exists():
        result.add_error(f"File not found: {file_path}")
        return result

    # Load YAML
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result.add_error(f"Invalid YAML syntax: {e}")
        return result

    if not raw_config:
        result.add_error("Empty configuration file")
        return result

    # Validate against Pydantic schema
    try:
        config = NicheConfig(**raw_config)
    except ValidationError as e:
        for error in e.errors():
            location = " -> ".join(str(loc) for loc in error["loc"])
            result.add_error(f"{location}: {error['msg']}")
        return result

    # Additional validation checks
    _validate_entity_types(config, result)
    _validate_requirement_types(config, result)
    _validate_document_types(config, result)
    _validate_workflow_rules(config, result)
    _validate_notification_templates(config, result)

    return result


def _validate_entity_types(config: NicheConfig, result: ValidationResult):
    """Validate entity type configurations."""
    valid_field_types = {
        "string", "text", "number", "currency", "date", "boolean",
        "email", "phone", "url", "select", "multi-select", "address"
    }

    codes_seen = set()
    for entity_type in config.entity_types:
        # Check for duplicate codes
        if entity_type.code in codes_seen:
            result.add_error(f"Duplicate entity type code: {entity_type.code}")
        codes_seen.add(entity_type.code)

        # Validate field types
        for field in entity_type.fields:
            if field.type not in valid_field_types:
                result.add_error(
                    f"Entity type '{entity_type.code}' field '{field.name}' has "
                    f"invalid type '{field.type}'"
                )

            # Check select fields have options
            if field.type in ("select", "multi-select") and not field.options:
                result.add_warning(
                    f"Entity type '{entity_type.code}' field '{field.name}' is "
                    f"a {field.type} but has no options defined"
                )


def _validate_requirement_types(config: NicheConfig, result: ValidationResult):
    """Validate requirement type configurations."""
    valid_frequencies = {"once", "daily", "weekly", "monthly", "quarterly", "annually"}
    valid_priorities = {"low", "medium", "high", "critical"}

    entity_type_codes = {et.code for et in config.entity_types}
    document_type_codes = {dt.code for dt in config.document_types}

    codes_seen = set()
    for req_type in config.requirement_types:
        # Check for duplicate codes
        if req_type.code in codes_seen:
            result.add_error(f"Duplicate requirement type code: {req_type.code}")
        codes_seen.add(req_type.code)

        # Validate frequency
        if req_type.frequency and req_type.frequency not in valid_frequencies:
            result.add_error(
                f"Requirement type '{req_type.code}' has invalid frequency: "
                f"'{req_type.frequency}'"
            )

        # Validate priority
        if req_type.default_priority not in valid_priorities:
            result.add_error(
                f"Requirement type '{req_type.code}' has invalid default_priority: "
                f"'{req_type.default_priority}'"
            )

        # Validate entity type references
        for et_code in req_type.applicable_entity_types:
            if et_code not in entity_type_codes:
                result.add_error(
                    f"Requirement type '{req_type.code}' references unknown "
                    f"entity type: '{et_code}'"
                )

        # Validate document type references
        for dt_code in req_type.required_document_types:
            if dt_code not in document_type_codes:
                result.add_error(
                    f"Requirement type '{req_type.code}' references unknown "
                    f"document type: '{dt_code}'"
                )

        # Validate notification rules
        for days in req_type.notification_rules.days_before:
            if days <= 0:
                result.add_error(
                    f"Requirement type '{req_type.code}' has invalid "
                    f"days_before value: {days}"
                )


def _validate_document_types(config: NicheConfig, result: ValidationResult):
    """Validate document type configurations."""
    valid_field_types = {"string", "text", "number", "date", "boolean", "array"}
    valid_validation_rules = {
        "date_after", "date_before", "date_not_past", "date_not_future",
        "min_value", "max_value", "min_length", "max_length",
        "pattern", "required_if", "one_of"
    }

    codes_seen = set()
    for doc_type in config.document_types:
        # Check for duplicate codes
        if doc_type.code in codes_seen:
            result.add_error(f"Duplicate document type code: {doc_type.code}")
        codes_seen.add(doc_type.code)

        # Check extraction prompt
        if not doc_type.extraction_prompt:
            result.add_warning(
                f"Document type '{doc_type.code}' has no extraction_prompt"
            )

        # Validate extraction schema field types
        extraction_fields = {f.name for f in doc_type.extraction_schema.fields}
        for field in doc_type.extraction_schema.fields:
            if field.type not in valid_field_types:
                result.add_warning(
                    f"Document type '{doc_type.code}' extraction field "
                    f"'{field.name}' has unusual type '{field.type}'"
                )

        # Validate validation rules
        for rule in doc_type.validation_rules:
            if rule.field not in extraction_fields:
                result.add_error(
                    f"Document type '{doc_type.code}' validation rule "
                    f"references unknown field: '{rule.field}'"
                )

            if rule.rule not in valid_validation_rules:
                result.add_warning(
                    f"Document type '{doc_type.code}' has unknown "
                    f"validation rule: '{rule.rule}'"
                )


def _validate_workflow_rules(config: NicheConfig, result: ValidationResult):
    """Validate workflow rule configurations."""
    valid_events = {
        "document.uploaded", "document.processed",
        "requirement.created", "requirement.expiring", "requirement.expired",
        "entity.created", "entity.updated"
    }
    valid_actions = {
        "create_requirement", "update_requirement", "send_notification",
        "link_document", "update_status", "assign_user"
    }
    valid_operators = {
        "equals", "not_equals", "greater_than", "less_than",
        "greater_than_or_equal", "less_than_or_equal",
        "contains", "not_contains", "in", "not_in"
    }

    codes_seen = set()
    for rule in config.workflow_rules:
        # Check for duplicate codes
        if rule.code in codes_seen:
            result.add_error(f"Duplicate workflow rule code: {rule.code}")
        codes_seen.add(rule.code)

        # Validate trigger event
        if rule.trigger.event not in valid_events:
            result.add_error(
                f"Workflow rule '{rule.code}' has invalid trigger event: "
                f"'{rule.trigger.event}'"
            )

        # Validate condition operators
        for condition in rule.trigger.conditions:
            if condition.operator not in valid_operators:
                result.add_error(
                    f"Workflow rule '{rule.code}' has invalid condition "
                    f"operator: '{condition.operator}'"
                )

        # Validate actions
        for action in rule.actions:
            if action.type not in valid_actions:
                result.add_error(
                    f"Workflow rule '{rule.code}' has invalid action type: "
                    f"'{action.type}'"
                )


def _validate_notification_templates(config: NicheConfig, result: ValidationResult):
    """Validate notification template configurations."""
    valid_types = {"reminder", "expiring", "overdue", "escalation", "status_change"}
    valid_channels = {"email", "in_app", "sms", "webhook"}

    codes_seen = set()
    for template in config.notification_templates:
        # Check for duplicate codes
        if template.code in codes_seen:
            result.add_error(f"Duplicate notification template code: {template.code}")
        codes_seen.add(template.code)

        # Validate notification type
        if template.notification_type not in valid_types:
            result.add_warning(
                f"Notification template '{template.code}' has unusual type: "
                f"'{template.notification_type}'"
            )

        # Validate channel
        if template.channel not in valid_channels:
            result.add_error(
                f"Notification template '{template.code}' has invalid channel: "
                f"'{template.channel}'"
            )

        # Check for template variables (basic check)
        if "{{" in template.subject or "{{" in template.body:
            # Jinja2 syntax found, which is expected
            pass
        else:
            result.add_warning(
                f"Notification template '{template.code}' has no template variables"
            )


def main():
    """CLI entry point for YAML validation."""
    if len(sys.argv) < 2:
        print("Usage: python -m app.config.yaml_validator <yaml_file>")
        print("       python -m app.config.yaml_validator --all")
        sys.exit(1)

    if sys.argv[1] == "--all":
        # Validate all YAML files in configs/niches
        from .settings import get_settings
        settings = get_settings()
        config_path = Path(settings.niches_config_path)

        if not config_path.exists():
            print(f"Config path not found: {config_path}")
            sys.exit(1)

        all_valid = True
        for yaml_file in config_path.glob("*.yaml"):
            print(f"\n{'='*60}")
            print(f"Validating: {yaml_file.name}")
            print("="*60)
            result = validate_yaml_file(yaml_file)
            result.print_report()
            if not result.is_valid:
                all_valid = False

        sys.exit(0 if all_valid else 1)
    else:
        # Validate single file
        file_path = Path(sys.argv[1])
        print(f"Validating: {file_path}")
        print("="*60)
        result = validate_yaml_file(file_path)
        result.print_report()
        sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
