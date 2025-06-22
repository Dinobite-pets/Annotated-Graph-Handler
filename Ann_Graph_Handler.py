"""
ПРОГРАММА ПОСТРОЕНИЯ АННОТИРОВАННОГО ГРАФА И ОБРАБОТКИ ЕГО АГЕНТ-ФУНКЦИЕЙ
Может быть использована для создания аннотированного графа — «цифровой двойник» 
физической системы (например, CAD-модель), а агент-функция — вычислительный эксперимент
над ней.

ПОДХОД К РЕАЛИЗАЦИИ
Для решения задачи использован ООП, который позволяет:
- инкапсулировать логику обработки графа;
- четко разделить структуры данных и алгоритмы;
- упростить модификацию и расширение кода;
- обеспечить читаемость и соответствие принципам SOLID.

ОСНОВНЫЕ КЛАССЫ:
- Vertex для представления вершин графа;
- Edge для представления рёбер;
- AnnotatedGraph для управления структурой графа;
- AgentFunction для обработки правил агкнт-функции;
- функция чтения/записи файлов;
- main() функция консольного запуска программы.

Пайплайн:
1.Чтение структурированных входных данных (input_file.txt)

2.Считывание параметров графа:
  - количество вершин (NV) и рёбер (NE)
  - данные о рёбрах — пары вершин, которые они соединяют
  - считываются правила агент-функции: сначала для всех вершин, затем для всех рёбер.

3.Инициализируются объекты классов вершин и рёбер с базовыми идентификаторами.

4.Построение структуры графа

5.Связывание рёбер с вершинами: каждое ребро добавляется в списки входящих и исходящих 
рёбер соответствующих вершин.
Создание словарей или других структур для быстрого доступа к вершинам и рёбрам по их ID.

6.Инициализация агент-функции
Создаётся объект класса, который будет выполнять вычисления атрибутов вершин и рёбер 
согласно считанным правилам.
Агент-функция хранит ссылку на граф и методы для обработки правил.

7. Вычисление атрибутов
Итеративный процесс, в котором агент-функция многократно проходит по вершинам и рёбрам,
вычисляя их атрибуты.
Для вершин и рёбер применяются правила (константы, копирование значений, минимумы, 
произведения и т.п.).
Процесс повторяется до тех пор, пока не перестанут появляться новые значения 
(стабилизация).

8.Запись результатов (файл output_file.txt)

Для запуска программы используйте команду терминала: 
<python Ann_Graph_Handler.py input_file.txt output_file.txt>
"""
import sys
from typing import List, Dict, Union, Optional

class Vertex:
    """Класс вершины графа с аннотациями"""
    def __init__(self, id: int):
        self.id = id
        self.attr: Optional[float] = None  # Значение атрибута вершины
        self.rule: Optional[str] = None    # Правило вычисления атрибута
        self.in_edges: List['Edge'] = []   # Входящие рёбра
        self.out_edges: List['Edge'] = []  # Исходящие рёбра

    def add_in_edge(self, edge: 'Edge'):
        """Добавление входящего ребра"""
        self.in_edges.append(edge)

    def add_out_edge(self, edge: 'Edge'):
        """Добавление исходящего ребра"""
        self.out_edges.append(edge)

    def __repr__(self):
        return f"Vertex(id={self.id}, attr={self.attr})"

class Edge:
    """Класс ребра графа с аннотациями"""
    def __init__(self, id: int, source: int, target: int):
        self.id = id
        self.source = source  # ID начальной вершины
        self.target = target  # ID конечной вершины
        self.attr: Optional[float] = None  # Значение атрибута ребра
        self.rule: Optional[str] = None    # Правило вычисления атрибута

    def __repr__(self):
        return f"Edge(id={self.id}, src={self.source}, tgt={self.target}, attr={self.attr})"

class AnnotatedGraph:
    """Класс - конструктор аннотированного графа"""
    def __init__(self):
        self.vertices: List[Vertex] = []  # Список вершин
        self.edges: List[Edge] = []       # Список рёбер
        self.vertex_map: Dict[int, Vertex] = {}  # Словарь для быстрого доступа

    def add_vertex(self, vertex: Vertex):
        """Добавление вершины в граф"""
        self.vertices.append(vertex)
        self.vertex_map[vertex.id] = vertex

    def add_edge(self, edge: Edge):
        """Добавление ребра в граф"""
        self.edges.append(edge)
        # Связываем ребро с вершинами
        if edge.source in self.vertex_map:
            self.vertex_map[edge.source].add_out_edge(edge)
        if edge.target in self.vertex_map:
            self.vertex_map[edge.target].add_in_edge(edge)

    def get_vertex(self, id: int) -> Vertex:
        """Получение вершины по ID"""
        return self.vertex_map[id]

