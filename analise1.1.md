# Nova revisão do repositório — TibiaBotWin

Repositório analisado:

```text
https://github.com/andspaulino/tibiabotwin
```

## Resultado geral

Algumas correções foram criadas, mas **boa parte ainda não está conectada ao fluxo principal**.

O projeto atualmente possui situações em que:

* a versão nova de um componente existe;
* a versão antiga também continua existindo;
* o `main.py` e o `BotEngine` ainda importam a versão antiga;
* a documentação afirma que a correção foi concluída, apesar de o fluxo real ainda não utilizá-la.

## Resumo dos 12 pontos

| Item                                | Situação atual                                    |
| ----------------------------------- | ------------------------------------------------- |
| 1. Documentação atualizada          | **Parcial**                                       |
| 2. Analyzer fora do domínio         | **Criado, mas não utilizado**                     |
| 3. Healer e combat sem input direto | **Não corrigido**                                 |
| 4. Cooldowns centralizados          | **Classe criada, mas não integrada**              |
| 5. Conflitos entre ações            | **Não corrigido**                                 |
| 6. Factory por plataforma           | **Não corrigido**                                 |
| 7. Analyzer usando WindowManager    | **Nova versão corrigida, mas fluxo usa a antiga** |
| 8. Validação de templates           | **Não corrigido**                                 |
| 9. `pz.enabled` respeitado          | **Corrigido apenas no analyzer novo**             |
| 10. Detecção de frame congelado     | **Não confirmado como corrigido**                 |
| 11. Métricas do scheduler/FPS       | **Não corrigido**                                 |
| 12. Killswitch imediato             | **Não corrigido**                                 |

---

# 1. Documentação

## Situação: parcial

O README foi atualizado e agora descreve:

* configuração externa;
* ROIs relativas;
* captura única;
* estado central;
* máquina de estados;
* `BotEngine`;
* sistema central de ações;
* testes automatizados;
* modo `--observe-only`;
* observabilidade.

Entretanto, ainda há inconsistências.

## Link local incorreto

O README ainda utiliza:

```markdown
[NEXT_STEPS.md](file:///c:/Users/ander/Projects/tibia-bot/NEXT_STEPS.md)
```

Esse link só funciona no computador em que esse caminho existe.

Deveria ser:

```markdown
[NEXT_STEPS.md](NEXT_STEPS.md)
```

O link local continua presente no início do README.

## README afirma mais do que o código entrega

O README afirma:

```text
AutoHealer, AutoAttacker e Overlay consomem apenas GameState.
```

Também afirma:

```text
Módulos não disparam inputs.
```

Porém, healer e combat ainda recebem `InputController` e possuem métodos legados que pressionam teclas diretamente. Portanto, a documentação está à frente do código real.

## Resultado

```text
[~] Documentação parcialmente atualizada
[ ] Remover link file:///
[ ] Corrigir afirmações que ainda não correspondem ao código
[ ] Garantir que AGENTS.md, NEXT_STEPS.md e README reflitam o fluxo realmente utilizado
```

---

# 2. GameAnalyzer fora do domínio

## Situação: criado, mas não utilizado

Foi criada uma nova implementação em:

```text
src/infrastructure/vision/game_analyzer.py
```

Essa versão recebe:

```python
frame: CapturedFrame
window_state: WindowState
```

Isso é melhor, pois o analyzer deixa de consultar diretamente HWND, foco e minimização.

Porém, a implementação antiga ainda existe:

```text
src/domain/analyzer.py
```

Ela continua importando:

```python
from src.utils.window import is_window_active, is_window_minimized
```

e recebe diretamente:

```python
hwnd_tibia
hwnd_obs
```

Isso mantém o domínio acoplado às janelas e à infraestrutura.

## O problema principal

O `main.py` continua importando:

```python
from src.domain.analyzer import GameAnalyzer
```

E o `BotEngine` também continua importando:

```python
from src.domain.analyzer import GameAnalyzer
```

Portanto, a implementação nova em `src/infrastructure/vision/` não está sendo utilizada pelo programa principal.

## Correção necessária

No `main.py`:

```python
from src.infrastructure.vision.game_analyzer import GameAnalyzer
```

