import tkinter as tk
from tkinter import ttk, messagebox
import json, os, hashlib, uuid, platform, time
import subprocess, sys 


USERS_FILE = "usuarios.json"
ICON_CANDIDATES = ["Logo.ico"]

# --- Script a abrir após login OK ---
NEXT_SCRIPT = "calc.py"   # <-- TROQUE AQUI PRO SEU ARQUIVO

# --- Logo do cabeçalho ---
LOGO_PATH = "calc.png"   # coloque o arquivo na mesma pasta do .py (recomendo PNG)
LOGO_SIZE = (44, 44)     # tamanho (largura, altura)

# ------------------- Estilo -------------------
PRIMARY = "#2563eb"
PRIMARY_ACTIVE = "#1d4ed8"
PRIMARY_LIGHT = "#dbeafe"
BG_APP = "#f3f4f6"
BG_CARD = "#ffffff"
FG_TITLE = "#111827"
FG_LABEL = "#374151"
FG_HINT = "#6b7280"
FG_ERROR = "#ef4444"
FG_SUCCESS = "#16a34a"

FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SUB = ("Segoe UI", 15, "bold")
FONT_LABEL = ("Segoe UI", 11, "bold")
FONT_TEXT = ("Segoe UI", 11)

# ---------------- Persistência ----------------
def carregar_usuarios():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salvar_usuarios(db):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def hash_senha(senha, salt=None):
    if not salt:
        salt = uuid.uuid4().hex
    hashed = hashlib.sha256((salt + senha).encode("utf-8")).hexdigest()
    return salt, hashed

def verificar_senha(senha_digitada, registro):
    salt = registro.get("salt", "")
    hashed_ok = registro.get("password", "")
    _, hashed_try = hash_senha(senha_digitada, salt=salt)
    return hashed_try == hashed_ok

# ---------------- Widgets custom ----------------
class EntryComBorda(tk.Frame):
    """Entry com 'borda' que muda a cor ao focar."""
    def __init__(self, master, textvariable=None, show=None):
        super().__init__(master, bg=BG_CARD)
        self.borda = tk.Frame(self, bg="#e5e7eb", highlightthickness=0)
        self.borda.pack(fill="x")
        self.entry = ttk.Entry(self.borda, textvariable=textvariable, font=FONT_TEXT)
        self.entry.pack(fill="x", ipady=6, padx=1, pady=1)
        if show:
            self.entry.config(show=show)
        self.entry.bind("<FocusIn>", self._on_focus)
        self.entry.bind("<FocusOut>", self._on_blur)
    def _on_focus(self, *_):
        self.borda.config(bg=PRIMARY)
    def _on_blur(self, *_):
        self.borda.config(bg="#e5e7eb")
    def focus_set(self):
        self.entry.focus_set()

