# Plano de Implementação Definitivo — Cavebot por Minimap

## Fases 12A a 12E

Este documento estabelece o plano final para a implementação da **Fase 12 — Cavebot e Navegação por Minimap** no projeto `tibiabotwin`.

A implementação deve respeitar estritamente o fluxo arquitetural:

```text
Captura → Percepção → Estado → Decisão → Execução
```

Também devem ser preservados os seguintes princípios:

* captura única do frame por ciclo;
* snapshot imutável por meio de `GameState`;
* separação entre percepção visual e regras da rota;
* módulos de automação apenas propõem ações;
* resolução centralizada de prioridades;
* execução centralizada de inputs;
* falha segura quando o estado visual for inválido ou ambíguo;
* nenhuma progressão automática de waypoint em caso de travamento;
* compatibilidade com o modo `--observe-only`.

---

## Status de implementação — 2026-07-23

| Fase | Estado | Evidência e escopo atual |
| --- | --- | --- |
| 12A — Percepção | Concluída em observação | `GameState.minimap`, ROI relativa calibrada, `flag0` e `flag1` detectados no frame único do Projetor. Frames reais ainda não foram versionados como fixtures. |
| 12B — Ações | Concluída | `KeyPayload` e `MouseClickPayload` centralizados; `--observe-only` nunca envia input e não consome cooldown físico. |
| 12C — Waypoint único | Concluída em observação | Seleção, chegada, cooldown de simulação e `STUCK` foram validados sem clique físico. |
| 12D — Rota sequencial | Parcialmente concluída | `--hunt`, JSON validado, `RouteRunner` e rota `flag0 → flag1` foram validados em tempo real em `--observe-only`, incluindo conclusão sem loop. |
| 12E — Fluxos avançados | Não iniciada | `STAND`, `ACTION`, `LABEL`, `GOTO` e transições permanecem fora do escopo atual. |

### Limites obrigatórios do estado atual

* O Cavebot só encaminha ações ao executor quando `--observe-only` está ativo; as ações são logs simulados.
* Nenhuma conversão confiável de coordenadas do frame do Projetor para coordenadas de tela foi implementada. Portanto, **cliques físicos do Cavebot não estão autorizados**.
* A retomada do mesmo waypoint após combate/PZ é preservada pelo `RouteRunner`, mas ainda requer teste de integração manual dedicado.
* O loop de uma rota possui teste unitário; ainda requer validação manual no Projetor.

---

# 1. Objetivo

Implementar um Cavebot capaz de navegar pelo minimapa utilizando marcadores visuais configurados previamente no jogo.

O módulo deverá:

1. detectar todos os marcadores visíveis no minimapa;
2. identificar o marcador correspondente ao waypoint atual;
3. clicar sobre o marcador selecionado;
4. acompanhar sua aproximação ao centro do minimapa;
5. confirmar a chegada utilizando distância em pixels;
6. interromper o movimento durante estados prioritários;
7. retomar o mesmo waypoint após combate ou outra interrupção;
8. detectar ausência de progresso;
9. realizar retentativas limitadas;
10. entrar em estado seguro quando não conseguir continuar.

---

# 2. Princípios Fundamentais

## 2.1 Posição do personagem no minimapa

O personagem permanece visualmente no centro da ROI do minimapa enquanto o conteúdo do mapa se desloca.

Portanto, a posição principal do personagem será definida como:

```python
player_position = minimap_state.center
```

A chegada ao waypoint será confirmada por:

```python
distance(marker.center, minimap_state.center) <= arrival_radius_pixels
```

O template `cross.png` não será utilizado como mecanismo principal de rastreamento a cada ciclo.

Sua função será restrita a:

* calibração inicial da ROI;
* validação do layout;
* auditoria de integridade do minimapa;
* detecção de alterações inesperadas na interface.

---

## 2.2 Captura única por ciclo

Nenhum componente do Cavebot poderá capturar um novo frame de forma independente.

O frame será obtido uma única vez pelo ciclo principal do engine e compartilhado com os componentes de percepção.

O fluxo esperado será:

```text
Frame capturado
    ↓
GameAnalyzer
    ↓
MinimapAnalyzer
    ↓
GameState.minimap
    ↓
CavebotController
    ↓
DecisionController
    ↓
ActionExecutor
```

O `MovementController`, o `MarkerSelector`, o `RouteRunner` e o `StuckDetector` não poderão acessar diretamente:

* OBS;
* janela do jogo;
* APIs de captura;
* OpenCV sobre um novo frame;
* estado visual fora do `GameState`.

---

## 2.3 Separação entre percepção e decisão

O `MinimapAnalyzer` será responsável exclusivamente por perceber o minimapa.

Ele deverá:

* recortar a ROI;
* calcular o centro;
* detectar todos os marcadores conhecidos;
* informar a confiança das detecções;
* validar opcionalmente o template `cross.png`;
* retornar um `MinimapState` imutável.

O analyzer não poderá conhecer:

* waypoint atual;
* rota ativa;
* `expected_region`;
* `match_threshold` específico do waypoint;
* índice da rota;
* regras de seleção;
* estado do Cavebot.

As regras da rota serão aplicadas posteriormente pelo `MarkerSelector`.

---

## 2.4 Falha segura

Quando não houver informação visual confiável, o Cavebot não deverá gerar cliques.

Os seguintes casos deverão bloquear movimento:

