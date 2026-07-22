O sistema precisa saber onde está, para onde deve ir, quando lutar, quando coletar loot e como continuar a rota depois de interrupções.

O fluxo principal ficaria assim:

Waypoint atual
    ↓
Navegar até ele
    ↓
Detectar inimigo
    ↓
Interromper rota e entrar em combate
    ↓
Aproximar, atacar e curar
    ↓
Loot
    ↓
Retomar rota
    ↓
Próximo waypoint
Componentes necessários
1. Waypoints

O cavebot precisa de uma lista de pontos que representam a rota.

from dataclasses import dataclass
from enum import Enum


class WaypointAction(Enum):
    WALK = "walk"
    WAIT = "wait"
    USE = "use"
    ROPE = "rope"
    SHOVEL = "shovel"
    LADDER = "ladder"
    DROP_DOWN = "drop_down"


@dataclass(frozen=True)
class Waypoint:
    x: int
    y: int
    floor: int
    action: WaypointAction = WaypointAction.WALK
    tolerance: int = 1

Exemplo de rota:

route:
  loop: true

  waypoints:
    - x: 102
      y: 84
      floor: 7
      action: walk

    - x: 110
      y: 84
      floor: 7
      action: walk

    - x: 115
      y: 90
      floor: 7
      action: use

    - x: 115
      y: 90
      floor: 6
      action: walk

O problema principal é descobrir essas coordenadas sem ler memória. Você pode trabalhar com:

posição relativa no minimapa;
deslocamento acumulado desde um ponto conhecido;
reconhecimento visual de marcos;
rotas relativas em vez de coordenadas globais.
2. Localização pelo minimapa

Para cavebot, o minimapa é provavelmente a fonte mais importante.

Você precisa detectar:

centro do jogador no minimapa;
deslocamento do mapa;
cor dos tiles;
paredes e caminhos;
mudança de andar;
posição relativa do próximo waypoint.

Uma abordagem inicial é tratar o personagem como centro fixo do minimapa e comparar o mapa antes e depois do movimento.

Minimapa anterior
    ↓
pressiona direita
    ↓
Minimapa novo
    ↓
conteúdo deslocou para esquerda
    ↓
personagem avançou para direita

Com isso, você atualiza uma posição acumulada:

@dataclass
class EstimatedPosition:
    x: int = 0
    y: int = 0
    floor: int = 0
position.x += delta_x
position.y += delta_y

Essa posição pode começar em (0, 0, 0). Para uma rota gravada, não é obrigatório conhecer a coordenada real do mundo.

3. Gravador de rota

A maneira mais prática de criar uma rota é ter um modo de gravação.

Fluxo:

Usuário ativa gravação
    ↓
Anda manualmente
    ↓
Bot observa mudanças no minimapa
    ↓
Registra os deslocamentos
    ↓
Usuário marca ações especiais
    ↓
Rota é salva em YAML

Exemplo:

waypoints:
  - dx: 0
    dy: -5
    action: walk

  - dx: 8
    dy: 0
    action: walk

  - dx: 0
    dy: 0
    action: use
    direction: north

  - dx: 0
    dy: -3
    action: walk

Uma rota relativa é mais fácil de implementar inicialmente do que uma coordenada global completa.

4. Máquina de estados do cavebot

O cavebot precisa de estados próprios.

class CavebotMode(Enum):
    DISABLED = "disabled"
    STARTING = "starting"
    NAVIGATING = "navigating"
    COMBAT = "combat"
    APPROACHING_TARGET = "approaching_target"
    LOOTING = "looting"
    INTERACTING = "interacting"
    RECOVERING_ROUTE = "recovering_route"
    STUCK = "stuck"
    PAUSED = "paused"
    UNSAFE = "unsafe"

Transições típicas:

NAVIGATING
    ├── inimigo detectado → COMBAT
    ├── waypoint alcançado → próximo waypoint
    ├── ação especial → INTERACTING
    ├── sem progresso → STUCK
    └── captura inválida → UNSAFE

COMBAT
    ├── alvo distante → APPROACHING_TARGET
    ├── alvo derrotado → LOOTING
    ├── novo alvo → COMBAT
    └── nenhum alvo → RECOVERING_ROUTE

LOOTING
    ├── loot finalizado → RECOVERING_ROUTE
    └── inimigo detectado → COMBAT

