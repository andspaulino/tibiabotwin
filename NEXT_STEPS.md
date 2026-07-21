# 📋 Próximos Passos (Next Steps) - Tibia Bot

Documento de planejamento detalhado com as próximas etapas de desenvolvimento do bot.

---

## 📊 Estado Atual do Projeto

- [x] **Iniciador & Ocultador de Janela**: Verificação de janelas do Tibia e OBS Studio/Projetor (`launcher.py`).
- [x] **Opacidade Win32**: Ocultação com opacidade 1 e restauração automática ao encerrar (`src/utils/window.py`).
- [x] **Arquitetura de Código**: Organização modular de pastas (`src/`, `src/utils/`, `src/bot/`, `tests/`, `templates/`).
- [x] **Captura em Tempo Real no Loop Principal**: Leitura ao vivo da área útil do Projetor OBS (`src/main.py`).
- [x] **Mapeamento & Leitura de ROIs (Projetor OBS)**:
  - **Barra de Vida (HP)**: `{'top': 0, 'left': 359, 'width': 539, 'height': 20}` (Leitura por dominância de cor BGR).
  - **Barra de Mana (MP)**: `{'top': 1, 'left': 1024, 'width': 537, 'height': 19}` (Filtro por canal Azul desconsiderando textos e bordas).
  - **Barra de Status**: `{'top': 1, 'left': 915, 'width': 110, 'height': 18}`.
- [x] **Detecção de Protection Zone (PZ)**:
  - Template matching no ícone da pombinha (`templates/pz.png`) + validação de cor azul (`is_in_pz()`).
  - Log em tempo real de eventos de entrada e saída de PZ.
- [x] **Módulo AutoHealer (`src/bot/healer.py`)**:
  - Hotkey `1`: Magia de Cura (HP <= 90%).
  - Hotkey `2`: Poção de Mana (MP <= 50%).
  - Hotkey `3`: Poção de Vida de Emergência (HP <= 30%).
  - Gerenciador de cooldowns (1.0s) e pausa automática em PZ.

---

## 🎯 Fase 1: Processamento de Imagem & ROIs (`src/utils/screen.py`)

- [x] **Mapeamento de ROIs (HP, MP e Status)**: Mapeadas via `tests/get_roi.py` e salvas em `capturas.txt`.
- [x] **Leitura de Porcentagem de HP / MP / Status**: Verificação por amostragem de pixels e detecção de atividade na barra de status.
- [x] **Integração da Captura no Loop Principal**: Conectada no `src/main.py` via `ScreenCapturer.capture_window_client_area(hwnd_obs)`.
- [ ] **Mapeamento da Battle List**:
  - Usar `tests/get_roi.py` para mapear as coordenadas da **Battle List**.

---

## 🏥 Fase 2: Cura Automática Avançada (`src/bot/healer.py`)

- [x] **Integração das Porcentagens de HP/MP com as Hotkeys**: Conectadas no método `check_and_heal(hp_pct, mp_pct, in_pz)`.
- [x] **Regras de Prioridade e Limiares (Thresholds)**:
  - **Hotkey 3**: Poção de Vida Emergência (HP <= 30%).
  - **Hotkey 1**: Magia de Cura Primária (HP <= 90%).
  - **Hotkey 2**: Poção de Mana (MP <= 50%).
- [x] **Gerenciador de Cooldowns & Proteção PZ**:
  - Respeita tempo de recarga entre magias e poções (1.0s) e pausa em Protection Zone.

---

## ⚔️ Fase 3: Combate & Targeting (`src/bot/combat.py`)

- [ ] **Mapeamento da ROI da Battle List**:
  - Capturar coordenadas e dimensões da Battle List no projetor OBS.
- [ ] **Detecção de Criaturas**:
  - Reconhecimento de alvos na Battle List via OpenCV (`template matching`).
- [ ] **Seleção de Alvo Automática**:
  - Enviar atalho de seleção de alvo (ex: `Space` ou `ESC` para desmarcar).
  - Verificar se o alvo selecionado contém a moldura vermelha de ataque.

---

## 🛡️ Fase 4: Segurança & Recursos de Controle

- [ ] **Hotkey de Emergência (Killswitch)**:
  - Integrar a biblioteca `keyboard` para escutar uma tecla de pânico (ex: `F12` ou `Pause`) que pausa imediatamente o bot.
- [ ] **Rotina Anti-AFK**:
  - Executar rotações de direção esporádicas (`Ctrl + Setas`) para evitar desconexão por inatividade.

---

## 🚀 Próxima Tarefa Recomendada

Para dar início à **Fase 3 (Combate & AutoAttacker)**:
1. Usar `python tests/get_roi.py` para capturar a ROI da **Battle List**.
2. Criar a lógica de verificação de criaturas e envio do comando de ataque (`Space`).
