# 📋 Próximos Passos (Next Steps) - Tibia Bot

Documento de planejamento detalhado com as próximas etapas de desenvolvimento do bot.

---

## 📊 Estado Atual do Projeto

- [x] **Iniciador & Ocultador de Janela**: Verificação de janelas do Tibia e OBS Studio/Projetor (`launcher.py`).
- [x] **Opacidade Win32**: Ocultação com opacidade 1 e restauração automática ao encerrar (`src/utils/window.py`).
- [x] **Segurança de Foco & Minimizado**:
  - Trava por foco ativo `is_window_active(hwnd_tibia)` (pausa automática ao alternar para outros programas).
  - Trava por janela minimizada `is_window_minimized(hwnd_tibia)`.
- [x] **Killswitch de Emergência (Botão de Pânico `Pause`)**:
  - Tecla global `Pause` integrada via `keyboard.on_press_key()` para pausar/retomar todas as ações do bot instantaneamente (`src/main.py`).
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

## 🎒 Fase 4: Auto-Loot & Recursos Avançados de Movimento

- [x] **Hotkey de Emergência (Killswitch)**:
  - Tecla de pânico (`Pause`) integrada para alternar pause/play do bot instantaneamente.
- [ ] **Coleta Automática de Loot (Auto-Loot)**:
  - Definir atalhos/cliques de botão direito sobre o corpo do monstro derrotado.
- [ ] **Rotina Anti-AFK**:
  - Viradas de direção esporádicas (`Ctrl + Setas`) com intervalo humanizado para evitar desconexão por inatividade.

---

## 🚀 Próxima Tarefa Recomendada

Para dar sequência à **Fase 4**:
1. Mapear a área central da tela do jogo para o módulo de **Auto-Loot**.
2. Criar o algoritmo de clique direito no centro do personagem/monstro derrotado.