* frame inválido;
* captura congelada;
* ROI do minimapa indisponível;
* `MinimapState.available` igual a `False`;
* `MinimapState.bounds` ausente;
* centro do minimapa ausente;
* marcador abaixo do limite de confiança;
* múltiplos candidatos sem critério seguro de desempate;
* validação do `cross.png` indicando layout incompatível;
* waypoint inválido;
* rota inválida;
* estado do Cavebot igual a `STUCK` ou `ERROR`;
* modo global diferente de `MOVING`.

Em caso de incerteza, a regra será:

```text
Não clicar.
Não avançar waypoint.
Registrar o motivo.
```

---

# 3. Separação de Responsabilidades

## 3.1 Domínio de percepção

### `src/domain/minimap.py`

Responsável pelos modelos imutáveis relacionados à percepção do minimapa.

Modelos:

* `MarkerDetection`;
* `MinimapState`;
* tipo ou estrutura utilizada para representar os limites absolutos da ROI.

### `src/domain/game_state.py`

Responsável por incorporar:

```python
minimap: MinimapState
```

ao snapshot central do jogo.

---

## 3.2 Infraestrutura de visão

### `src/infrastructure/vision/minimap_analyzer.py`

Responsável por:

* receber o frame já capturado;
* receber ou resolver a ROI configurada do minimapa;
* recortar a ROI;
* detectar todos os templates de marcador;
* calcular o centro local da ROI;
* retornar coordenadas locais à ROI;
* informar os limites absolutos da ROI;
* produzir um `MinimapState`.

O analyzer não aplicará regras de waypoint.

---

## 3.3 Domínio de ações

### `src/domain/actions.py`

Responsável por:

* `BotAction`;
* `ActionType`;
* `ActionPriority`;
* `KeyPayload`;
* `MouseClickPayload`;
* união tipada `ActionPayload`;
* informações de cooldown;
* justificativa da ação.

---

## 3.4 Automação do Cavebot

### `src/bot/cavebot/marker_selector.py`

Responsável por selecionar o marcador aplicável ao waypoint atual.

Aplicará:

* `template_id`;
* `match_threshold`;
* `expected_region`;
* critérios de desempate;
* proximidade esperada;
* rejeição por ambiguidade.

### `src/bot/cavebot/movement_controller.py`

Responsável por:

* receber o `GameState`;
* receber o waypoint atual;
* receber o marcador selecionado;
* calcular distância ao centro;
* converter coordenadas locais da ROI em coordenadas absolutas;
* gerar uma intenção de clique;
* informar chegada;
* nunca executar diretamente o input.

### `src/bot/cavebot/stuck_detector.py`

Responsável por:

* acompanhar convergência da distância;
* ignorar oscilações pequenas;
* controlar tempo sem progresso;
* controlar quantidade de retentativas;
* informar quando o movimento está travado.

### `src/bot/cavebot/route_runner.py`

Responsável por:

* controlar o índice do waypoint atual;
* avançar somente após confirmação de chegada;
* aplicar loop quando configurado;
* preservar o waypoint durante combate;
* reacquirir o marcador após interrupções;
* finalizar rotas sem loop;
* nunca pular waypoint devido a travamento.

### `src/bot/cavebot/cavebot_controller.py`

Ponto de entrada da automação.

Responsável por:

* consultar o estado da rota;
* inspecionar o `GameState`;
* informar se existe intenção de movimento;
* produzir `CavebotIntent`;
* respeitar o modo global calculado pela máquina de estados;
* não produzir ações quando o modo final não for `MOVING`.

---

## 3.5 Aplicação

### `src/application/state_machine.py`

Responsável por:

* calcular o modo global;
* inserir o novo modo `BotMode.MOVING`;
* impedir movimento em estados prioritários;
* manter ordem determinística de transição.

### `src/application/decision_controller.py`

Responsável por:

* receber todas as ações propostas;
* comparar prioridades;
* validar compatibilidade com o modo global;
* descartar movimentos durante combate, pausa ou estado inseguro;
* validar cooldown sem registrá-lo antecipadamente;
* selecionar as ações finais.

### `src/application/action_executor.py`

Responsável por:

* executar `KeyPayload`;
* executar `MouseClickPayload`;
* respeitar `--observe-only`;
* registrar cooldown somente após execução efetiva;
* registrar sucesso ou falha da execução.

### `src/application/bot_engine.py`

Responsável por:

* coordenar os módulos;
* manter o fluxo de alto nível;
* não implementar regras internas do Cavebot;
* não conhecer detalhes dos templates ou waypoints.

---

# 4. Estrutura Final de Arquivos

```text
src/
├── domain/
│   ├── actions.py
│   ├── bot_state.py
│   ├── game_state.py
│   └── minimap.py
│
├── infrastructure/
│   └── vision/
│       └── minimap_analyzer.py
│
├── config/
│   └── route_loader.py
│
├── bot/
│   ├── healer.py
│   ├── combat.py
│   └── cavebot/
│       ├── __init__.py
│       ├── models.py
│       ├── marker_selector.py
│       ├── movement_controller.py
│       ├── stuck_detector.py
│       ├── route_runner.py
│       └── cavebot_controller.py
│
└── application/
    ├── action_executor.py
    ├── bot_engine.py
    ├── decision_controller.py
    ├── cooldown_manager.py
    └── state_machine.py

config/
└── hunts/
    └── default_hunt.json

templates/
└── markers/
    ├── cross.png
    ├── flag0.png
    ├── flag1.png
    └── ...

tests/
├── fixtures/
│   └── minimap/
│       ├── marker_single.png
│       ├── marker_multiple.png
│       ├── marker_missing.png
│       └── invalid_layout.png
│
├── unit/
│   ├── test_actions.py
│   ├── test_action_executor.py
│   ├── test_state_machine.py
│   ├── test_minimap_analyzer.py
│   ├── test_marker_selector.py
│   ├── test_movement_controller.py
│   ├── test_stuck_detector.py
│   ├── test_route_loader.py
│   ├── test_route_runner.py
│   └── test_engine_cavebot.py
│
└── integration/
    └── test_full_pipeline.py
```

