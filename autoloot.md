## Fase 11 — Auto-Loot

O Tibia possui o recurso **Quick Loot Nearby Corpses**, capaz de coletar os corpos presentes no tile do personagem e nos 8 tiles adjacentes com uma única ação.

Por isso, a primeira implementação do Auto-Loot não precisa localizar ou clicar individualmente nos corpos.

O fluxo recomendado é:

```text
Alvo ativo
    ↓
Alvo deixa de existir
    ↓
Verificar se ainda existem criaturas
    ↓
Aguardar uma pequena janela de segurança
    ↓
Executar hotkey de Quick Loot Nearby Corpses
    ↓
Retomar combate ou navegação
```

---

### Requisitos anteriores

* [ ] Detectar a transição de alvo ativo para alvo derrotado.
* [ ] Saber se ainda existem criaturas na Battle List.
* [ ] Garantir que nenhuma cura de emergência esteja pendente.
* [ ] Garantir que o bot não esteja em estado inseguro.
* [ ] Garantir que o loot não conflite com combate ou movimento.
* [ ] Configurar no cliente do Tibia o Quick Loot Nearby Corpses.
* [ ] Configurar uma hotkey para o Quick Loot Nearby Corpses.
* [ ] Externalizar essa hotkey no arquivo de configuração.
* [ ] Garantir que a hotkey seja executada somente pelo executor central.

A posição visual exata do personagem não é obrigatória para essa primeira versão, pois o próprio cliente coleta os corpos nos SQMs próximos ao personagem.

---

### Configuração sugerida

```yaml
loot:
  enabled: true
  nearby_corpses_key: "alt+q"

  trigger:
    after_target_lost: true
    require_empty_battle_list: false
    delay_ms: 200

  cooldown_ms: 500
  max_attempts_per_combat: 1
```

Também pode ser utilizada uma hotkey simples configurada diretamente no cliente:

```yaml
loot:
  enabled: true
  nearby_corpses_key: "f12"
  cooldown_ms: 500
```

Nesse caso, o usuário configura `F12` no Tibia para executar o Quick Loot Nearby Corpses.

---

### Estado necessário

Adicionar um estado de combate que permita identificar transições:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class TargetState:
    has_battle_targets: bool | None
    has_active_target: bool | None
```

O controller deve receber o estado atual e o anterior:

```python
previous_state: GameState
current_state: GameState
```

A derrota ou perda do alvo pode ser inferida inicialmente por:

```python
target_was_active = (
    previous_state.target.has_active_target is True
)

target_is_inactive = (
    current_state.target.has_active_target is False
)

target_ended = target_was_active and target_is_inactive
```

Essa transição não garante sozinha que o alvo morreu. Ela também pode ocorrer quando:

* o jogador troca de alvo;
* o alvo sai da tela;
* o alvo é desmarcado;
* a detecção visual falha;
* o personagem perde o alvo por distância;
* o usuário cancela manualmente o ataque.

Por isso, o Auto-Loot deve combinar mais de um sinal.

---

### Condição inicial recomendada

```python
def should_request_loot(
    previous_state: GameState,
    current_state: GameState,
    bot_state: BotState,
) -> bool:
    if not current_state.is_safe_to_act:
        return False

    if bot_state.mode in {
        BotMode.PAUSED,
        BotMode.UNSAFE,
        BotMode.IN_PROTECTION_ZONE,
    }:
        return False

    if previous_state.target.has_active_target is not True:
        return False

    if current_state.target.has_active_target is not False:
        return False

    return True
```

Para reduzir falsos positivos, pode-se exigir que o alvo permaneça ausente por alguns frames:

```python
target_missing_confirmations >= 2
```

Ou por um pequeno período:

```python
target_missing_duration_ms >= 150
```

---

### Política quando ainda existem criaturas

Existem duas estratégias possíveis.

#### Estratégia conservadora

Lotear somente quando a Battle List estiver vazia:

```yaml
loot:
  trigger:
    require_empty_battle_list: true
```

Fluxo:

```text
Alvo derrotado
    ↓
Battle List vazia
    ↓
Loot
    ↓
