import ply.yacc as yacc
import ply.lex as lex
import json

tokens = (
    'ID', 'NUMBER', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 'POWER',
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'COMMA', 'SEMICOLON',
    'EQUAL', 'LESS', 'LESSEQUAL', 'GREATER', 'GREATEREQUAL', 'DEQUAL', 'NEQUAL',
    'IF', 'ELSE', 'DO', 'WHILE', 'SWITCH', 'CASE', 'INT', 'INTEGER', 'FLOAT', 'CHAR', 'STRING', 'BOOLEAN', 'DOUBLE', 'MAIN', 'CIN', 'COUT',
    'PLUSPLUS', 'MINUSMINUS', 'AND', 'OR', 'END'
)

reserved = {
    'if': 'IF',
    'else': 'ELSE',
    'do': 'DO',
    'while': 'WHILE',
    'switch': 'SWITCH',
    'case': 'CASE',
    'int': 'INT',
    'integer': 'INTEGER',
    'float': 'FLOAT',
    'char': 'CHAR',
    'string': 'STRING',
    'boolean': 'BOOLEAN',
    'double': 'DOUBLE',
    'main': 'MAIN',
    'cin': 'CIN',
    'cout': 'COUT',
    'and': 'AND',
    'or': 'OR',
    'end': 'END'
}

t_PLUSPLUS = r'\+\+'
t_MINUSMINUS = r'\-\-'
t_PLUS = r'\+'
t_MINUS = r'\-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'
t_POWER = r'\^'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_COMMA = r','
t_SEMICOLON = r';'
t_EQUAL = r'='
t_LESS = r'<'
t_LESSEQUAL = r'<='
t_GREATER = r'>'
t_GREATEREQUAL = r'>='
t_DEQUAL = r'=='
t_NEQUAL = r'!='

t_ignore = ' \t'

def t_NUMBER(t):
    r'\d+(\.\d+)?'
    if '.' in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Error léxico en el carácter: '{t.value[0]}' en la línea: {t.lineno}")
    t.lexer.skip(1)

lexer = lex.lex()

precedence = (
    ('right', 'PLUSPLUS', 'MINUSMINUS'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'POWER'),
)

def p_programa(p):
    'programa : MAIN LBRACE listaDeclaracion RBRACE'
    p[0] = {'label': p[1], 'children': p[3]}

def p_listaDeclaracion(p):
    '''listaDeclaracion : listaDeclaracion declaracion
                        | declaracion'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_declaracion(p):
    '''declaracion : declaracionVariable
                   | listaSentencias'''
    p[0] = p[1]

def p_declaracionVariable(p):
    '''declaracionVariable : tipo listaIdentificadores SEMICOLON
                           | tipo ID EQUAL expresion SEMICOLON'''
    if len(p) == 4:
        p[0] = {'label': p[1], 'children': [{'label': id, 'children': []} for id in p[2]]}
    else:
        p[0] = {'label': p[1], 'children': [{'label': p[2], 'children': [p[3], p[4]]}]}

def p_listaIdentificadores(p):
    '''listaIdentificadores : ID
                            | ID COMMA listaIdentificadores'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_tipo(p):
    '''tipo : INT
            | INTEGER
            | FLOAT
            | CHAR
            | STRING
            | BOOLEAN
            | DOUBLE'''
    p[0] = p[1]