---

# 5. Modelos de Percepção

## 5.1 Coordenadas

As coordenadas de `MarkerDetection.center` serão locais à ROI do minimapa.

Exemplo:

```text
ROI absoluta do minimapa:
x = 1600
y = 50
width = 200
height = 200

MarkerDetection.center:
x = 120
y = 60
```

A coordenada absoluta de clique será:

```python
screen_x = minimap.bounds.x + marker.center[0]
screen_y = minimap.bounds.y + marker.center[1]
```

Essa regra deverá ser documentada diretamente no modelo para evitar ambiguidade.

---

## 5.2 `MarkerDetection`

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class MarkerDetection:
    template_id: str
    center: tuple[int, int]
    confidence: float
```

Regras:

* `center` usa coordenadas locais da ROI;
* `confidence` deve estar entre `0.0` e `1.0`;
* o analyzer pode retornar múltiplos marcadores do mesmo template;
* nenhuma seleção de waypoint será realizada nesse estágio.

---

## 5.3 `MinimapState`

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class MinimapBounds:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class MinimapState:
    available: bool
    bounds: MinimapBounds | None
    center: tuple[int, int] | None
    markers: tuple[MarkerDetection, ...]
    cross_confidence: float | None = None
    reason: str | None = None
```

Regras:

* `center` será local à ROI;
* `bounds` será absoluto em relação ao frame ou tela projetada;
* `markers` será uma tupla imutável;
* `available=False` impedirá qualquer movimento;
* `reason` explicará indisponibilidade ou invalidação;
* `cross_confidence` será opcional e usado apenas para auditoria.

Exemplo de centro:

```python
center = (
    bounds.width // 2,
    bounds.height // 2,
)
```

---

# 6. Modelos de Ação

## 6.1 Prioridades

```python
from enum import IntEnum


class ActionPriority(IntEnum):
    MOVEMENT = 40
    ATTACK = 60
    MANA = 70
    HEAL = 80
    EMERGENCY = 100
```

Os valores deverão ser compatíveis com as prioridades já existentes no projeto.

Não deverão existir prioridades numéricas mágicas espalhadas pelos módulos.

---

## 6.2 Payloads

```python
from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True)
class KeyPayload:
    key: str


@dataclass(frozen=True)
class MouseClickPayload:
    x: int
    y: int
    button: str = "left"


ActionPayload: TypeAlias = KeyPayload | MouseClickPayload
```

---

## 6.3 `BotAction`

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class BotAction:
    action_type: ActionType
    priority: ActionPriority
    payload: ActionPayload
    reason: str
    cooldown_ms: int = 0
    cooldown_key: str | None = None
```

Regras:

* toda ação deve possuir `reason`;
* `priority` deverá usar `ActionPriority`;
* `cooldown_key` será independente do tipo da ação;
* o cooldown não será consumido quando a ação for apenas proposta;
* o cooldown não será consumido se a ação for descartada;
* o cooldown será registrado somente após execução efetiva.

Exemplo de movimento:

```python
BotAction(
    action_type=ActionType.MOVE,
    priority=ActionPriority.MOVEMENT,
    payload=MouseClickPayload(
        x=screen_x,
        y=screen_y,
        button="left",
    ),
    reason=(
        "Waypoint wp_01: marcador flag0 selecionado "
        "com confiança 0.93"
    ),
    cooldown_ms=1500,
    cooldown_key="cavebot:movement",
)
```

---

# 7. Impacto da Refatoração de `BotAction`

A migração para payloads explícitos afetará todos os produtores existentes de ações.

Exemplo anterior:

```python
BotAction(
    action_type=ActionType.HEAL,
    key="F1",
    priority=80,
)
```

Novo formato:

```python
BotAction(
    action_type=ActionType.HEAL,
    priority=ActionPriority.HEAL,
    payload=KeyPayload("F1"),
    reason="Vida abaixo do limite configurado",
    cooldown_ms=500,
    cooldown_key="healer:primary",
)
```

A Fase 12B deverá atualizar explicitamente:

```text
src/bot/healer.py
src/bot/combat.py
src/application/decision_controller.py
src/application/action_executor.py
src/application/cooldown_manager.py
tests/unit/test_actions.py
tests/unit/test_action_executor.py
tests/integration/test_full_pipeline.py
```

Qualquer outro módulo que instancie `BotAction` também deverá ser migrado.

A suíte completa deverá permanecer funcional antes do início da Fase 12C.

---

# 8. Modelos do Cavebot

## 8.1 Tipos de waypoint

```python
from enum import Enum, auto


class WaypointType(Enum):
    MARKER_CLICK = auto()
    STAND = auto()
    ACTION = auto()
    LABEL = auto()
    GOTO = auto()
```

Nas fases 12C e 12D, somente `MARKER_CLICK` deverá ser executado.

Os demais tipos serão implementados na Fase 12E.

---

## 8.2 Região esperada

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class RelativeRegion:
    x: float
    y: float
    width: float
    height: float
```

Todos os valores deverão estar entre `0.0` e `1.0`.