Retomar rota
```

Vantagens:

* reduz conflito com ataque;
* facilita a primeira implementação;
* comportamento mais previsível.

Desvantagens:

* o personagem só coleta depois de matar todas as criaturas próximas;
* pode se afastar de alguns corpos antes de lotear.

#### Estratégia rápida

Lotear entre um alvo e outro, mesmo com criaturas na Battle List:

```yaml
loot:
  trigger:
    require_empty_battle_list: false
```

Fluxo:

```text
Alvo derrotado
    ↓
Hotkey de loot
    ↓
Selecionar próximo alvo
```

Vantagens:

* coleta o corpo antes de se afastar;
* aproveita o Quick Loot Nearby Corpses;
* reduz corpos esquecidos.

Desvantagens:

* exige prioridade e compatibilidade de ações bem definidas;
* não pode atrasar cura ou seleção urgente de alvo.

Para a primeira versão, a estratégia conservadora é mais simples. Depois, o loot entre alvos pode ser habilitado por configuração.

---

### Nova ação central

Adicionar uma ação específica:

```python
class ActionType(Enum):
    EMERGENCY_HEAL = "emergency_heal"
    HEAL = "heal"
    USE_MANA = "use_mana"
    ATTACK = "attack"
    LOOT_NEARBY = "loot_nearby"
    MOVE = "move"
```

Modelo:

```python
@dataclass(frozen=True)
class BotAction:
    action_type: ActionType
    priority: int
    key: str | None
    reason: str
    cooldown_ms: int = 0
```

A ação proposta pelo loot controller:

```python
BotAction(
    action_type=ActionType.LOOT_NEARBY,
    priority=40,
    key=config.loot.nearby_corpses_key,
    reason="Alvo deixou de estar ativo; solicitando loot dos corpos próximos.",
    cooldown_ms=config.loot.cooldown_ms,
)
```

---

### Prioridade recomendada

```text
1. Killswitch
2. Estado inseguro
3. Cura de emergência
4. Cura normal
5. Recuperação crítica de mana
6. Loot do alvo recém-derrotado
7. Seleção do próximo alvo
8. Movimento
9. Navegação da rota
```

Caso você prefira que o próximo alvo seja selecionado imediatamente, a ordem pode ser:

```text
1. Killswitch
2. Segurança
3. Cura de emergência
4. Cura
5. Mana
6. Ataque
7. Loot
8. Movimento
```

Porém, nesse caso, o personagem pode começar a andar em direção ao próximo inimigo antes de coletar os corpos.

Uma alternativa melhor é permitir uma janela curta após o alvo desaparecer:

```text
Alvo desapareceu
    ↓
Reservar 150–300 ms para loot
    ↓
Depois liberar ataque e movimento
```

---

### Estado do Auto-Loot

```python
from dataclasses import dataclass
from enum import Enum


class LootStatus(Enum):
    IDLE = "idle"
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class LootState:
    status: LootStatus
    pending_since: float | None
    last_execution_at: float | None
    attempts_in_current_combat: int
```

Para uma primeira versão, isso pode ser simplificado para:

```python
@dataclass
class LootControllerState:
    pending: bool = False
    target_missing_since: float | None = None
    last_loot_at: float | None = None
```

---

### Controller sugerido

```python
import time


