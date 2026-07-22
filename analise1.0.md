# Revisão da Implementação — TibiaBotWin

Revisão realizada sobre o estado atual da branch `main`, comparando o código existente com as etapas definidas anteriormente no roadmap arquitetural.

---

# Resumo geral

As etapas iniciais foram implementadas de forma real no projeto.

Não são apenas arquivos vazios ou estruturas preparadas: já existem configurações, estados, engine, scheduler, ações e testes.

Entretanto, ainda há alguns pontos arquiteturais importantes que precisam ser corrigidos antes de iniciar funcionalidades mais complexas, como:

* cavebot;
* movimentação;
* auto-loot;
* navegação por minimapa;
* aproximação automática de inimigos.

## Situação atual das etapas

| Etapa                        | Situação                                |
| ---------------------------- | --------------------------------------- |
| 1. Configuração externa      | Quase concluída                         |
| 2. ROIs relativas            | Implementada                            |
| 3. Captura única por ciclo   | Implementada                            |
| 4. Estado central            | Implementado, com dependência incorreta |
| 5. Máquina de estados        | Implementada parcialmente               |
| 6. BotEngine e scheduler     | Implementados                           |
| 7. Abstrações por plataforma | Parcial e incompleta                    |
| 8. Sistema central de ações  | Parcial, com bypass legado              |
| 9. Testes automatizados      | Estrutura implementada                  |
| 10. Observabilidade          | Parcial                                 |
| Documentação                 | Desatualizada                           |

---

# O que foi implementado corretamente

## 1. Configuração externa

Foi criado um sistema real de configuração contendo:

* `AppConfig`;
* configuração de janelas;
* configuração do healer;
* configuração de combate;
* configuração de Protection Zone;
* configuração de ROIs;
* intervalo do loop;
* carregamento do `default.yaml`;
* sobreposição de valores por profile;
* validação de percentuais;
* validação de hotkeys;
* validação de cooldowns;
* validação das ROIs.

Também existem opções de inicialização como:

```bash
python -m src.main --config caminho.yaml
```

```bash
python -m src.main --profile nome-do-perfil
```

```bash
python -m src.main --observe-only
```

Essa implementação está alinhada com o roadmap.

### Situação

```text
[~] Quase concluída
```

Ainda faltam algumas validações, principalmente de arquivos de templates.

---

## 2. ROIs relativas

A implementação das ROIs está bem estruturada.

Foram criados conceitos como:

* `RelativeROI`;
* `AbsoluteROI`;
* validação dos valores entre `0.0` e `1.0`;
* conversão de coordenadas relativas para pixels;
* limitação das coordenadas dentro do frame;
* compatibilidade temporária com o formato absoluto antigo.

Exemplo conceitual:

```yaml
regions:
  hp:
    x: 0.187
    y: 0.000
    width: 0.281
    height: 0.018
```

Isso permite que as regiões sejam recalculadas conforme a resolução real do frame.

### Situação

```text
[x] Implementada
```

---

## 3. Captura única por ciclo

O `BotEngine` realiza apenas uma captura principal por iteração.

Fluxo atual:

```text
captura
    ↓
CapturedFrame
    ↓
GameAnalyzer
    ↓
GameState
```

O mesmo frame é utilizado para analisar:

* HP;
* mana;
* Protection Zone;
* Battle List;
* alvo ativo;
* estado visual geral.

Healer e combat não realizam novas capturas durante o fluxo principal.

Isso evita:

* frames de instantes diferentes;
* capturas duplicadas;
* uso desnecessário de CPU;
* inconsistência entre os módulos.

O capturador também possui:

* timestamp;
* largura;
* altura;
* status;
* contagem de falhas;
* detecção de frame possivelmente congelado;
* encerramento explícito.

### Situação

```text
[x] Implementada
```

---

## 4. Estado central do jogo

Foram criados estados centrais e imutáveis.

Entre eles:

* `GameState`;
* `PlayerState`;
* `TargetState`;
* `WindowState`;
* `CaptureState`;
* `BotState`;
* `BotMode`;
* `StateTransition`.

Os estados utilizam estruturas imutáveis, como:

```python
@dataclass(frozen=True)
class GameState:
    ...
```

