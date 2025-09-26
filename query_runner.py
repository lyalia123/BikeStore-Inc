import psycopg2
import re

class QueryRunner:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host="localhost",
                port=5433,
                database="bikestore",
                user="postgres",
                password="Alpieva2006"
            )
            print(" Успешно подключились к базе данных bikestore")
        except Exception as e:
            print(f" Ошибка подключения к базе данных: {e}")
            exit(1)
    
    def get_queries_from_file(self):
        """Извлекает отдельные запросы из файла queries.sql"""
        try:
            with open('queries.sql', 'r', encoding='utf-8') as file:
                content = file.read()
            
            queries = []
            # Разделяем по номерам запросов
            query_blocks = re.split(r'--\s*\d+\.', content)
            
            for i, block in enumerate(query_blocks[1:], 1):
                lines = block.strip().split('\n')
                
                if not lines:
                    continue
                    
                # Первая строка - описание
                description = lines[0].strip()
                
                # Ищем SQL код (игнорируем комментарии)
                sql_lines = []
                in_sql = False
                
                for line in lines[1:]:
                    line = line.strip()
                    if line.startswith('--') and not in_sql:
                        continue  # Пропускаем комментарии перед SQL
                    if line and not line.startswith('--'):
                        in_sql = True
                        sql_lines.append(line)
                    elif in_sql and line.startswith('--'):
                        break  # Комментарий после SQL - заканчиваем
                
                sql = ' '.join(sql_lines).strip()
                if sql.endswith(';'):
                    sql = sql[:-1]
                
                if sql:
                    queries.append({
                        'number': i,
                        'description': description,
                        'sql': sql
                    })
            
            return queries
        except FileNotFoundError:
            print(" Файл queries.sql не найден!")
            return []
        except Exception as e:
            print(f" Ошибка чтения файла: {e}")
            return []
    
    def format_table(self, results, colnames):
        """Форматирует вывод таблицы"""
        if not results:
            print("📭 Нет данных для отображения")
            return
        
        # Определяем ширину колонок
        col_widths = []
        for i, colname in enumerate(colnames):
            max_width = len(str(colname))
            for row in results:
                cell_str = str(row[i] if row[i] is not None else 'NULL')
                max_width = max(max_width, len(cell_str))
            col_widths.append(min(max_width, 30))  # Ограничиваем максимальную ширину
        
        # Создаем разделитель
        total_width = sum(col_widths) + 3 * (len(col_widths) - 1) + 2
        separator = "┼".join("─" * (w + 2) for w in col_widths)
        separator = "┌" + separator + "┐"
        
        # Заголовок таблицы
        header = "│"
        for i, colname in enumerate(colnames):
            header += f" {str(colname).ljust(col_widths[i])} │"
        print(separator)
        print(header)
        
        # Разделитель заголовка и данных
        separator = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
        print(separator)
        
        # Данные
        for row in results[:20]:  # Ограничиваем вывод 20 строками
            row_str = "│"
            for i, cell in enumerate(row):
                cell_display = str(cell if cell is not None else 'NULL')
                if len(cell_display) > 30:
                    cell_display = cell_display[:27] + "..."
                row_str += f" {cell_display.ljust(col_widths[i])} │"
            print(row_str)
        
        # Нижний разделитель
        separator = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"
        print(separator)
    
    def run_single_query(self, query_info):
        """Выполняет один запрос"""
        print(f"\n{'═' * 80}")
        print(f" Запрос #{query_info['number']}: {query_info['description']}")
        print(f"{'═' * 80}")
        print(f" SQL: {query_info['sql']}")
        print(f"{'═' * 80}")
        
        cur = self.conn.cursor()
        try:
            cur.execute(query_info['sql'])
            
            if query_info['sql'].strip().upper().startswith('SELECT'):
                results = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                
                print(f" Найдено строк: {len(results)}")
                if results:
                    self.format_table(results, colnames)
                
                if len(results) > 20:
                    print(f"ℹ️  Показаны первые 20 строк из {len(results)}")
            else:
                print(f" Запрос выполнен успешно!")
                print(f" Затронуто строк: {cur.rowcount}")
            
            self.conn.commit()
            
        except Exception as e:
            print(f" Ошибка выполнения запроса: {e}")
            self.conn.rollback()
        finally:
            cur.close()
    
    def run_all_queries(self):
        """Выполняет все запросы подряд"""
        queries = self.get_queries_from_file()
        
        if not queries:
            print("Нет запросов для выполнения")
            return
        
        print(f"\n Найдено {len(queries)} запросов. Запускаем выполнение...")
        
        for i, query in enumerate(queries, 1):
            self.run_single_query(query)
            
            if i < len(queries):
                input("\n⏎ Нажмите Enter для перехода к следующему запросу...")
    
    def run_query_by_number(self, query_num):
        """Выполняет конкретный запрос по номеру"""
        queries = self.get_queries_from_file()
        
        for query in queries:
            if query['number'] == int(query_num):
                self.run_single_query(query)
                return True
        
        print(f" Запрос #{query_num} не найден!")
        return False
    
    def show_menu(self):
        """Показывает меню с запросами"""
        queries = self.get_queries_from_file()
        
        if not queries:
            print(" Не удалось загрузить запросы из файла queries.sql")
            return
        
        while True:
            print(" БАЗА ДАННЫХ BIKE STORE - МЕНЮ ЗАПРОСОВ")
            for query in queries:
                print(f"#{query['number']}. {query['description']}")
            
            print("\n" + "─" * 60)
            print("a - Выполнить ВСЕ запросы подряд")
            print(f"1-{len(queries)} - Выполнить конкретный запрос")
            print("q - Выход")
            print("─" * 60)
            
            choice = input(" Ваш выбор: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == 'a':
                self.run_all_queries()
            elif choice.isdigit() and 1 <= int(choice) <= len(queries):
                self.run_query_by_number(choice)
                input("\n⏎ Нажмите Enter чтобы вернуться в меню...")
            else:
                print(" Неверный выбор! Попробуйте снова.")
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    print("Запуск системы управления запросами Bike Store")
    print("Инициализация...")
    
    runner = QueryRunner()
    runner.show_menu()

if __name__ == "__main__":
    main()