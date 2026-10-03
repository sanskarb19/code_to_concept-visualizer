from visualization.variables import VariableVisualizer
from visualization.loops import LoopVisualizer
from visualization.functions import FunctionVisualizer
from visualization.recursion import RecursionVisualizer
from visualization.lists import ListVisualizer
from visualization.stack import StackVisualizer
from visualization.queue import QueueVisualizer
from visualization.linked_list import LinkedListVisualizer
from visualization.tree import TreeVisualizer
from visualization.graph import GraphVisualizer

CONCEPTS = [
    "Variables & Assignment", "If / Else",
    "For Loop", "While Loop", "Nested Loops",
    "Functions", "Recursion",
    "Lists", "Strings", "Dictionary",
    "Stack", "Queue", "Searching", "Sorting",
    "Linked List", "Tree", "Graph",
]


def get_visualizer(concept):
    if concept in ("Variables & Assignment", "If / Else", "Dictionary",
                   "Strings", "Searching", "Sorting"):
        return VariableVisualizer()
    if concept in ("For Loop", "While Loop", "Nested Loops"):
        return LoopVisualizer()
    if concept == "Functions":
        return FunctionVisualizer()
    if concept == "Recursion":
        return RecursionVisualizer()
    if concept == "Lists":
        return ListVisualizer()
    if concept == "Stack":
        return StackVisualizer()
    if concept == "Queue":
        return QueueVisualizer()
    if concept == "Linked List":
        return LinkedListVisualizer()
    if concept == "Tree":
        return TreeVisualizer()
    if concept == "Graph":
        return GraphVisualizer()
    return VariableVisualizer()