No `bot_engine.py`:

```python
from src.infrastructure.vision.game_analyzer import GameAnalyzer
```

O engine também precisa construir o `WindowState`:

```python
window_state = WindowState(
    tibia_focused=self.window_manager.is_focused(self.hwnd_tibia),
    tibia_minimized=self.window_manager.is_minimized(self.hwnd_tibia),
    projector_available=self.hwnd_obs > 0,
)
```

E chamar:

```python
game_state = self.analyzer.analyze(
    frame=frame,
    window_state=window_state,
    config=self.config,
)
```

Depois disso, remover:

```text
src/domain/analyzer.py
```

## Resultado

```text
[~] Nova implementação criada
[ ] main.py ainda usa analyzer antigo
[ ] BotEngine ainda usa analyzer antigo
[ ] domain/analyzer.py ainda existe
```

---

# 3. Dependência do domínio para infraestrutura

## Situação: não corrigido

O arquivo:

```text
src/domain/game_state.py
```

ainda importa:

```python
from src.infrastructure.capture.frame import FrameStatus
```

Isso faz o domínio depender da infraestrutura.

A direção atual é:

```text
domain
    ↓
infrastructure
```

A direção desejada é o contrário:

```text
infrastructure
    ↓
domain
```

## Correção recomendada

Mover o enum para:

```text
src/domain/capture_status.py
```

Exemplo:

```python
from enum import Enum


class FrameStatus(Enum):
    VALID = "valid"
    STALE = "stale"
    FROZEN = "frozen"
    FAILED = "failed"
```

Então:

```python
# src/domain/game_state.py
from src.domain.capture_status import FrameStatus
```

```python
# src/infrastructure/capture/frame.py
from src.domain.capture_status import FrameStatus
```

O `CapturedFrame` pode continuar na infraestrutura, mas seu status deve utilizar o tipo definido no domínio.

## Problema adicional

Em `CapturedFrame`, a anotação usa:

```python
image: Optional[Any]
```

mas `Any` aparentemente não é importado no arquivo mostrado. Isso pode gerar erro ao importar o módulo dependendo da versão e da avaliação das annotations.

Deveria existir:

```python
from typing import Any, Optional
```

## Resultado

```text
[ ] FrameStatus ainda está na infraestrutura
[ ] GameState ainda depende da infraestrutura
[ ] Verificar import ausente de Any
```

---

# 4. Healer sem input direto

## Situação: não corrigido

O `AutoHealer` ainda recebe:

```python
input_controller: Optional[InputController]
```

e cria um controlador quando não recebe:

```python
self.input_controller = input_controller or create_input_controller()
```

Além disso, o método legado:

```python
check_and_heal()
```

executa:

```python
self.input_controller.press_key(act.key)
```

Isso contorna completamente:

* `DecisionController`;
* `ActionExecutor`;
* `--observe-only`;
* resolução de conflitos;
* validação final de segurança;
* cooldown central.

O `main.py` continua injetando o input diretamente:

```python
healer = AutoHealer(
    config.healer,
    input_controller=input_controller,
)
```

## Correção necessária

Construtor:

```python
class AutoHealer:
    def __init__(
        self,
        config: Optional[HealerConfig] = None,
    ):
        self.config = config or HealerConfig()
        self.enabled = False
```

Remover:

```python
InputController
create_input_controller
self.input_controller
check_and_heal
```

Ou manter temporariamente o nome `check_and_heal`, mas fazê-lo retornar ações:

```python
def check_and_heal(
    self,
    game_state: GameState,
) -> list[BotAction]:
    return self.get_proposed_actions(game_state)
```

## Resultado

```text
[ ] InputController ainda está no healer
[ ] Método legado ainda envia input
[ ] main.py ainda injeta input no healer
```

---

# 5. Combat sem input direto

## Situação: não corrigido

O mesmo problema existe no `AutoAttacker`.

Ele ainda possui:

```python
input_controller: Optional[InputController]
```

e:

```python
self.input_controller.press_key(act.key)
```

dentro do método legado `update()`.

O `main.py` também continua fazendo:

```python
combat = AutoAttacker(
    config.combat,
    input_controller=input_controller,
)
```