Essa é uma boa decisão, pois cada ciclo representa um snapshot do jogo.

Outro ponto positivo é que falhas de detecção não retornam valores falsamente seguros.

Por exemplo, quando uma informação não pode ser determinada, ela pode retornar:

```python
hp_percent = None
mana_percent = None
in_protection_zone = None
```

Em vez de assumir:

```python
hp_percent = 100
mana_percent = 100
in_protection_zone = False
```

### Situação

```text
[~] Implementada, mas com dependência arquitetural incorreta
```

---

## 5. Máquina de estados

Já existe uma máquina de estados capaz de representar modos como:

```python
class BotMode(Enum):
    PAUSED = "paused"
    UNSAFE = "unsafe"
    IDLE = "idle"
    IN_PROTECTION_ZONE = "in_protection_zone"
    COMBAT = "combat"
```

Também existem registros de transição com:

* estado anterior;
* estado atual;
* motivo;
* timestamp.

A prioridade básica está organizada da seguinte forma:

```text
Killswitch
    ↓
Validação das janelas
    ↓
Validação da captura
    ↓
Protection Zone
    ↓
Combate
    ↓
Idle
```

Essa fundação está correta.

### Situação

```text
[~] Implementada parcialmente
```

Ainda faltam estados futuros, regras de compatibilidade e integração completa com as ações.

---

## 6. BotEngine e scheduler

O `main.py` está começando a funcionar corretamente como composition root.

Responsabilidades atuais aproximadas:

```text
main.py
    ↓
carrega configuração
    ↓
cria dependências
    ↓
cria BotEngine
    ↓
inicia execução
```

O `BotEngine` centraliza o fluxo:

```text
captura
    ↓
análise
    ↓
GameState
    ↓
BotState
    ↓
propostas de ação
    ↓
resolução de conflitos
    ↓
execução
    ↓
overlay e métricas
```

Também existe tratamento de encerramento com:

* `finally`;
* liberação de teclas;
* fechamento do capturador;
* restauração da opacidade;
* finalização de componentes.

O scheduler controla o intervalo do loop e reduz a necessidade de `sleep()` espalhado.

### Situação

```text
[x] Implementados
```

---

## 7. Sistema central de ações

Foram criados elementos como:

* `BotAction`;
* `ActionType`;
* `DecisionController`;
* `ActionExecutor`;
* prioridades;
* bloqueios de segurança;
* bloqueio de ações ofensivas em Protection Zone;
* prioridade para cura emergencial;
* modo `--observe-only`.

O fluxo esperado está começando a ser respeitado:

```text
Módulo
    ↓
propõe BotAction
    ↓
DecisionController
    ↓
ActionExecutor
    ↓
input real
```

Essa estrutura é uma evolução importante.

### Situação

```text
[~] Parcial
```

Ainda existem métodos legados capazes de executar inputs diretamente.

---

## 8. Testes

O projeto possui testes relacionados a:

* ações;
* captura;
* configuração;
* diagnósticos;
* engine;
* estado;
* abstrações de plataforma;
* ROI;
* máquina de estados;
* fixtures de visão computacional;
* pipeline completo.

A estrutura geral está próxima de:

```text
tests/
├── fixtures/
├── unit/
├── integration/
└── manual/
```

### Situação

```text
[x] Estrutura implementada
```

A existência dos testes foi confirmada, mas eles ainda precisam ser executados para confirmar que passam.

Não se deve afirmar que os testes passaram sem executar:

```bash
pytest
```

---

# Problemas encontrados

## 1. A documentação está desatualizada

Este é um dos problemas mais evidentes.

O código já implementou partes importantes da nova arquitetura, mas os documentos públicos ainda descrevem a estrutura antiga.

## NEXT_STEPS.md

O arquivo ainda apresenta um roadmap antigo e não contém todas as fases discutidas.

Ele ainda pode indicar Auto-Loot como próxima etapa, mesmo com várias fundações ainda incompletas.

## AGENTS.md

O arquivo ainda mantém regras antigas, como:

* dependência direta de Win32;
* uso obrigatório de `pydirectinput`;
* estrutura baseada em `src/bot` e `src/utils`;
* ausência de regras sobre `GameState`;
* ausência de regras sobre `BotEngine`;
* ausência de executor central;
* ausência de abstração por plataforma.

