import json

class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.loc_counter = 0  # Contador para el número de registro

    def add(self, name, var_type, value=None, line=None):
        if name in self.symbols:
            # Si el tipo es diferente, generar error
            if self.symbols[name]['type'] != var_type:
                first_declared_line = self.symbols[name]['line'][0]  # Obtener la primera línea de declaración
                raise Exception(f"Error: Variable '{name}' redeclarada con un tipo diferente en la línea {line}."
                                f"La declaración original fue en la línea {first_declared_line}.")
            else:               
                # Actualizar línea si es el mismo tipo
                if line is not None and line not in self.symbols[name]['line']:  # Asegurarse de que no se repita
                    print(f"Actualizando línea para la variable '{name}': {line}")
                    self.symbols[name]['line'].append(line)
        else:
            print(f"Añadiendo nueva variable '{name}' de tipo '{var_type}' en línea {line}.")
            self.symbols[name] = {
                'type': var_type,
                'value': value,
                'line': [line] if line is not None else [],  # Lista de líneas donde aparece
                'loc': self.loc_counter  # Usar loc_counter como el número de registro
            }
            self.loc_counter += 1  # Incrementar el contador después de añadir una variable


    def get(self, name, line):
        if name in self.symbols:
            return self.symbols[name]
        else:
            raise Exception(f"Error: Variable '{name}' no está declarada antes de su uso en la línea {line}.")

    def update(self, name, value, line=None):
        if name in self.symbols:
            self.symbols[name]['value'] = value
            if line is not None and line not in self.symbols[name]['line']:  # Agregar línea solo si no está ya presente
                self.symbols[name]['line'].append(line)  # Agregar la nueva línea si se proporciona
        else:
            raise Exception(f"Error: Variable '{name}' no está declarada.")

    def __repr__(self):
        return json.dumps(self.symbols, indent=2)

# Cargar las líneas del archivo analisisSyntax.txt
def load_lines_from_file(file_path):
    line_mapping = {}
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split(",")
            if len(parts) != 3:  # Asegurarse de que la línea tiene tres partes
                print(f"Formato incorrecto en la línea: {line.strip()}")
                continue

            try:
                tipo = parts[0].split(":")[1].strip()
                valor = parts[1].split(":")[1].strip()
                linea = int(parts[2].split(":")[1].strip())
                line_mapping[valor] = linea
            except (IndexError, ValueError) as e:
                print(f"Error al procesar la línea: {line.strip()} - {e}")
                continue
    return line_mapping


errors = []

def semantic_check(ast, symbol_table, error_callback, line_mapping):
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
                    semantic_check(child, symbol_table, error_callback, line_mapping)  # Procesar cada hijo del nodo 'main'
                return None
            
            # Manejar declaraciones de variables
            if label in ['integer', 'double', 'char', 'float', 'boolean', 'string']:
                var_type = label
                for var in children:
                    var_name = var['label']
                    line_number = line_mapping.get(var_name, 'desconocida')  # Obtener la línea del archivo
                    symbol_table.add(var_name, var_type, line=line_number)  # Agregar variable con su línea
                return None  # No es necesario devolver un valor ya que estamos declarando variables

            # Asignaciones
            elif label == '=':
                var_name = children[0]['label']
                line_number = line_mapping.get(var_name, 'desconocida')
                
                # Verificar si la variable ha sido declarada antes de usarla
                try:
                    var_info = symbol_table.get(var_name, line_number)
                except Exception as e:
                    error_callback(str(e))
                    return {'type': 'error', 'value': None}

                expr = semantic_check(children[1], symbol_table, error_callback, line_mapping)
                var_type = var_info['type']

                # Verificar la promoción de tipos si es necesario
                if var_type != expr['type']:
                    error_message = f"Error: Incompatibilidad de tipos en asignación para '{var_name}'. Esperado '{var_type}', recibido '{expr['type']}' en la línea {line_number}."
                    error_callback(error_message)

                # Actualizar la tabla de símbolos con el nuevo valor y línea
                symbol_table.update(var_name, expr['value'], line=line_number)
                return {'type': var_type, 'value': expr['value']}

            # Operaciones aritméticas
            elif label in ['+', '-', '*', '/', '%']:
                left = semantic_check(children[0], symbol_table, error_callback, line_mapping)
                right = semantic_check(children[1], symbol_table, error_callback, line_mapping)

                # Verificar tipos en ambos lados
                if left['type'] != right['type']:
                    error_message = f"Error: Incompatibilidad de tipos en operación '{label}' entre '{left['type']}' y '{right['type']}'."
                    print(error_message)
                    error_callback(error_message)
                    return {'type': 'error', 'value': None}

                # Tipo resultante será el mismo que el de los operandos
                return {'type': left['type'], 'value': eval(f"{left['value']} {label} {right['value']}")}

            # Operaciones relacionales y comparaciones
            elif label in ['<', '<=', '>', '>=', '==', '!=']:
                left = semantic_check(children[0], symbol_table, error_callback, line_mapping)
                right = semantic_check(children[1], symbol_table, error_callback, line_mapping)

                # Verificar tipos en ambos lados
                if left['type'] != right['type']:
                    error_message = f"Error: Incompatibilidad de tipos en comparación '{label}' entre '{left['type']}' y '{right['type']}'."
                    print(error_message)
                    error_callback(error_message)
                    return {'type': 'error', 'value': None}

                result_value = eval(f"{left['value']} {label} {right['value']}")
                return {'type': 'boolean', 'value': result_value}

            # Condicionales (if)
            elif label == 'if':
                condition = semantic_check(children[0], symbol_table, error_callback, line_mapping)
                if condition['type'] != 'boolean':
                    error_message = "Error: La condición de la sentencia 'if' debe ser de tipo booleano."
                    print(error_message)
                    error_callback(error_message)
                    return {'type': 'error', 'value': None}

                # Procesar las sentencias dentro del bloque 'if'
                semantic_check(children[1], symbol_table, error_callback, line_mapping)
                if len(children) > 2:  # Procesar bloque 'else' si existe
                    semantic_check(children[2], symbol_table, error_callback, line_mapping)

            # Bucles (while)
            elif label == 'while':
                condition = semantic_check(children[0], symbol_table, error_callback, line_mapping)
                if condition['type'] != 'boolean':
                    error_message = "Error: La condición de la sentencia 'while' debe ser de tipo booleano."
                    print(error_message)
                    error_callback(error_message)
                    return {'type': 'error', 'value': None}

                # Procesar las sentencias dentro del bloque 'while'
                semantic_check(children[1], symbol_table, error_callback, line_mapping)
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
        if label in symbol_table.symbols:
            var_info = symbol_table.get(label, line=None)  # Pass 'None' or a valid line number
            annotated_node['type'] = var_info['type']
            annotated_node['value'] = var_info['value']

        # Si es una operación o asignación
        if label == '=' or label in ['+', '-', '*', '/', '%']:
            expr_type = ast.get('type', 'Desconocido')
            annotated_node['type'] = expr_type
            annotated_node['value'] = ast.get('value', 'Desconocido')

        # Recursión para los hijos
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


def perform_semantic_analysis(ast, output_annotated_file, output_symbol_table_file, line_mapping, error_callback=None):
    symbol_table = SymbolTable()  # Crear una instancia de SymbolTable
    try:
        semantic_check(ast, symbol_table, error_callback, line_mapping)  # Pasar error_callback aquí
        save_annotated_tree(ast, symbol_table, output_annotated_file)
        save_symbol_table(symbol_table, output_symbol_table_file)
    except Exception as e:
        print(e)
        return False

    return True
