import time


class ArithmeticCompiler:
    """Компилятор простых арифметических выражений"""

    def __init__(self):
        self.operators = {'+': 1, '-': 1, '*': 2, '/': 2}

    def tokenize(self, expression):
        """Разбивает выражение на токены"""
        tokens = []
        i = 0
        n = len(expression)

        while i < n:
            char = expression[i]

            # Пропускаем пробелы
            if char.isspace():
                i += 1
                continue

            # Числа (включая отрицательные числа в начале или после оператора)
            if char.isdigit() or (char == '-' and (i == 0 or expression[i - 1] in '+-*/( ')):
                num_str = char
                i += 1
                while i < n and (expression[i].isdigit() or expression[i] == '.'):
                    num_str += expression[i]
                    i += 1
                tokens.append(('NUM', float(num_str)))
                continue

            # Операторы и скобки
            if char in '+-*/()':
                tokens.append(('OP', char))
                i += 1
                continue

            raise ValueError(f"Неизвестный символ: {char}")

        return tokens

    def to_rpn(self, tokens):
        """Преобразует инфиксную запись в обратную польскую нотацию"""
        output = []
        stack = []

        for token_type, value in tokens:
            if token_type == 'NUM':
                output.append(value)
            elif token_type == 'OP':
                if value == '(':
                    stack.append(value)
                elif value == ')':
                    while stack and stack[-1] != '(':
                        output.append(stack.pop())
                    stack.pop()  # Удаляем '('
                else:
                    while (stack and stack[-1] != '(' and
                           self.operators.get(stack[-1], 0) >= self.operators[value]):
                        output.append(stack.pop())
                    stack.append(value)

        while stack:
            output.append(stack.pop())

        return output

    def evaluate_rpn(self, rpn):
        """Вычисляет значение выражения в обратной польской нотации"""
        stack = []

        for token in rpn:
            if isinstance(token, (int, float)):
                stack.append(token)
            else:
                b = stack.pop()
                a = stack.pop()

                if token == '+':
                    stack.append(a + b)
                elif token == '-':
                    stack.append(a - b)
                elif token == '*':
                    stack.append(a * b)
                elif token == '/':
                    if b == 0:
                        raise ZeroDivisionError("Деление на ноль")
                    stack.append(a / b)

        return stack[0] if stack else 0

    def compile(self, expression):
        """Основной метод компиляции и вычисления выражения"""
        try:
            tokens = self.tokenize(expression)
            rpn = self.to_rpn(tokens)
            result = self.evaluate_rpn(rpn)
            return result
        except Exception as e:
            raise ValueError(f"Ошибка при вычислении выражения '{expression}': {e}")

    def compile_with_time(self, expression):
        """Вычисляет выражение и возвращает результат и время выполнения"""
        start_time = time.time()
        result = self.compile(expression)
        elapsed_time = (time.time() - start_time) * 1000  # в миллисекундах
        return result, elapsed_time


def test_compiler():
    """Тестирование компилятора"""
    compiler = ArithmeticCompiler()

    test_cases = [
        ("2+3", 5),
        ("2 + (-5)*(7-8)", 2 + (-5) * (7 - 8)),  # 2 + (-5)*(-1) = 2 + 5 = 7
        ("10/2", 5),
        ("(1+2)*3", 9),
        ("2.5*2", 5.0),
        ("-5+3", -2),
    ]

    print("Тестирование компилятора:")
    print("-" * 40)

    for expr, expected in test_cases:
        try:
            result, exec_time = compiler.compile_with_time(expr)
            status = "✓" if abs(result - expected) < 0.0001 else "✗"
            print(f"{status} {expr} = {result} (ожидалось: {expected}) - {exec_time:.3f} мс")
        except Exception as e:
            print(f"✗ {expr} - Ошибка: {e}")


if __name__ == "__main__":
    test_compiler()