class AutoLootController:
    def __init__(self, config: LootConfig):
        self.config = config
        self.target_missing_since: float | None = None
        self.loot_requested_for_current_target = False

    def get_proposed_actions(
        self,
        previous_state: GameState | None,
        current_state: GameState,
        bot_state: BotState,
    ) -> list[BotAction]:
        if not self.config.enabled:
            return []

        if previous_state is None:
            return []

        if not current_state.is_safe_to_act:
            self._cancel_pending()
            return []

        if bot_state.mode in {
            BotMode.PAUSED,
            BotMode.UNSAFE,
            BotMode.IN_PROTECTION_ZONE,
        }:
            self._cancel_pending()
            return []

        emergency_heal_required = (
            current_state.player.hp_percent is not None
            and current_state.player.hp_percent
            <= self.config.emergency_hp_threshold
        )

        if emergency_heal_required:
            self._cancel_pending()
            return []

        target_was_active = (
            previous_state.target.has_active_target is True
        )

        target_is_inactive = (
            current_state.target.has_active_target is False
        )

        if not target_was_active or not target_is_inactive:
            if current_state.target.has_active_target is True:
                self.loot_requested_for_current_target = False

            return []

        if self.loot_requested_for_current_target:
            return []

        if (
            self.config.require_empty_battle_list
            and current_state.target.has_battle_targets is not False
        ):
            return []

        now = time.monotonic()

        if self.target_missing_since is None:
            self.target_missing_since = now
            return []

        elapsed_ms = (
            now - self.target_missing_since
        ) * 1000

        if elapsed_ms < self.config.delay_ms:
            return []

        self.loot_requested_for_current_target = True
        self.target_missing_since = None

        return [
            BotAction(
                action_type=ActionType.LOOT_NEARBY,
                priority=self.config.priority,
                key=self.config.nearby_corpses_key,
                reason=(
                    "Alvo anteriormente ativo deixou de existir; "
                    "solicitando Quick Loot Nearby Corpses."
                ),
                cooldown_ms=self.config.cooldown_ms,
            )
        ]

    def _cancel_pending(self) -> None:
        self.target_missing_since = None
```

O controller apenas propõe uma ação. Ele não deve pressionar a hotkey diretamente.

---

### Controle de repetição

Como uma única ação já coleta os 9 SQMs próximos, inicialmente não é necessário clicar repetidamente.

Use:

```yaml
loot:
  max_attempts_per_combat: 1
```

O módulo deve marcar que já solicitou loot para aquela transição:

```python
self.loot_requested_for_current_target = True
```

Esse valor deve ser liberado quando:

* um novo alvo ficar ativo;
* um novo ciclo de combate começar;
* o personagem voltar a navegar;
* o controller for reinicializado.

Para casos excepcionais com muitos corpos empilhados, pode existir:

```yaml
loot:
  max_attempts_per_combat: 2
  retry_delay_ms: 700
```

Mas a primeira versão deve usar apenas uma tentativa.

---

### Cancelamento

O loot pendente deve ser cancelado quando:

* o killswitch for acionado;
* a captura ficar inválida;
* o frame ficar antigo;
* a janela perder foco;
* o jogo for minimizado;
* uma cura de emergência for necessária;
* um novo alvo ficar ativo;
* o personagem entrar em Protection Zone;
* o bot iniciar encerramento;
* a configuração do Auto-Loot for desabilitada.

Exemplo:

```python
if current_state.target.has_active_target is True:
    self._cancel_pending()
    return []
```

---

### Executor central

O `ActionExecutor` deve ser o único componente que executa a hotkey.

```python
def execute_action(
    self,
    action: BotAction,
    game_state: GameState,
) -> ActionExecutionResult:
    if not game_state.is_safe_to_act:
        return ActionExecutionResult.rejected(
            action,
            "Estado inseguro.",
        )

    if action.action_type == ActionType.LOOT_NEARBY:
        self.input_controller.press_key(action.key)

        return ActionExecutionResult.executed(
            action,
            "Quick Loot Nearby Corpses executado.",
        )

    ...
```

Caso a hotkey use uma combinação como `Alt + Q`, a abstração de input deve suportar combinações:

```python
self.input_controller.press_hotkey(
    ["alt", "q"]
)
```

Entretanto, é mais simples configurar no cliente uma única tecla, como:

```text
F12 → Quick Loot Nearby Corpses
```

Assim, o executor continua utilizando:

```python
self.input_controller.press_key("f12")
```

---

### Testes necessários

#### Detecta fim do alvo

```python
def test_requests_loot_when_active_target_disappears():
    previous = game_state(
        has_active_target=True,
        has_battle_targets=False,
    )

    current = game_state(
        has_active_target=False,
        has_battle_targets=False,
    )

    actions = controller.get_proposed_actions(
        previous,
        current,
        safe_bot_state(),
    )

    assert actions[0].action_type == ActionType.LOOT_NEARBY
```

#### Não repete loot

```python
def test_does_not_request_loot_twice_for_same_target():
    ...
```

#### Não loteia durante cura crítica

```python
def test_does_not_loot_when_emergency_heal_is_required():
    ...