def p_listaSentencias(p):
    '''listaSentencias : listaSentencias sentencia
                       | sentencia
                       | empty'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    elif len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = []

def p_sentencia(p):
    '''sentencia : seleccion
                 | iteracion
                 | repeticion
                 | andor
                 | elseif
                 | sentIn
                 | sentOut
                 | asignacion
                 | incremento'''
    p[0] = p[1]

def p_asignacion(p):
    '''asignacion : ID EQUAL sentExpresion
                  | ID DEQUAL sentExpresion'''
    p[0] = {'label': p[2], 'children': [p[1], p[3]]}

def p_incremento(p):
    '''incremento : ID PLUSPLUS SEMICOLON
                  | ID MINUSMINUS SEMICOLON'''
    if p[2] == '++':
        p[0] = {'label': '=', 'children': [p[1],{'label': '+', 'children': [p[1], '1']}]}
    else:
        p[0] = {'label': '=', 'children': [p[1],{'label': '-', 'children': [p[1], '1']}]}

def p_sentExpresion(p):
    '''sentExpresion : expresion SEMICOLON
                     | incremento SEMICOLON
                     | SEMICOLON'''
    if len(p) == 3:
        p[0] = p[1]
    else:
        p[0] = None

def p_seleccion(p):
    '''seleccion : IF expresion LBRACE listaSentencias RBRACE
                 | IF expresion LBRACE listaSentencias RBRACE elseif
                 | IF LPAREN andor RPAREN LBRACE listaSentencias RBRACE
                 | IF LPAREN andor RPAREN LBRACE listaSentencias RBRACE elseif'''
    if len(p) == 6:
        p[0] = {'label': p[1], 'children': [p[2], p[4]]}
    elif len(p) == 7:
        p[0] = {'label': p[1], 'children': [p[2], p[4], p[6]]}
    elif len(p) == 8:
        p[0] = {'label': p[1], 'children': [p[3], p[6]]}
    elif len(p) == 9:
        p[0] = {'label': p[1], 'children': [p[3], p[6], p[8]]}
    else:
        p[0] = {'label': 'if', 'children': [p[2], p[4], p[6], p[8]]}

def p_elseif(p):
    '''elseif : ELSE LBRACE listaSentencias RBRACE'''
    p[0] = {'label': p[1], 'children': p[3]}

def p_andor(p):
    '''andor : expresion AND expresion
             | expresion OR expresion'''
    p[0] = {'label': p[2], 'children': [p[1], p[3]]}

def p_iteracion(p):
    '''iteracion : WHILE expresion
                 | WHILE expresion LBRACE listaSentencias RBRACE'''
    if len(p) == 3:
        p[0] = {'label': p[1], 'children': [p[2]]}
    else:
        p[0] = {'label': p[1], 'children': [p[2], p[4]]}

def p_repeticion(p):
    'repeticion : DO LBRACE listaSentencias RBRACE iteracion'
    p[0] = {'label': p[1], 'children': [p[3], p[5]]}

def p_sentIn(p):
    '''sentIn : CIN ID SEMICOLON'''
    p[0] = {'label': p[1], 'children': [p[2]]}

def p_sentOut(p):
    '''sentOut : COUT expresion SEMICOLON'''
    p[0] = {'label': p[1], 'children': [p[2]]}

def p_expresion(p):
    '''expresion : expresionSimple
                 | expresionSimple relacionOp expresionSimple'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {'label': p[2], 'children': [p[1], p[3]]}

def p_relacionOp(p):
    '''relacionOp : LESS
                  | LESSEQUAL
                  | GREATER
                  | GREATEREQUAL
                  | DEQUAL
                  | NEQUAL'''
    p[0] = p[1]

def p_expresionSimple(p):
    '''expresionSimple : expresionSimple sumaOp termino
                       | termino'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {'label': p[2], 'children': [p[1], p[3]]}

def p_sumaOp(p):
    '''sumaOp : PLUS
              | MINUS'''
    p[0] = p[1]

def p_termino(p):
    '''termino : termino mulOp factor
               | factor'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {'label': p[2], 'children': [p[1], p[3]]}

def p_mulOp(p):
    '''mulOp : TIMES
             | DIVIDE
             | MOD'''
    p[0] = p[1]

def p_factor(p):
    '''factor : factor POWER primario
              | primario'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {'label': p[2], 'children': [p[1], p[3]]}

def p_primario(p):
    '''primario : LPAREN expresion RPAREN
                | ID
                | NUMBER'''
    if len(p) == 2:
        p[0] = {'label': p[1], 'children': []}
    else:
        p[0] = p[2]

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    print(f"Error de sintaxis en '{p.value}' en la línea: {p.lineno}")

parser = yacc.yacc()

def parse(input_text):
    result = parser.parse(input_text)
    if parser.errorok:
        return result, True
    else:
        return None, False
    

def write_token_info(tokens, output_file):
    with open(output_file, 'w') as file:
        for token in tokens:
            file.write(f'Tipo: {token.type}, Valor: {token.value}, Linea: {token.lineno}\n')

def write_ast_info(ast, output_file):
    with open(output_file, 'w') as file:
        if ast is not None:
            json_str = json.dumps(ast, indent=2)
            json_str = json_str.replace('null', 'None') 
            file.write(json_str)
        else:
            file.write("")

def clear_file_content(output_file):
    with open(output_file, 'w') as file:
        file.write("")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        sys.exit(1)

    input_file = sys.argv[1]
    token_output_file = 'analisisSyntax.txt'
    ast_output_file = 'arbol.txt'

    try:
        with open(input_file, 'r') as file:
            text = file.read()
    except FileNotFoundError:
        print(f"Archivo '{input_file}' no encontrado.")
        sys.exit(1)

    lexer.input(text)
    tokens = list(lexer)
    result, no_syntax_error = parse(text)
    
    if no_syntax_error:
        write_token_info(tokens, token_output_file)
        write_ast_info(result, ast_output_file)

    else:
        clear_file_content(token_output_file)
        clear_file_content(ast_output_file)