## Correção necessária

Remover do `AutoAttacker`:

```python
InputController
create_input_controller
self.input_controller
```

O módulo deve apenas retornar:

```python
list[BotAction]
```

## Resultado

```text
[ ] InputController ainda está no combat
[ ] Método legado ainda envia input
[ ] main.py ainda injeta input no combat
```

---

# 6. Cooldowns centralizados

## Situação: classe criada, mas não integrada

Foi criado:

```text
src/application/cooldown_manager.py
```

A classe possui:

```python
can_execute()
register_execution()
```

e sua documentação afirma que o registro deve acontecer somente depois da execução física bem-sucedida. Essa direção está correta.

Porém, o componente não está conectado ao fluxo.

O `BotEngine` não importa nem recebe `CooldownManager`.

O `ActionExecutor` também não utiliza `CooldownManager`.

O `DecisionController` mantém:

```python
self.last_action_times
```

mas não utiliza esse dicionário para nada.

## Healer ainda consome cooldown na proposta

O healer continua fazendo:

```python
self.last_emergency_potion_time = now
self.last_spell_time = now
self.last_mana_potion_time = now
```

logo após adicionar a ação proposta.

## Combat ainda consome cooldown na proposta

O combat continua fazendo:

```python
self.last_attack_time = now
```

logo após propor o ataque.

Isso significa que uma ação simulada, descartada ou não executada pode consumir o cooldown.

## Estrutura recomendada

O `BotAction` precisa carregar o cooldown:

```python
@dataclass(frozen=True)
class BotAction:
    action_type: ActionType
    priority: int
    key: str | None = None
    reason: str = ""
    cooldown_ms: int = 0
```

No executor:

```python
class ActionExecutor:
    def __init__(
        self,
        input_controller: InputController,
        cooldown_manager: CooldownManager,
    ):
        self.input_controller = input_controller
        self.cooldown_manager = cooldown_manager

    def execute(
        self,
        actions: list[BotAction],
        game_state: GameState,
        observe_only: bool = False,
    ) -> list[BotAction]:
        executed = []

        if not game_state.is_safe_to_act:
            return executed

        for action in actions:
            if not self.cooldown_manager.can_execute(
                action.action_type,
                action.cooldown_ms,
            ):
                continue

            if observe_only:
                continue

            self.input_controller.press_key(action.key)
            self.cooldown_manager.register_execution(
                action.action_type
            )
            executed.append(action)

        return executed
```

## Resultado

```text
[x] CooldownManager criado
[ ] CooldownManager não está no BotEngine
[ ] CooldownManager não está no ActionExecutor
[ ] Healer ainda controla cooldown
[ ] Combat ainda controla cooldown
[ ] Cooldown ainda é consumido na proposta
```

---

# 7. Conflitos entre ações

## Situação: não corrigido

O `DecisionController` continua adicionando todas as ações à lista:

```python
resolved.append(action)
```

A única exceção é a cura emergencial, que substitui as demais.

Assim, em um ciclo ainda podem ser executadas:

```text
HEAL
USE_MANA
ATTACK
```

O `ActionExecutor` percorre todas as ações recebidas e envia todas as respectivas teclas.

## Correção mínima recomendada

Inicialmente, permitir uma ação por ciclo:

```python
for action in sorted_actions:
    if not self._is_allowed(action, game_state, bot_state):
        continue

    return [action]

return []
```

## Alternativa posterior

Criar matriz explícita de compatibilidade:

```python
COMPATIBLE_ACTIONS = {
    ActionType.EMERGENCY_HEAL: set(),
    ActionType.HEAL: {
        ActionType.USE_MANA,
    },
    ActionType.USE_MANA: {
        ActionType.HEAL,
    },
    ActionType.ATTACK: set(),
    ActionType.LOOT: set(),
    ActionType.MOVE: set(),
}
```

## Resultado

```text
[ ] Ainda permite várias ações por ciclo
[ ] Não existe matriz de compatibilidade
[ ] last_action_times não é utilizado
```

---

# 8. Factory por plataforma

## Situação: não corrigido

A factory continua fazendo:

```python
if sys.platform == "win32":
    return WindowsWindowManager()

return WindowsWindowManager()
```

