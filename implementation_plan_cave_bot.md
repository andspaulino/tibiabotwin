# Plano de Implementação Definitivo — Cavebot por Minimap (Fases 12A a 12E)

Este documento estabelece o plano final e validado para a implementação da **Fase 12 (Cavebot e Navegação por Minimap)** do projeto `tibiabotwin`, respeitando estritamente o fluxo arquitetural `Captura → Percepção → Estado → Decisão → Execução`, o snapshot imutável `GameState`, a captura única por ciclo e a segurança operacional.

---

## 🏗️ Separação Estrita de Responsabilidades e Módulos

### 1. Percepção no Domínio (`src/domain/minimap.py` e `src/domain/game_state.py`)
- `MarkerDetection(template_id: str, center: tuple[int, int], confidence: float)`: Percepção de um marcador candidato no minimap.
- `MinimapState(available: bool, center: tuple[int, int] | None, markers: tuple[MarkerDetection, ...], cross_confidence: float | None)`: Estado imutável do minimap incorporado no `GameState.minimap`.
- `MinimapAnalyzer` (`src/infrastructure/vision/minimap_analyzer.py`): Analisa o frame capturado e detecta todos os marcadores visíveis sem conhecimento sobre waypoints ou rotas.

### 2. Seleção e Decisão (`src/bot/cavebot/`)
- `MarkerSelector`: Filtra e seleciona a melhor `MarkerDetection` do `GameState.minimap` aplicando o `expected_region` e `match_threshold` do waypoint atual.
- `models.py`: Modelos específicos da automação (`WaypointType`, `Waypoint`, `HuntRoute`, `RouteSettings`, `MovementState`, `CavebotStatus`, `CavebotIntent`).
- `MovementController`: Recebe `game_state` e o waypoint ativo. Gera intenção de movimento sem capturar nem recortar frames isoladamente.
- `StuckDetector`: Avalia progresso considerando `progress_epsilon_pixels` (1.5px). Se exceder retentativas, entra em `CavebotStatus.STUCK` sem pular waypoints.
- `RouteRunner`: Controla o índice do waypoint atual e orquestra a progressão.
- `CavebotController`: Ponto de entrada do módulo de Cavebot, produzindo `CavebotIntent`.

---

## 📁 Estrutura de Arquivos Final

```text
src/
├── domain/
│   ├── actions.py           # BotAction, ActionPriority, KeyPayload, MouseClickPayload
│   ├── minimap.py           # MarkerDetection, MinimapState
│   └── game_state.py        # Adição de minimap: MinimapState
├── infrastructure/
│   └── vision/
│       └── minimap_analyzer.py # Percepção pura do minimap (sem regras da rota)
├── config/
│   └── route_loader.py      # Parser e validador de rotas JSON
└── bot/
    └── cavebot/
        ├── __init__.py
        ├── models.py            # Modelos específicos do Cavebot (Waypoint, HuntRoute, etc)
        ├── marker_selector.py   # Seleção de marcador aplicável ao waypoint ativo
        ├── movement_controller.py # Geração da ação MARKER_CLICK baseada em GameState.minimap
        ├── stuck_detector.py     # Progresso com epsilon, retentativas e detecção de travamento
        ├── route_runner.py       # Controle de índice de waypoint e retomada pós-combate
        └── cavebot_controller.py # Avalia GameState e produz CavebotIntent

config/
└── hunts/
    └── default_hunt.json

tests/
└── unit/
    ├── test_minimap_analyzer.py
    ├── test_marker_selector.py
    ├── test_stuck_detector.py
    ├── test_route_runner.py
    └── test_engine_cavebot.py
```

---

## 🎯 Modelos de Dados & Intenções

### ActionPriority e Payloads (`src/domain/actions.py`)
```python
class ActionPriority(IntEnum):
    MOVEMENT = 40
    ATTACK = 60
    MANA = 70
    HEAL = 80
    EMERGENCY = 100

@dataclass(frozen=True)
class KeyPayload:
    key: str

@dataclass(frozen=True)
class MouseClickPayload:
    x: int
    y: int
    button: str = "left"

ActionPayload = KeyPayload | MouseClickPayload

@dataclass(frozen=True)
class BotAction:
    action_type: ActionType
    priority: int
    payload: ActionPayload
    reason: str
    cooldown_ms: int = 0
    cooldown_key: str | None = None
```