Exemplo:

```json
{
  "x": 0.5,
  "y": 0.0,
  "width": 0.5,
  "height": 1.0
}
```

representa a metade direita do minimapa.

---

## 8.3 Configurações da rota

```python
@dataclass(frozen=True)
class RouteSettings:
    match_threshold: float
    arrival_radius_pixels: float
    progress_epsilon_pixels: float
    stuck_timeout_ms: int
    click_cooldown_ms: int
    max_retries: int
```

Valores iniciais recomendados:

```text
match_threshold = 0.88
arrival_radius_pixels = 4.0
progress_epsilon_pixels = 1.5
stuck_timeout_ms = 15000
click_cooldown_ms = 1500
max_retries = 2
```

---

## 8.4 Waypoint

```python
@dataclass(frozen=True)
class Waypoint:
    id: str
    type: WaypointType
    marker: str | None
    expected_region: RelativeRegion | None
    match_threshold: float | None
    description: str
```

Durante as fases 12C e 12D:

* `type` deverá ser `MARKER_CLICK`;
* `marker` será obrigatório;
* `expected_region` será obrigatório inicialmente;
* `match_threshold` poderá sobrescrever o valor global da rota.

---

## 8.5 HuntRoute

```python
@dataclass(frozen=True)
class HuntRoute:
    hunt_name: str
    version: int
    loop: bool
    settings: RouteSettings
    waypoints: tuple[Waypoint, ...]
```

---

## 8.6 Estado do Cavebot

```python
from enum import Enum, auto


class CavebotStatus(Enum):
    INACTIVE = auto()
    SEARCHING_MARKER = auto()
    NAVIGATING = auto()
    ARRIVED = auto()
    WAITING_RETRY = auto()
    SUSPENDED = auto()
    COMPLETED = auto()
    STUCK = auto()
    ERROR = auto()
```

Significados:

### `INACTIVE`

Nenhuma rota está carregada ou o Cavebot está desativado.

### `SEARCHING_MARKER`

A rota está ativa, mas o marcador atual ainda não foi selecionado com segurança.

### `NAVIGATING`

O marcador foi localizado e o movimento está em andamento.

### `ARRIVED`

O marcador entrou no raio de chegada.

### `WAITING_RETRY`

O movimento não apresentou progresso e aguarda nova tentativa.

### `SUSPENDED`

O Cavebot está temporariamente interrompido por um estado prioritário, como combate.

### `COMPLETED`

A rota terminou e `loop=false`.

### `STUCK`

O máximo de retentativas foi atingido sem progresso suficiente.

### `ERROR`

O estado visual, a rota ou a configuração é inválida.

---

## 8.7 Estado de movimento

```python
@dataclass(frozen=True)
class MovementState:
    waypoint_id: str
    best_distance: float | None
    last_distance: float | None
    last_progress_at: float
    retry_count: int
    click_sent_at: float | None
```

Regras:

* o estado pertence ao Cavebot, não ao `GameState`;
* a detecção visual do marcador não será preservada entre ciclos;
* o marcador será readquirido continuamente;
* coordenadas antigas não serão reutilizadas após combate;
* o estado será reinicializado ao avançar de waypoint.

---

## 8.8 Intenção operacional

```python
@dataclass(frozen=True)
class CavebotIntent:
    active: bool
    movement_requested: bool
    action: BotAction | None
    status: CavebotStatus
    reason: str
```

Regras:

* `active` indica que existe uma rota operacional;
* `movement_requested` indica que o Cavebot deseja que a máquina global entre em `MOVING`;
* `action` poderá ser `None` durante busca, cooldown, espera ou suspensão;
* rota ativa e movimento solicitado não são equivalentes.

O valor de `movement_requested` poderá ser derivado de:

```python
movement_requested = status in {
    CavebotStatus.SEARCHING_MARKER,
    CavebotStatus.NAVIGATING,
    CavebotStatus.WAITING_RETRY,
}
```

Quando `status` for `STUCK`, `ERROR`, `SUSPENDED`, `COMPLETED` ou `INACTIVE`, nenhum movimento deverá ser solicitado.

---

# 9. Seleção de Marcadores

O `MinimapAnalyzer` retornará todos os candidatos detectados.

O `MarkerSelector` será responsável por aplicar as regras do waypoint.

Fluxo:

```text
GameState.minimap.markers
    ↓
Filtrar por template_id
    ↓
Filtrar por match_threshold
    ↓
Filtrar por expected_region
    ↓
Aplicar desempate
    ↓
Selecionar candidato ou rejeitar
```

Assinatura sugerida:

```python
class MarkerSelector:
    def select(
        self,
        minimap: MinimapState,
        waypoint: Waypoint,
        default_threshold: float,
    ) -> MarkerDetection | None:
        ...
```

Critérios mínimos:

1. mesmo `template_id`;
2. confiança maior ou igual ao limite;
3. centro contido em `expected_region`;
4. rejeição quando não houver candidato;
5. rejeição quando houver empate sem desempate seguro.

Em caso de ambiguidade:

```text
status = SEARCHING_MARKER
action = None
reason = "Mais de um marcador válido sem desempate seguro"
```

O sistema não deverá selecionar arbitrariamente o primeiro resultado.

---

# 10. Confirmação de Chegada

A distância será calculada em coordenadas locais da ROI:

```python
from math import hypot


distance = hypot(
    marker.center[0] - minimap.center[0],
    marker.center[1] - minimap.center[1],
)
```

A chegada será confirmada quando:

