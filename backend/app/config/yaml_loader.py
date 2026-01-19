"""YAML configuration loader for niche templates."""
import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, validator

from .settings import get_settings


# =============================================================================
# Pydantic Models for YAML Schema Validation
# =============================================================================

class FieldDefinition(BaseModel):
    """Definition of a custom field."""
    name: str
    label: str
    type: str
    required: bool = False
    default: Any = None
    options: list[str] = []
    validation: dict[str, Any] = {}


class EntityTypeConfig(BaseModel):
    """Configuration for an entity type."""
    code: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    fields: list[FieldDefinition] = []


class NotificationRulesConfig(BaseModel):
    """Notification rules configuration."""
    days_before: list[int] = []
    escalation: dict[str, Any] = {}


class RequirementTypeConfig(BaseModel):
    """Configuration for a requirement type."""
    code: str
    name: str
    description: Optional[str] = None
    frequency: Optional[str] = None
    default_priority: str = "medium"
    applicable_entity_types: list[str] = []
    required_document_types: list[str] = []
    notification_rules: NotificationRulesConfig = NotificationRulesConfig()
    fields: list[FieldDefinition] = []


class ExtractionField(BaseModel):
    """Field definition for document extraction."""
    name: str
    label: str
    type: str
    required: bool = False


class ExtractionSchema(BaseModel):
    """Schema for document extraction."""
    fields: list[ExtractionField] = []


class ValidationRule(BaseModel):
    """Validation rule for extracted data."""
    field: str
    rule: str
    value: Any = None
    message: str = ""


class DocumentTypeConfig(BaseModel):
    """Configuration for a document type."""
    code: str
    name: str
    description: Optional[str] = None
    accepted_mime_types: list[str] = ["application/pdf", "image/png", "image/jpeg"]
    extraction_prompt: Optional[str] = None
    extraction_schema: ExtractionSchema = ExtractionSchema()
    validation_rules: list[ValidationRule] = []


class WorkflowCondition(BaseModel):
    """Condition for a workflow trigger."""
    field: str
    operator: str
    value: Any


class WorkflowAction(BaseModel):
    """Action to perform in a workflow."""
    type: str
    params: dict[str, Any] = {}


class WorkflowTrigger(BaseModel):
    """Trigger configuration for a workflow."""
    event: str
    conditions: list[WorkflowCondition] = []


class WorkflowRuleConfig(BaseModel):
    """Configuration for a workflow rule."""
    code: str
    name: str
    description: Optional[str] = None
    enabled: bool = True
    trigger: WorkflowTrigger
    actions: list[WorkflowAction] = []


class NotificationTemplateConfig(BaseModel):
    """Configuration for a notification template."""
    code: str
    name: str
    notification_type: str
    channel: str = "email"
    subject: str
    body: str


class NicheMetadata(BaseModel):
    """Metadata about a niche."""
    id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"


class NicheConfig(BaseModel):
    """Complete niche configuration."""
    niche: NicheMetadata
    entity_types: list[EntityTypeConfig] = []
    requirement_types: list[RequirementTypeConfig] = []
    document_types: list[DocumentTypeConfig] = []
    workflow_rules: list[WorkflowRuleConfig] = []
    notification_templates: list[NotificationTemplateConfig] = []

    @validator("requirement_types")
    def validate_requirement_entity_types(cls, v, values):
        """Validate that referenced entity types exist."""
        if "entity_types" not in values:
            return v

        valid_codes = {et.code for et in values["entity_types"]}
        for req_type in v:
            for et_code in req_type.applicable_entity_types:
                if et_code not in valid_codes:
                    raise ValueError(
                        f"Requirement type '{req_type.code}' references unknown "
                        f"entity type '{et_code}'"
                    )
        return v

    @validator("requirement_types")
    def validate_requirement_document_types(cls, v, values):
        """Validate that referenced document types exist."""
        if "document_types" not in values:
            return v

        valid_codes = {dt.code for dt in values["document_types"]}
        for req_type in v:
            for dt_code in req_type.required_document_types:
                if dt_code not in valid_codes:
                    raise ValueError(
                        f"Requirement type '{req_type.code}' references unknown "
                        f"document type '{dt_code}'"
                    )
        return v


# =============================================================================
# YAML Loader
# =============================================================================

class NicheConfigLoader:
    """Loads and manages niche configurations from YAML files."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the loader with a config directory path."""
        settings = get_settings()
        self.config_path = Path(config_path or settings.niches_config_path)
        self._configs: dict[str, NicheConfig] = {}

    def load_all(self) -> dict[str, NicheConfig]:
        """Load all niche configurations from the config directory."""
        if not self.config_path.exists():
            print(f"Warning: Niche config path does not exist: {self.config_path}")
            return {}

        for yaml_file in self.config_path.glob("*.yaml"):
            try:
                config = self.load_file(yaml_file)
                self._configs[config.niche.id] = config
                print(f"Loaded niche config: {config.niche.id} ({config.niche.name})")
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")

        return self._configs

    def load_file(self, file_path: Path) -> NicheConfig:
        """Load a single niche configuration file."""
        with open(file_path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        return NicheConfig(**raw_config)

    def get_config(self, niche_id: str) -> Optional[NicheConfig]:
        """Get a loaded niche configuration by ID."""
        return self._configs.get(niche_id)

    def get_all_configs(self) -> dict[str, NicheConfig]:
        """Get all loaded niche configurations."""
        return self._configs

    def get_entity_types(self, niche_id: str) -> list[EntityTypeConfig]:
        """Get entity types for a specific niche."""
        config = self.get_config(niche_id)
        return config.entity_types if config else []

    def get_requirement_types(self, niche_id: str) -> list[RequirementTypeConfig]:
        """Get requirement types for a specific niche."""
        config = self.get_config(niche_id)
        return config.requirement_types if config else []

    def get_document_types(self, niche_id: str) -> list[DocumentTypeConfig]:
        """Get document types for a specific niche."""
        config = self.get_config(niche_id)
        return config.document_types if config else []

    def get_workflow_rules(self, niche_id: str) -> list[WorkflowRuleConfig]:
        """Get workflow rules for a specific niche."""
        config = self.get_config(niche_id)
        return config.workflow_rules if config else []

    def get_notification_templates(self, niche_id: str) -> list[NotificationTemplateConfig]:
        """Get notification templates for a specific niche."""
        config = self.get_config(niche_id)
        return config.notification_templates if config else []


# Global loader instance
_loader: Optional[NicheConfigLoader] = None


def get_niche_loader() -> NicheConfigLoader:
    """Get the global niche config loader instance."""
    global _loader
    if _loader is None:
        _loader = NicheConfigLoader()
        _loader.load_all()
    return _loader


def reload_niche_configs() -> dict[str, NicheConfig]:
    """Reload all niche configurations."""
    global _loader
    _loader = NicheConfigLoader()
    return _loader.load_all()
