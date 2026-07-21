# 📋 Próximos Passos (Next Steps) - Tibia Bot

Documento de planejamento detalhado com as próximas etapas de desenvolvimento do bot.

---

## 📊 Estado Atual do Projeto

- [x] **Iniciador & Ocultador de Janela**: Verificação de janelas do Tibia e OBS Studio/Projetor (`launcher.py`).
- [x] **Opacidade Win32**: Ocultação com opacidade 1 e restauração automática ao encerrar (`src/utils/window.py`).
- [x] **Segurança de Foco & Minimizado**:
  - Trava por foco ativo `is_window_active(hwnd_tibia)` (pausa automática ao alternar para outros programas).
  - Trava por janela minimizada `is_window_minimized(hwnd_tibia)`.
- [x] **Arquitetura de Código**: Organização modular de pastas (`src/`, `src/utils/`, `src/bot/`, `tests/`, `templates/`).
- [x] **Mapeamento & Leitura de ROIs (Projetor OBS)**:
  - **Barra de Vida (HP)**: `{'top': 0, 'left': 359, 'width': 539, 'height': 20}`.
  - **Barra de Mana (MP)**: `{'top': 1, 'left': 1024, 'width': 537, 'height': 19}`.
  - **Barra de Status**: `{'top': 1, 'left': 915, 'width': 110, 'height': 18}`.
  - **Battle List**: `{'top': 390, 'left': 1744, 'width': 111, 'height': 98}`.
- [x] **Detecção de Protection Zone (PZ)**:
  - Template matching no ícone da pombinha (`templates/pz.png`) + validação de cor azul (`is_in_pz()`).
  - Log de evento ao entrar/sair de PZ.
- [x] **Módulo AutoHealer (`src/bot/healer.py`)**:
  - Hotkey `1`: Magia de Cura (HP <= 90%, execução silenciosa).
  - Hotkey `2`: Poção de Mana (MP <= 50%, execução silenciosa).
  - Hotkey `3`: Poção de Vida de Emergência (HP <= 30%, registrado no log).
- [x] **Módulo AutoAttacker (`src/bot/combat.py`)**:
  - Detecção de alvos na Battle List com filtro de densidade de pixels de HP bar (`hp_pixels >= 10`).
  - Reconhecimento de alvo ativo via densidade de cor vermelha pura + Template Matching (`templates/target_red.png` 20x20).
  - Envio de atalho de ataque (`Space`) sem repetição spammada.
- [x] **Sistema Centralizado de Logs & HUD (`src/utils/logger.py` + `src/utils/overlay.py`)**:
  - Singleton `Logger` com categorias padronizadas e exportação automática para `logs_hud.txt` (OBS Studio).
  - Overlay de tela transparente em formato "Click-Through" (`WS_EX_TRANSPARENT`) sem timestamps no HUD visual.
  - Variação humanizada de delays gaussianos (`src/utils/humanizer.py`).

---

## 🎯 Fase 1: Core & Processamento de Imagem (`src/utils/screen.py`)

- [x] **Mapeamento de ROIs (HP, MP, Status e Battle List)**: Mapeadas via `tests/get_roi.py` e salvas em `capturas.txt`.
- [x] **Leitura de Porcentagem de HP / MP / Status**: Verificação por amostragem de pixels e atividade.
- [x] **Integração da Captura no Loop Principal**: Conectada em `src/main.py` via `ScreenCapturer.capture_window_client_area(hwnd_obs)`.
- [x] **Mapeamento da Battle List**: ROI mapeada em `top: 390, left: 1744, width: 111, height: 98`.

---

## 🏥 Fase 2: Cura Automática & Proteções (`src/bot/healer.py`)

- [x] **Integração de Porcentagens e Hotkeys**: Conectadas em `check_and_heal(hp_pct, mp_pct, in_pz)`.
- [x] **Regras de Prioridade e Silenciamento de Logs**:
  - Hotkey 3 (Poção de Vida): Registrada no log apenas em emergências (`HP <= 30%`).
  - Hotkeys 1 e 2 (Magia e Mana): Executadas em modo silencioso sem poluir telas.
- [x] **Gerenciador de Cooldowns & Pausa PZ**: Tempo de recarga humanizado (1.0s) e pausa em PZ.

---

## ⚔️ Fase 3: Combate & Targeting (`src/bot/combat.py`)

- [x] **Mapeamento da Battle List**: ROI `top: 390, left: 1744`.
- [x] **Detecção de Criaturas**: Filtro de densidade de pixels de barrinha de vida (`hp_pixels >= 10`).
- [x] **Seleção de Alvo Automática & Target Box**:
  - Detecção da moldura vermelha de alvo ativo com `templates/target_red.png`.
  - Envio de atalho de ataque (`Space`) sem repetição indevida.

---

## 🎒 Fase 4: Auto-Loot & Recursos Avançados de Movimento

- [ ] **Coleta Automática de Loot (Auto-Loot)**:
  - Definir atalhos/cliques de botão direito sobre o corpo do monstro derrotado.
- [ ] **Hotkey de Emergência (Killswitch)**:
  - Tecla de pânico (ex: `Pause` / `F12`) para alternar pause/play do bot instantaneamente.
- [ ] **Rotina Anti-AFK**:
  - Viradas de direção esporádicas (`Ctrl + Setas`) com intervalo humanizado para evitar desconexão por inatividade.

---

## 🚀 Próxima Tarefa Recomendada

Para dar início à **Fase 4**:
1. Implementar o **Killswitch de emergência** (tecla de pânico para pausar o bot instantaneamente).
2. Mapear a área central da tela do jogo para o módulo de **Auto-Loot**.