## README.md

O README ainda possui informações antigas, como:

* arquitetura monolítica;
* ROIs absolutas;
* ausência de documentação sobre profiles;
* ausência de `--observe-only`;
* ausência do `BotEngine`;
* ausência do sistema central de ações;
* possíveis links locais `file:///`.

### Correção necessária

Atualizar e sincronizar:

```text
README.md
NEXT_STEPS.md
AGENTS.md
```

A documentação deve refletir o comportamento real do código.

---

## 2. O domínio depende da infraestrutura

Existe uma dependência incorreta do domínio para a infraestrutura.

Exemplo conceitual:

```python
from src.infrastructure.capture.frame import FrameStatus
```

dentro de um arquivo de domínio.

A direção correta deveria ser:

```text
domain
    ↑
application
    ↑
infrastructure
```

O domínio não deve importar infraestrutura.

## Problema adicional no GameAnalyzer

O `GameAnalyzer` está dentro de `src/domain`, mas utiliza elementos como:

```python
import cv2
```

Além de dependências de:

* captura;
* janela;
* OpenCV;
* HWND;
* sistema de arquivos;
* utilitários específicos de plataforma.

Portanto, o analyzer não é domínio puro.

### Estrutura recomendada

```text
src/
├── domain/
│   ├── game_state.py
│   ├── bot_state.py
│   ├── actions.py
│   └── capture_status.py
│
└── infrastructure/
    └── vision/
        ├── game_analyzer.py
        ├── hp_detector.py
        ├── mana_detector.py
        ├── pz_detector.py
        └── target_detector.py
```

## Correção recomendada

Mover:

```text
src/domain/analyzer.py
```

para:

```text
src/infrastructure/vision/game_analyzer.py
```

Mover o `FrameStatus` para uma estrutura neutra:

```text
src/domain/capture_status.py
```

ou:

```text
src/domain/capture.py
```

---

## 3. Healer e combat ainda podem executar input diretamente

Apesar de existir um fluxo novo baseado em propostas de ação, métodos antigos ainda utilizam:

```python
self.input_controller.press_key(...)
```

Isso permite contornar:

* `DecisionController`;
* prioridade global;
* bloqueios de segurança;
* executor central;
* modo de observação;
* matriz de compatibilidade.

## Problema arquitetural

Atualmente existem dois caminhos:

```text
Caminho correto:
Healer → BotAction → DecisionController → ActionExecutor
```

```text
Caminho legado:
Healer → InputController
```

O segundo caminho deve ser removido.

## Correção recomendada

Healer e combat não devem receber `InputController`.

Exemplo:

```python
class AutoHealer:
    def get_proposed_actions(
        self,
        game_state: GameState,
    ) -> list[BotAction]:
        ...
```

Remover ou adaptar métodos como:

```python
check_and_heal()
```

para retornarem ações:

```python
def check_and_heal(
    self,
    game_state: GameState,
) -> list[BotAction]:
    return self.get_proposed_actions(game_state)
```

O mesmo deve ser feito para o `AutoAttacker`.

---

## 4. Cooldown é consumido antes da execução

Atualmente, módulos podem fazer algo semelhante a:

```python
actions.append(action)
self.last_spell_time = now
```

Isso atualiza o cooldown quando a ação é proposta, e não quando ela é executada.

## Problema

A ação pode ser:

* descartada;
* bloqueada;
* substituída por outra;
* simulada em `--observe-only`;
* interrompida pelo killswitch;
* rejeitada pelo executor;
* falhar durante o envio do input.

Mesmo assim, o módulo passa a considerar que ela foi executada.

## Fluxo correto

```text
ação proposta
    ↓
ação aprovada
    ↓
input executado com sucesso
    ↓
cooldown registrado
```

## Estrutura recomendada

```python
if cooldown_manager.can_execute(action):
    result = executor.execute(action)

    if result.success:
        cooldown_manager.register_execution(action)
```

## Correção necessária

Centralizar cooldowns em um componente como:

```text
src/application/cooldown_manager.py
```

Exemplo:

