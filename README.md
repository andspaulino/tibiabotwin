# Tibia Bot - Reconhecimento de Imagem 🎮👁️

Este é um projeto para o desenvolvimento de um bot para Tibia utilizando técnicas de **Visão Computacional (Reconhecimento de Imagem)** e simulação de input físico de teclado/mouse via hardware scan codes. 

Diferente de bots que leem ou injetam dados na memória do jogo, este bot age puramente observando a tela (pixels e padrões) e simulando comandos de teclado/mouse de forma humanizada, o que torna sua detecção por sistemas como o BattlEye extremamente mais complexa.

📌 **Acompanhe o roadmap detalhado e próximos passos em [NEXT_STEPS.md](file:///c:/Users/ander/Projects/tibia-bot/NEXT_STEPS.md)**.

---

## 🚀 Funcionalidades Concluídas

### 1. Captura Otimizada & Trava de Foco (`launcher.py` + `src/utils/window.py`)
- Ocultação da janela do Tibia com opacidade 1 via Win32 API `SetLayeredWindowAttributes`.
- Captura de tela ao vivo sem lag focando na janela do **Projetor do OBS Studio**.
- **Trava de Foco Ativo (`is_window_active`)**: O bot só executa ações quando a janela do Tibia for a janela ativa no Windows.
- **Trava de Minimizado (`is_window_minimized`)**: Pausa automática caso a janela seja minimizada.
- Restauração automática da visibilidade nativa ao encerrar.

### 2. Visão Computacional & Análise de Interface (`src/utils/screen.py`)
- **Barra de Vida (HP)**: Análise por amostragem de dominância de cor BGR.
- **Barra de Mana (MP)**: Filtro de cor azul desconsiderando textos e bordas.
- **Protection Zone (PZ)**: Template Matching (`templates/pz.png`) + validação de cor azul (`is_in_pz()`).
- **Battle List & Targeting**: Mapeamento da ROI (`top: 390, left: 1744`) e filtro de densidade de pixels de HP bar (`hp_pixels >= 10`).

### 3. Auto-Healer Inteligente (`src/bot/healer.py`)
- **Hotkey 1**: Magia de Cura (`HP <= 90%`, execução silenciosa).
- **Hotkey 2**: Poção de Mana (`MP <= 50%`, execução silenciosa).
- **Hotkey 3**: Poção de Vida (`HP <= 30%`, registrado no log de emergência).
- **Pausa Automática em PZ**: Interrompe magias e poções em Protection Zone.

### 4. Auto-Attacker & Targeting (`src/bot/combat.py`)
- **Ataque Automático (`Space`)**: Seleção de alvos presentes na Battle List com intervalo humanizado.
- **Reconhecimento de Alvo Ativo**: Identificação de moldura vermelha via densidade de cor + Template Matching (`templates/target_red.png` 20x20).
- **Zero Repetição de Atalhos**: Mantém o combate travado sem spam indevido de teclas.

### 5. Logger Centralizado & HUD Overlay (`src/utils/logger.py` + `src/utils/overlay.py`)
- **Logger Central**: Formatação padronizada por categorias (`HEALER`, `COMBAT`, `PZ`, `SYSTEM`).
- **Sincronização para OBS**: Exportação contínua para `logs_hud.txt` (Fonte de texto GDI+ no OBS).
- **HUD Transparente On-Screen**: Janela flutuante no canto inferior da tela com a flag **Click-Through** (`WS_EX_TRANSPARENT`).
- **Módulo de Humanização (`src/utils/humanizer.py`)**: Delays com Curva de Gauss, retenção de teclas entre 30ms-75ms e Curvas de Bézier.

---

## 🎥 Captura de Tela com OBS Studio ⚠️

Devido ao bloqueio de renderização direta do cliente do Tibia (tela preta), o bot utiliza o seguinte fluxo:
1. O **OBS Studio** roda com uma fonte de **Captura de Jogo / Janela** apontando para o Tibia.
2. Abrimos um **Projetor em Janela** no OBS.
3. O iniciador deixa o Tibia invisível (`opacidade = 1`), mas o OBS continua capturando o DirectX/Vulkan perfeitamente!
4. O bot lê a área do cliente do Projetor OBS e envia os comandos diretamente para o Tibia via `pydirectinput`.

---

## 🚀 Como Executar

1. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Execute o iniciador**:
   ```bash
   python launcher.py
   ```

---

## 📁 Estrutura do Projeto

```text
tibia-bot/
├── src/
│   ├── bot/
│   │   ├── healer.py      # Módulo AutoHealer (Hotkeys 1, 2, 3)
│   │   └── combat.py      # Módulo AutoAttacker (Battle List e target_red)
│   ├── utils/
│   │   ├── window.py      # Controle Win32, foco e minimização de janelas
│   │   ├── screen.py      # Captura MSS, leitura de HP/MP/PZ/Battle List
│   │   ├── input.py       # Simulação DirectX (pydirectinput)
│   │   ├── humanizer.py   # Delays gaussianos, key holds e curvas de Bézier
│   │   ├── logger.py      # Logger centralizado e sincronização de logs_hud.txt
│   │   └── overlay.py     # HUD Transparente On-Screen (Click-Through)
│   └── main.py            # Motor principal e loop de monitoramento
├── templates/             # Imagens base para Template Matching (pz.png, target_red.png)
├── tests/                 # Utilitários de testes e ROI
│   ├── test_bars.py       # Teste de leitura de HP/MP/Status
│   ├── test_pz.py         # Teste de detecção dinâmica de PZ
│   ├── test_combat.py     # Teste de combate e Battle List
│   ├── test_humanizer.py  # Teste de delays e curvas de Bézier
│   ├── test_overlay.py    # Teste do HUD transparente de tela
│   ├── get_roi.py         # Seletor interativo de coordenadas de ROI
│   └── get_mouse_pos.py   # Inspetor de posição do cursor
├── launcher.py            # Atalho/Iniciador principal na raiz
├── requirements.txt       # Dependências do Python
├── AGENTS.md              # Diretrizes para Agentes de IA
└── README.md              # Documentação principal
```

---

## ⚠️ Isenção de Responsabilidade (Disclaimer)

Este projeto tem fins estritamente de estudo e aprendizado sobre visão computacional e automação. O uso de softwares de automação (bots) viola os Termos de Serviço do Tibia (CipSoft) e pode resultar na exclusão permanente da sua conta. Use por sua conta e risco.