Portanto, qualquer plataforma recebe a implementação Windows.

No Linux, o `WindowsWindowManager` simplesmente retorna janelas vazias porque seus métodos verificam `sys.platform != "win32"`. Isso não é suporte a Linux; é apenas uma falha silenciosa.

## Correção necessária

```python
class UnsupportedPlatformError(RuntimeError):
    pass


def create_window_manager() -> WindowManager:
    if sys.platform == "win32":
        return WindowsWindowManager()

    if sys.platform.startswith("linux"):
        return X11WindowManager()

    raise UnsupportedPlatformError(
        f"Plataforma sem WindowManager: {sys.platform}"
    )
```

Caso o X11 ainda não esteja pronto:

```python
if sys.platform.startswith("linux"):
    raise UnsupportedPlatformError(
        "Linux detectado, mas X11WindowManager ainda não foi implementado."
    )
```

É melhor falhar claramente do que retornar uma implementação incorreta.

## Input

No input, plataformas não Windows retornam `MockInputController`. Isso é seguro, mas deve ser explícito no log e preferencialmente exigir `--observe-only`.

## Resultado

```text
[ ] Linux ainda recebe WindowsWindowManager
[ ] Não existe X11WindowManager no fluxo verificado
[ ] Plataforma não suportada não gera erro explícito
```

---

# 9. Analyzer usando WindowManager

## Situação: parcialmente corrigido

A interface do `WindowManager` possui:

```python
is_focused()
is_minimized()
```

A nova versão de `GameAnalyzer` recebe um `WindowState`, o que está correto.

Porém, o fluxo principal ainda usa a versão antiga de `GameAnalyzer`, que chama diretamente:

```python
is_window_active()
is_window_minimized()
```

## Resultado

```text
[x] WindowManager possui métodos necessários
[x] Novo analyzer aceita WindowState
[ ] Engine ainda não constrói WindowState
[ ] Engine ainda chama analyzer antigo
```

---

# 10. Validação dos templates

## Situação: não corrigido

O loader ainda converte os caminhos para string:

```python
target_tmpl = str(...)
pz_tmpl = str(...)
```

mas não verifica:

* se o arquivo existe;
* se é um arquivo;
* se o OpenCV consegue abri-lo;
* se o caminho relativo foi resolvido pela raiz do projeto.

## Correção recomendada

```python
def _validate_template_path(
    value: str,
    field_name: str,
    project_root: Path,
    enabled: bool,
) -> str:
    if not enabled:
        return value

    path = Path(value)

    if not path.is_absolute():
        path = project_root / path

    path = path.resolve()

    if not path.exists():
        raise ConfigValidationError(
            f"Template não encontrado em '{field_name}': {path}"
        )

    if not path.is_file():
        raise ConfigValidationError(
            f"Template inválido em '{field_name}': {path}"
        )

    return str(path)
```

Aplicação:

```python
target_tmpl = _validate_template_path(
    target_tmpl,
    "combat.target_template_path",
    project_root,
    combat_enabled,
)
```

```python
pz_tmpl = _validate_template_path(
    pz_tmpl,
    "pz.template_path",
    project_root,
    pz_enabled,
)
```

## Resultado

```text
[ ] Templates ainda não são validados
[ ] Caminhos continuam armazenados como strings relativas
```

---

# 11. `pz.enabled`

## Situação: corrigido apenas no analyzer novo

Na implementação nova:

```python
if cfg and not cfg.pz.enabled:
    in_pz = None
else:
    in_pz = is_in_pz(...)
```

Isso está correto.

Porém, a implementação antiga ainda chama `is_in_pz()` sem verificar `cfg.pz.enabled`.

Como `main.py` e `BotEngine` continuam usando o analyzer antigo, a configuração ainda não é respeitada no fluxo real.

## Resultado

```text
[x] Corrigido no analyzer novo
[ ] Não corrigido no analyzer atualmente utilizado
```

---

# 12. Detecção de frame congelado

## Situação: não confirmada como corrigida

O arquivo padrão ainda usa:

```yaml
loop_interval_ms: 50
```

Não encontrei no trecho revisado uma nova configuração por tempo, como:

