import json

class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.loc_counter = 0  # Contador para el número de registro

    def add(self, name, var_type, value=None, line=None):
        if name in self.symbols:
            # Si el tipo es diferente, generar error
            if self.symbols[name]['type'] != var_type:
                raise Exception(f"Error: Variable '{name}' redeclarada con un tipo diferente en la línea {line}.")
            else:
                # Actualizar línea si es el mismo tipo
                self.symbols[name]['line'].append(line)
        else:
            self.symbols[name] = {
                'type': var_type,
                'value': value,
                'line': [line],  # Lista de líneas donde aparece
                'loc': self.loc_counter  # Usar loc_counter como el número de registro
            }
            self.loc_counter += 1  # Incrementar el contador después de añadir una variable


    def get(self, name):
        if name in self.symbols:
            return self.symbols[name]
        else:
            raise Exception(f"Error: Variable '{name}' no está declarada.")

    def update(self, name, value, line=None):
        if name in self.symbols:
            self.symbols[name]['value'] = value
            if line is not None:
                self.symbols[name]['line'].append(line)  # Agregar la nueva línea si se proporciona
        else:
            raise Exception(f"Error: Variable '{name}' no está declarada.")

    def __repr__(self):
        return json.dumps(self.symbols, indent=2)
    
errors = []

def semantic_check(ast, symbol_table, error_callback):
    if ast is None:
        return None

    print("Processing node:", ast)

    if isinstance(ast, dict):
        label = ast['label']
        children = ast.get('children', [])

        # Asegúrate de que children sea una lista
        if not isinstance(children, list):
            error_message = f"Error: 'children' no es una lista: {children}"
            print(error_message)
            error_callback(error_message)
            return None

        try: 
            if label == 'main':
                print("Entering 'main' function.")
                for child in children:
                    semantic_check(child, symbol_table, error_callback)  # Procesar cada hijo del nodo 'main'
                return None
            
            # Manejar declaraciones de variables
            if label in ['integer', 'double', 'char', 'float', 'boolean', 'string']:
                var_type = label
                for var in children:
                    var_name = var['label']
                    symbol_table.add(var_name, var_type, line=var.get('line'))  # Agregar variable con su línea
                return None  # No es necesario devolver un valor ya que estamos declarando variables

            elif label == '=':
                var_name = children[0]['label']  # Suponiendo que el primer hijo es el nombre de la variable
                expr = semantic_check(children[1], symbol_table, error_callback)  # Procesa la expresión

                var_info = symbol_table.get(var_name)
                var_type = var_info['type']

                if var_type != expr['type']:
                    error_message = f"Error: Incompatibilidad de tipos en asignación para '{var_name}'. Esperado '{var_type}', recibido '{expr['type']}' en la línea {ast.get('line', 'desconocida')}."
                    error_callback(error_message)

                symbol_table.update(var_name, expr['value'], line=ast.get('line'))  # Actualizar variable y agregar línea
                return {'type': var_type, 'value': expr['value']}

            # Otros casos como operaciones aritméticas, if, while...
            elif label in ['+', '-', '*', '/', '%']:
                # Operaciones aritméticas
                left = semantic_check(children[0], symbol_table, error_callback)
                right = semantic_check(children[1], symbol_table, error_callback)

                if left['type'] != right['type']:
                    error_message = f"Error: Incompatibilidad de tipos en operación '{label}'."
                    print(error_message)
                    error_callback(error_message)

                # Tipo resultante será el mismo que el de los operandos
                return {'type': left['type'], 'value': eval(f"{left['value']} {label} {right['value']}")}

            # Operaciones relacionales y condicionales
            elif label in ['<', '<=', '>', '>=', '==', '!=']:
                # Operaciones relacionales
                left = semantic_check(children[0], symbol_table, error_callback)
                right = semantic_check(children[1], symbol_table, error_callback)

                if left['type'] != right['type']:
                    error_message = f"Error: Incompatibilidad de tipos en comparación '{label}'."
                    print(error_message)
                    error_callback(error_message)
                    return {'type': 'error', 'value': None}

                result_value = eval(f"{left['value']} {label} {right['value']}")
                return {'type': 'boolean', 'value': result_value}

            elif label == 'if':
                condition = semantic_check(children[0], symbol_table, error_callback)
                if condition['type'] != 'boolean':
                    error_message = "Error: La condición de la sentencia 'if' debe ser de tipo booleano."
                    print(error_message)
                    error_callback(error_message)
                    return {'type': 'error', 'value': None}

                semantic_check(children[1], symbol_table, error_callback)  # Verificar sentencias dentro del if
                if len(children) > 2:
                    semantic_check(children[2], symbol_table, error_callback)  # Verificar sentencias dentro del else

            elif label == 'while':
                condition = semantic_check(children[0], symbol_table, error_callback)
                if condition['type'] != 'boolean':
                    error_message = "Error: La condición de la sentencia 'while' debe ser de tipo booleano."
                    print(error_message)
                    error_callback(error_message)
                    return {'type': 'error', 'value': None}

                semantic_check(children[1], symbol_table, error_callback)  # Verificar sentencias dentro del while
            else:
                error_message = f"Error: Nodo desconocido '{label}'."
                print(error_message)
                error_callback(error_message)
                return {'type': 'error', 'value': None}

        except Exception as e:
            error_message = str(e)
            errors.append(error_message)
            error_callback(error_message)
            return {'type': 'error', 'value': None}

def error_callback(message):
    print(f"Error encontrado: {message}")
    
def annotate_tree(ast, symbol_table):
    if isinstance(ast, dict):
        label = ast['label']
        annotated_node = {'label': label, 'children': []}

        # Si es un identificador (variable)
        if label in symbol_table.symbols and ast.get('children') is None:
            var_info = symbol_table.get(label)
            annotated_node['type'] = var_info['type']
            annotated_node['value'] = var_info['value']

        for child in ast.get('children', []):
            annotated_node['children'].append(annotate_tree(child, symbol_table))

        return annotated_node

    elif isinstance(ast, list):
        return [annotate_tree(child, symbol_table) for child in ast]

    return ast


def save_annotated_tree(ast, symbol_table, output_file):
    annotated_tree = annotate_tree(ast, symbol_table)
    with open(output_file, 'w') as file:
        json_str = json.dumps(annotated_tree, indent=2)
        file.write(json_str)

def save_symbol_table(symbol_table, output_file):
    with open(output_file, 'w') as file:
        # Escribir los encabezados de la tabla
        file.write(f"{'Nombre de Variable':<20} | {'Tipo':<10} | {'Valor':<10} | {'Registro':<10} | {'Números de Línea':<20}\n")
        file.write("-" * 80 + "\n")

        # Escribir cada entrada de la tabla de símbolos
        for name, info in symbol_table.symbols.items():
            line_numbers = " ".join(map(str, info['line']))
            loc = info['loc'] if info['loc'] is not None else 'N/A'
            value = info['value'] if info['value'] is not None else 'No asignado'
            file.write(f"{name:<20} | {info['type']:<10} | {value:<10} | {loc:<10} | {line_numbers:<20}\n")

def perform_semantic_analysis(ast, output_annotated_file, output_symbol_table_file, error_callback=None):
    symbol_table = SymbolTable()  # Crear una instancia de SymbolTable
    try:
        semantic_check(ast, symbol_table, error_callback)  # Pasar error_callback aquí
        save_annotated_tree(ast, symbol_table, output_annotated_file)
        save_symbol_table(symbol_table, output_symbol_table_file)
    except Exception as e:
        print(e)
        return False

    return True
