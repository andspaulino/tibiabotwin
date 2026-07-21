# 📋 Próximos Passos (Next Steps) - Tibia Bot

Documento de planejamento detalhado com as próximas etapas de desenvolvimento do bot.

---

## 📊 Estado Atual do Projeto

- [x] **Iniciador & Ocultador de Janela**: Verificação de janelas do Tibia e OBS Studio/Projetor (`launcher.py`).
- [x] **Opacidade Win32**: Ocultação com opacidade 1 e restauração automática ao encerrar (`src/utils/window.py`).
- [x] **Arquitetura de Código**: Organização modular de pastas (`src/`, `src/utils/`, `src/bot/`, `tests/`, `templates/`).
- [x] **Ferramentas de Captura & Inspeção**: Seletor visual de ROI (`tests/get_roi.py`) e inspetor de cursor (`tests/get_mouse_pos.py`).
- [x] **Mapeamento de ROIs (Projetor OBS)**:
  - **Barra de Vida (HP)**: `{'top': 0, 'left': 359, 'width': 539, 'height': 20}`
  - **Barra de Mana (MP)**: `{'top': 1, 'left': 1024, 'width': 537, 'height': 19}`
  - **Barra de Status**: `{'top': 1, 'left': 915, 'width': 110, 'height': 18}`
- [x] **Leitura de Porcentagem & Validação**: Funções `get_hp_percentage()`, `get_mp_percentage()` e `get_status_bar_activity()` implementadas e testadas com 100% de precisão (`tests/test_bars.py`).

---

## 🎯 Fase 1: Processamento de Imagem & ROIs (`src/utils/screen.py`)

- [x] **Mapeamento de ROIs (HP, MP e Status)**: Mapeadas via `tests/get_roi.py` e salvas em `capturas.txt`.
- [x] **Leitura de Porcentagem de HP / MP / Status**: Verificação por amostragem de pixels e detecção de atividade na barra de status.
- [ ] **Integração da Captura no Loop Principal**:
  - Conectar a captura em tempo real em `src/main.py` com `ScreenCapturer.capture_window_client_area(hwnd_obs)`.
- [ ] **Mapeamento da Battle List**:
  - Mapear as coordenadas da **Battle List** para o módulo de combate.

---

## 🏥 Fase 2: Cura Automática Avançada (`src/bot/healer.py`)

- [ ] **Integração das Porcentagens de HP/MP com as Hotkeys**:
  - Conectar os valores de `get_hp_percentage()` e `get_mp_percentage()` ao método `check_and_heal()`.
- [ ] **Regras de Prioridade e Limiares (Thresholds)**:
  - **Cura de Emergência**: HP < 40% -> Ativar poção de vida ou cura forte (ex: `F3`).
  - **Cura Primária**: HP < 80% -> Ativar magia de cura (ex: `F1`).
  - **Manutenção de Mana**: MP < 60% -> Usar poção de mana (ex: `F2`).
- [ ] **Gerenciador de Cooldowns & Timers**:
  - Respeitar o tempo de recarga global do Tibia (1.0s / 2.0s) entre o uso de magias e poções.
  - Variação aleatória humanizada de delay (ex: +15ms a +50ms) via `src/utils/input.py`.

---

## ⚔️ Fase 3: Combate & Targeting (`src/bot/combat.py`)

- [ ] **Detecção de Criaturas**:
  - Reconhecimento de alvos na Battle List via OpenCV (`template matching`).
- [ ] **Seleção de Alvo Automática**:
  - Enviar atalho de seleção de alvo (ex: `Space` ou `ESC` para desmarcar).
  - Verificar se a barra de vida da ativada contém a moldura de seleção vermelha.

---

## 🛡️ Fase 4: Segurança & Recursos de Controle

- [ ] **Hotkey de Emergência (Killswitch)**:
  - Integrar a biblioteca `keyboard` para escutar uma tecla de pânico (ex: `F12` ou `Pause`) que pausa imediatamente o bot.
- [ ] **Rotina Anti-AFK**:
  - Executar rotações de direção esporádicas (`Ctrl + Setas`) para evitar desconexão por inatividade.

---

## 🚀 Próxima Tarefa Recomendada

Para dar sequência à **Fase 2 (AutoHealer)**:
1. Conectar a captura contínua de tela do Projetor OBS no `src/main.py`.
2. Executar a checagem em tempo real de `get_hp_percentage()` e `get_mp_percentage()` e acionar as hotkeys via `src/utils/input.py`.