```python
distance <= route.settings.arrival_radius_pixels
```

Somente após essa confirmação o `RouteRunner` poderá avançar para o próximo waypoint.

Não será permitido avançar devido a:

* timeout;
* marcador desaparecido;
* combate;
* clique executado;
* cooldown concluído;
* quantidade de tentativas;
* ausência temporária de detecção.

---

# 11. Detecção de Progresso e Travamento

O `StuckDetector` deverá comparar a melhor distância já observada com a distância atual.

Progresso válido:

```python
best_distance - current_distance >= progress_epsilon_pixels
```

Oscilações menores que `progress_epsilon_pixels` não deverão reiniciar o timeout.

Exemplo:

```text
best_distance = 40.0
current_distance = 39.2
epsilon = 1.5

Progresso insuficiente.
```

```text
best_distance = 40.0
current_distance = 37.9
epsilon = 1.5

Progresso confirmado.
```

Fluxo de travamento:

```text
Movimento iniciado
    ↓
Distância não melhora dentro do timeout
    ↓
retry_count < max_retries?
    ├── Sim → readquirir marcador e reenviar clique
    └── Não → CavebotStatus.STUCK
```

Ao entrar em `STUCK`:

* não gerar nova ação;
* não avançar waypoint;
* registrar motivo;
* manter o índice atual;
* exigir retomada explícita ou política segura futura.

---

# 12. Máquina Global de Estados

## 12.1 Novo modo

Adicionar em:

```text
src/domain/bot_state.py
```

o modo:

```python
BotMode.MOVING
```

---

## 12.2 Ordem de prioridade

A ordem conceitual deverá ser:

```text
PAUSED
UNSAFE
IN_PROTECTION_ZONE
COMBAT
LOOTING
MOVING
IDLE
```

Caso `LOOTING` ainda não esteja implementado, a ordem será:

```text
PAUSED
UNSAFE
IN_PROTECTION_ZONE
COMBAT
MOVING
IDLE
```

A máquina somente entrará em `MOVING` quando:

* `movement_requested=True`;
* o frame for válido;
* o bot não estiver pausado;
* o bot não estiver inseguro;
* o personagem não estiver em proteção;
* não houver combate;
* não houver ação de prioridade superior.

Assinatura sugerida:

```python
def update(
    self,
    game_state: GameState,
    killswitch_paused: bool,
    movement_requested: bool = False,
) -> BotState:
    ...
```

Também deverão ser atualizados:

```text
tests/unit/test_state_machine.py
src/utils/overlay.py
```

O overlay deverá reconhecer e exibir `MOVING`.

---

# 13. Suspensão e Retomada Após Combate

O waypoint atual deverá ser preservado durante combate.

Fluxo esperado:

```text
MOVING
    ↓
COMBAT
    ↓
CavebotStatus.SUSPENDED
    ↓
Nenhuma ação de movimento
    ↓
Combate termina
    ↓
Readquirir marcador do mesmo waypoint
    ↓
Retomar MOVING
```

Durante a suspensão serão preservados:

* índice do waypoint;
* `retry_count`;
* estado da rota;
* identificador do waypoint atual.

Não serão preservados:

* objeto `MarkerDetection`;
* coordenada antiga;
* confiança antiga;
* distância antiga como fonte visual confiável.

Após o combate, o marcador deverá ser novamente selecionado a partir de:

```python
game_state.minimap.markers
```

---

# 14. Fluxo de Integração no Engine

O `GameAnalyzer` deverá encapsular os componentes de percepção, incluindo o `MinimapAnalyzer`.

O `BotEngine` não deverá chamar cada detector individualmente.

## 14.1 Percepção

```python
game_state = self.game_analyzer.analyze(
    frame=frame,
    window_state=window_state,
    config=self.config,
)
```

Internamente:

```python
class GameAnalyzer:
    def analyze(
        self,
        frame,
        window_state,
        config,
    ) -> GameState:
        minimap_state = self.minimap_analyzer.analyze(
            frame=frame,
            minimap_roi=config.regions.minimap,
        )

        return GameState(
            # demais percepções...
            minimap=minimap_state,
        )
```

---

## 14.2 Avaliação da rota antes do modo global

O Cavebot deverá primeiro inspecionar sua rota para informar se existe intenção de movimento, sem gerar o clique final.

```python
cavebot_status = self.cavebot_controller.inspect(game_state)
```

---

## 14.3 Máquina de estados

```python
bot_state = self.state_machine.update(
    game_state=game_state,
    killswitch_paused=self.killswitch_paused,
    movement_requested=cavebot_status.movement_requested,
)
```

---

## 14.4 Proposta de ação após o modo global

Somente após conhecer o modo final o Cavebot poderá propor uma ação.

```python
cavebot_intent = self.cavebot_controller.propose(
    game_state=game_state,
    bot_state=bot_state,
)
```

Regra:

```python
if bot_state.mode is not BotMode.MOVING:
    return CavebotIntent(
        active=True,
        movement_requested=False,
        action=None,
        status=CavebotStatus.SUSPENDED,
        reason=f"Cavebot suspenso pelo modo {bot_state.mode.name}",
    )
```

---

## 14.5 Resolução das ações

```python
extra_actions = (
    [cavebot_intent.action]
    if cavebot_intent.action is not None
    else []
)

resolved_actions = self.decision_controller.resolve(
    proposed_actions + extra_actions,
    game_state=game_state,
    bot_state=bot_state,
    config=self.config,
)
```

---

## 14.6 Execução

