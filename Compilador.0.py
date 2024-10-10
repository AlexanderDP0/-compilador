import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, PhotoImage
from ply import lex, yacc
import pyautogui
from PIL import Image, ImageTk
from lexico import Lexer 
import json
import semantic


#Botones
array_strings = ["Abrir", "Guardar", "Guardar como...", "Cerrar", "Tabla Hash","Analizador Lexico", "Analizador Sintactico", "Analizador Semantico", "Codigo Intermedio", "Ejecucion"]

ruta_actual=""

# Funciones para manejar archivos
# Variable global para contar el número de documentos guardados
num_documento = 1

def guardar_archivo_como(text_area, nombre_por_defecto="documento"):
    global num_documento
    try:
        # Generar el nombre por defecto con el número de documento
        nombre_completo = f"{nombre_por_defecto}{num_documento}.txt"
        archivo = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=nombre_completo, filetypes=[("Archivos de Texto", ".txt"), ("Todos los archivos", ".*")])
        if archivo:
            with open(archivo, "w") as file:
                contenido = text_area.get("1.0", tk.END)
                file.write(contenido)
                ruta_actual = archivo
                # Incrementar el número de documento para el próximo archivo
                num_documento += 1
    except Exception as e:
        print(f"Error al guardar el archivo: {e}")



def guardar_archivo(text_area):
    global ruta_actual
    if ruta_actual:
        try:
            with open(ruta_actual, "w") as archivo:
                contenido = text_area.get("1.0", tk.END)
                archivo.write(contenido)
        except Exception as e:
            print(f"Error al guardar el archivo: {e}")
    else:
        guardar_archivo_como(text_area)


def cerrar_archivo(text_area):
    global ruta_actual
    text_area.delete("1.0", tk.END)
    ruta_actual = ""  # Establecer la ruta_actual como una cadena vacía al cerrar el archivo