```python
class CooldownManager:
    def can_execute(
        self,
        action: BotAction,
        now: float,
    ) -> bool:
        ...

    def register_execution(
        self,
        action: BotAction,
        now: float,
    ) -> None:
        ...
```

Módulos não devem manter `last_spell_time` ou `last_attack_time` quando o cooldown for responsabilidade global.

---

## 5. O resolvedor permite várias ações incompatíveis

O `DecisionController` pode permitir múltiplas ações no mesmo ciclo.

Exemplo:

```text
HEAL
USE_MANA
ATTACK
```

Isso pode gerar três inputs quase simultaneamente.

Mesmo que tecnicamente algumas ações possam coexistir, deve existir uma regra explícita.

## Primeira opção: uma ação por ciclo

A solução mais simples inicialmente:

```python
return sorted_actions[:1]
```

## Segunda opção: matriz de compatibilidade

Exemplo:

```python
COMPATIBILITY = {
    ActionType.EMERGENCY_HEAL: set(),
    ActionType.HEAL: {
        ActionType.USE_MANA,
    },
    ActionType.USE_MANA: {
        ActionType.HEAL,
    },
    ActionType.ATTACK: set(),
}
```

## Prioridade recomendada

```text
1. EMERGENCY_HEAL
2. HEAL
3. USE_MANA
4. ATTACK
5. LOOT
6. MOVE
7. IDLE_ACTION
```

Na primeira versão, é mais seguro permitir apenas uma ação principal por ciclo.

---

## 6. A abstração por plataforma ainda está incorreta

A factory seleciona implementações por plataforma, mas existe um fallback inadequado.

Comportamento atual aproximado:

```text
Windows → WindowsWindowManager
Linux → WindowsWindowManager
```

Isso é incorreto.

Uma plataforma não suportada não deve receber uma implementação Windows silenciosamente.

## Comportamento correto

```python
if sys.platform == "win32":
    return WindowsWindowManager()

if sys.platform.startswith("linux"):
    return X11WindowManager()

raise UnsupportedPlatformError(
    f"Plataforma não suportada: {sys.platform}"
)
```

## Sobre o input no Linux

Retornar um `MockInputController` pode ser seguro durante desenvolvimento, mas precisa estar explícito.

Exemplo de log:

```text
[AVISO] Input real não disponível para Linux.
[AVISO] Aplicação executando em modo simulado.
```

O sistema não deve aparentar ter suporte completo quando está usando mock.

---

## 7. GameAnalyzer ignora a abstração de janela

Mesmo existindo um `WindowManager`, o analyzer ainda chama funções diretas de janela.

Exemplo conceitual:

```python
is_window_active(hwnd_tibia)
is_window_minimized(hwnd_tibia)
```

Isso volta a acoplar a análise a funções específicas de plataforma.

## Fluxo recomendado

O `WindowManager` deve produzir o estado da janela:

```python
window_state = WindowState(
    tibia_focused=window_manager.is_focused(hwnd_tibia),
    tibia_minimized=window_manager.is_minimized(hwnd_tibia),
    projector_available=window_manager.exists(hwnd_obs),
)
```

Depois o analyzer deve receber esse estado:

```python
game_state = analyzer.analyze(
    frame=frame,
    window_state=window_state,
)
```

O analyzer não deveria conhecer HWND diretamente.

---

## 8. Configuração não valida a existência dos templates

A configuração aceita caminhos como:

```yaml
combat:
  target_template_path: templates/target_red.png
```

```yaml
protection_zone:
  template_path: templates/pz.png
```

Mas aparentemente não confirma se os arquivos realmente existem.

## Risco

O bot inicia normalmente e falha apenas durante a análise visual.

## Correção recomendada

Durante o carregamento:

```python
def validate_existing_file(
    path_value: str,
    field_name: str,
    project_root: Path,
) -> Path:
    path = Path(path_value)

    if not path.is_absolute():
        path = project_root / path

    path = path.resolve()

    if not path.exists():
        raise ConfigError(
            f"Arquivo não encontrado em '{field_name}': {path}"
        )

    if not path.is_file():
        raise ConfigError(
            f"O caminho de '{field_name}' não é um arquivo: {path}"
        )

    return path
```

Também é importante resolver caminhos relativos pela raiz do projeto, não pelo diretório atual do terminal.