```python
execution_results = self.action_executor.execute(
    resolved_actions,
    game_state=game_state,
    observe_only=self.observe_only,
)
```

O executor deverá informar quais ações foram realmente executadas.

---

## 14.7 Registro do cooldown

O cooldown será registrado somente após execução confirmada.

Fluxo correto:

```text
Ação proposta
    ↓
Ação resolvida
    ↓
Validação final
    ↓
Input executado
    ↓
Cooldown registrado
```

Fluxo proibido:

```text
Ação proposta
    ↓
Cooldown registrado
    ↓
Ação descartada
```

Exemplo:

```python
for result in execution_results:
    if result.executed:
        self.cooldown_manager.register(
            key=result.action.cooldown_key,
            cooldown_ms=result.action.cooldown_ms,
        )
```

O próprio `ActionExecutor` também poderá registrar o cooldown, desde que isso ocorra somente após o input ter sido aceito.

---

# 15. Schema do Arquivo de Hunt

Exemplo inicial:

```json
{
  "hunt_name": "Minotaurs Yalahar",
  "version": 1,
  "loop": true,
  "settings": {
    "match_threshold": 0.88,
    "arrival_radius_pixels": 4.0,
    "progress_epsilon_pixels": 1.5,
    "stuck_timeout_ms": 15000,
    "click_cooldown_ms": 1500,
    "max_retries": 2
  },
  "waypoints": [
    {
      "id": "wp_01",
      "type": "MARKER_CLICK",
      "marker": "flag0",
      "expected_region": {
        "x": 0.5,
        "y": 0.0,
        "width": 0.5,
        "height": 1.0
      },
      "description": "Primeiro marcador"
    },
    {
      "id": "wp_02",
      "type": "MARKER_CLICK",
      "marker": "flag1",
      "expected_region": {
        "x": 0.0,
        "y": 0.0,
        "width": 0.5,
        "height": 1.0
      },
      "description": "Segundo marcador"
    }
  ]
}
```

---

# 16. Validação do Arquivo de Hunt

O `RouteLoader` deverá validar:

* arquivo existente;
* JSON válido;
* `hunt_name` não vazio;
* versão suportada;
* pelo menos um waypoint;
* IDs únicos;
* tipos de waypoint conhecidos;
* marcador obrigatório para `MARKER_CLICK`;
* template do marcador existente;
* valores relativos entre `0.0` e `1.0`;
* região com largura e altura maiores que zero;
* `match_threshold` entre `0.0` e `1.0`;
* `arrival_radius_pixels` maior que zero;
* `progress_epsilon_pixels` maior ou igual a zero;
* `stuck_timeout_ms` maior que zero;
* `click_cooldown_ms` maior ou igual a zero;
* `max_retries` maior ou igual a zero;
* referências de `LABEL` e `GOTO` válidas na Fase 12E.

Erros deverão impedir o carregamento da rota.

O sistema não deverá tentar corrigir silenciosamente arquivos inválidos.

---

# 17. Roteiro Incremental

> **Atualização de estado:** as Fases 12A, 12B e 12C foram concluídas em modo de observação. A Fase 12D está em andamento: carregamento de rota JSON, avanço sequencial e conclusão sem loop foram validados com `flag0 → flag1`; ainda faltam validações manuais de loop e suspensão/retomada por combate ou PZ.

## Fase 12A — Percepção do minimapa

### Objetivo

Criar a percepção imutável do minimapa sem gerar inputs.

### Alterações

```text
[NEW] src/domain/minimap.py
[MODIFY] src/domain/game_state.py
[NEW] src/infrastructure/vision/minimap_analyzer.py
[MODIFY] src/config/models.py
[MODIFY] src/application/game_analyzer.py
[NEW] tests/unit/test_minimap_analyzer.py
[NEW] tests/fixtures/minimap/*
```

### Entregas

* `MarkerDetection`;
* `MinimapBounds`;
* `MinimapState`;
* ROI configurável;
* centro local calculado;
* detecção de todos os marcadores;
* confiança por detecção;
* validação opcional do `cross.png`;
* integração em `GameState.minimap`;
* nenhuma ação ou clique.

### Critério de conclusão

A fase estará concluída quando:

* o analyzer funcionar apenas com o frame compartilhado;
* todos os marcadores forem retornados;
* coordenadas locais e limites absolutos estiverem corretos;
* estados inválidos produzirem `available=False`;
* os testes com fixtures passarem.

---

## Fase 12B — Payloads de mouse e executor

### Objetivo

Adicionar suporte tipado a cliques sem implementar ainda a rota.

### Alterações

```text
[MODIFY] src/domain/actions.py
[MODIFY] src/bot/healer.py
[MODIFY] src/bot/combat.py
[MODIFY] src/application/action_executor.py
[MODIFY] src/application/decision_controller.py
[MODIFY] src/application/cooldown_manager.py
[MODIFY] tests/unit/test_actions.py
[MODIFY] tests/unit/test_action_executor.py
[MODIFY] tests/integration/test_full_pipeline.py
```

### Entregas

* `ActionPriority`;
* `KeyPayload`;
* `MouseClickPayload`;
* `ActionPayload`;
* `BotAction` refatorado;
* migração das ações existentes;
* execução de cliques;
* suporte a `observe-only`;
* cooldown registrado após execução.

### Critério de conclusão

A fase estará concluída quando:

* healer e combate usarem `KeyPayload`;
* cliques puderem ser simulados;
* nenhum input real ocorrer em `observe-only`;
* ações descartadas não consumirem cooldown;
* a suíte existente permanecer verde.

