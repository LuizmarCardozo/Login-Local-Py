
import tkinter as tk
from tkinter import messagebox, filedialog
import re
from datetime import datetime
import os
import sys
import subprocess

HISTORICO_ARQUIVO = "historico_calculos.txt"

class CalculadoraGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora - Python (com histórico em .txt)")
        self.root.resizable(False, False)

        # Display
        self.display = tk.Entry(root, font=("Segoe UI", 18), justify="right", bd=8, relief="groove")
        self.display.grid(row=0, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")
        self.display.focus_set()

        # History (session)
        self.history = tk.Listbox(root, height=6, font=("Consolas", 11))
        self.history.grid(row=1, column=0, columnspan=5, padx=10, pady=(0,10), sticky="nsew")

        # Buttons layout
        buttons = [
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2), ("/", 2, 3), ("C", 2, 4),
            ("4", 3, 0), ("5", 3, 1), ("6", 3, 2), ("*", 3, 3), ("←", 3, 4),
            ("1", 4, 0), ("2", 4, 1), ("3", 4, 2), ("-", 4, 3), ("(", 4, 4),
            ("0", 5, 0), (",", 5, 1), (".", 5, 2), ("+", 5, 3), (")", 5, 4),
            ("=", 6, 0, 5),
        ]

        for item in buttons:
            if len(item) == 3:
                text, r, c = item
                colspan = 1
            else:
                text, r, c, colspan = item
            btn = tk.Button(root, text=text, font=("Segoe UI", 14), width=4, height=1,
                            command=lambda t=text: self.on_button_click(t))
            btn.grid(row=r, column=c, columnspan=colspan, padx=5, pady=5, sticky="nsew")

        # Extra controls
        extra_frame = tk.Frame(root)
        extra_frame.grid(row=7, column=0, columnspan=5, padx=10, pady=(0,10), sticky="nsew")
        tk.Button(extra_frame, text="Abrir histórico (txt)", command=self.abrir_historico).pack(side="left")
        tk.Button(extra_frame, text="Salvar histórico como...", command=self.salvar_historico_como).pack(side="left", padx=6)
        tk.Button(extra_frame, text="Limpar histórico da sessão", command=self.limpar_historico_sessao).pack(side="left")

        # Keyboard bindings
        root.bind("<Return>", lambda e: self.calcular())
        root.bind("<KP_Enter>", lambda e: self.calcular())
        root.bind("<BackSpace>", lambda e: self.backspace())

        # Ensure history file exists
        self._garantir_arquivo_historico()

    def _garantir_arquivo_historico(self):
        try:
            if not os.path.exists(HISTORICO_ARQUIVO):
                with open(HISTORICO_ARQUIVO, "w", encoding="utf-8") as f:
                    f.write("=== Histórico de cálculos ===\n")
                    f.write(f"Criado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível criar o arquivo de histórico:\n{e}")

    def on_button_click(self, char):
        if char == "C":
            self.display.delete(0, tk.END)
        elif char == "←":
            self.backspace()
        elif char == "=":
            self.calcular()
        else:
            self.display.insert(tk.END, char)

    def backspace(self):
        current = self.display.get()
        if current:
            self.display.delete(len(current)-1, tk.END)

    def _normalizar_expressao(self, expr: str) -> str:
        # Suporta vírgula decimal brasileira -> ponto
        expr = expr.replace(",", ".")
        # Permite usar 'x' ou '÷' se o usuário digitar
        expr = expr.replace("x", "*").replace("X", "*").replace("÷", "/")
        # Suporta '^' como potência
        expr = expr.replace("^", "**")
        return expr

    def _expressao_valida(self, expr: str) -> bool:
        # Apenas números, ponto, operadores básicos e parênteses
        padrao = re.compile(r"^[0-9\.\+\-\*\/\%\(\)\s\*\*]+$")
        # O padrão acima permite ** pois já convertemos ^ -> **
        return bool(padrao.match(expr))

    def calcular(self):
        expr = self.display.get().strip()
        if not expr:
            return

        expr_norm = self._normalizar_expressao(expr)

        if not self._expressao_valida(expr_norm):
            messagebox.showwarning("Expressão inválida", "Use apenas números e operadores (+, -, *, /, %, ^, parênteses).")
            return

        try:
            # Avalia a expressão com eval numa sandbox simples.
            # Como validamos com regex, evitamos nomes/atributos.
            resultado = eval(expr_norm, {"__builtins__": {}}, {})
            # Evita números longos demais exibindo com até 12 dígitos significativos
            if isinstance(resultado, float):
                # Remove -0.0
                if abs(resultado) < 1e-12:
                    resultado = 0.0
                exib = f"{resultado:.12g}"
            else:
                exib = str(resultado)

            self.display.delete(0, tk.END)
            self.display.insert(0, exib)

            linha_hist = f"{expr} = {exib}"
            self._adicionar_ao_historico(linha_hist)
            self._salvar_no_txt(linha_hist)

        except ZeroDivisionError:
            messagebox.showerror("Erro", "Divisão por zero não é permitida.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível calcular a expressão.\nDetalhes: {e}")

    def _adicionar_ao_historico(self, linha: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.history.insert(tk.END, f"[{timestamp}] {linha}")
        self.history.see(tk.END)

    def _salvar_no_txt(self, linha: str):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(HISTORICO_ARQUIVO, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} - {linha}\n")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", f"Não foi possível gravar no arquivo de histórico.\n{e}")

    def abrir_historico(self):
        caminho = os.path.abspath(HISTORICO_ARQUIVO)
        if not os.path.exists(caminho):
            self._garantir_arquivo_historico()
        try:
            if sys.platform.startswith("win"):
                os.startfile(caminho)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", caminho])
            else:
                subprocess.Popen(["xdg-open", caminho])
        except Exception as e:
            messagebox.showinfo("Abrir histórico", f"O arquivo está em:\n{caminho}\n\nNão foi possível abrir automaticamente. Erro: {e}")

    def salvar_historico_como(self):
        # Salva o histórico da SESSÃO (o Listbox) em outro arquivo txt à parte
        conteudo = "\n".join(self.history.get(0, tk.END))
        if not conteudo.strip():
            conteudo = "(Sem itens no histórico da sessão)"

        caminho = filedialog.asksaveasfilename(
            title="Salvar histórico da sessão como...",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt")]
        )
        if caminho:
            try:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write("=== Histórico da sessão ===\n")
                    f.write(conteudo + "\n")
                messagebox.showinfo("Salvo", "Histórico da sessão salvo com sucesso.")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar o arquivo.\n{e}")

    def limpar_historico_sessao(self):
        self.history.delete(0, tk.END)

def main():
    root = tk.Tk()
    app = CalculadoraGUI(root)

    # Tornar colunas/linhas responsivas (para leve redimensionamento interno)
    for c in range(5):
        root.grid_columnconfigure(c, weight=1)
    for r in range(8):
        root.grid_rowconfigure(r, weight=0)

    root.mainloop()

if __name__ == "__main__":
    main()
