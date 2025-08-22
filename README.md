# Login Local Py

Este projeto é um sistema de login local com interface gráfica em Python, que após autenticação abre uma calculadora avançada. Ideal para uso pessoal ou demonstração de autenticação simples.

## Funcionalidades
- Login e cadastro de usuários (dados salvos localmente)
- Senhas protegidas por hash e salt
- Interface moderna com Tkinter
- Calculadora com histórico salvo em arquivo `.txt`
- Executáveis prontos para Windows (`main.exe` e `calc.exe`)

## Como usar
1. Execute `main.exe` para abrir a tela de login/cadastro.
2. Após login, a calculadora será aberta automaticamente.
3. O histórico de cálculos é salvo em `historico_calculos.txt`.

## Requisitos
- Windows 10 ou superior
- Python 3.13+ (apenas para rodar os scripts `.py`)
- Para usar os executáveis, não é necessário Python instalado.

## Estrutura dos arquivos
- `main.py` — Tela de login/cadastro
- `calc.py` — Calculadora com histórico
- `main.exe` — Executável do login
- `calc.exe` — Executável da calculadora
- `Logo.ico` — Ícone do programa
- `calc.png` — Imagem do cabeçalho
- `usuarios.json` — Banco de dados local de usuários
- `historico_calculos.txt` — Histórico dos cálculos

## Créditos
Desenvolvido por Luizmar Cardozo

## Observações
- Para distribuir, basta compactar os arquivos da pasta `dist`.
- O projeto pode ser facilmente adaptado para outras funções.

---

Se tiver dúvidas ou sugestões, abra uma issue ou contribua!