---

## Fase 12C — Seleção e movimento por um marcador

### Objetivo

Navegar até um único marcador sem execução de rota completa.

### Alterações

```text
[NEW] src/bot/cavebot/models.py
[NEW] src/bot/cavebot/marker_selector.py
[NEW] src/bot/cavebot/movement_controller.py
[NEW] src/bot/cavebot/stuck_detector.py
[NEW] tests/unit/test_marker_selector.py
[NEW] tests/unit/test_movement_controller.py
[NEW] tests/unit/test_stuck_detector.py
```

### Entregas

* seleção por template;
* seleção por confiança;
* seleção por região;
* rejeição de ambiguidade;
* conversão ROI local → coordenada absoluta;
* cálculo de distância;
* confirmação de chegada;
* detecção de progresso;
* retentativas limitadas;
* estado `STUCK`.

### Critério de conclusão

A fase estará concluída quando:

* um único waypoint puder ser acompanhado;
* o clique for proposto corretamente;
* a chegada for confirmada pelo raio;
* ruído pequeno não contar como progresso;
* o waypoint nunca for concluído por timeout;
* o máximo de retentativas resultar em `STUCK`.

---

## Fase 12D — Rota e integração completa

### Objetivo

Executar uma sequência de waypoints e integrar o Cavebot ao ciclo principal.

### Alterações

```text
[NEW] src/config/route_loader.py
[NEW] src/bot/cavebot/route_runner.py
[NEW] src/bot/cavebot/cavebot_controller.py
[MODIFY] src/domain/bot_state.py
[MODIFY] src/application/state_machine.py
[MODIFY] src/application/bot_engine.py
[MODIFY] src/utils/overlay.py
[MODIFY] launcher.py
[NEW] config/hunts/default_hunt.json
[NEW] tests/unit/test_route_loader.py
[NEW] tests/unit/test_route_runner.py
[NEW] tests/unit/test_engine_cavebot.py
[MODIFY] tests/unit/test_state_machine.py
```

### Entregas

* carregamento por `--hunt`;
* `BotMode.MOVING`;
* execução sequencial;
* suporte a `loop`;
* finalização sem loop;
* suspensão em combate;
* retomada do mesmo waypoint;
* reaquisição visual após combate;
* integração com `DecisionController`;
* logs em `observe-only`;
* overlay para `MOVING`.

### Critério de conclusão

A fase estará concluída quando:

* uma rota de marcadores puder ser executada;
* o Cavebot perder prioridade para combate;
* nenhum clique ocorrer durante combate;
* o mesmo waypoint for retomado;
* o próximo waypoint só for iniciado após chegada;
* rotas sem loop terminarem em `COMPLETED`;
* rotas com loop retornarem ao primeiro waypoint.

---

## Fase 12E — Fluxos avançados

### Objetivo

Adicionar comandos de rota que não são movimentos simples por marcador.

### Tipos

```text
STAND
ACTION
LABEL
GOTO
TRANSITION
```

### Responsabilidades

O `RouteRunner` deverá delegar:

```text
MARKER_CLICK → MovementController
STAND        → controlador de espera
ACTION       → geração de KeyPayload ou interação
LABEL        → índice lógico da rota
GOTO         → alteração controlada de fluxo
TRANSITION   → mudança de andar ou contexto visual
```

### Regras

* `MovementController` não executará `STAND`;
* `MovementController` não executará hotkeys;
* `MovementController` não controlará labels;
* cada tipo terá validação própria;
* mudanças de andar deverão exigir confirmação visual;
* nenhuma transição avançará apenas porque uma tecla foi pressionada.

---

# 18. Testes Obrigatórios

## 18.1 `test_minimap_analyzer.py`

Cobrir:

* ROI válida;
* ROI inválida;
* centro correto;
* marcador único;
* múltiplos marcadores;
* marcador ausente;
* confiança;
* coordenadas locais;
* limites absolutos;
* validação do cross;
* retorno seguro em layout inválido.

---

## 18.2 `test_marker_selector.py`

Cobrir:

* seleção por template;
* seleção por região;
* limite de confiança;
* candidato fora da região;
* múltiplos candidatos;
* empate sem desempate;
* ausência de candidato;
* threshold específico do waypoint.

---

## 18.3 `test_movement_controller.py`

Cobrir:

* conversão de coordenadas;
* geração de `MouseClickPayload`;
* prioridade de movimento;
* cooldown correto;
* motivo obrigatório;
* chegada dentro do raio;
* ausência de ação quando o minimapa for inválido;
* ausência de ação quando não houver marcador.

---

## 18.4 `test_stuck_detector.py`

Cobrir:

* progresso real;
* oscilação menor que o epsilon;
* reinício do timeout após progresso;
* timeout sem progresso;
* primeira retentativa;
* segunda retentativa;
* limite máximo;
* entrada em `STUCK`;
* nunca avançar waypoint.

---

## 18.5 `test_route_runner.py`

Cobrir:

* índice inicial;
* avanço após chegada;
* não avançar por clique;
* não avançar por timeout;
* manutenção durante combate;
* retomada do mesmo waypoint;
* loop;
* conclusão sem loop;
* reinicialização de `MovementState`;
* preservação do índice em `STUCK`.

---

## 18.6 `test_engine_cavebot.py`

Cobrir:

* rota inativa;
* entrada em `MOVING`;
* movimento bloqueado em `PAUSED`;
* movimento bloqueado em `UNSAFE`;
* movimento bloqueado em PZ;
* combate acima de movimento;
* frame inválido;
* minimapa inválido;
* ação proposta e resolvida;
* ação descartada sem cooldown;
* clique simulado em `observe-only`.