```yaml
capture:
  frozen_timeout_seconds: 8
```

A documentação afirma que existe detecção por N ciclos, mas isso ainda pode provocar falsos positivos quando o jogo permanece visualmente parado.

## Recomendação

Preferir timeout temporal:

```yaml
capture:
  frozen_detection:
    enabled: true
    timeout_seconds: 8
    difference_threshold: 0.5
```

E armazenar:

```python
self.last_visual_change_at
```

em vez de depender somente do número de frames iguais.

## Resultado

```text
[ ] Não foi identificada configuração temporal
[ ] Risco de falso positivo permanece
```

---

# 13. Scheduler e FPS

## Situação: não corrigido

O scheduler ainda calcula:

```python
elapsed_sec = time.perf_counter() - cycle_start_perf
self.last_cycle_time_ms = elapsed_sec * 1000
```

antes de executar o `sleep()`.

Depois, `average_fps` usa:

```python
1000.0 / self.last_cycle_time_ms
```

Isso representa aproximadamente o FPS de processamento, não o FPS real do loop.

Também não é uma média: utiliza apenas o último ciclo.

## Correção recomendada

```python
def tick(self, cycle_start_perf: float) -> float:
    processing_elapsed = time.perf_counter() - cycle_start_perf

    target_sleep = max(
        0.0,
        self.target_interval_ms / 1000.0 - processing_elapsed,
    )

    if target_sleep > 0:
        time.sleep(target_sleep)

    full_cycle_elapsed = time.perf_counter() - cycle_start_perf

    self.last_processing_time_ms = processing_elapsed * 1000.0
    self.last_cycle_time_ms = full_cycle_elapsed * 1000.0
    self.total_cycles += 1

    return self.last_cycle_time_ms
```

E:

```python
@property
def actual_fps(self) -> float:
    if self.last_cycle_time_ms <= 0:
        return 0.0

    return 1000.0 / self.last_cycle_time_ms
```

## Resultado

```text
[ ] FPS ainda ignora o sleep
[ ] average_fps ainda não é uma média
```

---

# 14. Killswitch imediato

## Situação: não corrigido

O callback continua apenas alternando:

```python
self.killswitch_paused
```

e registrando o log.

A chamada:

```python
self.input_controller.release_all()
```

ocorre apenas no método `stop()`, durante o encerramento completo do engine.

## Correção necessária

```python
def toggle_killswitch(self, event=None) -> None:
    self.killswitch_paused = not self.killswitch_paused

    if self.killswitch_paused:
        try:
            self.input_controller.release_all()
        except Exception as exc:
            logger.log(
                "SYSTEM",
                f"Falha ao liberar inputs: {exc}",
                level="ERROR",
            )

        self.scheduler.cancel_pending()
        self.action_executor.cancel_pending()

        logger.log(
            "SYSTEM",
            "KILLSWITCH ACIONADO: ações interrompidas.",
            level="WARNING",
        )
        return

    logger.log(
        "SYSTEM",
        "KILLSWITCH DESATIVADO.",
        level="INFO",
    )
```

Mesmo que ainda não existam filas pendentes, `release_all()` deve acontecer imediatamente.

## Resultado

```text
[ ] Callback não libera teclas
[ ] Callback não limpa ações pendentes
[ ] Liberação ocorre somente no encerramento
```

---

# Problemas adicionais encontrados

## 1. Duplicação do GameAnalyzer

Atualmente existem duas implementações:

```text
src/domain/analyzer.py
src/infrastructure/vision/game_analyzer.py
```

Uma duplicação assim é perigosa porque correções podem ser feitas em uma versão enquanto o programa executa a outra. Isso já aconteceu com `pz.enabled`.

### Correção

Manter apenas:

```text
src/infrastructure/vision/game_analyzer.py
```

---

## 2. ActionExecutor recebe dependências no método

Atualmente:

```python
execute(
    actions,
    game_state,
    input_controller,
    observe_only,
)
```

É mais consistente injetar o `InputController` no construtor:

```python
class ActionExecutor:
    def __init__(
        self,
        input_controller: InputController,
        cooldown_manager: CooldownManager,
    ):
        self.input_controller = input_controller
        self.cooldown_manager = cooldown_manager
```

