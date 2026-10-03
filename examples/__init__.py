EXAMPLES = {
    "Variables & Assignment": """x = 10
y = 20
sum = x + y
print("Sum:", sum)
""",

    "For Loop": """total = 0
for i in range(5):
    total = total + i
    print("i =", i, "total =", total)
print("Done:", total)
""",

    "While Loop": """n = 5
fact = 1
while n > 1:
    fact = fact * n
    n = n - 1
print("5! =", fact)
""",

    "If / Else": """score = 78
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"
print("Grade:", grade)
""",

    "Functions": """def add(a, b):
    return a + b

def mul(a, b):
    return a * b

x = add(5, 10)
y = mul(x, 2)
print(x, y)
""",

    "Recursion": """def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(4)
print("4! =", result)
""",

    "Lists": """numbers = [5, 2, 9, 1, 7]
for i in range(len(numbers)):
    if numbers[i] % 2 == 0:
        numbers[i] = numbers[i] * 10
print(numbers)
""",

    "Stack": """stack = []
stack.append(1)
stack.append(2)
stack.append(3)
top = stack.pop()
print("popped:", top)
""",

    "Queue": """queue = []
queue.append("a")
queue.append("b")
queue.append("c")
front = queue.pop(0)
print("served:", front)
""",

    "Dictionary": """ages = {}
ages["alice"] = 30
ages["bob"] = 25
for name in ages:
    print(name, ages[name])
""",
}


def get_example(concept: str) -> str:
    return EXAMPLES.get(concept, EXAMPLES["Variables & Assignment"])