class SpinnerOverlay:
    """Overlay com spinner animado; bloqueia a UI até parar."""
    def __init__(self, root, texto="Processando..."):
        self.root = root
        self.top = tk.Toplevel(root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        try:
            self.top.attributes("-toolwindow", True)
        except Exception:
            pass

        root.update_idletasks()
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()
        self.top.geometry(f"{w}x{h}+{x}+{y}")

        self.bg = tk.Frame(self.top, bg="#000000")
        try:
            self.top.attributes("-alpha", 0.18)
        except Exception:
            pass
        self.bg.pack(fill="both", expand=True)

        self.container = tk.Frame(self.bg, bg=BG_CARD)
        self.container.place(relx=0.5, rely=0.5, anchor="center")
        self.container.configure(bd=0, highlightthickness=0)
        tk.Label(self.container, text=texto, font=("Segoe UI", 11), bg=BG_CARD, fg=FG_LABEL)\
            .pack(pady=(12, 6))

        self.canvas = tk.Canvas(self.container, width=64, height=64, highlightthickness=0, bg=BG_CARD)
        self.canvas.pack(padx=20, pady=(0, 16))
        self.canvas.create_oval(8, 8, 56, 56, outline="#e5e7eb", width=6)
        self.arc = self.canvas.create_arc(8, 8, 56, 56, start=0, extent=90, style="arc",
                                          outline=PRIMARY, width=6)
        self._running = True
        self._angle = 0
        self._animate()

        self._disable_all(self.root)

    def _disable_all(self, widget):
        try:
            widget_state = widget.cget("state")
            if widget_state not in ("disabled",):
                widget._prev_state = widget_state
                widget.config(state="disabled")
        except Exception:
            pass
        for child in widget.winfo_children():
            self._disable_all(child)

    def _enable_all(self, widget):
        try:
            prev = getattr(widget, "_prev_state", None)
            if prev is not None:
                widget.config(state=prev)
                delattr(widget, "_prev_state")
        except Exception:
            pass
        for child in widget.winfo_children():
            self._enable_all(child)

    def _animate(self):
        if not self._running:
            return
        self._angle = (self._angle + 12) % 360
        try:
            self.canvas.itemconfig(self.arc, start=self._angle)
        except Exception:
            pass
        self.canvas.after(16, self._animate)

    def stop(self):
        self._running = False
        self._enable_all(self.root)
        self.top.destroy()

class Toast:
    """Toast simples que desliza do rodapé e some."""
    def __init__(self, root, text, bg="#111827", fg="white", duration=1800):
        self.root = root
        self.duration = duration
        self.top = tk.Toplevel(root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)

        self.frame = tk.Frame(self.top, bg=bg)
        self.label = tk.Label(self.frame, text=text, bg=bg, fg=fg, font=("Segoe UI", 10))
        self.label.pack(padx=16, pady=10)
        self.frame.pack()

        root.update_idletasks()
        rw = root.winfo_width()
        rh = root.winfo_height()
        rx = root.winfo_rootx()
        ry = root.winfo_rooty()

        self.width = self.frame.winfo_reqwidth()
        self.height = self.frame.winfo_reqheight()
        self.x = rx + (rw - self.width) // 2
        self.y_start = ry + rh + 10
        self.y_end = ry + rh - self.height - 24
        self.top.geometry(f"+{self.x}+{self.y_start}")

        self._slide_in()

    def _slide_in(self, step=0):
        if step >= 10:
            self.top.geometry(f"+{self.x}+{self.y_end}")
            self.top.after(self.duration, self._slide_out)
            return
        y = self.y_start - (self.y_start - self.y_end) * (step / 10)
        self.top.geometry(f"+{self.x}+{int(y)}")
        self.top.after(16, lambda: self._slide_in(step + 1))

    def _slide_out(self, step=0):
        if step >= 10:
            self.top.destroy()
            return
        y = self.y_end + (self.y_start - self.y_end) * (step / 10)
        self.top.geometry(f"+{self.x}+{int(y)}")
        self.top.after(16, lambda: self._slide_out(step + 1))

# ---------------- Aplicação ----------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Disdal • Acesso")
        self.configure(bg=BG_APP)
        self._set_app_icon()
        self.after(0, self._maximize)

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TNotebook", background=BG_CARD, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 10), font=("Segoe UI", 11))
        style.map("TNotebook.Tab", background=[("selected", BG_APP)])

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.card = tk.Frame(self, bg=BG_CARD)
        self.card.grid(row=0, column=0, sticky="nsew", padx=32, pady=32)

        # --- carrega logo do cabeçalho ---
        self._load_header_logo()

        # -------- Cabeçalho (logo + textos) --------
        header = tk.Frame(self.card, bg=BG_CARD)
        header.pack(fill="x", padx=28, pady=(24, 8))

        row = tk.Frame(header, bg=BG_CARD)
        row.pack(anchor="w")

        # Logo à esquerda (se presente)
        if getattr(self, "header_logo_img", None):
            tk.Label(row, image=self.header_logo_img, bg=BG_CARD).pack(side="left", padx=(0, 10))

        # Bloco de textos ao lado do logo
        text_box = tk.Frame(row, bg=BG_CARD)
        text_box.pack(side="left")
        tk.Label(text_box, text="Calculadora MASTER", font=FONT_TITLE, fg=FG_TITLE, bg=BG_CARD).pack(anchor="w")
        tk.Label(text_box, text="Faça login ou crie sua conta.", font=FONT_TEXT, fg=FG_HINT, bg=BG_CARD).pack(anchor="w", pady=(4, 0))

        # Abas
        self.tabs = ttk.Notebook(self.card)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(8, 20))
        self.tab_login = tk.Frame(self.tabs, bg=BG_CARD)
        self.tab_cad = tk.Frame(self.tabs, bg=BG_CARD)
        self.tabs.add(self.tab_login, text="Entrar")
        self.tabs.add(self.tab_cad, text="Cadastrar")

        # Telas
        self._montar_login(self.tab_login)
        self._montar_cadastro(self.tab_cad)

        # Rodapé
        footer = tk.Frame(self.card, bg=BG_CARD)
        footer.pack(fill="x", padx=20, pady=(0, 20))
        tk.Label(footer, text="As credenciais são salvas apenas neste computador.",
                 font=("Segoe UI", 10), fg=FG_HINT, bg=BG_CARD).pack(anchor="w")

        self.db = carregar_usuarios()

    # ----------- Ícone, maximização e logo -----------
    def _set_app_icon(self):
        for path in ICON_CANDIDATES:
            if os.path.exists(path):
                try:
                    if path.lower().endswith(".ico") and platform.system() == "Windows":
                        self.iconbitmap(path); return
                    else:
                        img = tk.PhotoImage(file=path)
                        self.iconphoto(True, img)
                        self._icon_img = img
                        return
                except Exception:
                    pass

    def _maximize(self):
        try:
            self.state("zoomed"); return
        except Exception:
            pass
        try:
            self.attributes("-zoomed", True); return
        except Exception:
            pass
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")

    def _load_header_logo(self):
        """Carrega o logo do cabeçalho em self.header_logo_img (opcional)."""
        self.header_logo_img = None
        if os.path.exists(LOGO_PATH):
            try:
                from PIL import Image, ImageTk  # opcional (pip install pillow)
                img = Image.open(LOGO_PATH).convert("RGBA")
                img = img.resize(LOGO_SIZE, Image.LANCZOS)
                self.header_logo_img = ImageTk.PhotoImage(img)
            except Exception:
                try:
                    # Sem Pillow: carrega direto (funciona para PNG/GIF)
                    self.header_logo_img = tk.PhotoImage(file=LOGO_PATH)
                except Exception:
                    self.header_logo_img = None

    # ----------------- Helpers UI -----------------
    def _campo(self, parent, rotulo, textvar, show=None):
        wrap = tk.Frame(parent, bg=BG_CARD)
        wrap.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(wrap, text=rotulo, font=FONT_LABEL, fg=FG_LABEL, bg=BG_CARD)\
            .pack(anchor="w", pady=(0, 6))
        e = EntryComBorda(wrap, textvariable=textvar, show=show)
        e.pack(fill="x")
        return e

    def _btn_primary(self, parent, texto, comando):
        btn = tk.Button(
            parent, text=texto, command=comando, font=("Segoe UI", 12, "bold"),
            fg="white", bg=PRIMARY, activebackground=PRIMARY_ACTIVE,
            activeforeground="white", bd=0, relief="flat", padx=18, pady=12, cursor="hand2"
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=PRIMARY_ACTIVE))
        btn.bind("<Leave>", lambda e: btn.config(bg=PRIMARY))
        return btn

    def _btn_ghost(self, parent, texto, comando):
        btn = tk.Button(
            parent, text=texto, command=comando, font=("Segoe UI", 12),
            fg=PRIMARY, bg=PRIMARY_LIGHT, activebackground="#c7ddff",
            bd=0, relief="flat", padx=16, pady=12, cursor="hand2"
        )
        btn.bind("<Enter>", lambda e: btn.config(bg="#c7ddff"))
        btn.bind("<Leave>", lambda e: btn.config(bg=PRIMARY_LIGHT))
        return btn

    # ----------------- Telas -----------------
    def _montar_login(self, parent):
        w = tk.Frame(parent, bg=BG_CARD)
        w.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(w, text="Bem-vindo de volta", font=FONT_SUB, fg=FG_TITLE, bg=BG_CARD)\
            .pack(anchor="w", padx=12, pady=(6, 0))
        self.login_usuario = tk.StringVar()
        self.login_senha = tk.StringVar()
        self.e_login_user = self._campo(w, "Usuário", self.login_usuario)
        self.e_login_pass = self._campo(w, "Senha", self.login_senha, show="•")
        btns = tk.Frame(w, bg=BG_CARD)
        btns.pack(fill="x", padx=12, pady=(16, 0))
        self.btn_entrar = self._btn_primary(btns, "Entrar", self.logar)
        self.btn_entrar.pack(side="left")
        self._btn_ghost(btns, "Criar conta", lambda: self.tabs.select(self.tab_cad)).pack(side="left", padx=10)
        self.after(200, self.e_login_user.focus_set)

    def _montar_cadastro(self, parent):
        w = tk.Frame(parent, bg=BG_CARD)
        w.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(w, text="Crie sua conta", font=FONT_SUB, fg=FG_TITLE, bg=BG_CARD)\
            .pack(anchor="w", padx=12, pady=(6, 0))
        self.cad_usuario = tk.StringVar()
        self.cad_senha = tk.StringVar()
        self.cad_confirma = tk.StringVar()
        self._campo(w, "Usuário", self.cad_usuario)
        self._campo(w, "Senha", self.cad_senha, show="•")
        self._campo(w, "Confirmar senha", self.cad_confirma, show="•")
        self.btn_cadastrar = self._btn_primary(w, "Cadastrar", self.cadastrar)
        self.btn_cadastrar.pack(anchor="w", padx=12, pady=(14, 0))

    # --------------- Animações auxiliares ---------------
    def _shake_window(self):
        """Treme a janela rapidamente (erro)."""
        try:
            self.update_idletasks()
            geom = self.geometry()
            w, h, x, y = self._parse_geometry(geom)
            seq = [0, 10, -10, 6, -6, 3, -3, 0]
            for dx in seq:
                self.geometry(f"{w}x{h}+{x+dx}+{y}")
                self.update()
                time.sleep(0.015)
        except Exception:
            pass

    @staticmethod
    def _parse_geometry(geom):
        wh, xy = geom.split("+", 1)
        w, h = map(int, wh.split("x"))
        x, y = map(int, xy.split("+"))
        return w, h, x, y

    # --------------- Execução do próximo script ---------------
    def _run_next_script(self, usuario: str):
        """Abre NEXT_SCRIPT em outro processo e fecha esta janela."""
        # Procura o executável calc.exe na pasta do main.exe
        exe_path = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), 'calc.exe')
        script_path = os.path.join(os.path.dirname(__file__), NEXT_SCRIPT)
        try:
            if os.path.exists(exe_path):
                # Executa calc.exe de forma oculta
                subprocess.Popen([exe_path, '--user', usuario], creationflags=subprocess.CREATE_NO_WINDOW)
                self.destroy()
            elif os.path.exists(script_path):
                subprocess.Popen([sys.executable, script_path, '--user', usuario], creationflags=subprocess.CREATE_NO_WINDOW)
                self.destroy()
            else:
                Toast(self, f"Script ou executável não encontrado.", bg=FG_ERROR)
        except Exception as e:
            Toast(self, f"Erro ao abrir: {e}", bg=FG_ERROR)

    # ----------------- Ações -----------------
    def logar(self):
        usuario = self.login_usuario.get().strip()
        senha = self.login_senha.get()
        if not usuario or not senha:
            Toast(self, "Preencha usuário e senha.", bg=FG_ERROR)
            self._shake_window()
            return

        self.btn_entrar.config(state="disabled")
        spinner = SpinnerOverlay(self, "Entrando...")
        self.after(750, lambda: self._finalizar_login(spinner, usuario, senha))

    def _finalizar_login(self, spinner, usuario, senha):
        registro = self.db.get(usuario)
        ok = bool(registro and verificar_senha(senha, registro))
        spinner.stop()
        self.btn_entrar.config(state="normal")
        if ok:
            Toast(self, f"Bem-vindo, {usuario}!", bg=FG_SUCCESS)
            # Abre o outro script e fecha a tela de login
            self.after(350, lambda: self._run_next_script(usuario))
        else:
            Toast(self, "Usuário ou senha incorretos.", bg=FG_ERROR)
            self._shake_window()

    def cadastrar(self):
        usuario = self.cad_usuario.get().strip()
        senha = self.cad_senha.get()
        confirma = self.cad_confirma.get()

        if not usuario or not senha or not confirma:
            Toast(self, "Preencha todos os campos.", bg=FG_ERROR)
            self._shake_window()
            return
        if len(usuario) < 3:
            Toast(self, "Usuário deve ter ao menos 3 caracteres.", bg=FG_ERROR)
            self._shake_window()
            return
        if len(senha) < 4:
            Toast(self, "Senha muito curta (mín. 4).", bg=FG_ERROR)
            self._shake_window()
            return
        if senha != confirma:
            Toast(self, "As senhas não conferem.", bg=FG_ERROR)
            self._shake_window()
            return
        if usuario in self.db:
            Toast(self, "Usuário já existe.", bg=FG_ERROR)
            self._shake_window()
            return

        self.btn_cadastrar.config(state="disabled")
        spinner = SpinnerOverlay(self, "Cadastrando...")
        self.after(800, lambda: self._finalizar_cadastro(spinner, usuario, senha))

    def _finalizar_cadastro(self, spinner, usuario, senha):
        salt, hashed = hash_senha(senha)
        self.db[usuario] = {"salt": salt, "password": hashed}
        salvar_usuarios(self.db)
        spinner.stop()
        self.btn_cadastrar.config(state="normal")
        Toast(self, "Usuário cadastrado com sucesso!", bg=FG_SUCCESS)
        self.tabs.select(self.tab_login)
        self.login_usuario.set(usuario)
        self.login_senha.set("")

if __name__ == "__main__":
    App().mainloop()
