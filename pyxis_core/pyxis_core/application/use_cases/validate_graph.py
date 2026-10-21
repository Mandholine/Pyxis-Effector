# -*- coding: utf-8 -*-
# Pyxis Effector — Application Use Cases (Validate Graph)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from ..dtos.validate_dto import ValidateGraphRequestDTO, ValidationResultDTO
from ..mappers.graph_mapper import GraphMapper


class ValidateGraphUseCase:
    """Use case to validate node graph syntax, connections, and circular loops."""

    def execute(self, request: ValidateGraphRequestDTO) -> ValidationResultDTO:
        try:
            node_graph = GraphMapper.to_domain(request.graph)
            graph_dict = GraphMapper.to_dict(node_graph)

            from ...infrastructure.engine.node_validator import NodeValidator

            # Validate structure
            errors = []
            warnings = []

            # Check nodes exist
            if not graph_dict.get("nodes"):
                return ValidationResultDTO(valid=False, errors=["El grafo no contiene ningún nodo."])

            # Use internal validator if available
            validator = NodeValidator(graph_dict)
            if hasattr(validator, "validate"):
                result = validator.validate()
                if isinstance(result, dict):
                    errors.extend(result.get("errors", []))
                    warnings.extend(result.get("warnings", []))
                elif isinstance(result, tuple):
                    is_valid, errs = result
                    if not is_valid:
                        errors.extend(errs if isinstance(errs, list) else [str(errs)])

            return ValidationResultDTO(
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
            )
        except Exception as e:
            return ValidationResultDTO(
                valid=False,
                errors=[f"Error durante la validación del grafo: {str(e)}"],
                warnings=[],
            )
