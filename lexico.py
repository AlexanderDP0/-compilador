import sys

class Token:
    def __init__(self, token_type, value, line, column):
        self.token_type = token_type
        self.value = value
        self.line = line
        self.column = column

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.current_char = self.text[self.pos]
        self.palabrasC = {'if','else','do','while','switch','case','double','int','float','char','string','main','cin','cout'}
        self.operador_aritmetico = {'+','-','*','/','%','^','++','--'}
        self.operador_relacional= {'<','>','!=','<=','>=','=='}
        self.operador_logico = {'and','or'}
        self.simbolos = {'(',')','{','}','[',']',',',';',':'}
    
    def next(self):
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
            if self.current_char == '\n':
                self.line += 1
                self.column = 0
            else:
                self.column += 1
        else:
            self.current_char = None

    def salto_espacio(self):
        while self.current_char is not None and self.current_char.isspace():
            self.next()

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.salto_espacio()
                continue

            if self.current_char.isdigit():
                return self.tokenize_numero()  # Reconocer números enteros y reales

            if self.current_char.isalpha() or self.current_char == '_':
                return self.tokenize_id()  # Reconocer identificadores y operador logico

            if self.current_char == '/':
                return self.tokenize_comentario()

            if self.current_char in self.operador_aritmetico:
                return self.tokenize_operador_aritmetico()  # Reconocer operadores aritméticos
            
            if self.current_char in self.operador_relacional:
                return self.tokenize_operador_relacional()  # Reconocer operador relacional

            if self.current_char in self.simbolos:
                return self.tokenize_simbolo()  # Reconocer símbolos

            if self.current_char == '=':
                return self.tokenize_asignacion()  # Reconocer asignación

            # Manejar caracteres no válidos y tokens no reconocidos
            if not self.current_char.isalnum() and self.current_char not in ['_', '/', ' ', '\t', '\n']:
                return self.tokenize_wrong()

            # Avanzar al siguiente carácter si no se ha reconocido ningún token
            self.next()

        return Token('EOF', None, self.line, self.column)
    
    def tokenize_numero(self):
        token_start_line = self.line
        token_start_column = self.column
        num = ''
        is_real = False
        has_sign = False  # Variable para indicar si hay un signo antes del número

    # Manejar signo antes del número
        if self.current_char in ['+', '-']:
            num += self.current_char
            self.next()
            has_sign = True

        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char.isdigit():
                num += self.current_char
            elif self.current_char == '.':
                if is_real:
                    # Si ya se encontró un punto decimal, marca como error y sale del bucle
                    return Token('NUMERO', num, token_start_line, token_start_column)
                is_real = True
                num += self.current_char
            self.next()

    # Verificar si hay al menos un dígito después del punto decimal
        if is_real and len(num.split('.')[1]) == 0:
            # Si no hay dígitos después del punto decimal, marca como error
            return Token('ERROR', num, token_start_line, token_start_column)
        else:
        # Devuelve el token dependiendo de si es un número entero o real
            if has_sign:
                return Token('NUMERO', num, token_start_line, token_start_column)
            if is_real:
                return Token('NUMERO', float(num), token_start_line, token_start_column)
            else:
                return Token('NUMERO', int(num), token_start_line, token_start_column)
        
    def tokenize_id(self):
        token_start_line = self.line
        token_start_column = self.column
        result = ''

        # Permitir números después de la primera letra
        while self.current_char is not None and (self.current_char.isalpha() or self.current_char == '_' or (self.current_char.isdigit() and result and result[-1].isalnum())):  
            result += self.current_char
            self.next()

        # Verificar si el resultado es una palabra reservada
        if result.lower() in self.palabrasC:
            return Token('PALABRA_RESERVADA', result, token_start_line, token_start_column)
        else:
            if result.lower() in self.operador_logico:
                return Token('OPERADOR_LOGICO', result, token_start_line, token_start_column)
            # Verificar si el resultado comienza con un dígito, si es así, es un identificador inválido
            elif result[0].isdigit():
                return Token('ERROR', result, token_start_line, token_start_column)
            else:
                return Token('ID', result, token_start_line, token_start_column)

    def tokenize_comentario(self):
        token_start_line = self.line
        token_start_column = self.column
        if self.current_char == '/':
            self.next()
            if self.current_char == '/':
                # Comentario de una línea
                while self.current_char != '\n' and self.current_char is not None:
                    self.next()
                return Token('COMENTARIO', 'Comentario de una línea', token_start_line, token_start_column)
            elif self.current_char == '*':
                # Comentario de varias líneas
                self.next()
                while True:
                    if self.current_char is None:
                        # Manejar comentarios de varias líneas sin cierre
                        return Token('ERROR', 'Comentario de varias líneas sin cerrar', token_start_line, token_start_column)
                    if self.current_char == '*':
                        self.next()
                        if self.current_char == '/':
                            self.next()
                            break
                    else:
                        self.next()
                return Token('COMENTARIO', 'Comentario de varias líneas', token_start_line, token_start_column)
        return Token('OPERADOR_ARITMETICO', '/', token_start_line, token_start_column)

    def tokenize_operador_aritmetico(self):
        token_start_line = self.line
        token_start_column = self.column
        result = self.current_char
        self.next()
        if result in ['+', '-']:
            operator = result
            if self.current_char == result:  # Si el siguiente carácter es el mismo que el actual (+ o -)
                operator += self.current_char
                self.next()
            return Token('OPERADOR_ARITMETICO', operator, token_start_line, token_start_column)
        else:
            while self.current_char is not None and self.current_char in self.operador_aritmetico and result + self.current_char in self.operador_aritmetico:
                result += self.current_char
                self.next()
        return Token('OPERADOR_RELACIONAL', result, token_start_line, token_start_column)

    def tokenize_operador_relacional(self):
        token_start_line = self.line
        token_start_column = self.column
        result = self.current_char
        self.next()
        if self.current_char == '=':  # Si el siguiente carácter es "=", combina el operador relacional
            result += self.current_char
            self.next()
        elif result == '!':
            return Token('ERROR', result, token_start_line, token_start_column)
        return Token('OPERADOR_RELACIONAL', result, token_start_line, token_start_column)
        
    def tokenize_simbolo(self):
        token_start_line = self.line
        token_start_column = self.column
        result = self.current_char
        self.next()
        return Token('SIMBOLO', result, token_start_line, token_start_column)

    def tokenize_asignacion(self):
        token_start_line = self.line
        token_start_column = self.column
        result = self.current_char
        self.next()
        if self.current_char == '=':  # Si el siguiente carácter es "=", combina el operador relacional
            result += self.current_char
            self.next()
            return Token('OPERADOR_RELACIONAL', result, token_start_line, token_start_column)
        else:
            return Token('ASIGNACION', result, token_start_line, token_start_column)

    def tokenize_wrong(self):
        token_start_line = self.line
        token_start_column = self.column
        result = self.current_char
        self.next()
        return Token('ERROR', result, token_start_line, token_start_column)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r') as file:
            text = file.read()
    except FileNotFoundError:
        print(f"File '{input_file}' not found.")
        sys.exit(1)

    lexer = Lexer(text)
    while True:
        token = lexer.get_next_token()
        if token.token_type == 'EOF':
            break
        print(f'{token.token_type}: {token.value} (Line: {token.line}, Column: {token.column})')
