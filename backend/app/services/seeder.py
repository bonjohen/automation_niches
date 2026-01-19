"""Database seeder - populates lookup tables from YAML configurations."""
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.config.yaml_loader import (
    NicheConfigLoader,
    NicheConfig,
    EntityTypeConfig,
    RequirementTypeConfig,
    DocumentTypeConfig,
    get_niche_loader,
)
from app.models.entity import EntityType
from app.models.requirement import RequirementType
from app.models.document import DocumentType


class DatabaseSeeder:
    """Seeds the database with lookup table data from YAML configurations."""

    def __init__(self, db: Session, loader: Optional[NicheConfigLoader] = None):
        self.db = db
        self.loader = loader or get_niche_loader()

    def seed_all(self) -> dict[str, int]:
        """
        Seed all lookup tables from all loaded niche configurations.

        Returns dict with counts of seeded records per table.
        """
        results = {
            "entity_types": 0,
            "requirement_types": 0,
            "document_types": 0,
        }

        for niche_id, config in self.loader.get_all_configs().items():
            niche_results = self.seed_niche(config)
            for key, count in niche_results.items():
                results[key] += count

        self.db.commit()
        return results

    def seed_niche(self, config: NicheConfig) -> dict[str, int]:
        """Seed lookup tables for a single niche configuration."""
        results = {
            "entity_types": 0,
            "requirement_types": 0,
            "document_types": 0,
        }

        # Seed entity types
        for et_config in config.entity_types:
            if self._seed_entity_type(et_config, config.niche.id):
                results["entity_types"] += 1

        # Seed document types (before requirement types due to references)
        for dt_config in config.document_types:
            if self._seed_document_type(dt_config, config.niche.id):
                results["document_types"] += 1

        # Seed requirement types
        for rt_config in config.requirement_types:
            if self._seed_requirement_type(rt_config, config.niche.id):
                results["requirement_types"] += 1

        return results

    def _seed_entity_type(self, config: EntityTypeConfig, niche_id: str) -> bool:
        """Seed or update an entity type. Returns True if created/updated."""
        existing = self.db.query(EntityType).filter(
            EntityType.code == config.code
        ).first()

        field_schema = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        for field in config.fields:
            field_schema["properties"][field.name] = {
                "type": self._map_field_type(field.type),
                "title": field.label,
            }
            if field.options:
                field_schema["properties"][field.name]["enum"] = field.options
            if field.default is not None:
                field_schema["properties"][field.name]["default"] = field.default
            if field.required:
                field_schema["required"].append(field.name)

        if existing:
            # Update existing
            existing.name = config.name
            existing.description = config.description
            existing.icon = config.icon
            existing.field_schema = field_schema
            existing.niche_id = niche_id
            return False
        else:
            # Create new
            entity_type = EntityType(
                code=config.code,
                name=config.name,
                description=config.description,
                icon=config.icon,
                field_schema=field_schema,
                niche_id=niche_id,
            )
            self.db.add(entity_type)
            return True

    def _seed_requirement_type(self, config: RequirementTypeConfig, niche_id: str) -> bool:
        """Seed or update a requirement type. Returns True if created."""
        existing = self.db.query(RequirementType).filter(
            RequirementType.code == config.code
        ).first()

        notification_rules = {
            "days_before": config.notification_rules.days_before,
            "escalation": config.notification_rules.escalation,
        }

        field_schema = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        for field in config.fields:
            field_schema["properties"][field.name] = {
                "type": self._map_field_type(field.type),
                "title": field.label,
            }
            if field.default is not None:
                field_schema["properties"][field.name]["default"] = field.default
            if field.required:
                field_schema["required"].append(field.name)

        if existing:
            # Update existing
            existing.name = config.name
            existing.description = config.description
            existing.frequency = config.frequency
            existing.default_priority = config.default_priority
            existing.notification_rules = notification_rules
            existing.applicable_entity_types = config.applicable_entity_types
            existing.required_document_types = config.required_document_types
            existing.field_schema = field_schema
            existing.niche_id = niche_id
            return False
        else:
            # Create new
            req_type = RequirementType(
                code=config.code,
                name=config.name,
                description=config.description,
                frequency=config.frequency,
                default_priority=config.default_priority,
                notification_rules=notification_rules,
                applicable_entity_types=config.applicable_entity_types,
                required_document_types=config.required_document_types,
                field_schema=field_schema,
                niche_id=niche_id,
            )
            self.db.add(req_type)
            return True

    def _seed_document_type(self, config: DocumentTypeConfig, niche_id: str) -> bool:
        """Seed or update a document type. Returns True if created."""
        existing = self.db.query(DocumentType).filter(
            DocumentType.code == config.code
        ).first()

        extraction_schema = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        for field in config.extraction_schema.fields:
            extraction_schema["properties"][field.name] = {
                "type": self._map_field_type(field.type),
                "title": field.label,
            }
            if field.required:
                extraction_schema["required"].append(field.name)

        validation_rules = {
            "rules": [
                {
                    "field": rule.field,
                    "rule": rule.rule,
                    "value": rule.value,
                    "message": rule.message,
                }
                for rule in config.validation_rules
            ]
        }

        if existing:
            # Update existing
            existing.name = config.name
            existing.description = config.description
            existing.accepted_mime_types = config.accepted_mime_types
            existing.extraction_prompt = config.extraction_prompt
            existing.extraction_schema = extraction_schema
            existing.validation_rules = validation_rules
            existing.niche_id = niche_id
            return False
        else:
            # Create new
            doc_type = DocumentType(
                code=config.code,
                name=config.name,
                description=config.description,
                accepted_mime_types=config.accepted_mime_types,
                extraction_prompt=config.extraction_prompt,
                extraction_schema=extraction_schema,
                validation_rules=validation_rules,
                niche_id=niche_id,
            )
            self.db.add(doc_type)
            return True

    def _map_field_type(self, yaml_type: str) -> str:
        """Map YAML field types to JSON Schema types."""
        type_map = {
            "string": "string",
            "text": "string",
            "number": "number",
            "currency": "number",
            "date": "string",  # format: date
            "boolean": "boolean",
            "email": "string",  # format: email
            "phone": "string",
            "url": "string",  # format: uri
            "select": "string",
            "multi-select": "array",
            "address": "string",
            "array": "array",
        }
        return type_map.get(yaml_type, "string")


def seed_database(db: Session) -> dict[str, int]:
    """Convenience function to seed the database."""
    seeder = DatabaseSeeder(db)
    return seeder.seed_all()
