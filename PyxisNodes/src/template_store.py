# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc
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
# For any question you can visit: https://discord.gg/fsxRESeQZN

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


try:
    from version import PYXIS_VERSION as PYXIS_ENGINE_VERSION
except ImportError:
    PYXIS_ENGINE_VERSION = "1.1.4"
SCHEMA_VERSION = 1
_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_-]+")


class TemplateStoreError(Exception):
    """Controlled error for template storage."""


class TemplateStore:
    """Manages persistent disk storage and serialisation of Pyxis graph templates.

    Provides a dual-directory architecture separating system-provided built-in
    templates from mutable user templates stored in `%APPDATA%/PyxisNodes/templates`.
    Supports atomic file writes, automatic schema migrations, metadata indexing,
    and validation of node graph structures.
    """

    def __init__(
        self,
        templates_dir: str | os.PathLike[str] | None = None,
        aegisub_version: str = "unknown",
        user_templates_dir: str | os.PathLike[str] | None = None,
    ):
        """Initialises the template storage manager with user and system directories.

        Args:
            templates_dir (str | os.PathLike[str] | None, optional): Legacy or
                custom directory for templates. If `user_templates_dir` is not
                specified, this path serves as both user and system storage.
            aegisub_version (str, optional): Running Aegisub version string
                recorded into template metadata. Defaults to "unknown".
            user_templates_dir (str | os.PathLike[str] | None, optional): Explicit
                directory for user-authored templates. Defaults to
                `%APPDATA%/PyxisNodes/templates`.
        """
        if user_templates_dir is not None:
            self.user_templates_dir = Path(user_templates_dir)
            self.system_templates_dir = Path(templates_dir) if templates_dir else Path(__file__).parent / "templates"
        elif templates_dir is not None:
            self.user_templates_dir = Path(templates_dir)
            self.system_templates_dir = Path(templates_dir)
        else:
            appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            self.user_templates_dir = Path(appdata_dir) / "PyxisNodes" / "templates"
            self.system_templates_dir = Path(__file__).parent / "templates"

        self.templates_dir = self.user_templates_dir
        self.aegisub_version = str(aegisub_version or "unknown")

    def ensure_directory(self) -> None:
        """Ensures that the user templates storage directory exists on the filesystem."""
        self.user_templates_dir.mkdir(parents=True, exist_ok=True)

    def save_template(
        self,
        name: str,
        comment: str,
        graph_data: dict[str, Any],
        *,
        template_id: str | None = None,
    ) -> dict[str, Any]:
        """Saves or updates a node graph template atomically to disk.

        Validates the graph topology, sanitises the template name, generates
        rich indexing metadata (node counts, node types, timestamps, host OS,
        Aegisub version), and performs an atomic write via a temporary file. If
        an existing template ID is updated, previously established properties
        such as creation timestamp and favourite status are preserved, and
        the old file is safely unlinked if the filename changed.

        Args:
            name (str): User-facing display name of the template.
            comment (str): Descriptive notes or instructions for the template.
            graph_data (dict[str, Any]): Serialised LiteGraph canvas dictionary
                containing nodes and link topologies.
            template_id (str | None, optional): Unique template identifier. If
                None, a new identifier composed of a timestamp and random hex is
                generated.

        Returns:
            dict[str, Any]: The complete metadata dictionary written with the template.

        Raises:
            TemplateStoreError: If the template name is empty or the graph
                structure is invalid.
        """
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
        """Lists and aggregates all available templates from system and user directories.

        Discovers templates across both system storage and user storage,
        applies on-the-fly schema migrations, extracts metadata summaries
        (node count, node types, favorite flag, system badge), and returns
        a list sorted by `updated_at` in descending order. User templates
        override system templates that share the same template ID.

        Returns:
            list[dict[str, Any]]: A sorted list of template metadata dictionaries.
        """
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
        """Loads and parses a template document by its unique template identifier.

        Resolves the file in user or system directories, validates its JSON
        structure and graph topology, and performs on-the-fly schema migration.

        Args:
            template_id (str): Unique template identifier to search and load.

        Returns:
            dict[str, Any]: Complete template document containing schema version,
                metadata, and the graph definition.

        Raises:
            TemplateStoreError: If the template cannot be found or contains an
                invalid graph structure.
        """
        template_file = self._find_template_file(template_id)
        document = self._read_document(template_file)
        document = self._migrate_document(document)
        graph = document.get("graph")
        if not isinstance(graph, dict):
            raise TemplateStoreError("Template does not contain a valid graph")
        self._validate_graph(graph)
        return document

    def toggle_favorite(self, template_id: str) -> bool:
        """Toggles the favourite bookmark flag of a template.

        If the template is currently in system storage, saving the toggled state
        automatically copies and persists the modified template document into
        the user templates directory.

        Args:
            template_id (str): Unique identifier of the template to update.

        Returns:
            bool: The new favourite status (True if marked as favourite, False otherwise).

        Raises:
            TemplateStoreError: If the template cannot be located or written.
        """
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
        """Upgrades legacy template documents to the current schema version.

        Backfills missing metadata attributes such as `node_count`, `node_types`,
        and `is_favorite` for older templates created prior to schema v1.

        Args:
            document (dict[str, Any]): Raw loaded template document.

        Returns:
            dict[str, Any]: Migrated template document matching `SCHEMA_VERSION`.
        """
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
        """Deletes a user-created template file from disk.

        Enforces security checks ensuring that built-in system templates
        cannot be deleted or altered by the user.

        Args:
            template_id (str): Unique identifier of the user template to remove.

        Raises:
            TemplateStoreError: If the template is built-in or cannot be unlinked.
        """
        template_file = self._find_template_file(template_id)
        if self._is_in_user_dir(template_file):
            template_file.unlink()
        else:
            raise TemplateStoreError("Cannot delete built-in system templates")

    def _is_in_user_dir(self, file_path: Path) -> bool:
        """Validates that a resolved file path resides strictly inside user_templates_dir.

        Guards against directory traversal attacks and prevents inadvertent
        modifications to system directories.

        Args:
            file_path (Path): Path to check.

        Returns:
            bool: True if `file_path` is a subdirectory/child of `user_templates_dir`.
        """
        try:
            file_path.resolve().relative_to(self.user_templates_dir.resolve())
            return True
        except ValueError:
            return False

    def _find_template_file(self, template_id: str) -> Path:
        """Locates the template file associated with a given template identifier.

        Searches recursively within user storage first, falling back to system
        storage if not found in user templates.

        Args:
            template_id (str): Unique template identifier to search for.

        Returns:
            Path: Filesystem path to the matching template JSON file.

        Raises:
            TemplateStoreError: If the identifier is invalid or no matching template
                file exists.
        """
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
        """Writes a template document atomically to disk with explicit fsync flush.

        Saves to a hidden temporary sibling file (`.<target_file>.tmp`), flushes
        buffers, issues `os.fsync` to guarantee physical disk persistence, and
        atomically replaces the destination path using `os.replace`.

        Args:
            target_file (Path): Final target path on the filesystem.
            document (dict[str, Any]): Serialised template document.

        Raises:
            TemplateStoreError: If writing or disk flushing fails.
        """
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
        """Reads and deserialises a JSON template file using UTF-8 encoding.

        Args:
            template_file (Path): Filesystem path to the template file.

        Returns:
            dict[str, Any]: Parsed JSON dictionary.

        Raises:
            TemplateStoreError: If file I/O fails or the document is not a JSON object.
        """
        with template_file.open("r", encoding="utf-8") as file_handle:
            document = json.load(file_handle)
        if not isinstance(document, dict):
            raise TemplateStoreError("Invalid template format")
        return document

    @staticmethod
    def _validate_graph(graph_data: Any) -> None:
        """Validates that a node graph structure complies with LiteGraph invariants.

        Args:
            graph_data (Any): Arbitrary object to validate as a graph.

        Raises:
            TemplateStoreError: If the graph is not a dictionary, contains no
                nodes, or contains malformed link definitions.
        """
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
        """Sanitises a user-provided template name into a safe filesystem string.

        Strips reserved path characters (`<>:"/\\|?*`), control codes, and
        leading/trailing punctuation, truncating to a maximum of 80 characters.

        Args:
            name (str): Raw template name.

        Returns:
            str: Filesystem-safe slugified string.
        """
        clean_name = re.sub(r'[<>:"/\\|?*\x00-\x1f\s]+', "_", str(name or "").strip())
        return clean_name.strip("._-")[:80]

    @staticmethod
    def _node_types(graph_data: dict[str, Any]) -> list[str]:
        """Extracts a sorted list of unique node types present in a graph.

        Args:
            graph_data (dict[str, Any]): Graph structure containing nodes.

        Returns:
            list[str]: Sorted list of unique node type strings.
        """
        node_types = {
            str(node.get("type"))
            for node in graph_data.get("nodes", [])
            if isinstance(node, dict) and node.get("type")
        }
        return sorted(node_types)

    @staticmethod
    def _os_description() -> str:
        """Generates a human-readable platform description string.

        Returns:
            str: Formatted operating system, release, and architecture description.
        """
        return f"{platform.system()} {platform.release()} ({platform.machine()})"