## Correto

```text
project_root/templates/pz.png
```

## Incorreto

```text
diretorio-onde-o-terminal-foi-aberto/templates/pz.png
```

---

## 9. `pz.enabled` aparentemente não é respeitado

A configuração possui algo semelhante a:

```yaml
protection_zone:
  enabled: false
```

Mas o detector continua sendo chamado.

## Comportamento esperado

```python
if not config.pz.enabled:
    pz_state = None
else:
    pz_state = pz_detector.detect(frame)
```

Também deve existir uma diferença clara entre:

```text
False = detector executou e não encontrou PZ
None = detector desabilitado ou resultado desconhecido
```

---

## 10. Detecção de frame congelado pode gerar falso positivo

O loop executa rapidamente.

Exemplo:

```yaml
loop_interval_ms: 50
```

Se o limite for 30 frames iguais, o sistema pode considerar o frame congelado em aproximadamente:

```text
30 × 50 ms = 1500 ms
```

Ou seja, cerca de 1,5 segundo.

Um jogador parado pode produzir uma imagem praticamente estática.

## Riscos

O bot pode entrar em `UNSAFE` mesmo com o Projetor funcionando corretamente.

## Abordagem melhor

Combinar múltiplos sinais:

* tempo total sem alteração;
* diferença visual;
* estado da janela;
* sucesso da API de captura;
* presença de algum elemento animado;
* hash parcial de regiões dinâmicas;
* threshold configurável em segundos.

Exemplo de configuração:

```yaml
capture:
  frozen_detection:
    enabled: true
    timeout_seconds: 8
    difference_threshold: 0.5
    required_identical_checks: 5
```

Também é melhor analisar apenas uma região que normalmente muda, em vez de exigir que o frame inteiro mude.

---

## 11. Scheduler calcula FPS de maneira incorreta

O scheduler mede o tempo de processamento antes do `sleep()`.

Assim, o valor chamado de FPS pode representar:

```text
velocidade máxima de processamento
```

e não:

```text
frequência real do loop
```

Também pode não ser uma média real.

## Sugestão de métricas separadas

```python
processing_time_ms
cycle_time_ms
sleep_time_ms
actual_fps
processing_fps
```

Exemplo:

```python
cycle_start = time.perf_counter()

run_cycle()

processing_end = time.perf_counter()
processing_time = processing_end - cycle_start

sleep_time = scheduler.sleep_remaining(
    processing_time
)

cycle_end = time.perf_counter()
cycle_time = cycle_end - cycle_start

actual_fps = (
    1.0 / cycle_time
    if cycle_time > 0
    else 0.0
)
```

Se a métrica atual mede apenas processamento, ela deveria ser chamada:

```text
processing_fps
```

---

## 12. Killswitch não libera imediatamente os inputs

O callback do killswitch altera apenas o estado de pausa.

Entretanto, a regra definida anteriormente exige prioridade absoluta.

Ao ativar o killswitch, ele deve:

* interromper novas ações;
* limpar ações pendentes;
* cancelar scheduler de input;
* liberar teclas pressionadas;
* interromper movimento;
* atualizar overlay;
* registrar a mudança.

## Correção recomendada

```python
def toggle_killswitch(self) -> None:
    self.killswitch_paused = not self.killswitch_paused

    if self.killswitch_paused:
        self.input_controller.release_all()
        self.action_queue.clear()
        self.logger.warning(
            "Killswitch ativado. Inputs interrompidos."
        )
```

O executor também deve verificar o killswitch imediatamente antes de cada ação.

---

# Avaliação atual

A arquitetura principal já está próxima do fluxo planejado:

```text
CapturedFrame
    ↓
GameState
    ↓
BotState
    ↓
BotAction
    ↓
DecisionController
    ↓
ActionExecutor
```

Isso representa uma evolução significativa.

Entretanto, algumas partes antigas ainda permitem contornar esse fluxo.

## Checklist atual