class AgentFunction:
    """Класс для выполнения агент-функций на графе"""
    def __init__(self, graph: AnnotatedGraph):
        self.graph = graph
        self.dependencies = {}  # Зависимости для отслеживания порядка вычислений

    def _parse_rule(self, rule: str) -> Union[float, tuple]:
        """Разбор строки правила на компоненты"""
        try:
            return float(rule)  # Числовое значение
        except ValueError:
            parts = rule.split()
            if len(parts) == 1: # проверяем на '*/min'
                return parts[0]  # Функция '*' или 'min'
            return (parts[0], int(parts[1]) - 1)  # Копирование (v/e + индекс), ' - 1'- номера нидексов приводим в соответствие с внутренней индексацией списков Python, т.е. с '0'.    
    
    def _compute_vertex_attr(self, vertex: Vertex):
        """Вычисление атрибута для вершины"""
        rule = self._parse_rule(vertex.rule)
        
        if isinstance(rule, float):
            vertex.attr = rule  # Непосредственное значение
        
        elif isinstance(rule, tuple) and rule[0] == 'v':
            # Копирование из другой вершины
            src_vertex = self.graph.get_vertex(rule[1])
            if src_vertex.attr is not None:
                vertex.attr = src_vertex.attr
        
        elif isinstance(rule, tuple) and rule[0] == 'e':
            # Копирование из ребра
            src_edge = self.graph.edges[rule[1]]
            if src_edge.attr is not None:
                vertex.attr = src_edge.attr
        
        elif rule == 'min':
            # Минимум из входящих рёбер
            if all(e.attr is not None for e in vertex.in_edges):
                vertex.attr = min(e.attr for e in vertex.in_edges)

    def _compute_edge_attr(self, edge: Edge):
        """Вычисление атрибута для ребра"""
        rule = self._parse_rule(edge.rule)
        
        if isinstance(rule, float):
            edge.attr = rule  # Непосредственное значение
        
        elif isinstance(rule, tuple) and rule[0] == 'v':
            # Копирование из вершины
            src_vertex = self.graph.get_vertex(rule[1])
            if src_vertex.attr is not None:
                edge.attr = src_vertex.attr
        
        elif isinstance(rule, tuple) and rule[0] == 'e':
            # Копирование из ребра
            src_edge = self.graph.edges[rule[1]]
            if src_edge.attr is not None:
                edge.attr = src_edge.attr
        
        elif rule == '*':
            # Произведение: vertex[source] * (произведение входящих рёбер)
            src_vertex = self.graph.get_vertex(edge.source)
            if src_vertex.attr is not None and all(e.attr is not None for e in src_vertex.in_edges):
                product = 1.0
                for e in src_vertex.in_edges:
                    product *= e.attr
                edge.attr = src_vertex.attr * product

    def execute(self):
        """Выполнение агент-функции на графе
           Многопроходный алгоритм для обработки зависимостей:
           - для учита взаимозависимости атрибутов
           - гарантирует корректное вычисление при сложных зависимостях
           - автоматически обрабатывает порядок вычислений"""
        changed = True
        while changed:
            changed = False
            for vertex in self.graph.vertices:
                if vertex.attr is None:
                    prev = vertex.attr
                    self._compute_vertex_attr(vertex)
                    if vertex.attr != prev:
                        changed = True
            
            for edge in self.graph.edges:
                if edge.attr is None:
                    prev = edge.attr
                    self._compute_edge_attr(edge)
                    if edge.attr != prev:
                        changed = True

def read_input_file(filename: str) -> AnnotatedGraph:
    """Чтение входного файла и построение графа"""
    graph = AnnotatedGraph()
    with open(filename, 'r') as f:
        # Чтение количества вершин и рёбер
        nv, ne = map(int, f.readline().split())
        f.readline()  # Пропуск пустой строки
        
        # Добавление вершин
        for i in range(nv):
            graph.add_vertex(Vertex(i))
        
        # Чтение рёбер
        for i in range(ne):
            src, tgt = map(int, f.readline().split())
            # Индексация вершин с 0
            graph.add_edge(Edge(i, src - 1, tgt - 1))
        
        f.readline()  # Пропуск пустой строки
        
        # Чтение правил для вершин
        for i in range(nv):
            rule = f.readline().strip()
            graph.vertices[i].rule = rule
        
        # Чтение правил для рёбер
        for i in range(ne):
            rule = f.readline().strip()
            graph.edges[i].rule = rule
    
    return graph

def write_output_file(filename: str, graph: AnnotatedGraph):
    """Запись результатов в файл"""
    with open(filename, 'w') as f:
        # Запись атрибутов вершин
        for vertex in graph.vertices:
            f.write(f"{vertex.attr}\n")
        
        # Запись атрибутов рёбер
        for edge in graph.edges:
            f.write(f"{edge.attr}\n")

def main():
    """Основная функция программ - вызывается для вызова всего скрипта"""
    if len(sys.argv) != 3:
        print("Используйте команду терминала: python Ann_Graph_Handler.py input_file.txt output_file.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Построение графа из файла
    graph = read_input_file(input_file)
    
    # Применение агент-функции
    agent = AgentFunction(graph)
    agent.execute()
    
    # Сохранение результатов
    write_output_file(output_file, graph)

# Используем переменную __name__ для обеспечения вызова функции main() только при запуске на прямую (через консоль)
# !Скрипт не будет запускаться при его импорте или в ноде IDE! 
if __name__ == "__main__":
    main()