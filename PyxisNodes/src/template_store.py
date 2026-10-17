# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc and Pyxis Effector contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any question you can visit: https://discord.gg/rYsARc3fB9

"""Persistent storage for Pyxis Engine 1.1.4 templates."""

from __future__ import annotations

import json
import os
import platform
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PYXIS_ENGINE_VERSION = "1.1.4"
SCHEMA_VERSION = 1
_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_-]+")


class TemplateStoreError(Exception):
    """Controlled error for template storage."""


class TemplateStore:
    def __init__(
        self,
        templates_dir: str | os.PathLike[str] | None = None,
        aegisub_version: str = "unknown",
        user_templates_dir: str | os.PathLike[str] | None = None,
    ):
        if user_templates_dir is not None:
            self.user_templates_dir = Path(user_templates_dir)
            self.system_templates_dir = Path(templates_dir) if templates_dir else Path(__file__).parent / "templates"
        elif templates_dir is not None:
            self.user_templates_dir = Path(templates_dir)
            self.system_templates_dir = Path(templates_dir)
        else:
            try:
                from paths import get_user_data_dir
                base_dir = get_user_data_dir()
            except Exception:
                base_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
                base_dir = os.path.join(base_dir, "PyxisNodes")
            self.user_templates_dir = Path(base_dir) / "templates"
            self.system_templates_dir = Path(__file__).parent / "templates"

        self.templates_dir = self.user_templates_dir
        self.aegisub_version = str(aegisub_version or "unknown")

    def ensure_directory(self) -> None:
        self.user_templates_dir.mkdir(parents=True, exist_ok=True)

    def save_template(
        self,
        name: str,
        comment: str,
        graph_data: dict[str, Any],
        *,
        template_id: str | None = None,
    ) -> dict[str, Any]:
        self._validate_graph(graph_data)
        raw_name = str(name or "").strip()
        if not raw_name:
            raise TemplateStoreError("Template name cannot be empty")
        clean_name = self._clean_name(raw_name) or "template"

        self.ensure_directory()
        now = datetime.now(timezone.utc).astimezone()
        timestamp = now.strftime("%Y%m%d_%H%M%S")

        existing_file = None
        created_at = now.isoformat(timespec="seconds")
        is_favorite = False
        existing_comment = ""

        if template_id:
            try:
                existing_file = self._find_template_file(template_id)
                existing_doc = self._read_document(existing_file)
                existing_meta = existing_doc.get("metadata", {})
                created_at = existing_meta.get("created_at", created_at)
                is_favorite = existing_meta.get("is_favorite", False)
                existing_comment = existing_meta.get("comment", "")
            except TemplateStoreError:
                existing_file = None

        template_id = template_id or f"{timestamp}_{uuid.uuid4().hex[:8]}"
        file_name = f"{timestamp}_{clean_name}_{template_id[-8:]}.json"
        template_file = self.user_templates_dir / file_name

        final_comment = str(comment).strip() if (comment is not None and str(comment).strip() != "") else existing_comment

        metadata = {
            "template_id": template_id,
            "name": str(name).strip(),
            "comment": final_comment,
            "created_at": created_at,
            "updated_at": now.isoformat(timespec="seconds"),
            "aegisub_version": self.aegisub_version,
            "os": self._os_description(),
            "pyxis_engine_version": PYXIS_ENGINE_VERSION,
            "node_count": len(graph_data.get("nodes", [])),
            "node_types": self._node_types(graph_data),
            "is_favorite": is_favorite,
        }
        document = {
            "schema_version": SCHEMA_VERSION,
            "metadata": metadata,
            "graph": graph_data,
        }

        self._write_document(template_file, document)

        if existing_file and existing_file.exists():
            try:
                if existing_file.resolve() != template_file.resolve() and self._is_in_user_dir(existing_file):
                    existing_file.unlink()
            except OSError:
                pass

        return metadata

    def list_templates(self) -> list[dict[str, Any]]:
        templates_map: dict[str, dict[str, Any]] = {}

        if self.system_templates_dir.exists() and self.system_templates_dir != self.user_templates_dir:
            for template_file in self.system_templates_dir.rglob("*.json"):
                if not template_file.is_file() or template_file.name.startswith("."):
                    continue
                try:
                    document = self._read_document(template_file)
                    document = self._migrate_document(document)
                    metadata = document.get("metadata", {})
                    graph = document.get("graph", {})
                    t_id = metadata.get("template_id")
                    if not t_id:
                        continue
                    meta_copy = dict(metadata)
                    meta_copy.setdefault("node_count", len(graph.get("nodes", [])))
                    meta_copy.setdefault("node_types", self._node_types(graph))
                    meta_copy.setdefault("is_favorite", False)
                    meta_copy["file_name"] = template_file.name
                    meta_copy["is_system"] = True
                    templates_map[t_id] = meta_copy
                except (OSError, ValueError, TemplateStoreError):
                    continue

        if self.user_templates_dir.exists():
            for template_file in self.user_templates_dir.rglob("*.json"):
                if not template_file.is_file() or template_file.name.startswith("."):
                    continue
                try:
                    document = self._read_document(template_file)
                    document = self._migrate_document(document)
                    metadata = document.get("metadata", {})
                    graph = document.get("graph", {})
                    t_id = metadata.get("template_id")
                    if not t_id:
                        continue
                    meta_copy = dict(metadata)
                    meta_copy.setdefault("node_count", len(graph.get("nodes", [])))
                    meta_copy.setdefault("node_types", self._node_types(graph))
                    meta_copy.setdefault("is_favorite", False)
                    meta_copy["file_name"] = template_file.name
                    meta_copy["is_system"] = False
                    templates_map[t_id] = meta_copy
                except (OSError, ValueError, TemplateStoreError):
                    continue

        templates = list(templates_map.values())
        return sorted(
            templates,
            key=lambda item: item.get("updated_at", ""),
            reverse=True,
        )

    def load_template(self, template_id: str) -> dict[str, Any]:
        template_file = self._find_template_file(template_id)
        document = self._read_document(template_file)
        document = self._migrate_document(document)
        graph = document.get("graph")
        if not isinstance(graph, dict):
            raise TemplateStoreError("Template does not contain a valid graph")
        self._validate_graph(graph)
        return document

    def toggle_favorite(self, template_id: str) -> bool:
        template_file = self._find_template_file(template_id)
        document = self._read_document(template_file)
        document = self._migrate_document(document)
        metadata = document.setdefault("metadata", {})
        new_fav = not metadata.get("is_favorite", False)
        metadata["is_favorite"] = new_fav
        metadata["updated_at"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        
        target_file = self.user_templates_dir / template_file.name
        self._write_document(target_file, document)
        return new_fav

    def _migrate_document(self, document: dict[str, Any]) -> dict[str, Any]:
        schema = document.get("schema_version", 0)
        if schema < SCHEMA_VERSION:
            metadata = document.setdefault("metadata", {})
            graph = document.setdefault("graph", {"nodes": []})
            if "node_count" not in metadata:
                metadata["node_count"] = len(graph.get("nodes", []))
            if "node_types" not in metadata:
                metadata["node_types"] = self._node_types(graph)
            if "is_favorite" not in metadata:
                metadata["is_favorite"] = False
            document["schema_version"] = SCHEMA_VERSION
        return document

    def delete_template(self, template_id: str) -> None:
        template_file = self._find_template_file(template_id)
        if self._is_in_user_dir(template_file):
            template_file.unlink()
        else:
            raise TemplateStoreError("Cannot delete built-in system templates")

    def _is_in_user_dir(self, file_path: Path) -> bool:
        try:
            file_path.resolve().relative_to(self.user_templates_dir.resolve())
            return True
        except ValueError:
            return False

    def _find_template_file(self, template_id: str) -> Path:
        if not template_id or Path(template_id).name != template_id:
            raise TemplateStoreError("Invalid template identifier")

        if self.user_templates_dir.exists():
            for template_file in self.user_templates_dir.rglob("*.json"):
                if not template_file.is_file() or template_file.name.startswith("."):
                    continue
                try:
                    document = self._read_document(template_file)
                except (OSError, ValueError, TemplateStoreError):
                    continue
                if document.get("metadata", {}).get("template_id") == template_id:
                    return template_file

        if self.system_templates_dir.exists() and self.system_templates_dir != self.user_templates_dir:
            for template_file in self.system_templates_dir.rglob("*.json"):
                if not template_file.is_file() or template_file.name.startswith("."):
                    continue
                try:
                    document = self._read_document(template_file)
                except (OSError, ValueError, TemplateStoreError):
                    continue
                if document.get("metadata", {}).get("template_id") == template_id:
                    return template_file

        raise TemplateStoreError("Template not found")

    def _write_document(self, target_file: Path, document: dict[str, Any]) -> None:
        self.ensure_directory()
        tmp_file = target_file.parent / f".{target_file.name}.tmp"
        try:
            with tmp_file.open("w", encoding="utf-8", newline="\n") as file_handle:
                json.dump(document, file_handle, ensure_ascii=False, indent=2)
                file_handle.write("\n")
                file_handle.flush()
                os.fsync(file_handle.fileno())
            os.replace(tmp_file, target_file)
        except Exception as error:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except OSError:
                    pass
            raise TemplateStoreError(f"Could not save template: {error}") from error

    @staticmethod
    def _read_document(template_file: Path) -> dict[str, Any]:
        with template_file.open("r", encoding="utf-8") as file_handle:
            document = json.load(file_handle)
        if not isinstance(document, dict):
            raise TemplateStoreError("Invalid template format")
        return document

    @staticmethod
    def _validate_graph(graph_data: Any) -> None:
        if not isinstance(graph_data, dict):
            raise TemplateStoreError("Graph must be a JSON object")
        if not isinstance(graph_data.get("nodes"), list):
            raise TemplateStoreError("Graph must contain a list of nodes")
        if len(graph_data.get("nodes", [])) == 0:
            raise TemplateStoreError("Graph contains no nodes (it is empty)")
        if "links" in graph_data and not isinstance(graph_data["links"], list):
            raise TemplateStoreError("Graph links must be a list")

    @staticmethod
    def _clean_name(name: str) -> str:
        clean_name = re.sub(r'[<>:"/\\|?*\x00-\x1f\s]+', "_", str(name or "").strip())
        return clean_name.strip("._-")[:80]

    @staticmethod
    def _node_types(graph_data: dict[str, Any]) -> list[str]:
        node_types = {
            str(node.get("type"))
            for node in graph_data.get("nodes", [])
            if isinstance(node, dict) and node.get("type")
        }
        return sorted(node_types)

    @staticmethod
    def _os_description() -> str:
        return f"{platform.system()} {platform.release()} ({platform.machine()})"