RECOVERING_ROUTE
    ├── rota encontrada → NAVIGATING
    └── posição desconhecida → STUCK
5. Navegação curta e longa

Você deve separar dois tipos de navegação.

Navegação longa

Usada entre waypoints.

Fonte principal:

minimapa

Responsável por:

seguir rota;
escolher direção;
confirmar progresso;
contornar pequenos bloqueios;
detectar que chegou ao waypoint.
Navegação curta

Usada dentro da viewport.

Fonte principal:

área do jogo

Responsável por:

andar até o inimigo;
posicionar-se para atacar;
chegar perto de escada ou buraco;
clicar ou usar um tile específico;
coletar loot.

Estrutura:

src/modules/navigation/
├── route_controller.py
├── waypoint_controller.py
├── minimap_localizer.py
├── local_movement.py
├── stuck_detector.py
├── recovery.py
└── models.py
6. Pathfinding

Existem duas estratégias.

Rota gravada

Mais simples e indicada inicialmente.

Waypoint A → Waypoint B → Waypoint C

O bot tenta seguir os pontos previamente registrados.

Vantagens:

implementação mais simples;
não precisa interpretar todo o mapa;
bom para caminhos conhecidos;
mais fácil de testar.

Desvantagens:

menos adaptável;
pode falhar se algo bloquear a rota;
exige mecanismo de recuperação.
A* no minimapa

Mais avançado.

Você transforma o minimapa em uma grade:

class TileType(Enum):
    WALKABLE = 0
    BLOCKED = 1
    UNKNOWN = 2
    TARGET = 3
grid = [
    [0, 0, 0, 1, 1],
    [0, 1, 0, 0, 0],
    [0, 1, 0, 1, 0],
]

Depois:

path = astar(
    grid=grid,
    start=current_position,
    goal=waypoint_position,
)

A dificuldade maior não é o A*. É classificar corretamente as cores e objetos do minimapa.

Para a primeira versão, use waypoints gravados e navegação por feedback.

7. Confirmação de movimento

Não basta pressionar a tecla e considerar que andou.

Cada passo precisa ser confirmado.

@dataclass(frozen=True)
class MovementResult:
    requested_direction: str
    position_changed: bool
    delta_x: int
    delta_y: int
    confidence: float

Fluxo:

captura minimapa
    ↓
envia passo
    ↓
captura novo minimapa
    ↓
compara imagens
    ↓
confirma ou rejeita movimento

Pseudocódigo:

previous = minimap_detector.read(frame_before)

executor.execute(MoveAction(direction="right"))

current = minimap_detector.read(frame_after)

delta = minimap_motion.estimate(previous, current)

if delta.confidence < 0.7:
    mark_position_uncertain()
elif delta.matches_expected_direction("right"):
    position.x += 1
else:
    register_blocked_step()
8. Detecção de travamento

O cavebot precisa saber quando não está progredindo.

Condições possíveis:

mesma imagem por muitos ciclos;
posição estimada não muda;
waypoint não se aproxima;
personagem alterna entre dois pontos;
mesma direção falha repetidamente;
posição fica incerta;
combate terminou, mas rota não foi reencontrada.

Modelo:

@dataclass
class StuckState:
    failed_steps: int = 0
    unchanged_frames: int = 0
    repeated_positions: int = 0
    recovery_attempts: int = 0

Exemplo:

if failed_steps >= 3:
    return RecoveryIntent(
        strategy="try_alternative_direction",
        reason="Three movement attempts without progress",
    )
9. Recuperação da rota

Depois de um combate, o personagem pode ter saído do caminho original.

O sistema precisa procurar o waypoint atual ou o próximo waypoint mais próximo.

Possíveis estratégias:

1. Voltar ao último waypoint confirmado
2. Procurar waypoint seguinte
3. Comparar o minimapa com snapshots conhecidos
4. Tentar direções laterais curtas
5. Pausar quando não houver confiança

Cada waypoint pode armazenar uma imagem de referência:

- id: cave_entry
  x: 20
  y: 15
  floor: 0
  reference_image: templates/routes/cave_entry.png

O bot compara a região atual do minimapa com imagens conhecidas para relocalização.

10. Ações especiais

Uma cave possui escadas, buracos, cordas e portas.

