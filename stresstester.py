import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
import numpy as np
import re


# ============================================================
# Author: johon0error
# ============================================================

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

            # Обработка чисел (включая отрицательные)
            if char.isdigit() or (char == '-' and (i == 0 or expression[i - 1] in '+-*/( ')):
                num_str = char
                i += 1
                # Собираем число
                while i < n and (expression[i].isdigit() or expression[i] == '.'):
                    num_str += expression[i]
                    i += 1
                try:
                    tokens.append(('NUM', float(num_str)))
                except ValueError:
                    raise ValueError(f"Ошибка преобразования числа: {num_str}")
                continue

            # Обработка операторов и скобок
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
                    if stack and stack[-1] == '(':
                        stack.pop()
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
                if len(stack) < 2:
                    raise ValueError("Недостаточно операндов для операции")
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

        if len(stack) != 1:
            raise ValueError("Некорректное выражение")

        return stack[0]

    def compile(self, expression):
        """Основной метод компиляции и вычисления выражения"""
        try:
            # Очищаем выражение от лишних пробелов
            expression = expression.strip()
            tokens = self.tokenize(expression)
            rpn = self.to_rpn(tokens)
            result = self.evaluate_rpn(rpn)
            return result
        except Exception as e:
            raise ValueError(f"{e}")


# ============================================================
# НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ
# ============================================================

class LoadTester:
    """Класс для нагрузочного тестирования"""

    def __init__(self, compiler):
        self.compiler = compiler
        self.sequential_results = None
        self.parallel_results = []

    def single_request(self, expression, request_id):
        """Выполнение одного запроса"""
        try:
            start_time = time.perf_counter()
            result = self.compiler.compile(expression)
            end_time = time.perf_counter()
            response_time = (end_time - start_time) * 1000  # в миллисекундах
            return {
                'request_id': request_id,
                'success': True,
                'response_time': response_time,
                'result': result
            }
        except Exception as e:
            return {
                'request_id': request_id,
                'success': False,
                'error': str(e),
                'response_time': None
            }

    def sequential_test(self, expressions, iterations=100):
        """Последовательное тестирование"""
        print("\n" + "=" * 70)
        print("📊 ПОСЛЕДОВАТЕЛЬНОЕ ТЕСТИРОВАНИЕ")
        print("=" * 70)

        total_requests = len(expressions) * iterations
        response_times = []
        successes = 0
        errors = 0

        start_time = time.perf_counter()

        for i in range(iterations):
            for expr in expressions:
                result = self.single_request(expr, i)
                if result['success']:
                    successes += 1
                    response_times.append(result['response_time'])
                else:
                    errors += 1

        end_time = time.perf_counter()
        total_time = end_time - start_time

        rps = total_requests / total_time if total_time > 0 else 0

        avg_time = statistics.mean(response_times) if response_times else 0
        median_time = statistics.median(response_times) if response_times else 0
        p95 = np.percentile(response_times, 95) if response_times else 0
        p99 = np.percentile(response_times, 99) if response_times else 0

        print(f"\n📌 РЕЗУЛЬТАТЫ:")
        print(f"   ├─ Всего запросов: {total_requests}")
        print(f"   ├─ Успешных: {successes}")
        print(f"   ├─ Ошибок: {errors}")
        print(f"   ├─ Общее время: {total_time:.3f} сек")
        print(f"   ├─ Среднее время ответа: {avg_time:.3f} мс")
        print(f"   ├─ Медианное время: {median_time:.3f} мс")
        print(f"   ├─ 95-й перцентиль: {p95:.3f} мс")
        print(f"   ├─ 99-й перцентиль: {p99:.3f} мс")
        print(f"   └─ 📈 RPS (запросов/сек): {rps:.2f}")

        self.sequential_results = {
            'rps': rps,
            'avg_response_time': avg_time,
            'median_response_time': median_time,
            'p95': p95,
            'p99': p99,
            'total_requests': total_requests,
            'total_time': total_time,
            'successes': successes,
            'errors': errors
        }

        return self.sequential_results

    def parallel_test(self, expressions, num_parallel, iterations=20):
        """Параллельное тестирование"""
        print(f"\n--- 🔄 Тест с {num_parallel} параллельными запросами ---")

        total_requests = len(expressions) * iterations
        response_times = []
        successes = 0
        errors = 0

        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=num_parallel) as executor:
            futures = []
            for i in range(iterations):
                for expr in expressions:
                    future = executor.submit(self.single_request, expr, i)
                    futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    successes += 1
                    if result['response_time'] is not None:
                        response_times.append(result['response_time'])
                else:
                    errors += 1

        end_time = time.perf_counter()
        total_time = end_time - start_time

        avg_response_time = statistics.mean(response_times) if response_times else 0
        success_rate = (successes / total_requests) * 100 if total_requests > 0 else 0

        print(f"   ├─ Успешных: {successes}/{total_requests} ({success_rate:.1f}%)")
        print(f"   ├─ Ошибок: {errors}")
        print(f"   ├─ Общее время: {total_time:.3f} сек")
        print(f"   └─ Среднее время ответа: {avg_response_time:.3f} мс")

        result = {
            'num_parallel': num_parallel,
            'total_time': total_time,
            'avg_response_time': avg_response_time,
            'success_rate': success_rate,
            'successes': successes,
            'errors': errors,
            'total_requests': total_requests
        }

        self.parallel_results.append(result)
        return result

    def run_full_load_test(self, expressions):
        """Запуск полного нагрузочного тестирования"""
        print("\n" + "🚀" * 35)
        print("НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ")
        print("🚀" * 35)

        self.sequential_test(expressions, iterations=100)

        print("\n" + "=" * 70)
        print("📊 ПАРАЛЛЕЛЬНОЕ ТЕСТИРОВАНИЕ")
        print("=" * 70)

        parallel_counts = [1, 2, 4, 8, 16, 32, 64, 128]

        for count in parallel_counts:
            result = self.parallel_test(expressions, count, iterations=20)

            if result['success_rate'] < 95:
                print(f"\n⚠️ Достигнут предел производительности при {count} параллельных запросах!")
                print(f"   Успешность упала до {result['success_rate']:.1f}%")
                break

        return self.sequential_results, self.parallel_results

    def plot_results(self):
        """Построение графика"""
        if not self.parallel_results:
            print("Нет данных для построения графика")
            return

        x = [r['num_parallel'] for r in self.parallel_results]
        y = [r['avg_response_time'] for r in self.parallel_results]

        plt.figure(figsize=(12, 7))
        plt.plot(x, y, 'b-o', linewidth=2, markersize=10, markerfacecolor='red', markeredgecolor='darkred')
        plt.xscale('log', base=2)

        plt.xlabel('Количество параллельных запросов (логарифмическая шкала, основание 2)', fontsize=14,
                   fontweight='bold')
        plt.ylabel('Среднее время ответа (миллисекунды)', fontsize=14, fontweight='bold')
        plt.title('Зависимость времени ответа от количества параллельных запросов', fontsize=16, fontweight='bold')

        plt.grid(True, alpha=0.3, linestyle='--')
        plt.xticks(x, [str(i) for i in x], fontsize=11)
        plt.yticks(fontsize=11)

        for i, (xi, yi) in enumerate(zip(x, y)):
            plt.annotate(f'{yi:.3f} мс',
                         (xi, yi),
                         textcoords="offset points",
                         xytext=(0, 15),
                         ha='center',
                         fontsize=10,
                         bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))

        plt.tight_layout()
        plt.savefig('load_test_graph.png', dpi=150, bbox_inches='tight')
        print("\n✅ График сохранен как 'load_test_graph.png'")
        plt.show()

    def find_max_parallel_without_failures(self):
        """Определение максимальной нагрузки без сбоев"""
        max_parallel = 0
        for result in self.parallel_results:
            if result['success_rate'] >= 99.5:
                max_parallel = result['num_parallel']
            else:
                break
        return max_parallel

    def print_conclusions(self):
        """Выводы по результатам"""
        print("\n" + "=" * 70)
        print("📋 ВЫВОДЫ ПО РЕЗУЛЬТАТАМ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ")
        print("=" * 70)

        if self.sequential_results:
            print(f"\n1️⃣ Последовательная обработка:")
            print(f"   ✅ Приложение обрабатывает {self.sequential_results['rps']:.2f} запросов в секунду")
            print(f"   📊 Среднее время обработки одного запроса: {self.sequential_results['avg_response_time']:.3f} мс")

        max_parallel = self.find_max_parallel_without_failures()
        print(f"\n2️⃣ Максимальная нагрузка без сбоев:")
        if max_parallel > 0:
            print(f"   ✅ Приложение может обрабатывать до {max_parallel} параллельных запросов без сбоев")
        else:
            print(f"   ⚠️ Приложение не справляется даже с 1 параллельным запросом")

        if self.parallel_results:
            print(f"\n3️⃣ Результаты параллельного тестирования:")
            print(f"   {'Потоков':<10} {'Время ответа (мс)':<20} {'Успешность':<15}")
            print(f"   {'-' * 45}")
            for r in self.parallel_results:
                print(f"   {r['num_parallel']:<10} {r['avg_response_time']:<20.3f} {r['success_rate']:<15.1f}%")

        print("\n" + "=" * 70)