### Operational Intent (`CavebotIntent`)
```python
@dataclass(frozen=True)
class CavebotIntent:
    active: bool
    movement_requested: bool
    action: BotAction | None
    status: CavebotStatus
    reason: str
```

---

## 🔄 Fluxo de Integração no Engine (`BotEngine.run_cycle`)

```python
# 1. Percepção (Visão única no frame)
minimap_state = self.minimap_analyzer.analyze(frame, minimap_roi)
game_state = self.analyzer.analyze(frame, window_state, minimap_state, self.config)

# 2. Avaliação do Cavebot
cavebot_intent = self.cavebot_controller.evaluate(game_state)

# 3. Transição na Máquina de Estados
bot_state = self.state_machine.update(
    game_state,
    killswitch_paused=self.killswitch_paused,
    movement_requested=cavebot_intent.movement_requested
)

# 4. Resolução de Ações (DecisionController)
extra_actions = [cavebot_intent.action] if cavebot_intent.action else []
resolved_actions = self.decision_controller.resolve(
    proposed_actions + extra_actions, game_state, bot_state, config=self.config
)

# 5. Execução (ActionExecutor)
self.action_executor.execute(resolved_actions, game_state, observe_only=self.observe_only)
```

---

## 🛠️ Roteiro Incremental de Implementação (Fases 12A a 12E)

### 🔹 Fase 12A — Percepção do Minimap
- Criar `src/domain/minimap.py` (`MarkerDetection`, `MinimapState`).
- Atualizar `GameState` em `src/domain/game_state.py`.
- Criar `src/infrastructure/vision/minimap_analyzer.py` (detecção pura de marcadores e centro).
- Adicionar `test_minimap_analyzer.py` com fixtures de minimap.

### 🔹 Fase 12B — Payloads de Mouse & ActionExecutor
- Refatorar `BotAction` em `src/domain/actions.py` (`KeyPayload`, `MouseClickPayload`, `cooldown_key`, `ActionPriority`).
- Atualizar `ActionExecutor` em `src/application/action_executor.py` para processar `MouseClickPayload`.
- Atualizar `DecisionController` para validar `cooldown_key`.

### 🔹 Fase 12C — Seleção de Marcador, MovementController e StuckDetector
- Criar `src/bot/cavebot/models.py`.
- Criar `src/bot/cavebot/marker_selector.py` (aplica `expected_region` e `match_threshold`).
- Criar `src/bot/cavebot/stuck_detector.py` (progresso com `progress_epsilon_pixels`, retentativas e travamento).
- Criar `src/bot/cavebot/movement_controller.py` (gera `BotAction(action_type=ActionType.MOVE)`).
- Adicionar `test_marker_selector.py` e `test_stuck_detector.py`.

### 🔹 Fase 12D — Executor de Rota & Integração no Engine
- Criar `src/config/route_loader.py` (parser e validador de rotas JSON em `config/hunts/`).
- Criar `src/bot/cavebot/route_runner.py` (gerencia waypoints, ciclo e reaquisição do marcador pós-combate).
- Criar `src/bot/cavebot/cavebot_controller.py` (produz `CavebotIntent`).
- Atualizar `StateMachine` e `BotEngine` para integrar `CavebotIntent`.
- Adicionar `test_route_runner.py` e `test_engine_cavebot.py`.

### 🔹 Fase 12E — Ações Avançadas
- Extensão do `RouteRunner` para suporte a `STAND`, `ACTION`, `LABEL`, `GOTO` e transição de andares.

---

## 🧪 Plano de Verificação por Fases

1. **Fase 12A:** `pytest tests/unit/test_minimap_analyzer.py`
2. **Fase 12B:** `pytest tests/unit/test_action_executor.py`
3. **Fase 12C:** `pytest tests/unit/test_marker_selector.py tests/unit/test_stuck_detector.py`
4. **Fase 12D:** `pytest tests/unit/test_route_runner.py tests/unit/test_engine_cavebot.py`
5. **Modo Observação (Simulação Completa):** `python launcher.py --observe-only --hunt config/hunts/default_hunt.json`