```

#### Não loteia com captura inválida

```python
def test_does_not_loot_with_invalid_capture():
    ...
```

#### Cancela ao aparecer novo alvo

```python
def test_cancels_pending_loot_when_new_target_appears():
    ...
```

#### Não controla input diretamente

```python
def test_loot_controller_only_returns_actions():
    ...
```

#### Executor simulado

```python
def test_observe_only_does_not_send_loot_hotkey():
    ...
```

---

### Tarefas revisadas

* [ ] Criar `LootConfig`.
* [ ] Adicionar `loot` ao `AppConfig`.
* [ ] Adicionar configuração ao `default.yaml`.
* [ ] Criar `ActionType.LOOT_NEARBY`.
* [ ] Criar `AutoLootController`.
* [ ] Armazenar o `GameState` anterior no `BotEngine`.
* [ ] Detectar transição de alvo ativo para inativo.
* [ ] Confirmar ausência do alvo por tempo ou número de frames.
* [ ] Criar ação de hotkey pelo executor central.
* [ ] Executar somente uma tentativa por transição.
* [ ] Adicionar cooldown central.
* [ ] Cancelar loot durante cura de emergência.
* [ ] Cancelar loot quando surgir novo alvo.
* [ ] Cancelar loot em estado inseguro.
* [ ] Permitir exigir Battle List vazia.
* [ ] Permitir desabilitar Auto-Loot.
* [ ] Registrar solicitação, execução, cancelamento e rejeição.
* [ ] Criar testes com `MockInputController`.
* [ ] Criar testes para `--observe-only`.
* [ ] Documentar como configurar a hotkey no cliente.

---

### Tarefas removidas da primeira versão

As tarefas abaixo não são necessárias para o Quick Loot Nearby Corpses:

* [x] Não mapear individualmente corpos na área central.
* [x] Não definir uma lista de possíveis posições de corpos.
* [x] Não detectar visualmente cada corpo.
* [x] Não clicar em cada corpo.
* [x] Não controlar o mouse no Auto-Loot básico.
* [x] Não armazenar coordenadas de corpos já clicados.
* [x] Não conhecer obrigatoriamente a posição visual exata do personagem.
* [x] Não implementar pathfinding para o loot básico.

Esses recursos só seriam necessários para alguma mecânica alternativa de loot que não utilize a hotkey do cliente.

---

### Critérios de conclusão

* [ ] O Auto-Loot utiliza exclusivamente a hotkey configurada.
* [ ] O módulo de loot não controla teclado ou mouse diretamente.
* [ ] A hotkey é enviada somente pelo executor central.
* [ ] Uma transição de alvo gera no máximo uma solicitação inicial.
* [ ] Loot não interrompe cura de emergência.
* [ ] Loot não ocorre com captura inválida ou antiga.
* [ ] Loot não ocorre com o bot pausado.
* [ ] Loot é cancelado quando um novo alvo aparece.
* [ ] Loot pode ser configurado para exigir Battle List vazia.
* [ ] Loot não conflita com movimento.
* [ ] Loot não conflita com seleção de alvo.
* [ ] Cooldown é registrado somente após execução real.
* [ ] `--observe-only` não envia a hotkey.
* [ ] Testes automatizados não utilizam input real.

---

### Primeira implementação recomendada

A primeira versão pode ser reduzida a:

```text
1. Guardar GameState anterior.
2. Detectar ativo → inativo.
3. Esperar aproximadamente 200 ms.
4. Confirmar que o estado é seguro.
5. Confirmar que não existe cura emergencial.
6. Emitir LootNearbyAction.
7. Executor pressiona a hotkey configurada.
8. Marcar a transição como processada.
```

Não é necessário mapear corpos ou mover o mouse.

---

### Evolução futura opcional

Depois da versão básica, podem ser adicionados:

* repetição opcional quando houver muitos corpos;
* confirmação pelo Server Log;
* confirmação pela animação visual de loot;
* contagem de corpos coletados por OCR;
* controle de capacidade;
* detecção de containers cheios;
* pausa quando não houver espaço;
* loot entre alvos;
* loot somente após Battle List vazia;
* integração com o cavebot;
* bloqueio temporário de movimento durante a janela de loot.