Cada ação precisa de uma implementação própria.

@dataclass(frozen=True)
class InteractionAction:
    interaction_type: WaypointAction
    target_offset: tuple[int, int]
    item_hotkey: str | None

Exemplos:

Escada
andar até o tile
    ↓
confirmar proximidade
    ↓
andar na direção da escada
    ↓
confirmar mudança de andar
Buraco com pá
chegar perto
    ↓
usar hotkey da pá
    ↓
clicar no tile
    ↓
confirmar mudança visual
Corda
chegar perto do rope spot
    ↓
usar hotkey da corda
    ↓
clicar
    ↓
confirmar mudança de andar
Porta
chegar em frente
    ↓
usar ou clicar
    ↓
confirmar que o caminho abriu

Nenhuma ação deve ser considerada concluída apenas porque o input foi enviado.

11. Integração com combate

O cavebot não deve possuir lógica própria de ataque ou cura. Ele deve coordenar módulos já existentes.

CavebotController
    ├── NavigationController
    ├── CombatController
    ├── HealerController
    ├── LootController
    └── InteractionController

Prioridades:

1. Killswitch
2. Segurança
3. Cura de emergência
4. Cura
5. Inimigo ativo
6. Aproximação do inimigo
7. Loot
8. Recuperação da rota
9. Navegação até waypoint
10. Ação ociosa

Quando surgir um inimigo:

if state.target.exists:
    return CavebotMode.COMBAT

Quando ele morrer:

if previous.target.active and not current.target.active:
    return CavebotMode.LOOTING

Depois do loot:

return CavebotMode.RECOVERING_ROUTE
12. Estado central necessário
@dataclass(frozen=True)
class NavigationState:
    estimated_position: tuple[int, int, int] | None
    current_waypoint_index: int
    distance_to_waypoint: float | None
    expected_direction: str | None
    last_confirmed_position: tuple[int, int, int] | None
    route_confidence: float
    is_stuck: bool
@dataclass(frozen=True)
class CavebotState:
    enabled: bool
    mode: CavebotMode
    route_name: str | None
    navigation: NavigationState
    interrupted_by_combat: bool
    pending_interaction: WaypointAction | None
Primeira versão recomendada

Não tente fazer um cavebot completamente autônomo logo de início.

Implemente nesta ordem:

Etapa 1 — Rota fixa simples
configurar waypoints;
navegar apenas em área aberta;
quatro direções;
confirmar cada passo pelo minimapa;
sem combate;
sem loot;
sem troca de andar.
Etapa 2 — Combate interrompe rota
detectar inimigo;
pausar navegação;
atacar;
aproximar quando necessário;
aguardar fim do combate;
voltar à navegação.
Etapa 3 — Loot
detectar transição de morte;
fazer loot;
cancelar loot se aparecer inimigo;
retomar rota.
Etapa 4 — Recuperação
detectar travamento;
retornar ao último waypoint;
encontrar waypoint próximo;
pausar se confiança ficar baixa.
Etapa 5 — Ações especiais
escadas;
buracos;
corda;
pá;
portas;
mudança de andar.
Etapa 6 — Pathfinding
classificar minimapa;
construir grade;
executar A*;
recalcular caminho após bloqueios.
Estrutura sugerida
src/modules/cavebot/
├── controller.py
├── state_machine.py
├── route.py
├── route_loader.py
├── recorder.py
└── models.py

src/modules/navigation/
├── minimap_detector.py
├── minimap_motion.py
├── waypoint_controller.py
├── local_movement.py
├── pathfinder.py
├── stuck_detector.py
└── recovery.py

src/modules/interactions/
├── controller.py
├── ladder.py
├── rope.py
├── shovel.py
└── door.py
Principal dificuldade

O cavebot não é principalmente um problema de pressionar teclas. É um problema de localização confiável.

Sem leitura de memória, você precisa responder continuamente:

Onde estou?
O movimento realmente aconteceu?
Qual é o próximo ponto?
Saí da rota durante o combate?
O andar mudou?
Estou travado?

A melhor primeira implementação para o seu projeto seria um cavebot por waypoints relativos gravados, com confirmação visual pelo minimapa. Isso é muito mais viável inicialmente do que tentar reconhecer todo o mapa e usar A* desde o começo.