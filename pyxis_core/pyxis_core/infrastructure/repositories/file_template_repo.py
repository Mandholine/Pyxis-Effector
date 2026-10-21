# -*- coding: utf-8 -*-
# Pyxis Effector — Infrastructure Repositories (File Template Repository)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

import json
import os
import uuid
from typing import List, Optional

from ...domain.entities.template import EffectTemplate
from ...domain.repositories.i_template_repository import ITemplateRepository
from ...application.mappers.graph_mapper import GraphMapper
from ..engine.system import TEMPLATES_DIR, get_user_data_dir


class FileTemplateRepository(ITemplateRepository):
    """Concrete repository that loads and stores templates in filesystem directories."""

    def __init__(self, system_dir: Optional[str] = None, user_dir: Optional[str] = None):
        self.system_dir = system_dir or TEMPLATES_DIR
        self.user_dir = user_dir or os.path.join(get_user_data_dir(), "templates")
        os.makedirs(self.user_dir, exist_ok=True)

    def list_templates(self) -> List[EffectTemplate]:
        result: List[EffectTemplate] = []
        seen_names = set()

        # Check system dir then user dir
        for directory in (self.user_dir, self.system_dir):
            if not os.path.isdir(directory):
                continue
            for fname in sorted(os.listdir(directory)):
                if fname.endswith(".json"):
                    fpath = os.path.join(directory, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        name = data.get("name") or os.path.splitext(fname)[0]
                        if name in seen_names:
                            continue
                        seen_names.add(name)

                        template = EffectTemplate(
                            id=str(data.get("id", name)),
                            name=name,
                            comment=data.get("comment", ""),
                            author=data.get("author", ""),
                            category=data.get("category", "General"),
                            raw_payload=data,
                            created_at=data.get("created_at"),
                            updated_at=data.get("updated_at"),
                        )
                        result.append(template)
                    except Exception:
                        pass
        return result

    def get_template(self, identifier: str) -> Optional[EffectTemplate]:
        for t in self.list_templates():
            if t.id == identifier or t.name == identifier:
                return t
        return None

    def save_template(self, template: EffectTemplate) -> str:
        tid = template.id or str(uuid.uuid4())
        fname = f"{template.name}.json"
        target_path = os.path.join(self.user_dir, fname)

        payload = template.raw_payload or (GraphMapper.to_dict(template.graph) if template.graph else {})
        payload["id"] = tid
        payload["name"] = template.name
        payload["comment"] = template.comment
        payload["author"] = template.author
        payload["category"] = template.category

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        return tid

    def delete_template(self, identifier: str) -> bool:
        target_path = os.path.join(self.user_dir, f"{identifier}.json")
        if os.path.exists(target_path):
            os.remove(target_path)
            return True
        return False
