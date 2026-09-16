from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional


@dataclass(slots=True)
class DocumentNode:
    """
    Represents a node in a document hierarchy.

    A node may represent a document, section, subsection,
    paragraph, table, figure, or another structural element.
    """

    node_id: str
    node_type: str
    title: Optional[str] = None
    level: int = 0
    text: Optional[str] = None

    page_start: Optional[int] = None
    page_end: Optional[int] = None

    parent_id: Optional[str] = None

    children: list["DocumentNode"] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def add_child(self, child: "DocumentNode") -> None:
        """Add a child node to this node."""
        child.parent_id = self.node_id
        self.children.append(child)

    @property
    def is_leaf(self) -> bool:
        """Return True when the node has no children."""
        return not self.children

    @property
    def depth(self) -> int:
        """Return the hierarchy depth of this node."""
        return self.level

    def walk(self) -> Iterable["DocumentNode"]:
        """
        Traverse this node and all descendants depth-first.
        """
        yield self

        for child in self.children:
            yield from child.walk()

    def find(self, node_id: str) -> Optional["DocumentNode"]:
        """Find a node by ID."""
        if self.node_id == node_id:
            return self

        for child in self.children:
            result = child.find(node_id)
            if result is not None:
                return result

        return None


@dataclass(slots=True)
class DocumentStructure:
    """
    Represents the complete structural hierarchy of a document.
    """

    document_id: str
    root: DocumentNode

    metadata: dict[str, Any] = field(default_factory=dict)

    def all_nodes(self) -> list[DocumentNode]:
        """Return every node in document order."""
        return list(self.root.walk())

    def sections(self) -> list[DocumentNode]:
        """
        Return nodes representing sections or subsections.
        """
        section_types = {
            "section",
            "subsection",
            "subsubsection",
        }

        return [
            node
            for node in self.root.walk()
            if node.node_type.lower() in section_types
        ]

    def find(self, node_id: str) -> Optional[DocumentNode]:
        """Find a node anywhere in the document."""
        return self.root.find(node_id)


class DocumentStructureBuilder:
    """
    Builds a document hierarchy from a flat collection of nodes.
    """

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id

    def build(
        self,
        nodes: Iterable[DocumentNode],
        *,
        metadata: Optional[dict[str, Any]] = None,
    ) -> DocumentStructure:
        """
        Build a tree from nodes using parent_id relationships.

        Nodes without a parent become children of the root.
        """

        root = DocumentNode(
            node_id=f"{self.document_id}:root",
            node_type="document",
            level=0,
        )

        structure = DocumentStructure(
            document_id=self.document_id,
            root=root,
            metadata=metadata or {},
        )

        node_map: dict[str, DocumentNode] = {
            node.node_id: node
            for node in nodes
        }

        for node in node_map.values():
            node.children = []

        for node in node_map.values():
            if node.parent_id and node.parent_id in node_map:
                node_map[node.parent_id].add_child(node)
            else:
                root.add_child(node)

        return structure