# Crear la interfaz gráfica
class EditorCompilador:
    
    def __init__(self, root):
        # Crear un estilo personalizado para el Treeview
        style = ttk.Style()
        style.configure("Custom.Treeview", background="white", foreground="black", font=("Arial", 10))


        self.root = root
        self.root.title("Editor y Compilador")
        self.root.geometry("800x600")  # Tamaño inicial
       
         # Dividir la ventana en tres secciones con PanedWindow
        self.paned_window_top = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window_top.pack(expand=True, fill="both")

        # Área de número
        self.num_area = tk.Text(self.paned_window_top, width=4, padx=4, takefocus=0, border=0, background="lightgrey", state="disabled")
        self.paned_window_top.add(self.num_area)
 
       # Área de texto para mostrar archivos/editar
        self.text_area = scrolledtext.ScrolledText(self.paned_window_top, wrap=tk.WORD)
        self.text_area.config(wrap='none')  # Desactivar el ajuste automático de líneas
        self.paned_window_top.add(self.text_area)

        # Crear la barra de desplazamiento vertical antes de usarla en self.text_area
        self.scroll_y = tk.Scrollbar(self.paned_window_top, orient=tk.VERTICAL)
        
        # Configurar la barra de desplazamiento vertical
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.configure(yscrollcommand=self.scroll_y.set)
        self.num_area.configure(yscrollcommand=self.scroll_y.set)

        # Crear la barra de desplazamiento horizontal antes de usarla en self.text_area
        self.scroll_x = tk.Scrollbar(self.root, orient=tk.HORIZONTAL)
        
        # Configurar la barra de desplazamiento horizontal
        self.scroll_x.pack(side=tk.TOP, fill=tk.X)
        self.scroll_x.config(command=self.text_area.xview)
        self.text_area.configure(xscrollcommand=self.scroll_x.set)

        # Área para mostrar resultados del análisis con pestañas
        self.notebook_result = ttk.Notebook(self.paned_window_top)
        self.paned_window_top.add(self.notebook_result)

        self.lexical_frame = tk.Frame(self.notebook_result)
        self.notebook_result.add(self.lexical_frame, text="Resultados Lexicos")
        self.result_area = scrolledtext.ScrolledText(self.lexical_frame, wrap=tk.WORD)
        self.result_area.pack(expand=True, fill="both")
        
        self.syntax_frame = tk.Frame(self.notebook_result)
        self.notebook_result.add(self.syntax_frame, text="Resultados Sintácticos")
        self.syntax_area = scrolledtext.ScrolledText(self.syntax_frame, wrap=tk.WORD)
        self.syntax_area.pack(expand=True, fill="both")
        
        self.arbol_frame = tk.Frame(self.notebook_result)
        self.notebook_result.add(self.arbol_frame, text="Árbol Sintáctico")
        self.arbol_area = ttk.Treeview(self.arbol_frame)
        self.arbol_area.pack(expand=True, fill="both")

        self.arbol_anotaciones_frame = tk.Frame(self.notebook_result)
        self.notebook_result.add(self.arbol_anotaciones_frame, text="Árbol Sintáctico con anotaciones")
        self.arbol_anotaciones_area = ttk.Treeview(self.arbol_anotaciones_frame)
        self.arbol_anotaciones_area.pack(expand=True, fill="both")
        
        # Crear un Treeview para mostrar el árbol sintáctico
        #self.treeview = ttk.Treeview(self.arbol_frame)
        #self.treeview.pack(expand=True, fill="both")
        
        # Área de terminal con pestañas para errores
        self.notebook_terminal = ttk.Notebook(self.root)
        self.notebook_terminal.pack(expand=True, fill="both")

        self.text_area.bind("<KeyRelease>", lambda event: (self.highlight_tokens()))
        self.text_area.bind("<ButtonRelease>", lambda event: (self.highlight_tokens()))
        self.text_area.bind("<FocusIn>", lambda event: (self.highlight_tokens()))
        self.text_area.bind("<MouseWheel>", lambda event: (self.highlight_tokens()))
        self.text_area.bind("<Configure>", lambda event: (self.highlight_tokens()))

        # Configura las etiquetas para resaltar los tokens
        self.text_area.tag_configure("PALABRA_RESERVADA", foreground="purple")
        self.text_area.tag_configure("OPERADOR", foreground="brown")
        self.text_area.tag_configure("FLOAT", foreground="green")
        self.text_area.tag_configure("ENTERO", foreground="green")
        self.text_area.tag_configure("ID", foreground="blue")
        self.text_area.tag_configure("COMENTARIO", foreground="gray")
        self.text_area.tag_configure("ERROR", foreground="red")
        self.text_area.tag_configure("SIMBOLO", foreground="brown")
        self.text_area.tag_configure("ASIGNACION", foreground="brown")

        # Pestañas para errores
        self.lexical_error_frame = tk.Frame(self.notebook_terminal)
        self.notebook_terminal.add(self.lexical_error_frame, text="Errores Léxicos")

        self.syntax_error_frame = tk.Frame(self.notebook_terminal, bg="grey")
        self.notebook_terminal.add(self.syntax_error_frame, text="Errores Sintácticos")

        self.semantic_error_frame = tk.Frame(self.notebook_terminal, bg="pink")
        self.notebook_terminal.add(self.semantic_error_frame, text="Errores Semánticos")
        
        # Pestaña para la tabla hash
        self.hash_table_frame = tk.Frame(self.notebook_terminal, bg="lightblue")
        self.notebook_terminal.add(self.hash_table_frame, text="Tabla Hash")

        # Agregar un widget de texto para mostrar la tabla hash
        self.hash_table_text = tk.Text(self.hash_table_frame, width=50, height=1)  # Ajusta el tamaño según sea necesario
        self.hash_table_text.pack(expand=True, fill="both")
        #Ventana de errores
        self.error_display = tk.Text(self.lexical_error_frame,  width=50, height=1, state="normal")
        self.error_display.bind('<Button-1>', self.disable_click)
        self.error_display.pack(fill="both", expand=True)
        
        # Etiqueta para mostrar la posición del cursor
        self.cursor_position_label = tk.Label(self.root, text='')
        self.cursor_position_label.pack()

        # Llamar a la función para obtener la posición del cursor y numerar lineas
        self.get_cursor_position()
        self.numerar_lineas()

        # Menú principal
        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)
        
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)
        #file_menu.add_command(label="Abrir", image= photo, compound=tk.LEFT, command=self.abrir_archivo)
        file_menu.add_command(label="Abrir", compound="top", command=self.abrir_archivo)
        file_menu.add_separator()
        file_menu.add_command(label="Guardar", command=lambda: guardar_archivo(self.text_area, ))
        file_menu.add_separator()
        file_menu.add_command(label="Guardar Como", command=lambda: guardar_archivo_como(self.text_area))
        file_menu.add_separator()
        file_menu.add_command(label="Cerrar", command=lambda: cerrar_archivo(self.text_area))

        compile_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Compilar", menu=compile_menu)
        compile_menu.add_command(label="Análisis Léxico", command=self.analizador_lex)
        compile_menu.add_separator()
        compile_menu.add_command(label="Análisis Sintactico", command=self.compile_code)
        compile_menu.add_separator()
        compile_menu.add_command(label="Análisis Semantico", command=self.analizador_sem)
        compile_menu.add_separator()
        compile_menu.add_command(label="Codigo Intermedio")
        compile_menu.add_separator()
        compile_menu.add_command(label="Ejecucion")
        
        # Crear un frame para contener los botones
        frame_botones = tk.Frame(root)
        frame_botones.pack()

        # Crear varios botones
        for i in range(1, 10):
            if i == 1:
                boton = tk.Button(frame_botones, text=f"{array_strings[i-1]}", command=self.abrir_archivo)
            elif i == 2: 
                boton = tk.Button(frame_botones, text=f"{array_strings[i-1]}", command=lambda: guardar_archivo(self.text_area))
            elif i == 3: 
                boton = tk.Button(frame_botones, text=f"{array_strings[i-1]}", command=lambda: guardar_archivo_como(self.text_area))
            elif i == 4: 
                boton = tk.Button(frame_botones, text=f"{array_strings[i-1]}", command=lambda: cerrar_archivo(self.text_area))
            elif i == 5: 
                boton = tk.Button(frame_botones, text=f"{array_strings[i-1]}", command= self.mostrar_tabla_hash)
            elif i == 6: 
                boton = tk.Button(frame_botones, text=f"{array_strings[i-1]}", command= self.analizador_lex)
            elif i == 7: 
                boton = tk.Button(frame_botones, text=f"{array_strings[i-1]}", command=self.compile_code)
            elif i == 8: 
                boton = tk.Button(frame_botones, text=f"{array_strings[i-1]}", command= self.analizador_sem)
            elif i==9:
                boton = tk.Button(frame_botones, text=f"{array_strings[i-1]}")
            else: 
                boton = tk.Button(frame_botones, text=f"{array_strings[i-1]}")
            boton.pack(side=tk.LEFT, padx=5, pady=5)
        
    def disable_click(self, event):
        return 'break'  # Esto evita que se procesen los clics
    
    def agregar_texto_siguiente_linea(self, event):
        current_pos = self.text_area.index(tk.INSERT)
        self.text_area.insert(current_pos, "\n")
        return "break"  # Evita que se agregue un salto de línea adicional
    
    def sincronizar_scrollbars(self, *args):
        self.text_area.yview_moveto(args[0])
        self.num_area.yview_moveto(args[0])
        self.result_area.yview_moveto(args[0])

    def abrir_archivo(self):
        global ruta_actual
        archivo = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Archivos de Texto", ".txt"), ("Todos los archivos", ".*")])
        if archivo:
            with open(archivo, "r") as file:
                contenido = file.read()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, contenido)
            ruta_actual = archivo
            self.numerar_lineas()
        self.highlight_tokens()
            
    def analizador_lex(self):
        # Obtener el texto completo del editor
        text = self.text_area.get("1.0", tk.END)

        # Limpiar cualquier resaltado anterior
        for tag_name in ["PALABRA RESERVADA", "OPERADOR", "ENTERO", "ID", "COMENTARIO", "ERROR", "ASIGNACION", "SIMBOLO","FLOAT"]:
            self.text_area.tag_remove(tag_name, "1.0", tk.END)  # Configurar todos los tags para que el texto sea negro

        # Instanciar un objeto Lexer
        lexer = Lexer(text)
        tokens = []
        errors = []

        # Resaltar los tokens
        while True:
            token = lexer.get_next_token()
            if token.token_type == 'EOF':
                break
            
            if token.token_type=='ERROR':
                errors.append(token)
            else:
                tokens.append(token)

            start_line = token.line 
            start_column = token.column - 1  # Ajustar la columna inicial
            end_line = token.line
            end_column = start_column + len(str(token.value))

            # Agregar etiqueta de resaltado al token
            start_pos = f"{start_line}.{start_column}"
            end_pos = f"{end_line}.{end_column}"
            tag_name = self.get_tag_name(token.token_type)
            print("Token: " + tag_name)
            self.text_area.tag_add(tag_name, start_pos, end_pos)
                
        self.mostrar_tokens(tokens)
        self.mostrar_errors(errors)
    
    
    def mostrar_arbol_sintactico(self, arbol):
        # Limpiar el Treeview antes de mostrar el nuevo árbol
        self.arbol_area.delete(*self.arbol_area.get_children())

        # Función recursiva para agregar nodos al Treeview
        def agregar_nodos(parent, arbol):
            if isinstance(arbol, dict):
                nodo_id = self.arbol_area.insert(parent, "end", text=str(arbol['label']), open=True, tags=('dict_node',))
                for child in arbol.get('children', []):
                    agregar_nodos(nodo_id, child)
            elif isinstance(arbol, tuple):
                nodo_id = self.arbol_area.insert(parent, "end", text=str(arbol[0]), open=True, tags=('tuple_node',))
                for elemento in arbol[1:]:
                    agregar_nodos(nodo_id, elemento)
            elif isinstance(arbol, list):
                for elemento in arbol:
                    agregar_nodos(parent, elemento)
            else:
                self.arbol_area.insert(parent, "end", text=str(arbol), open=True, tags=('other_node',))  # Asegurar que los nodos individuales también sean colapsables

        # Mostrar el árbol sintáctico
        agregar_nodos("", arbol)

        # Aplicar estilos a los nodos según el tipo
        self.arbol_area.tag_configure('dict_node', foreground='green')
        self.arbol_area.tag_configure('other_node', foreground='black')  # Estilo por defecto

    def compile_code(self):
        text = self.text_area.get("1.0", tk.END).strip()
        input_file = 'temp_input.txt'  # Nombre del archivo temporal para pasar al subprocesso

        # Guardar el contenido en un archivo temporal
        with open(input_file, 'w') as file:
            file.write(text)

        try:
            result = subprocess.run(
                ['python', 'sintactic.py', input_file],
                check=True,
                text=True,
                capture_output=True
            )

            # Leer el archivo de análisis sintáctico y mostrar su contenido
            with open('analisisSyntax.txt', 'r') as file:
                content = file.read()
                self.syntax_area.delete("1.0", tk.END)
                self.syntax_area.insert(tk.END, content)
            try:
                with open('arbol.txt', 'r') as arbol_file:
                    arbol_content = arbol_file.read()
                    arbol_sintactico = eval(arbol_content)
                    self.mostrar_arbol_sintactico(arbol_sintactico)   
            except:    
                with open('ast_info.txt', 'r') as arbol_file:
                    arbol_content = arbol_file.read()
                    arbol_sintactico = eval(arbol_content)
                
            self.error_display.delete("1.0", tk.END)
            self.error_display.insert(tk.END, result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error ejecutando analizador sintáctico: {e}")
        finally:
            # Eliminar el archivo temporal después de usarlo
            try:
                os.remove(input_file)
            except Exception as e:
                print(f"No se pudo eliminar el archivo temporal: {e}")

    def analizador_sem(self):
        try:
            if not hasattr(self, 'arbol_sintactico'):
                self.arbol_sintactico = self.load_syntax_tree('arbol.txt')

            success = semantic.perform_semantic_analysis(
                self.arbol_sintactico,
                'arbol_anotado.txt',
                'tabla_hash.txt',
                error_callback=self.display_error
            )
            if not success:
                return

            self.arbol_anotado = self.load_syntax_tree('arbol_anotado.txt')
            self.mostrar_arbol_anotado(self.arbol_anotado)

            print("Análisis semántico completado sin errores.")

        except Exception as e:
            print(f"Error en análisis semántico: {e}")
            self.error_display.insert(tk.END, str(e) + '\n')

    def display_error(self, error_message):
        self.error_display.insert(tk.END, error_message + '\n')
    
    def mostrar_arbol_anotado(self, arbol_anotado):
        self.arbol_anotaciones_area.delete(*self.arbol_anotaciones_area.get_children())  # Limpiar la vista anterior

        # Función recursiva para agregar nodos anotados
        def agregar_nodos_anotados(parent, arbol):
            if isinstance(arbol, dict):
                nodo_id = self.arbol_anotaciones_area.insert(parent, "end", text=f"{arbol['label']} (Tipo: {arbol.get('type', 'Desconocido')})", open=True)
                for child in arbol.get('children', []):
                    agregar_nodos_anotados(nodo_id, child)
            elif isinstance(arbol, list):
                for item in arbol:
                    agregar_nodos_anotados(parent, item)  # Procesa cada item de la lista
            else:
                self.arbol_anotaciones_area.insert(parent, "end", text=str(arbol), open=True)

        agregar_nodos_anotados("", arbol_anotado)


    def load_syntax_tree(self,file_path):
        try:
            with open(file_path, 'r') as file:
                syntax_tree = json.load(file)
            return syntax_tree
        except json.JSONDecodeError as e:
            print(f"Error al cargar el árbol sintáctico: {str(e)}")
            return None
        
    def mostrar_tabla_hash(self):
        # Leer y mostrar la tabla hash en la pestaña correspondiente
        try:
            with open('tabla_hash.txt', 'r') as hash_file:
                tabla_hash = hash_file.read()
            
            self.hash_table_text.delete('1.0', tk.END)  # Limpiar el área antes de mostrar la nueva tabla
            self.hash_table_text.insert(tk.END, tabla_hash)  # Insertar la nueva tabla
        except FileNotFoundError:
            print("Error: El archivo de la tabla hash no se encontró.")
            self.hash_table_text.delete('1.0', tk.END)  # Limpiar el área
            self.hash_table_text.insert(tk.END, "Error: El archivo de la tabla hash no se encontró.")
        except Exception as e:
            print(f"Error mostrando la tabla hash: {e}")
            self.hash_table_text.delete('1.0', tk.END)  # Limpiar el área
            self.hash_table_text.insert(tk.END, str(e))



    def mostrar_errors(self, errors):
        self.error_display.delete("1.0", "end")

        # Mostrar los tokens de error en el widget de errores léxicos
        for token in errors:
            token_info = f"Tipo: {token.token_type}, Valor: {token.value}, Línea: {token.line}, Columna: {token.column-1}\n"
            self.error_display.insert(tk.END, token_info)
            
    def run_code():
        # Lógica para ejecutar el código
        pass
         
    def highlight_tokens(self, event=None):
        # Obtener el texto completo del editor
        text = self.text_area.get("1.0", tk.END)

        # Limpiar cualquier resaltado anterior
        for tag_name in ["PALABRA RESERVADA", "OPERADOR", "ENTERO", "ID", "COMENTARIO", "ERROR", "ASIGNACION", "SIMBOLO","FLOAT"]:
            self.text_area.tag_remove(tag_name, "1.0", tk.END)  # Configurar todos los tags para que el texto sea negro


        # Instanciar un objeto Lexer
        lexer = Lexer(text)
        tokens = []
        errors = []

        # Resaltar los tokens
        while True:
            token = lexer.get_next_token()
            if token.token_type == 'EOF':
                break
            
            if token.token_type=='ERROR':
                errors.append(token)
            else:
                tokens.append(token)

            start_line = token.line 
            start_column = token.column - 1  # Ajustar la columna inicial
            end_line = token.line
            end_column = start_column + len(str(token.value))

            # Agregar etiqueta de resaltado al token
            start_pos = f"{start_line}.{start_column}"
            end_pos = f"{end_line}.{end_column}"
            tag_name = self.get_tag_name(token.token_type)
            print("Tipo: " + tag_name)
            self.text_area.tag_add(tag_name, start_pos, end_pos)

    def mostrar_tokens(self, tokens):
        self.result_area.delete("1.0", tk.END)

        for token in tokens:
            token_info = f"Tipo: {token.token_type}, Valor: {token.value}, Línea: {token.line}, Columna: {token.column-1}\n"
            self.result_area.insert(tk.END, token_info)

    def get_tag_name(self, token_type):
        # Devuelve el nombre de la etiqueta para resaltar el token
        tag_names = {
            "PALABRA_RESERVADA": "PALABRA_RESERVADA",
            "OPERADOR": "OPERADOR",
            "ENTERO": "ENTERO",
            "FLOAT": "FLOAT",
            "ERROR" : "ERROR",
            "ASIGNACION": "ASIGNACION",
            "SIMBOLO": "SIMBOLO",
            "ID": "ID",
            "COMENTARIO": "COMENTARIO"
        }
        return tag_names.get(token_type, "DEFAULT")
    
    def numerar_lineas(self):
        # Obtener el contenido del área de texto
        contenido = self.text_area.get("1.0", tk.END)

        # Dividir el contenido en líneas
        lineas = contenido.split("\n")
        
        aux = len(lineas)
        # Crear la numeración y actualizar el área de numeración
        numeracion_numeros = '\n'.join(str(i+1) for i in range(aux-1))
        self.num_area.config(state="normal")
        self.num_area.delete(1.0, "end")
        self.num_area.insert("end", numeracion_numeros)
        self.num_area.config(state="disabled")

        # Configurar el área de números para desplazarse junto con el área de texto
        self.num_area.yview_moveto(self.text_area.yview()[0])
     
    def get_cursor_position(self):
        # Obtener la posición actual del cursor en el área de texto
        index = self.text_area.index(tk.INSERT)
        
        # El índice devuelto es en el formato "linea.columna", así que lo dividimos para obtener la fila y la columna
        row, col = index.split('.')
        
        # Actualizar la etiqueta con la posición del cursor
        if int(col) > 3:
            self.cursor_position_label.config(text=f'Cursor: Fila: {row}, Columna: {col}')
        else:
            self.cursor_position_label.config(text=f'Cursor: Fila: {row}, Columna: {col}')
    
        # Llamar a esta función cada cierto tiempo para actualizar la posición
        self.root.after(100, self.get_cursor_position)
        self.root.after(100, self.numerar_lineas)


# Iniciar la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    editor_compilador = EditorCompilador(root)
    root.mainloop()