```text
[x] Configuração externa básica
[x] ROIs relativas
[x] Captura única
[x] GameState imutável
[x] Máquina de estados básica
[x] BotEngine
[x] Scheduler básico
[~] Abstrações de plataforma
[~] Sistema central de ações
[x] Estrutura de testes
[ ] Documentação sincronizada
[ ] Remoção completa dos bypasses legados
[ ] Cooldowns centralizados
[ ] X11WindowManager
[ ] Separação correta entre domínio e infraestrutura
[ ] Templates validados na inicialização
[ ] Matriz de compatibilidade de ações
[ ] Killswitch com interrupção imediata
```

---

# Ordem recomendada para as próximas correções

## 1. Atualizar a documentação

Atualizar:

```text
AGENTS.md
NEXT_STEPS.md
README.md
```

Esses arquivos precisam representar a arquitetura atual.

---

## 2. Corrigir a separação entre domínio e infraestrutura

Mover:

```text
src/domain/analyzer.py
```

para:

```text
src/infrastructure/vision/game_analyzer.py
```

Mover ou recriar o status da captura dentro do domínio.

---

## 3. Remover inputs diretos de healer e combat

Remover:

```python
InputController
```

dos construtores de healer e combat.

Eliminar métodos que pressionam teclas diretamente.

---

## 4. Centralizar os cooldowns

Criar:

```text
src/application/cooldown_manager.py
```

Registrar cooldown apenas depois que a ação for executada com sucesso.

---

## 5. Corrigir o DecisionController

Inicialmente, limitar para uma ação principal por ciclo.

Depois, implementar uma matriz de compatibilidade.

---

## 6. Corrigir a factory por plataforma

Não retornar implementação Windows em sistemas Linux.

Criar comportamento explícito:

```text
Windows → implementação real
Linux/X11 → implementação real ou erro claro
Outros → erro de plataforma não suportada
```

---

## 7. Fazer o WindowManager construir o WindowState

O analyzer não deve acessar diretamente HWND ou funções Win32.

---

## 8. Respeitar configurações `enabled`

Garantir que:

```yaml
enabled: false
```

realmente impeça o detector ou módulo de executar.

Aplicar isso a:

* healer;
* combat;
* PZ;
* overlay;
* frozen frame;
* módulos futuros.

---

## 9. Validar templates na inicialização

Verificar:

* existência;
* tipo do caminho;
* resolução relativa à raiz;
* possibilidade de leitura pelo OpenCV.

---

## 10. Executar todos os testes

Comandos recomendados:

```bash
python -m compileall src
```

```bash
pytest
```

Se Ruff estiver configurado:

```bash
ruff check .
```

```bash
ruff format --check .
```

Se houver type checker:

```bash
mypy src
```

ou:

```bash
pyright
```

---

# Critérios para iniciar o cavebot

O cavebot não deve começar antes de concluir os itens abaixo:

```text
[ ] GameAnalyzer fora do domínio
[ ] Healer sem input direto
[ ] Combat sem input direto
[ ] Cooldowns centralizados
[ ] DecisionController com conflitos controlados
[ ] Factory corrigida
[ ] WindowManager utilizado corretamente
[ ] Killswitch imediato
[ ] Todos os testes passando
[ ] Documentação atualizada
```

Depois disso, a primeira versão de cavebot pode começar com:

```text
Waypoints relativos
    ↓
Movimento de um tile
    ↓
Confirmação visual pelo minimapa
    ↓
Detecção de travamento
    ↓
Combate interrompendo a rota
    ↓
Retorno ao waypoint
```

---

# Conclusão

As fundações foram implementadas em boa parte e a direção geral está correta.

Os maiores avanços foram:

* configuração externa;
* ROIs relativas;
* captura única;
* estado central;
* máquina de estados;
* `BotEngine`;
* scheduler;
* sistema de ações;
* modo de observação;
* estrutura de testes.

Os maiores problemas restantes são:

1. documentação antiga;
2. domínio dependendo da infraestrutura;
3. healer e combat executando inputs diretamente;
4. cooldown consumido antes da execução;
5. ações incompatíveis no mesmo ciclo;
6. factory retornando Windows no Linux;
7. analyzer ignorando o `WindowManager`;
8. templates não validados;
9. configurações `enabled` não respeitadas completamente;
10. detecção de frame congelado agressiva;
11. métricas de FPS incorretas;
12. killswitch sem liberação imediata.

A recomendação é corrigir esses pontos antes de implementar cavebot, movimentação ou auto-loot.
