#!/usr/bin/env python3
"""POC MCP server that returns Mermaid diagrams for Java/Spring code."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


SPRING_ROUTE_ANNOTATIONS = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
    "RequestMapping": "ANY",
}
SPRING_CONTROLLER_ANNOTATIONS = {"RestController", "Controller"}
COMPONENT_ANNOTATIONS = SPRING_CONTROLLER_ANNOTATIONS | {"Component", "Repository", "Service"}
COMPONENT_SUFFIXES = (
    "Controller",
    "Executor",
    "Engine",
    "Mapper",
    "Operator",
    "Reducer",
    "Registry",
    "Repository",
    "Service",
    "ServiceImpl",
    "Support",
    "Validator",
)
COMMON_TYPE_NAMES = {
    "String",
    "Integer",
    "Long",
    "Boolean",
    "Double",
    "Float",
    "Short",
    "Byte",
    "Character",
    "Object",
    "Void",
    "List",
    "Map",
    "Set",
    "Collection",
    "Optional",
    "ResponseEntity",
}


@dataclass
class AnnotationInfo:
    name: str
    values: list[str] = field(default_factory=list)


@dataclass
class FieldInfo:
    name: str
    type_text: str


@dataclass
class CallInfo:
    object_name: str | None
    method_name: str


@dataclass
class MethodInfo:
    name: str
    return_type: str
    parameters: list[str]
    annotations: list[AnnotationInfo]
    local_variables: dict[str, str]
    calls: list[CallInfo]
    line: int


@dataclass
class ClassInfo:
    name: str
    package: str
    kind: str
    file: Path
    annotations: list[AnnotationInfo]
    fields: dict[str, FieldInfo] = field(default_factory=dict)
    methods: dict[str, MethodInfo] = field(default_factory=dict)
    extends: str | None = None
    implements: list[str] = field(default_factory=list)

    @property
    def qualified_name(self) -> str:
        return f"{self.package}.{self.name}" if self.package else self.name


@dataclass
class RouteInfo:
    http_method: str
    path: str
    class_name: str
    method_name: str
    file: Path


@dataclass
class CodeIndex:
    repo: Path
    classes: dict[str, ClassInfo]
    classes_by_qualified_name: dict[str, ClassInfo]
    routes: dict[tuple[str, str], RouteInfo]
    implementations: dict[str, ClassInfo]


@dataclass
class ComponentEdge:
    fields: set[str] = field(default_factory=set)
    calls: set[str] = field(default_factory=set)


def require_dependency(module: str, package: str) -> Any:
    try:
        return __import__(module, fromlist=["*"])
    except ImportError as exc:
        raise RuntimeError(f"Missing dependency {package}. Install with `python3 -m pip install '.[codebomb]'`.") from exc


def text(source: bytes, node: Any | None) -> str:
    if node is None:
        return ""
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def field(node: Any, name: str) -> Any | None:
    try:
        return node.child_by_field_name(name)
    except Exception:
        return None


def descendants(node: Any, *types: str) -> Iterable[Any]:
    stack = list(reversed(node.children))
    wanted = set(types)
    while stack:
        current = stack.pop()
        if not wanted or current.type in wanted:
            yield current
        stack.extend(reversed(current.children))


def direct_child(node: Any, *types: str) -> Any | None:
    for child in node.children:
        if child.type in types:
            return child
    return None


def line_number(node: Any) -> int:
    point = node.start_point
    row = point.row if hasattr(point, "row") else point[0]
    return row + 1


def clean_string_literal(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        return raw[1:-1]
    return raw


def parse_annotations(source: bytes, node: Any) -> list[AnnotationInfo]:
    modifiers = direct_child(node, "modifiers")
    if modifiers is None:
        return []
    result: list[AnnotationInfo] = []
    for annotation in descendants(modifiers, "annotation", "marker_annotation"):
        name_node = field(annotation, "name")
        if name_node is None:
            name_node = direct_child(annotation, "identifier")
        name = text(source, name_node)
        values = [clean_string_literal(text(source, string_node)) for string_node in descendants(annotation, "string_literal")]
        if name:
            result.append(AnnotationInfo(name=name, values=values))
    return result


def parse_package(source: bytes, root: Any) -> str:
    package_node = direct_child(root, "package_declaration")
    if package_node is None:
        return ""
    for child in package_node.children:
        if child.type in {"scoped_identifier", "identifier"}:
            return text(source, child)
    return ""


def parse_field(source: bytes, node: Any) -> list[FieldInfo]:
    type_node = field(node, "type")
    type_text = text(source, type_node).strip()
    fields: list[FieldInfo] = []
    for declarator in descendants(node, "variable_declarator"):
        name_node = field(declarator, "name") or direct_child(declarator, "identifier")
        name = text(source, name_node).strip()
        if name and type_text:
            fields.append(FieldInfo(name=name, type_text=type_text))
    return fields


def parse_method(source: bytes, node: Any) -> MethodInfo | None:
    name_node = field(node, "name")
    if name_node is None:
        name_node = direct_child(node, "identifier")
    name = text(source, name_node).strip()
    if not name:
        return None

    type_node = field(node, "type")
    return_type = text(source, type_node).strip() if type_node is not None else ""
    parameters_node = field(node, "parameters")
    parameters = []
    if parameters_node is not None:
        for parameter in descendants(parameters_node, "formal_parameter"):
            parameters.append(" ".join(text(source, parameter).strip().split()))

    calls: list[CallInfo] = []
    local_variables: dict[str, str] = {}
    body = field(node, "body")
    if body is not None:
        for local_declaration in descendants(body, "local_variable_declaration"):
            for variable in parse_field(source, local_declaration):
                local_variables[variable.name] = variable.type_text
        for call in descendants(body, "method_invocation"):
            name_part = field(call, "name")
            method_name = text(source, name_part).strip()
            object_part = field(call, "object")
            object_name = text(source, object_part).strip() if object_part is not None else None
            if method_name:
                calls.append(CallInfo(object_name=object_name, method_name=method_name))

    return MethodInfo(
        name=name,
        return_type=return_type,
        parameters=parameters,
        annotations=parse_annotations(source, node),
        local_variables=local_variables,
        calls=calls,
        line=line_number(node),
    )


def simple_type(type_text: str) -> str:
    type_text = re.sub(r"<.*>", "", type_text)
    type_text = type_text.replace("[]", "").strip()
    if "." in type_text:
        type_text = type_text.rsplit(".", 1)[-1]
    return type_text


def referenced_types(type_text: str) -> list[str]:
    names = re.findall(r"\b[A-Z][A-Za-z0-9_]*\b", type_text)
    return [name for name in names if name not in COMMON_TYPE_NAMES]


def parse_inheritance(source: bytes, node: Any) -> tuple[str | None, list[str]]:
    extends = None
    implements: list[str] = []
    for child in node.children:
        if child.type == "superclass":
            names = [text(source, item) for item in descendants(child, "type_identifier", "identifier")]
            if names:
                extends = names[-1]
        elif child.type == "super_interfaces":
            implements.extend(text(source, item) for item in descendants(child, "type_identifier", "identifier"))
    return extends, implements


def parse_class(source: bytes, node: Any, package: str, path: Path) -> ClassInfo | None:
    name_node = field(node, "name") or direct_child(node, "identifier")
    name = text(source, name_node).strip()
    if not name:
        return None
    kind = node.type.replace("_declaration", "")
    extends, implements = parse_inheritance(source, node)
    info = ClassInfo(
        name=name,
        package=package,
        kind=kind,
        file=path,
        annotations=parse_annotations(source, node),
        extends=extends,
        implements=implements,
    )
    body = field(node, "body")
    if body is None:
        return info
    for child in body.children:
        if child.type == "field_declaration":
            for field_info in parse_field(source, child):
                info.fields[field_info.name] = field_info
        elif child.type in {"method_declaration", "constructor_declaration"}:
            method = parse_method(source, child)
            if method is not None:
                info.methods[method.name] = method
    return info


def annotation_values(annotations: list[AnnotationInfo], name: str) -> list[str]:
    values: list[str] = []
    for annotation in annotations:
        if annotation.name == name:
            values.extend(annotation.values or [""])
    return values


def normalize_path(path: str) -> str:
    if not path:
        return ""
    path = "/" + path.strip("/")
    return "/" if path == "/" else path


def join_paths(left: str, right: str) -> str:
    combined = "/".join(part.strip("/") for part in [left, right] if part and part != "/")
    return "/" + combined if combined else "/"


def route_annotations(annotations: list[AnnotationInfo]) -> list[tuple[str, list[str]]]:
    routes = []
    for annotation in annotations:
        http_method = SPRING_ROUTE_ANNOTATIONS.get(annotation.name)
        if http_method is None:
            continue
        paths = [normalize_path(value) for value in annotation.values] or [""]
        routes.append((http_method, paths))
    return routes


def build_routes(index: CodeIndex, class_info: ClassInfo) -> None:
    if not any(annotation.name in SPRING_CONTROLLER_ANNOTATIONS for annotation in class_info.annotations):
        return
    class_paths = annotation_values(class_info.annotations, "RequestMapping") or [""]
    class_paths = [normalize_path(path) for path in class_paths]
    for method in class_info.methods.values():
        for http_method, method_paths in route_annotations(method.annotations):
            for class_path in class_paths:
                for method_path in method_paths:
                    route_path = join_paths(class_path, method_path)
                    route = RouteInfo(
                        http_method=http_method,
                        path=route_path,
                        class_name=class_info.name,
                        method_name=method.name,
                        file=class_info.file,
                    )
                    index.routes[(http_method, route_path)] = route
                    if http_method == "ANY":
                        index.routes[("GET", route_path)] = route
                        index.routes[("POST", route_path)] = route


def make_parser() -> Any:
    tree_sitter = require_dependency("tree_sitter", "tree-sitter")
    tree_sitter_java = require_dependency("tree_sitter_java", "tree-sitter-java")
    return tree_sitter.Parser(tree_sitter.Language(tree_sitter_java.language()))


def build_index(repo: Path) -> CodeIndex:
    parser = make_parser()
    src_root = repo / "src" / "main" / "java"
    classes: dict[str, ClassInfo] = {}
    classes_by_qualified_name: dict[str, ClassInfo] = {}
    index = CodeIndex(repo=repo, classes=classes, classes_by_qualified_name=classes_by_qualified_name, routes={}, implementations={})
    for path in sorted(src_root.rglob("*.java")):
        source = path.read_bytes()
        tree = parser.parse(source)
        package = parse_package(source, tree.root_node)
        for node in tree.root_node.children:
            if node.type in {"class_declaration", "interface_declaration", "enum_declaration", "record_declaration"}:
                class_info = parse_class(source, node, package, path)
                if class_info is None:
                    continue
                classes[class_info.name] = class_info
                classes_by_qualified_name[class_info.qualified_name] = class_info
    for class_info in classes.values():
        for interface_name in class_info.implements:
            index.implementations.setdefault(interface_name, class_info)
        if class_info.name.endswith("Impl"):
            index.implementations.setdefault(class_info.name[:-4], class_info)
    for class_info in classes.values():
        build_routes(index, class_info)
    return index


def resolve_class(index: CodeIndex, name: str | None) -> ClassInfo | None:
    if not name:
        return None
    name = simple_type(name)
    class_info = index.classes.get(name) or index.classes_by_qualified_name.get(name)
    if class_info is not None and class_info.kind == "interface":
        return index.implementations.get(class_info.name) or class_info
    return class_info or index.implementations.get(name)


def resolve_call(
    index: CodeIndex,
    class_info: ClassInfo,
    call: CallInfo,
    method: MethodInfo | None = None,
) -> tuple[ClassInfo | None, MethodInfo | None, str]:
    if call.object_name in {None, "this"}:
        target_method = class_info.methods.get(call.method_name)
        if target_method is None:
            return None, None, class_info.name
        return class_info, target_method, class_info.name
    object_name = call.object_name or ""
    if "." in object_name:
        object_name = object_name.split(".")[-1]
    type_text = method.local_variables.get(object_name) if method is not None else None
    field_info = class_info.fields.get(object_name)
    if type_text is None and field_info is not None:
        type_text = field_info.type_text
    target_class = resolve_class(index, type_text or object_name)
    if target_class is None and type_text is not None:
        for type_name in referenced_types(type_text):
            target_class = resolve_class(index, type_name)
            if target_class is not None:
                break
    if target_class is None:
        return None, None, object_name
    return target_class, target_class.methods.get(call.method_name), target_class.name


def method_signature(method: MethodInfo) -> str:
    params = ", ".join(method.parameters)
    suffix = f" {method.return_type}" if method.return_type else ""
    return f"{method.name}({params}){suffix}"


def mermaid_id(name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", name)
    return value or "node"


def source_path(index: CodeIndex, path: Path) -> str:
    try:
        return path.relative_to(index.repo).as_posix()
    except ValueError:
        return str(path)


def find_entry(index: CodeIndex, entry: str) -> tuple[ClassInfo, MethodInfo] | None:
    entry = entry.strip()
    if "#" in entry:
        class_name, method_name = entry.split("#", 1)
        class_info = resolve_class(index, class_name.rsplit(".", 1)[-1])
        if class_info and method_name in class_info.methods:
            return class_info, class_info.methods[method_name]
        return None
    match = re.match(r"^([A-Za-z]+)\s+(.+)$", entry)
    if not match:
        return None
    http_method, path = match.group(1).upper(), normalize_path(match.group(2))
    route = index.routes.get((http_method, path)) or index.routes.get(("ANY", path))
    if route is None:
        return None
    class_info = index.classes.get(route.class_name)
    if class_info is None:
        return None
    method = class_info.methods.get(route.method_name)
    if method is None:
        return None
    return class_info, method


def sequence_diagram(index: CodeIndex, entry: str, max_depth: int = 3) -> dict[str, Any]:
    found = find_entry(index, entry)
    if found is None:
        return {"format": "mermaid", "diagram": "sequenceDiagram\n  Note over Codebomb: entry not found", "source_files": []}
    start_class, start_method = found
    lines = ["sequenceDiagram"]
    files = {start_class.file}
    edges: set[tuple[str, str, str]] = set()

    def visit(class_info: ClassInfo, method: MethodInfo, depth: int, stack: set[tuple[str, str]]) -> None:
        if depth > max_depth:
            return
        key = (class_info.name, method.name)
        if key in stack:
            return
        stack = set(stack)
        stack.add(key)
        for call in method.calls:
            target_class, target_method, label = resolve_call(index, class_info, call, method)
            if target_class is None:
                continue
            target_name = target_class.name if target_class else label
            edge = (class_info.name, target_name, call.method_name)
            if edge not in edges:
                lines.append(f"  {mermaid_id(class_info.name)}->>{mermaid_id(target_name)}: {call.method_name}()")
                edges.add(edge)
            if target_class is not None:
                files.add(target_class.file)
            if target_class is not None and target_method is not None:
                visit(target_class, target_method, depth + 1, stack)

    visit(start_class, start_method, 1, set())
    if len(lines) == 1:
        lines.append(f"  Note over {mermaid_id(start_class.name)}: no outgoing calls found")
    return {
        "format": "mermaid",
        "diagram": "\n".join(lines),
        "source_files": sorted(source_path(index, path) for path in files),
    }


def related_classes(index: CodeIndex, class_info: ClassInfo, max_classes: int) -> list[ClassInfo]:
    result: list[ClassInfo] = [class_info]
    seen = {class_info.name}

    def add(candidate: ClassInfo | None) -> None:
        if candidate is None or candidate.name in seen or len(result) >= max_classes:
            return
        seen.add(candidate.name)
        result.append(candidate)

    if class_info.extends:
        add(resolve_class(index, class_info.extends))
    for interface_name in class_info.implements:
        add(resolve_class(index, interface_name))
    for field_info in class_info.fields.values():
        for type_name in referenced_types(field_info.type_text):
            add(resolve_class(index, type_name))
    for method in class_info.methods.values():
        for call in method.calls:
            target_class, _, _ = resolve_call(index, class_info, call, method)
            add(target_class)
    return result


def class_diagram(index: CodeIndex, target: str, max_classes: int = 20) -> dict[str, Any]:
    class_info = resolve_class(index, target.rsplit(".", 1)[-1])
    if class_info is None:
        return {"format": "mermaid", "diagram": "classDiagram\n  class NotFound", "source_files": []}
    classes = related_classes(index, class_info, max_classes)
    class_names = {item.name for item in classes}
    lines = ["classDiagram"]
    edges: set[str] = set()
    for item in classes:
        lines.append(f"  class {mermaid_id(item.name)} {{")
        for field_info in item.fields.values():
            lines.append(f"    +{field_info.type_text} {field_info.name}")
        for method in item.methods.values():
            lines.append(f"    +{method_signature(method)}")
        lines.append("  }")
        if item.extends and simple_type(item.extends) in class_names:
            edges.add(f"  {mermaid_id(simple_type(item.extends))} <|-- {mermaid_id(item.name)}")
        for interface_name in item.implements:
            if simple_type(interface_name) in class_names:
                edges.add(f"  {mermaid_id(simple_type(interface_name))} <|.. {mermaid_id(item.name)}")
        for field_info in item.fields.values():
            for type_name in referenced_types(field_info.type_text):
                if type_name in class_names:
                    edges.add(f"  {mermaid_id(item.name)} --> {mermaid_id(type_name)} : {field_info.name}")
    lines.extend(sorted(edges))
    return {
        "format": "mermaid",
        "diagram": "\n".join(lines),
        "source_files": sorted(source_path(index, item.file) for item in classes),
    }


def component_name(package: str, scope: str) -> str:
    if package.startswith(scope):
        rest = package[len(scope) :].strip(".")
        if rest:
            return rest.split(".")[0]
    parts = package.split(".")
    return parts[-1] if parts else "default"


def in_scope(class_info: ClassInfo, scope: str) -> bool:
    return class_info.package == scope or class_info.package.startswith(scope + ".")


def is_component_candidate(class_info: ClassInfo) -> bool:
    if class_info.kind not in {"class", "record"}:
        return False
    if any(annotation.name in COMPONENT_ANNOTATIONS for annotation in class_info.annotations):
        return True
    return class_info.name.endswith(COMPONENT_SUFFIXES)


def resolve_field_components(index: CodeIndex, field_info: FieldInfo) -> list[ClassInfo]:
    targets: list[ClassInfo] = []
    seen: set[str] = set()
    for type_name in referenced_types(field_info.type_text):
        target = resolve_class(index, type_name)
        if target is None or target.qualified_name in seen:
            continue
        seen.add(target.qualified_name)
        targets.append(target)
    return targets


def edge_label(edge: ComponentEdge) -> str:
    values = sorted(edge.calls) if edge.calls else sorted(edge.fields)
    shown = values[:3]
    label = ", ".join(shown)
    if len(values) > len(shown):
        label = f"{label}, +{len(values) - len(shown)}"
    return label or "uses"


def mermaid_label(value: str) -> str:
    return value.replace('"', '\\"').replace("|", "/")


def component_diagram(index: CodeIndex, scope: str = "com.cmb.server") -> dict[str, Any]:
    candidates = {
        class_info.qualified_name: class_info
        for class_info in index.classes.values()
        if in_scope(class_info, scope) and is_component_candidate(class_info)
    }
    nodes: dict[str, ClassInfo] = {}
    edges: dict[tuple[str, str], ComponentEdge] = {}
    files: set[Path] = set()

    def add_node(class_info: ClassInfo) -> None:
        if class_info.qualified_name not in candidates:
            return
        nodes[class_info.qualified_name] = class_info
        files.add(class_info.file)

    def add_edge(source: ClassInfo, target: ClassInfo, label: str, kind: str) -> None:
        if source.qualified_name == target.qualified_name:
            return
        if source.qualified_name not in candidates or target.qualified_name not in candidates:
            return
        add_node(source)
        add_node(target)
        edge = edges.setdefault((source.qualified_name, target.qualified_name), ComponentEdge())
        if kind == "call":
            edge.calls.add(label)
        else:
            edge.fields.add(label)

    for class_info in candidates.values():
        if any(annotation.name in SPRING_CONTROLLER_ANNOTATIONS for annotation in class_info.annotations):
            add_node(class_info)
        for field_info in class_info.fields.values():
            for target_class in resolve_field_components(index, field_info):
                add_edge(class_info, target_class, field_info.name, "field")
        for method in class_info.methods.values():
            for call in method.calls:
                target_class, _, _ = resolve_call(index, class_info, call, method)
                if target_class is None:
                    continue
                add_edge(class_info, target_class, call.method_name, "call")

    lines = ["flowchart LR"]
    if not nodes:
        lines.append("  NoComponents[No component calls found]")
    grouped: dict[str, list[ClassInfo]] = {}
    for class_info in nodes.values():
        grouped.setdefault(component_name(class_info.package, scope), []).append(class_info)
    for group_name in sorted(grouped):
        group_id = mermaid_id(f"group_{group_name}")
        lines.append(f'  subgraph {group_id}["{mermaid_label(group_name)}"]')
        for class_info in sorted(grouped[group_name], key=lambda item: item.name):
            lines.append(f'    {mermaid_id(class_info.qualified_name)}["{mermaid_label(class_info.name)}"]')
        lines.append("  end")
    for (source_name, target_name), edge in sorted(edges.items()):
        source = nodes[source_name]
        target = nodes[target_name]
        lines.append(
            f'  {mermaid_id(source.qualified_name)} -->|{mermaid_label(edge_label(edge))}| '
            f"{mermaid_id(target.qualified_name)}"
        )
    return {
        "format": "mermaid",
        "diagram": "\n".join(lines),
        "source_files": sorted(source_path(index, path) for path in files),
    }


def serve(index: CodeIndex) -> None:
    fastmcp_module = require_dependency("mcp.server.fastmcp", "mcp")
    mcp = fastmcp_module.FastMCP(
        "codebomb",
        instructions="Codebomb returns read-only Mermaid diagrams for a local Java/Spring repository.",
    )

    @mcp.tool(name="codebomb.sequence_diagram")
    def mcp_sequence_diagram(entry: str, max_depth: int = 3) -> dict[str, Any]:
        """Return a Mermaid sequence diagram for an API route or Class#method entry."""
        return sequence_diagram(index, entry, max_depth)

    @mcp.tool(name="codebomb.class_diagram")
    def mcp_class_diagram(target: str, max_classes: int = 20) -> dict[str, Any]:
        """Return a Mermaid class diagram centered on a Java class."""
        return class_diagram(index, target, max_classes)

    @mcp.tool(name="codebomb.component_diagram")
    def mcp_component_diagram(scope: str = "com.cmb.server") -> dict[str, Any]:
        """Return a Mermaid component call diagram grouped by package area."""
        return component_diagram(index, scope)

    mcp.run()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the Codebomb Java diagram MCP server.")
    parser.add_argument("--repo", required=True, help="Local Java/Spring repository root.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        print(f"ERROR: repo does not exist: {repo}", file=sys.stderr)
        return 2
    try:
        index = build_index(repo)
        serve(index)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
