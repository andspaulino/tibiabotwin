# Tibia Bot - Reconhecimento de Imagem 🎮👁️

Este é um projeto para o desenvolvimento de um bot para Tibia utilizando técnicas de **Visão Computacional (Reconhecimento de Imagem)** e simulação de input físico de teclado/mouse via hardware scan codes. 

Diferente de bots que leem ou injetam dados na memória do jogo, este bot age puramente observando a tela (pixels e padrões) e simulando comandos de teclado/mouse de forma humanizada, o que torna sua detecção por sistemas como o BattlEye extremamente mais complexa.

📌 **Acompanhe o roadmap detalhado e próximos passos em [NEXT_STEPS.md](file:///c:/Users/ander/Projects/tibia-bot/NEXT_STEPS.md)**.

---

## 🚀 Funcionalidades Concluídas

### 1. Sistema de Configuração Externa & Perfis (`config/` + `src/config/`)
- **Arquivos YAML com validação estrita**: Hotkeys, thresholds de HP/MP, cooldowns e parâmetros de busca de janela totalmente externalizados.
- **Suporte a Perfis Sobrescrevíveis**: Crie perfis customizados em `config/profiles/` (ex: por personagem ou resolução) que sobrepõem as configurações padrão em `config/default.yaml`.
- **JSON Schema**: Validação formal e autocomplete via `config/schemas/config.schema.json`.

### 2. Sistema de ROIs Escalável & Resolução Dinâmica (`src/domain/roi.py`)
- **Coordenadas Relativas (0.0 a 1.0)**: Regiões de interesse (HP, MP, Status Bar, Battle List) armazenadas proporcionalmente ao tamanho total do frame.
- **`ROIResolver`**: Converte e valida ROIs relativas em pixels reais em tempo de execução. Redimensionar o Projetor do OBS recalcula automaticamente todas as regiões!
- **Ferramenta de Calibração Interativa (`tools/calibrate_roi.py`)**: Selecione regiões na tela com o mouse e salve diretamente as coordenadas relativas no perfil `.yaml`.

### 3. Captura Única por Ciclo & Infraestrutura (`src/infrastructure/capture/`)
- **Single Frame Capture**: Exatamente uma captura de tela BGR é realizada por ciclo e compartilhada por todos os detectores.
- **Timestamping & Status**: `CapturedFrame` imutável contendo timestamp, dimensões e status (`VALID`, `STALE`, `FROZEN`, `FAILED`).
- **Detecção de Frames Congelados/Inválidos**: Se a imagem congelar por N ciclos ou falhar, o bot entra em pausa de segurança e **impede qualquer envio de atalhos**.

### 4. Estado Central do Jogo Imutável (`src/domain/game_state.py` + `analyzer.py`)
- **`GameState` Snapshot**: Objeto imutável que consolida a percepção do ciclo (`PlayerState`, `TargetState`, `WindowState`, `CaptureState`).
- **`GameAnalyzer`**: Converte frames e estado das janelas em `GameState`. Valores indeterminados são explicitamente `None` (sem assunções inseguras de 100% HP).
- **Consumo Exclusivo por Estado**: `AutoHealer`, `AutoAttacker` e `OnScreenOverlay` consomem apenas o `GameState`, sem capturar a tela ou executar Win32 diretamente.

### 5. Máquina de Estados Finitos do Bot (`src/application/state_machine.py` + `BotMode`)
- **`BotMode` Finito**: Apenas um modo principal ativo por ciclo (`PAUSED`, `UNSAFE`, `IN_PROTECTION_ZONE`, `COMBAT`, `IDLE`).
- **Hierarquia Estrita de Prioridades**: Killswitch > Foco/Minimização > Validade da Captura > Protection Zone > Combate > Ocioso.
- **Auditoria de Transições**: Registra eventos no log `[STATE]` detalhando o modo anterior, novo modo e o motivo rastreável sem logs repetitivos.

### 6. Motor Principal & LoopScheduler (`src/application/bot_engine.py` + `scheduler.py`)
- **`BotEngine`**: Motor desacoplado que orquestra o ciclo de execução via injeção de dependências.
- **`LoopScheduler`**: Controle de frequência de loop (FPS target) e cálculo de métricas de tempo de ciclo.
- **Composition Root (`src/main.py`)**: `main.py` atua exclusivamente como ponto de composição (CLI -> Config -> Windows -> Motor).
- **Execução Atômica (`run_cycle()`)**: Permite rodar 1 único ciclo isolado para testes unitários com mocks.

### 7. Trava de Foco & Segurança de Janela (`launcher.py` + `src/utils/window.py`)
- Ocultação da janela do Tibia com opacidade 1 via Win32 API `SetLayeredWindowAttributes`.
- Captura de tela ao vivo sem lag focando na janela do **Projetor do OBS Studio**.
- **Trava de Foco Ativo (`is_window_active`)**: O bot só executa ações quando a janela do Tibia for a janela ativa no Windows.
- **Trava de Minimizado (`is_window_minimized`)**: Pausa automática caso a janela seja minimizada.
- Restauração automática da visibilidade nativa ao encerrar.

### 8. Killswitch de Emergência (`src/main.py`)
- **Tecla de Pânico (`Pause`)**: Atalho global do Windows que intercala entre **Pausado** e **Em Execução** instantaneamente a qualquer momento.

### 9. Auto-Healer Inteligente (`src/bot/healer.py`)
- **Magia de Cura**: Limite de HP, hotkey e cooldown configuráveis.
- **Poção de Mana**: Limite de MP, hotkey e cooldown configuráveis.
- **Poção de Emergência**: Limite de HP crítico, hotkey e cooldown configuráveis (registrado no log de emergência).
- **Pausa Automática em PZ**: Interrompe magias e poções em Protection Zone.

### 10. Auto-Attacker & Targeting (`src/bot/combat.py`)
- **Ataque Automático**: Seleção de alvos presentes na Battle List com atalho e cooldown configuráveis.
- **Reconhecimento de Alvo Ativo**: Identificação de moldura vermelha via densidade de cor + Template Matching configurável (`target_template_path`).
- **Zero Repetição de Atalhos**: Mantém o combate travado sem spam indevido de teclas.

### 11. Logger Centralizado & HUD Overlay (`src/utils/logger.py` + `src/utils/overlay.py`)
- **Logger Central**: Formatação padronizada por categorias (`HEALER`, `COMBAT`, `PZ`, `STATE`, `SYSTEM`).
- **Sincronização para OBS**: Exportação contínua para `logs_hud.txt` (Fonte de texto GDI+ no OBS).
- **HUD Transparente On-Screen**: Renderização em tempo real do estado central e modo ativo (`HP`, `MP`, `PZ`, `MODE`) + Click-Through (`WS_EX_TRANSPARENT`).
- **Módulo de Humanização (`src/utils/humanizer.py`)**: Delays com Curva de Gauss, retenção de teclas entre 30ms-75ms e Curvas de Bézier.

---

## ⚙️ Como Calibrar ROIs e Utilizar Perfis

### 🎯 Calibração Interativa de ROIs
Para recalibrar as regiões de interesse da tela para uma resolução ou layout de interface diferente:

```bash
# Executa a calibração capturando a janela do Projetor OBS ao vivo
python tools/calibrate_roi.py

# Salva diretamente o resultado em um perfil em config/profiles/
python tools/calibrate_roi.py --save-profile 1920x1080
```

### 🎮 Executando o Bot com Perfis
O sistema carrega a configuração base de `config/default.yaml` e pode mesclar parâmetros de um perfil de sobreposição:

```bash
# Execução padrão (utiliza config/default.yaml)
python -m src.main

# Execução utilizando um perfil específico em config/profiles/
python -m src.main --profile character-example

# Execução informando arquivo de configuração customizado
python -m src.main --config config/default.yaml --profile 1920x1080
```

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

3. **Para pausar/retomar a qualquer momento**: Pressione a tecla **`Pause`** no teclado.

---

## 📁 Estrutura do Projeto

```text
tibia-bot/
├── config/
│   ├── default.yaml               # Configuração padrão da aplicação (contém regions relativas)
│   ├── profiles/                  # Perfis de sobreposição (ex: por personagem ou resolução)
│   │   ├── 1920x1080.yaml
│   │   └── character-example.yaml
│   └── schemas/                   # JSON Schema para validação
│       └── config.schema.json
├── src/
│   ├── application/
│   │   ├── bot_engine.py          # Motor principal BotEngine (run, run_cycle, stop)
│   │   ├── scheduler.py           # LoopScheduler (frequência de loop e métricas)
│   │   └── state_machine.py       # Controlador StateMachine (hierarquia de prioridades de BotMode)
│   ├── bot/
│   │   ├── healer.py              # Módulo AutoHealer (consome GameState)
│   │   └── combat.py              # Módulo AutoAttacker (consome GameState)
│   ├── config/
│   │   ├── models.py              # Dataclasses de configuração (inclui RegionsConfig)
│   │   └── loader.py              # Carregador e validador estrito de YAML
│   ├── domain/
│   │   ├── roi.py                 # RelativeROI, AbsoluteROI e ROIResolver
│   │   ├── bot_state.py           # BotMode, StateTransition e BotState
│   │   ├── game_state.py          # PlayerState, TargetState, WindowState, CaptureState, GameState
│   │   └── analyzer.py           # GameAnalyzer (percepção -> GameState)
│   ├── infrastructure/
│   │   └── capture/               # CapturedFrame, FrameStatus e ProjectorFrameCapturer
│   │       ├── base.py
│   │       ├── frame.py
│   │       └── projector.py
│   ├── utils/
│   │   ├── window.py              # Controle Win32, foco e minimização de janelas
│   │   ├── screen.py              # Análise de amostragem e visão computacional
│   │   ├── input.py               # Simulação DirectX (pydirectinput)
│   │   ├── humanizer.py           # Delays gaussianos, key holds e curvas de Bézier
│   │   ├── logger.py              # Logger centralizado e sincronização de logs_hud.txt
│   │   └── overlay.py             # HUD Transparente On-Screen (renderiza GameState e BotState)
│   └── main.py                    # Composition Root (CLI args, config loader, DI, engine.run)
├── tools/
│   └── calibrate_roi.py           # Ferramenta interativa de calibração de ROIs
├── templates/                     # Imagens base para Template Matching (pz.png, target_red.png)
├── tests/                         # Utilitários e testes automatizados
│   ├── unit/
│   │   ├── test_config.py         # Testes unitários do sistema de configuração
│   │   ├── test_roi.py            # Testes unitários da resolução proporcional de ROIs
│   │   ├── test_capture.py        # Testes unitários da captura de infraestrutura
│   │   ├── test_game_state.py     # Testes unitários do estado central imutável
│   │   ├── test_state_machine.py # Testes unitários da máquina de estados finitos
│   │   └── test_engine.py        # Testes unitários do motor BotEngine e LoopScheduler
│   ├── test_bars.py               # Teste de leitura de HP/MP/Status
│   ├── test_pz.py                 # Teste de detecção dinâmica de PZ
│   ├── test_combat.py             # Teste de combate e Battle List
│   ├── test_killswitch.py         # Teste da tecla de pânico (Pause)
│   ├── test_humanizer.py          # Teste de delays e curvas de Bézier
│   ├── test_overlay.py            # Teste do HUD transparente de tela
│   ├── get_roi.py                 # Seletor interativo de coordenadas de ROI
│   └── get_mouse_pos.py           # Inspetor de posição do cursor
├── launcher.py                    # Atalho/Iniciador principal na raiz
├── requirements.txt               # Dependências do Python
├── AGENTS.md                      # Diretrizes para Agentes de IA
├── NEXT_STEPS.md                  # Roadmap e próximos passos do projeto
└── README.md                      # Documentação principal
```

---

## ⚠️ Isenção de Responsabilidade (Disclaimer)

Este projeto tem fins estritamente de estudo e aprendizado sobre visão computacional e automação. O uso de softwares de automação (bots) viola os Termos de Serviço do Tibia (CipSoft) e pode resultar na exclusão permanente da sua conta. Use por sua conta e risco.