def main():
    """Основная функция"""

    # Исправленные тестовые выражения (без лишних пробелов)
    test_expressions = [
        "2+(-5)*(7-8)",
        "15*(3+2)-10",
        "100/4+25*2",
        "(8+2)*(5-3)/4",
        "10+20*30/5-8",
        "-15+25*2/5",
        "2.5*3.5+4.2/1.2",
        "(10-5)*(8+2)/(3+2)",
        "100-50*2+30/3",
        "(5+5)*(5+5)/10"
    ]

    print("\n")
    print("🔧" * 35)
    print("ЛАБОРАТОРНАЯ РАБОТА №5")
    print("НАГРУЗОЧНОЕ И СТРЕССОВОЕ ТЕСТИРОВАНИЕ")
    print("🔧" * 35)

    print("\n📝 ПРОВЕРКА РАБОТЫ КОМПИЛЯТОРА")
    print("-" * 50)

    compiler = ArithmeticCompiler()

    for expr in test_expressions:
        try:
            start = time.perf_counter()
            result = compiler.compile(expr)
            elapsed = (time.perf_counter() - start) * 1000
            print(f"   ✅ {expr} = {result} ({elapsed:.3f} мс)")
        except Exception as e:
            print(f"   ❌ {expr} - Ошибка: {e}")

    tester = LoadTester(compiler)
    sequential_results, parallel_results = tester.run_full_load_test(test_expressions)

    tester.plot_results()
    tester.print_conclusions()

    print("\n" + "✅" * 35)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("✅" * 35)


if __name__ == "__main__":
    main()