from visualization.concepts import CONCEPTS


def get_visualizer(concept):
    if concept in ("Variables & Assignment", "If / Else", "Dictionary",
                   "Strings", "Searching", "Sorting"):
        from visualization.variables import VariableVisualizer
        return VariableVisualizer()
    if concept in ("For Loop", "While Loop", "Nested Loops"):
        from visualization.loops import LoopVisualizer
        return LoopVisualizer()
    if concept == "Functions":
        from visualization.functions import FunctionVisualizer
        return FunctionVisualizer()
    if concept == "Recursion":
        from visualization.recursion import RecursionVisualizer
        return RecursionVisualizer()
    if concept == "Lists":
        from visualization.lists import ListVisualizer
        return ListVisualizer()
    if concept == "Stack":
        from visualization.stack import StackVisualizer
        return StackVisualizer()
    if concept == "Queue":
        from visualization.queue import QueueVisualizer
        return QueueVisualizer()
    if concept == "Linked List":
        from visualization.linked_list import LinkedListVisualizer
        return LinkedListVisualizer()
    if concept == "Tree":
        from visualization.tree import TreeVisualizer
        return TreeVisualizer()
    if concept == "Graph":
        from visualization.graph import GraphVisualizer
        return GraphVisualizer()
    from visualization.variables import VariableVisualizer
    return VariableVisualizer()
