# 🤖 AGENTS.md - Diretrizes para Agentes de IA (Tibia Bot)

Este arquivo define os princípios arquiteturais, regras de codificação, padrões de segurança e fluxos de teste que todo agente de IA deve seguir ao trabalhar no projeto `tibia-bot`.

---

## 🏛️ Princípios Arquiteturais

### 1. Visão Computacional Pura (Zero Leitura de Memória)
- **NUNCA** utilizar DLL Injection, leitura/escrita na memória do processo (`ReadProcessMemory`, Cheat Engine) ou rotinas que abram a handle do processo do jogo.
- **TODAS** as decisões de estado (porcentagem de HP, MP, Protection Zone e Battle List) DEVEM ser obtidas via Visão Computacional e amostragem de pixels/templates no OpenCV.

### 2. Captura Otimizada via OBS Studio
- A captura de tela é feita exclusivamente na área útil do **Projetor do OBS** (`'Projector - Source: Game Capture'`) para contornar telas pretas do BattlEye/DirectX/Vulkan.
- A janela nativa do cliente do Tibia deve permanecer oculta via Win32 `SetLayeredWindowAttributes` com opacidade 1 (`src/utils/window.py`).

### 3. Simulação de Input Físico & Humanização
- Comandos de teclado e mouse DEVEM utilizar **Hardware Scan Codes** (`pydirectinput`) em `src/utils/input.py`.
- **TODOS** os delays, tempos de retenção de tecla e movimentos de cursor DEVEM passar pelo módulo de humanização (`src/utils/humanizer.py`):
  - Delays baseados em **Distribuição Gaussiana / Curva Normal**.
  - Duração de retenção física de tecla (*Key Hold*) entre 30ms e 75ms.
  - Trajetória de mouse curva via **Curvas de Bézier** com aceleração/desaceleração e trepidação (*jitter*).
  - Pausa automática de ações caso o personagem esteja em **Protection Zone (PZ)**.

### 4. Compatibilidade e Encoding no Windows
- Sempre reconfigurar `sys.stdout` e `sys.stderr` para UTF-8.
- Utilizar marcadores de console compatíveis com o terminal do Windows (`[OK]`, `[X]`, `[!]`, `[*]`) para prevenir `UnicodeEncodeError`.

---

## 📁 Convenção de Estrutura de Arquivos

```text
tibia-bot/
├── src/
│   ├── bot/           # Lógicas de módulos (healer.py, combat.py)
│   ├── utils/         # Utilitários core (window.py, screen.py, input.py, humanizer.py)
│   └── main.py        # Motor principal e loop de execução
├── templates/         # Templates base para Template Matching (ex: pz.png)
├── tests/             # Scripts de testes autônomos (test_bars.py, test_pz.py, test_humanizer.py)
├── launcher.py        # Iniciador raiz do projeto
├── requirements.txt   # Dependências do Python
└── AGENTS.md          # Diretrizes para Agentes de IA
```

---

## 🧪 Regras de Verificação obrigatoria

Após modificar qualquer código:
1. Compilar a sintaxe de todos os arquivos tocados (`python -m py_compile <arquivos>`).
2. Garantir que scripts de teste autônomos na pasta `tests/` rodem sem exceções não tratadas.
3. Atualizar o `walkthrough.md` e os arquivos de documentação (`README.md` e `NEXT_STEPS.md`).