---

## 18.7 Teste completo de integração

Criar ao menos um cenário:

```text
Fixture de frame
    ↓
GameAnalyzer
    ↓
GameState.minimap
    ↓
MarkerSelector
    ↓
CavebotController
    ↓
BotMode.MOVING
    ↓
BotAction com MouseClickPayload
    ↓
DecisionController
    ↓
MockInputController
```

O teste deverá verificar:

* coordenada final;
* prioridade;
* motivo;
* cooldown;
* ausência de clique real;
* progressão somente após chegada.

---

# 19. Plano de Verificação

## Verificação de sintaxe

```bash
python -m compileall src
```

## Fase 12A

```bash
pytest tests/unit/test_minimap_analyzer.py
```

## Fase 12B

```bash
pytest \
  tests/unit/test_actions.py \
  tests/unit/test_action_executor.py \
  tests/integration/test_full_pipeline.py
```

## Fase 12C

```bash
pytest \
  tests/unit/test_marker_selector.py \
  tests/unit/test_movement_controller.py \
  tests/unit/test_stuck_detector.py
```

## Fase 12D

```bash
pytest \
  tests/unit/test_route_loader.py \
  tests/unit/test_route_runner.py \
  tests/unit/test_state_machine.py \
  tests/unit/test_engine_cavebot.py
```

## Suíte completa

```bash
pytest
```

## Simulação completa

```bash
python launcher.py \
  --observe-only \
  --hunt config/hunts/default_hunt.json
```

---

# 20. Logs e Observabilidade

Cada decisão do Cavebot deverá ser rastreável.

Exemplos:

```text
[CAVEBOT] Rota carregada: Minotaurs Yalahar, 12 waypoints
[CAVEBOT] Waypoint ativo: wp_01, marker=flag0
[CAVEBOT] 2 candidatos flag0 detectados
[CAVEBOT] Marcador selecionado por expected_region, confidence=0.93
[CAVEBOT] Distância atual=42.5px, melhor distância=45.0px
[CAVEBOT] Clique proposto em screen=(1720, 110)
[CAVEBOT] Movimento suspenso: modo global COMBAT
[CAVEBOT] Combate encerrado, readquirindo waypoint wp_01
[CAVEBOT] Chegada confirmada: distância=3.2px
[CAVEBOT] Avançando para waypoint wp_02
[CAVEBOT] Sem progresso por 15s, retry 1/2
[CAVEBOT] Máximo de retentativas atingido, status=STUCK
```

No modo `--observe-only`:

```text
[OBSERVE] Clique simulado: x=1720, y=110, button=left
```

Nenhuma função de input deverá ser chamada nesse modo.

---

# 21. Fora do Escopo Inicial

Os seguintes itens não fazem parte das fases 12A a 12D:

* pathfinding por tiles;
* leitura de coordenadas globais do personagem;
* reconhecimento automático de mapas;
* criação automática de rotas;
* detecção de obstáculos no mapa principal;
* desvio dinâmico de monstros;
* fallback por teclado;
* escolha automática de andares;
* persistência de progresso após reiniciar o processo;
* edição visual de rotas;
* gravação automática de waypoints;
* recuperação avançada de travamentos.

Esses recursos poderão ser tratados em fases futuras.

---

# 22. Critérios Globais de Aceitação

A Fase 12 será considerada concluída quando:

1. o minimapa fizer parte do `GameState`;
2. nenhuma captura adicional ocorrer dentro do Cavebot;
3. o analyzer não conhecer regras da rota;
4. os marcadores forem representados por modelos imutáveis;
5. as coordenadas locais e absolutas estiverem claramente definidas;
6. ações de teclado e mouse utilizarem payloads tipados;
7. healer e combate estiverem migrados para o novo `BotAction`;
8. `BotMode.MOVING` estiver integrado;
9. movimento tiver prioridade inferior a combate e cura;
10. cliques forem executados somente pelo `ActionExecutor`;
11. cooldowns forem registrados somente após execução;
12. `observe-only` nunca enviar inputs;
13. o waypoint atual for preservado durante combate;
14. marcadores forem readquiridos após interrupções;
15. um waypoint avançar somente após confirmação visual de chegada;
16. travamentos não provocarem avanço automático;
17. ambiguidades visuais bloquearem o movimento;
18. a rota entrar em `STUCK` após exceder retentativas;
19. todos os testes unitários e de integração passarem;
20. uma rota completa funcionar em modo de observação.

---

# 23. Ordem Recomendada de Implementação

A implementação deverá seguir obrigatoriamente esta ordem:

```text
12A — MinimapState e percepção
    ↓
12B — Payloads e executor
    ↓
12C — Um marcador e stuck detection
    ↓
12D — Rota e engine
    ↓
12E — Ações avançadas
```

Não antecipar:

* `RouteRunner` antes do detector estar estável;
* cliques reais antes do modo de observação;
* `LABEL` e `GOTO` antes da rota sequencial funcionar;
* recuperação avançada antes do stuck detector básico;
* transição de andar antes de confirmação visual confiável.

A primeira entrega funcional deverá ser somente:

```text
Frame gravado
    ↓
Detecção do marcador
    ↓
Seleção segura
    ↓
Cálculo da coordenada
    ↓
Log do clique em observe-only
```

Somente após essa entrega ser validada deverão ser habilitados cliques reais.