Assim, o executor fica pronto para uso e mais fácil de testar.

---

## 3. ActionExecutor não retorna resultado

Atualmente o executor retorna `None`.

Para registrar cooldown corretamente e melhorar a observabilidade, ele deveria retornar algo como:

```python
@dataclass(frozen=True)
class ActionExecutionResult:
    action: BotAction
    executed: bool
    simulated: bool
    reason: str
```

---

## 4. `main.py` ainda injeta infraestrutura em módulos de regra

O `main.py` injeta o mesmo `input_controller` em:

```python
AutoHealer
AutoAttacker
BotEngine
```

O input deveria ser entregue somente ao `ActionExecutor`.

Fluxo correto:

```text
AutoHealer ─┐
            ├─ BotAction → DecisionController → ActionExecutor → InputController
AutoCombat ─┘
```

---

# Estado final atualizado

```text
[~] README atualizado, mas ainda inconsistente
[ ] Link file:/// removido
[~] Novo GameAnalyzer criado
[ ] Novo GameAnalyzer conectado ao main.py
[ ] Novo GameAnalyzer conectado ao BotEngine
[ ] Analyzer antigo removido
[ ] FrameStatus movido ao domínio
[ ] Healer sem InputController
[ ] Combat sem InputController
[ ] Métodos legados de input removidos
[x] CooldownManager criado
[ ] CooldownManager conectado ao executor
[ ] Cooldown registrado somente após execução
[ ] Uma ação principal por ciclo
[ ] Matriz de compatibilidade
[ ] Factory corrigida para Linux
[ ] X11WindowManager implementado ou erro explícito
[~] pz.enabled corrigido apenas no analyzer novo
[ ] Templates validados
[ ] Detecção de congelamento baseada em tempo
[ ] Métrica de FPS corrigida
[ ] Killswitch liberando inputs imediatamente
```

---

# Ordem recomendada de correção

## Prioridade 1 — eliminar duplicações

1. Alterar imports para `src.infrastructure.vision.game_analyzer`.
2. Fazer o engine construir `WindowState`.
3. Apagar `src/domain/analyzer.py`.

## Prioridade 2 — fechar o único caminho de input

4. Remover `InputController` do healer.
5. Remover `InputController` do combat.
6. Remover `check_and_heal()` legado.
7. Remover `update()` legado ou fazê-lo retornar ações.
8. Injetar input apenas no `ActionExecutor`.

## Prioridade 3 — cooldown e ações

9. Integrar `CooldownManager`.
10. Adicionar `cooldown_ms` ao `BotAction`.
11. Registrar cooldown somente após input bem-sucedido.
12. Limitar inicialmente a uma ação por ciclo.

## Prioridade 4 — segurança

13. Liberar inputs dentro do killswitch.
14. Corrigir factory por plataforma.
15. Validar templates na inicialização.
16. Corrigir detecção de frames congelados.

## Prioridade 5 — qualidade

17. Corrigir scheduler e FPS.
18. Mover `FrameStatus` para o domínio.
19. Corrigir README, AGENTS e NEXT_STEPS.
20. Executar toda a suíte de testes.

---

# Veredito

As correções foram **iniciadas**, mas ainda não foram aplicadas completamente.

A mudança mais importante criada foi o novo:

```text
src/infrastructure/vision/game_analyzer.py
```

Porém, como o fluxo principal continua importando:

```text
src/domain/analyzer.py
```

essa correção ainda não produz efeito na execução real.

O mesmo acontece com o `CooldownManager`: a classe existe, mas nenhum componente principal a utiliza.

Antes de considerar essa fase concluída, os pontos mínimos são:

```text
[ ] Usar somente o analyzer novo
[ ] Remover input direto de healer e combat
[ ] Integrar CooldownManager
[ ] Controlar conflitos de ações
[ ] Corrigir factory por plataforma
[ ] Killswitch liberar inputs imediatamente
[ ] Executar e validar os testes
```

Não iniciei nem executei o repositório localmente; esta revisão foi feita sobre os arquivos públicos atuais da branch `main`. Portanto, confirmei estrutura e código publicado, mas não posso afirmar que a suíte de testes passa.
