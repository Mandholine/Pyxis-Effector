# -*- coding: utf-8 -*-
# Pyxis Effector — Application Use Cases (Templates)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from typing import Optional
from ...domain.entities.template import EffectTemplate
from ...domain.repositories.i_template_repository import ITemplateRepository
from ..dtos.template_dto import TemplateDTO, TemplateListDTO
from ..mappers.graph_mapper import GraphMapper


class ManageTemplatesUseCase:
    """Use case to list, retrieve, save, and delete effect templates."""

    def __init__(self, template_repo: ITemplateRepository):
        self.template_repo = template_repo

    def list_templates(self) -> TemplateListDTO:
        templates = self.template_repo.list_templates()
        dto_list = [
            TemplateDTO(
                id=t.id,
                name=t.name,
                comment=t.comment,
                author=t.author,
                category=t.category,
                payload=t.raw_payload or (GraphMapper.to_dict(t.graph) if t.graph else {}),
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ]
        return TemplateListDTO(templates=dto_list, total=len(dto_list))

    def get_template(self, identifier: str) -> Optional[TemplateDTO]:
        t = self.template_repo.get_template(identifier)
        if not t:
            return None
        return TemplateDTO(
            id=t.id,
            name=t.name,
            comment=t.comment,
            author=t.author,
            category=t.category,
            payload=t.raw_payload or (GraphMapper.to_dict(t.graph) if t.graph else {}),
            created_at=t.created_at,
            updated_at=t.updated_at,
        )

    def save_template(self, dto: TemplateDTO) -> str:
        domain_template = EffectTemplate(
            id=dto.id,
            name=dto.name,
            comment=dto.comment,
            author=dto.author,
            category=dto.category,
            raw_payload=dto.payload,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
        return self.template_repo.save_template(domain_template)

    def delete_template(self, identifier: str) -> bool:
        return self.template_repo.delete_template(identifier)
