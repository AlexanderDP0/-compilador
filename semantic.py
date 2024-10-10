import json

class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def add(self, name, var_type, value=None, line=None, loc=None):
        if name not in self.symbols:
            self.symbols[name] = {
                'type': var_type,
                'value': value,
                'line': line,
                'loc': loc  # Añadir el número de registro
            }
        else:
            raise Exception(f"Error: Variable '{name}' ya está declarada en la línea {line}.")


    def get(self, name):
        if name in self.symbols:
            return self.symbols[name]
        else:
            raise Exception(f"Error: Variable '{name}' no está declarada.")

    def update(self, name, value, line=None):
        if name in self.symbols:
            self.symbols[name]['value'] = value
        else:
            raise Exception(f"Error: Variable '{name}' no está declarada en la línea {line}.")

    def __repr__(self):
        return json.dumps(self.symbols, indent=2)

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
            if label == '=':
                # Verificación de asignación
                var_name = children[0]  # Suponiendo que el primer hijo es el nombre de la variable
                expr = semantic_check(children[1], symbol_table, error_callback)  # Procesa la expresión

                # Obtener tipo de la variable asignada
                var_info = symbol_table.get(var_name)
                if var_info is None:
                    raise Exception(f"Error: Variable '{var_name}' no está definida.")
                var_type = var_info['type']

                if var_type != expr['type']:
                        error_message = f"Error: Incompatibilidad de tipos en asignación para '{var_name}'. Esperado '{var_type}', recibido '{expr['type']}'."
                        print(error_message)
                        error_callback(error_message)

                symbol_table.update(var_name, expr['value'])
                return {'type': var_type, 'value': expr['value']}


            elif label in ['+', '-', '*', '/', '%']:
                # Operaciones aritméticas
                left = semantic_check(children[0], symbol_table, error_callback)
                right = semantic_check(children[1], symbol_table, error_callback)

                if left['type'] != right['type']:
                    error_callback(f"Error: Incompatibilidad de tipos en operación '{label}'.")
                    return {'type': 'error', 'value': None}

                # Tipo resultante será el mismo que el de los operandos
                result_value = eval(f"{left['value']} {label} {right['value']}")
                return {'type': left['type'], 'value': result_value}

            elif label in ['<', '<=', '>', '>=', '==', '!=']:
                # Operaciones relacionales
                left = semantic_check(children[0], symbol_table, error_callback)
                right = semantic_check(children[1], symbol_table, error_callback)

                if left['type'] != right['type']:
                    error_callback(f"Error: Incompatibilidad de tipos en comparación '{label}'.")
                    return {'type': 'error', 'value': None}

                result_value = eval(f"{left['value']} {label} {right['value']}")
                return {'type': 'boolean', 'value': result_value}

            elif label == 'if':
                condition = semantic_check(children[0], symbol_table, error_callback)
                if condition['type'] != 'boolean':
                    error_callback("Error: La condición de la sentencia 'if' debe ser de tipo booleano.")
                    return {'type': 'error', 'value': None}

                semantic_check(children[1], symbol_table, error_callback)  # Verificar sentencias dentro del if
                if len(children) > 2:
                    semantic_check(children[2], symbol_table, error_callback)  # Verificar sentencias dentro del else

            elif label == 'while':
                condition = semantic_check(children[0], symbol_table, error_callback)
                if condition['type'] != 'boolean':
                    error_callback("Error: La condición del 'while' debe ser de tipo booleano.")
                    return {'type': 'error', 'value': None}

                semantic_check(children[1], symbol_table, error_callback)  # Verificar sentencias dentro del while

            elif label == 'do':
                semantic_check(children[0], symbol_table, error_callback)  # Verificar sentencias dentro del do
                condition = semantic_check(children[1], symbol_table, error_callback)
                if condition['type'] != 'boolean':
                    error_callback("Error: La condición del 'do-while' debe ser de tipo booleano.")
                    return {'type': 'error', 'value': None}

            elif label == 'declaracionVariable':
                # Declaración de variables
                var_type = children[0]  # Tipo de variable
                for idx, var in enumerate(children[1:], start=1):  # A partir del segundo elemento
                    var_name = var[1]  # Suponiendo que el nombre de la variable está en el segundo elemento
                    line_number = var[2] if len(var) > 2 else None  # Suponiendo que el número de línea está en el tercer elemento
                    symbol_table.add(var_name, var_type, line=line_number, loc=idx)

        except Exception as e:
            error_message = str(e)
            print(error_message)
            error_callback(error_message)

        # Continuar procesando otros nodos
        for child in children:
            semantic_check(child, symbol_table, error_callback)

    elif isinstance(ast, list):
        for node in ast:
            semantic_check(node, symbol_table, error_callback)


def annotate_tree(ast, symbol_table):
    if isinstance(ast, dict):
        label = ast['label']
        annotated_node = {'label': label, 'children': []}

        if label == 'ID':
            var_info = symbol_table.get(ast['label'])
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
        for name, info in symbol_table.symbols.items():
            line = info['line'] if info['line'] is not None else 'N/A'
            loc = info['loc'] if info['loc'] is not None else 'N/A'
            file.write(f"Nombre de Variable: {name}, Tipo: {info['type']}, Valor: {info['value']}, Número de Registro: {loc}, Números de Línea: {line}\n")


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

