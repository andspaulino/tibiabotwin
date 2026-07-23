# Próximos Passos — Tibia Bot

Este documento registra o estado atual, as decisões arquiteturais e a ordem recomendada para evolução do projeto.

O objetivo é evoluir o projeto de um conjunto de módulos que observam a tela e enviam comandos para um fluxo centralizado:

```text
Captura → Percepção → Estado → Decisão → Execução
```

---

## Estado atual do projeto

### Fase 12A — Percepção do minimapa (em calibração)

* [x] Adicionar `MinimapState` imutável ao `GameState`.
* [x] Analisar a ROI configurável de minimapa no frame único do ciclo.
* [x] Detectar todos os templates de marcador com confiança e coordenadas locais.
* [x] Permitir auditoria opcional do layout por `cross.png`.
* [x] Retornar estado indisponível para frame, ROI ou validação inválidos.
* [x] Cobrir a análise com testes unitários sintéticos.
* [ ] Calibrar `regions.minimap` e validar com frames reais versionados.
* [x] Implementar a Fase 12B: payloads tipados de tecla e mouse, executor central e simulação em `--observe-only`.
* [~] Fase 12C: `MarkerSelector`, cálculo de distância, confirmação de chegada e `StuckDetector` implementados e testados como componentes puros.
* [x] Integrar o `CavebotController` ao `BotEngine` exclusivamente em `--observe-only`; o perfil `cavebot` simula um waypoint `flag0` sem clique físico.
* [ ] Antes de habilitar input real, converter coordenadas do frame do Projetor para coordenadas de tela e validar a rota completa com controles de segurança.


### Inicialização e gerenciamento de janelas

* [x] Verificar a existência da janela do Tibia.
* [x] Verificar a existência da janela do Projetor do OBS.
* [x] Inicializar o bot pelo `launcher.py`.
* [x] Ocultar visualmente a janela do Tibia.
* [x] Restaurar a opacidade da janela ao encerrar a aplicação.
* [x] Interromper ações quando a janela estiver minimizada.
* [x] Interromper ações quando o Tibia não estiver com foco.

### Segurança operacional

* [x] Adicionar killswitch global pela tecla `Pause`.
* [x] Permitir pausar e retomar todos os módulos.
* [x] Evitar envio de comandos quando o bot estiver pausado.
* [x] Evitar envio de comandos quando a janela correta não estiver disponível.
* [x] Criar um estado global de segurança.
* [x] Bloquear todas as ações quando o estado da captura for inválido.
* [x] Bloquear ações quando uma ROI obrigatória não puder ser analisada.
* [x] Garantir que nenhuma ação automática seja executada na inicialização.

### Captura e visão computacional

* [x] Capturar a área do Projetor do OBS.
* [x] Ler a barra de vida.
* [x] Ler a barra de mana.
* [x] Detectar Protection Zone.
* [x] Detectar criaturas na Battle List.
* [x] Detectar alvo ativo.
* [x] Utilizar template matching para elementos específicos.
* [x] Utilizar amostragem e densidade de pixels para barras e estados.

### ROIs atualmente mapeadas

```python
HP = {
    "top": 0,
    "left": 359,
    "width": 539,
    "height": 20,
}

MP = {
    "top": 1,
    "left": 1024,
    "width": 537,
    "height": 19,
}

STATUS_BAR = {
    "top": 1,
    "left": 915,
    "width": 110,
    "height": 18,
}

BATTLE_LIST = {
    "top": 390,
    "left": 1744,
    "width": 111,
    "height": 98,
}
```

Esses valores são temporários e dependem da resolução, da escala, do tamanho da janela e do layout da interface.

### AutoHealer

* [x] Usar magia de cura quando o HP estiver abaixo do limite.
* [x] Usar poção de mana quando a mana estiver abaixo do limite.
* [x] Usar poção de emergência quando o HP estiver crítico.
* [x] Aplicar cooldown para evitar spam de teclas.
* [x] Registrar ações importantes no log.
* [x] Remover thresholds fixos do código.
* [x] Carregar hotkeys, limites e cooldowns pela configuração.
* [ ] Adicionar histerese para evitar alternância rápida perto dos limites.
* [ ] Adicionar prioridade explícita entre os diferentes tipos de cura.

### AutoAttacker

* [x] Detectar possíveis alvos pela Battle List.
* [x] Identificar quando existe um alvo ativo.
* [x] Enviar a hotkey de ataque.
* [x] Evitar spam contínuo da hotkey.
* [ ] Representar o alvo dentro do estado central do jogo.
* [ ] Adicionar tempo mínimo entre trocas de alvo.
* [ ] Detectar perda de alvo.
* [ ] Diferenciar Battle List vazia, alvo selecionado e alvo derrotado.
* [ ] Impedir troca de alvo durante ações críticas.

### Logs e overlay

* [x] Centralizar logs.
* [x] Separar categorias de eventos.
* [x] Exportar informações para `logs_hud.txt`.
* [x] Criar overlay transparente.
* [x] Configurar overlay como click-through.
* [x] Aplicar delays variáveis pelo módulo de humanização.
* [ ] Exibir estado global atual do bot.
* [ ] Exibir FPS ou frequência de análise.
* [ ] Exibir idade do último frame válido.
* [ ] Exibir módulo que possui prioridade de execução.
* [ ] Exibir motivo da pausa automática.
* [ ] Exibir perfil de configuração carregado.

---

# Roadmap recomendado

## Fase 1 — Configuração externa

Antes de adicionar movimentação ou loot, remover do código todas as configurações específicas de personagem, resolução e interface.

### Estrutura sugerida

```text
config/
├── default.yaml
├── profiles/
│   ├── 1920x1080.yaml
│   └── character-example.yaml
└── schemas/
    └── config.schema.json
```

### Configurações de janela

* [x] Mover o título da janela do Tibia para a configuração.
* [x] Mover o título do Projetor do OBS para a configuração.
* [x] Permitir busca parcial por título.
* [x] Permitir selecionar entre múltiplas janelas encontradas.
* [x] Validar a configuração antes de iniciar o loop.

### Configurações do healer

* [x] Externalizar hotkey da magia de cura.
* [x] Externalizar percentual de HP da magia.
* [x] Externalizar cooldown da magia.
* [x] Externalizar hotkey da poção de mana.
* [x] Externalizar percentual mínimo de mana.
* [x] Externalizar hotkey da poção de emergência.
* [x] Externalizar percentual crítico de HP.
* [x] Permitir habilitar ou desabilitar cada recurso.

Exemplo:

```yaml
healer:
  enabled: true

  spell:
    enabled: true
    key: "1"
    hp_below: 90
    cooldown_ms: 1000

  mana_potion:
    enabled: true
    key: "2"
    mana_below: 50
    cooldown_ms: 1000

  emergency_potion:
    enabled: true
    key: "3"
    hp_below: 30
    cooldown_ms: 1000
```

### Configurações de combate

* [x] Externalizar a hotkey de ataque.
* [x] Externalizar o limite mínimo de pixels da Battle List.
* [x] Externalizar thresholds das cores utilizadas.
* [x] Externalizar cooldown para seleção de alvo.
* [x] Permitir ativar ou desativar o AutoAttacker.

### Critérios de conclusão

* [x] Nenhuma hotkey de gameplay permanece hardcoded.
* [x] Nenhum threshold de HP ou mana permanece hardcoded.
* [x] Nenhum caminho de template permanece hardcoded.
* [x] Erros de configuração apresentam mensagens claras.
* [x] Existe pelo menos um arquivo de configuração de exemplo.
* [x] O README explica como criar um perfil.

---

## Fase 2 — Sistema de ROIs escalável

As coordenadas absolutas devem ser substituídas por regiões configuráveis e proporcionais ao conteúdo capturado.

### Modelo de ROI

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class RelativeROI:
    x: float
    y: float
    width: float
    height: float
```

Exemplo de configuração:

```yaml
regions:
  hp:
    x: 0.187
    y: 0.000
    width: 0.281
    height: 0.018

  mana:
    x: 0.533
    y: 0.001
    width: 0.280
    height: 0.018
```

### Tarefas

* [x] Criar uma classe responsável por converter ROI relativa em pixels.
* [x] Calcular as coordenadas a partir da dimensão real do frame.
* [x] Impedir ROIs fora dos limites do frame.
* [x] Validar largura e altura mínimas.
* [x] Manter suporte temporário para ROIs absolutas.
* [x] Registrar no log as coordenadas calculadas.
* [x] Criar ferramenta visual para desenhar as ROIs sobre o frame.
* [x] Permitir salvar a calibração em um perfil.
* [x] Permitir recalibrar sem alterar o código.
* [x] Criar perfis diferentes para resoluções ou layouts distintos.

### Critérios de conclusão

* [x] O mesmo código funciona com mais de uma resolução.
* [x] Redimensionar o Projetor atualiza corretamente as regiões.
* [x] Uma ROI inválida pausa o bot de forma segura.
* [x] O overlay consegue desenhar todas as regiões configuradas.

---

## Fase 3 — Captura única por ciclo

Todos os módulos devem analisar o mesmo frame.

Não deve existir uma captura independente dentro do healer, combat, overlay ou qualquer outro módulo.

### Fluxo esperado

```python
frame = capturer.capture()
state = analyzer.analyze(frame)

decision = controller.decide(state)

executor.execute(decision)
overlay.update(state, decision)
```

### Tarefas

* [x] Criar uma abstração `FrameCapturer`.
* [x] Fazer uma única captura em cada iteração.
* [x] Adicionar timestamp ao frame.
* [x] Enviar o mesmo frame para todos os detectores.
* [x] Remover capturas duplicadas dentro dos módulos.
* [x] Medir o tempo gasto em cada etapa.
* [x] Definir uma frequência máxima para o loop.
* [x] Detectar frames repetidos ou congelados.
* [x] Pausar ações quando o frame estiver antigo.
* [x] Registrar falhas consecutivas de captura.
* [x] Tentar recuperar a captura sem reiniciar todo o processo.

### Estrutura sugerida

```text
src/
└── infrastructure/
    └── capture/
        ├── base.py
        ├── frame.py
        └── projector.py
```

### Objeto de frame

```python
from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass(frozen=True)
class CapturedFrame:
    image: np.ndarray
    captured_at: datetime
    width: int
    height: int
    source: str
```

### Critérios de conclusão

* [x] Cada ciclo realiza somente uma captura principal.
* [x] Todos os detectores recebem o mesmo frame.
* [x] O loop continua funcionando após uma falha temporária.
* [x] Nenhuma tecla é enviada a partir de um frame inválido.

---

## Fase 4 — Estado central do jogo

Criar um objeto imutável que represente tudo que foi percebido em um ciclo.

### Modelo inicial

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CaptureStatus(Enum):
    VALID = "valid"
    STALE = "stale"
    FAILED = "failed"


@dataclass(frozen=True)
class GameState:
    timestamp: datetime
    capture_status: CaptureStatus

    hp_percent: float | None
    mana_percent: float | None

    in_protection_zone: bool
    has_battle_targets: bool
    has_active_target: bool

    tibia_focused: bool
    tibia_minimized: bool
    projector_available: bool
```

### Tarefas

* [x] Criar `GameState`.
* [x] Criar `PlayerState`.
* [x] Criar `TargetState`.
* [x] Criar `WindowState`.
* [x] Criar `CaptureState`.
* [x] Fazer os detectores retornarem dados, sem enviar comandos.
* [x] Fazer o healer consumir somente o estado.
* [x] Fazer o combat consumir somente o estado.
* [x] Fazer o overlay consumir somente o estado.
* [x] Preservar o estado anterior para detectar transições.
* [x] Registrar mudanças importantes, em vez de repetir o mesmo log.
* [x] Adicionar nível de confiança às detecções.
* [x] Marcar valores desconhecidos como `None`, sem assumir valores seguros.

### Separação obrigatória

```text
Detectores:
frame → informação

Módulos:
informação → intenção

Executor:
intenção → input
```

### Critérios de conclusão

* [x] Detectores não pressionam teclas.
* [x] Detectores não movem o mouse.
* [x] Módulos não capturam a tela.
* [x] O executor não interpreta pixels.
* [x] Um estado pode ser salvo e reproduzido em testes.

---

## Fase 5 — Máquina de estados do bot

Evitar conflitos entre cura, combate, loot e movimento.

### Estados iniciais

```python
from enum import Enum


class BotMode(Enum):
    STOPPED = "stopped"
    PAUSED = "paused"
    UNSAFE = "unsafe"
    IDLE = "idle"
    IN_PROTECTION_ZONE = "in_protection_zone"
    COMBAT = "combat"
    LOOTING = "looting"
    MOVING = "moving"
```

### Prioridade recomendada

```text
1. Killswitch
2. Validação da captura
3. Validação de foco e janela
4. Cura de emergência
5. Cura normal
6. Mana
7. Regras de Protection Zone
8. Combate
9. Loot
10. Movimento
11. Ações ociosas
```

### Tarefas

* [x] Criar `BotMode`.
* [x] Criar controlador de transições.
* [x] Registrar cada mudança de estado.
* [x] Impedir estados incompatíveis simultaneamente.
* [x] Impedir movimento durante cura de emergência.
* [x] Impedir loot enquanto existir alvo ativo.
* [x] Impedir ações de combate em Protection Zone.
* [x] Pausar quando a captura estiver inválida.
* [x] Pausar quando a janela perder foco.
* [x] Retomar somente quando todas as condições forem válidas.
* [x] Definir tempo mínimo em estados sensíveis.
* [x] Adicionar timeout para estados que não progridem.

### Critérios de conclusão

* [x] Existe somente um modo principal ativo por ciclo.
* [x] Toda transição possui causa registrada.
* [x] As prioridades são testadas automaticamente.
* [x] Nenhum módulo ignora o estado global de segurança.

---

## Fase 6 — Motor principal e scheduler

Evitar que `main.py` concentre captura, análise, decisão, logs, input e controle de estado.

### Estrutura sugerida

```text
src/
├── application/
│   ├── bot_engine.py
│   ├── decision_controller.py
│   ├── scheduler.py
│   └── state_machine.py
├── domain/
│   ├── actions.py
│   ├── bot_state.py
│   ├── game_state.py
│   ├── player_state.py
│   └── target_state.py
├── modules/
│   ├── healer/
│   ├── combat/
│   ├── loot/
│   └── movement/
└── infrastructure/
    ├── capture/
    ├── input/
    ├── logging/
    ├── overlay/
    └── windows/
```

### Responsabilidade do `BotEngine`

```python
class BotEngine:
    def run_cycle(self) -> None:
        frame = self.capturer.capture()
        game_state = self.analyzer.analyze(frame)
        bot_state = self.state_machine.update(game_state)
        actions = self.controller.decide(game_state, bot_state)
        self.executor.execute(actions)
        self.overlay.update(game_state, bot_state, actions)
```

### Tarefas

* [x] Criar `BotEngine`.
* [x] Manter `main.py` somente como composition root.
* [x] Criar scheduler para controlar a frequência do loop.
* [x] Evitar `sleep()` espalhado pelos módulos.
* [x] Centralizar cooldowns.
* [x] Centralizar prioridades.
* [x] Permitir encerramento gracioso.
* [x] Restaurar recursos dentro de `finally`.
* [x] Garantir que uma exceção de módulo não deixe teclas pressionadas.
* [x] Adicionar métricas do ciclo.

### Critérios de conclusão

* [x] `main.py` apenas cria dependências e inicia o motor.
* [x] Módulos podem ser habilitados ou desabilitados.
* [x] O motor pode executar um único ciclo em testes.
* [x] O motor pode ser encerrado sem deixar recursos ativos.

---

## Fase 7 — Abstrações por sistema operacional

Separar regras do bot das APIs específicas de Windows ou Linux.

### Estrutura sugerida

```text
src/infrastructure/
├── capture/
│   ├── base.py
│   ├── windows_projector.py
│   └── x11_projector.py
├── input/
│   ├── base.py
│   ├── windows_input.py
│   └── linux_input.py
└── window/
    ├── base.py
    ├── windows_manager.py
    └── x11_manager.py
```

### Interfaces sugeridas

```python
from typing import Protocol


class WindowManager(Protocol):
    def find_tibia(self) -> object | None:
        ...

    def find_projector(self) -> object | None:
        ...

    def is_focused(self) -> bool:
        ...

    def is_minimized(self) -> bool:
        ...


class InputController(Protocol):
    def press_key(self, key: str) -> None:
        ...

    def click(self, x: int, y: int, button: str) -> None:
        ...
```

### Tarefas

* [x] Criar interfaces independentes de plataforma.
* [x] Isolar chamadas Win32.
* [x] Isolar chamadas X11/Xlib.
* [x] Isolar implementação de teclado e mouse.
* [x] Selecionar implementação pela plataforma.
* [x] Apresentar erro claro para plataforma não suportada.
* [x] Evitar condicionais de sistema operacional dentro do domínio.
* [x] Documentar diferenças de suporte entre plataformas.
* [x] Garantir que a captura continue sendo feita pelo Projetor do OBS.
* [x] Não utilizar câmera ou `/dev/video0`.
* [x] Não adicionar captura automática por câmera virtual do OBS.

### Critérios de conclusão

* [x] Healer e combat não importam APIs de sistema operacional.
* [x] O motor principal não conhece detalhes de Win32 ou Xlib.
* [x] A implementação de plataforma pode ser substituída por mocks.
* [x] A origem da captura aparece claramente nos logs.

---

## Fase 8 — Sistema central de ações

Os módulos não devem executar inputs diretamente. Eles devem propor intenções para um controlador central.

### Modelo sugerido

```python
from dataclasses import dataclass
from enum import Enum


class ActionType(Enum):
    EMERGENCY_HEAL = "emergency_heal"
    HEAL = "heal"
    USE_MANA = "use_mana"
    ATTACK = "attack"
    LOOT = "loot"
    MOVE = "move"


@dataclass(frozen=True)
class BotAction:
    action_type: ActionType
    priority: int
    key: str | None = None
    reason: str = ""
```

### Tarefas

* [x] Fazer cada módulo retornar zero ou mais intenções.
* [x] Criar resolvedor de conflitos.
* [x] Ordenar ações por prioridade.
* [x] Permitir somente ações compatíveis no mesmo ciclo.
* [x] Centralizar cooldowns por tipo de ação.
* [x] Registrar ações descartadas e o motivo.
* [x] Impedir repetição da mesma ação sem necessidade.
* [x] Fazer o executor validar o estado antes do input.
* [x] Cancelar a fila quando o killswitch for acionado.

### Critérios de conclusão

* [x] Nenhum módulo chama diretamente `pydirectinput`, `keyboard` ou equivalente.
* [x] Toda entrada passa pelo executor.
* [x] Toda ação executada possui uma justificativa.
* [x] A cura de emergência sempre vence ações menos importantes.

---

## Fase 9 — Testes com frames gravados

Os testes de visão computacional não devem depender sempre do Tibia e do OBS abertos.

### Estrutura sugerida

```text
tests/
├── fixtures/
│   ├── hp/
│   ├── mana/
│   ├── pz/
│   ├── battle_list/
│   └── target/
├── unit/
├── integration/
└── manual/
```

### Dataset de testes

Salvar frames ou recortes representando:

* HP cheio.
* HP intermediário.
* HP crítico.
* Mana cheia.
* Mana baixa.
* Dentro de PZ.
* Fora de PZ.
* Battle List vazia.
* Battle List com uma criatura.
* Battle List com várias criaturas.
* Criatura selecionada.
* Nenhum alvo selecionado.
* Projetor redimensionado.
* Interface parcialmente coberta.
* Frame preto.
* Frame congelado.
* Captura inválida.

### Tarefas

* [x] Separar testes automatizados de scripts manuais.
* [x] Criar fixtures versionadas.
* [x] Testar cálculo de HP.
* [x] Testar cálculo de mana.
* [x] Testar detecção de PZ.
* [x] Testar detecção de Battle List.
* [x] Testar detecção de alvo ativo.
* [x] Testar conversão de ROI relativa.
* [x] Testar prioridades de ação.
* [x] Testar máquina de estados.
* [x] Testar cooldowns com relógio falso.
* [x] Testar falhas de captura.
* [x] Testar perda de foco.
* [x] Testar comportamento em janela minimizada.
* [x] Testar encerramento gracioso.
* [x] Adicionar regressão para falsos positivos conhecidos.

### Critérios de conclusão

* [x] Os detectores podem ser testados sem abrir o jogo.
* [x] Os testes não enviam comandos reais.
* [x] Existe cobertura das transições críticas.
* [x] Alterações nos thresholds podem ser comparadas com fixtures.

---

## Fase 10 — Observabilidade e diagnóstico

### Tarefas

* [x] Adicionar tempo total de cada ciclo.
* [x] Adicionar tempo de captura.
* [x] Adicionar tempo de análise.
* [x] Adicionar tempo de decisão.
* [x] Adicionar contagem de falhas consecutivas.
* [x] Adicionar taxa de frames válidos.
* [x] Adicionar modo de diagnóstico sem inputs.
* [x] Adicionar opção para salvar frames problemáticos.
* [x] Adicionar rotação de arquivos de log.
* [x] Evitar logs repetidos em todos os ciclos.
* [x] Adicionar identificador da sessão.
* [x] Adicionar nível de log configurável.
* [x] Ocultar informações excessivas do HUD visual.
* [x] Manter detalhes completos no arquivo de log.

### Modo de observação

Adicionar um modo no qual o sistema:

* captura a tela;
* analisa o estado;
* atualiza logs;
* atualiza o overlay;
* não envia teclado;
* não envia mouse.

Exemplo:

```bash
python -m src.main --observe-only
```

### Critérios de conclusão

* [x] É possível diagnosticar detectores sem executar ações.
* [x] Frames inválidos podem ser identificados posteriormente.
* [x] O overlay informa claramente quando inputs estão desabilitados.

---

## Fase 11 — Auto-Loot

Esta fase deve começar somente após captura única, estado central, máquina de estados e testes estarem funcionais.

### Requisitos anteriores

* [x] Detectar transição de alvo ativo para alvo derrotado.
* [x] Saber se ainda existem criaturas na Battle List.
* [x] Utilizar Quick Loot Nearby Corpses (hotkey nativa).
* [x] Garantir que nenhuma cura crítica esteja pendente.
* [x] Garantir que o bot não esteja em estado inseguro.
* [x] Garantir que o loot não conflite com combate ou movimento.

### Tarefas

* [x] Utilizar Quick Loot Nearby Corpses por hotkey via executor central.
* [x] Detectar o momento correto para iniciar o loot (transição de alvo ativo para inativo).
* [x] Criar uma janela curta para coleta (`delay_ms`).
* [x] Criar intenção `ActionType.LOOT_NEARBY` processada pelo executor central.
* [x] Evitar envio duplicado da hotkey para o mesmo alvo.
* [x] Cancelar loot quando surgir um novo alvo.
* [x] Cancelar loot durante cura de emergência.
* [x] Registrar tentativa e solicitação do loot nos logs.
* [x] Adicionar cooldown entre tentativas (`cooldown_ms`).
* [x] Permitir desabilitar o recurso na configuração (`loot.enabled`).
* [x] Criar testes sem envio de comandos reais.

### Critérios de conclusão

* [x] Loot não interrompe cura.
* [x] Loot não ocorre com captura inválida.
* [x] Loot é cancelado ao detectar novo combate.
* [x] O módulo não controla o teclado/mouse diretamente (usa executor central).

---

## Fase 12 — Movimento

O movimento deve operar por intenções e estados, nunca diretamente no loop principal.

### Requisitos anteriores

* [ ] Máquina de estados implementada.
* [ ] Executor central implementado.
* [ ] Sistema de cooldown implementado.
* [ ] Modo de observação implementado.
* [ ] Testes com input simulado implementados.

### Tarefas

* [ ] Criar `MovementIntent`.
* [ ] Adicionar direções válidas.
* [ ] Definir tempo máximo de retenção.
* [ ] Evitar teclas pressionadas após exceções.
* [ ] Bloquear movimento durante cura crítica.
* [ ] Bloquear movimento quando pausado.
* [ ] Bloquear movimento sem foco.
* [ ] Bloquear movimento com frame inválido.
* [ ] Registrar origem e motivo do movimento.
* [ ] Adicionar timeout para movimento sem progresso.
* [ ] Implementar detecção visual de progresso antes de sequências maiores.
* [ ] Permitir cancelar imediatamente qualquer movimento.

### Critérios de conclusão

* [ ] Nenhum movimento ocorre automaticamente ao iniciar.
* [ ] O killswitch interrompe movimento imediatamente.
* [ ] O encerramento libera todas as teclas.
* [ ] O movimento só ocorre com estado visual recente.

---

## Fase 13 — Rotinas ociosas opcionais

Estas rotinas devem ser opcionais, conservadoras e ter prioridade inferior a todas as ações importantes.

### Tarefas

* [ ] Adicionar configuração para ativar ou desativar.
* [ ] Executar somente no estado `IDLE`.
* [ ] Não executar em combate.
* [ ] Não executar durante loot.
* [ ] Não executar durante cura.
* [ ] Não executar sem foco.
* [ ] Não executar com captura inválida.
* [ ] Cancelar imediatamente ao mudar de estado.
* [ ] Registrar a execução no log.

---

## Fase 14 — Refinamento da humanização

A humanização deve continuar centralizada e não pode corrigir problemas de arquitetura.

### Tarefas

* [ ] Centralizar todos os delays.
* [ ] Centralizar duração de retenção das teclas.
* [ ] Centralizar trajetórias de mouse.
* [ ] Definir limites mínimos e máximos.
* [ ] Evitar delays aleatórios que bloqueiem o motor principal.
* [ ] Usar scheduler em vez de longos `sleep()`.
* [ ] Permitir desligar humanização durante testes.
* [ ] Usar gerador aleatório determinístico nos testes.
* [ ] Registrar somente atrasos relevantes em modo debug.
* [ ] Garantir que delays não atrasem cura crítica.

---

## Fase 15 — Qualidade e automação

### Padronização

* [ ] Adicionar `pyproject.toml`.
* [ ] Configurar Ruff.
* [ ] Configurar formatter.
* [ ] Configurar type checker.
* [ ] Adicionar tipagem aos módulos principais.
* [ ] Adicionar docstrings somente em APIs relevantes.
* [ ] Remover código duplicado.
* [ ] Remover imports não utilizados.
* [ ] Padronizar nomes de eventos e logs.

### Testes e CI

* [ ] Adicionar Pytest.
* [ ] Executar testes unitários automaticamente.
* [ ] Executar verificação de sintaxe.
* [ ] Executar lint.
* [ ] Executar type checking.
* [ ] Criar workflow de CI.
* [ ] Não executar testes que enviem inputs reais no CI.
* [ ] Validar arquivos YAML ou JSON.
* [ ] Validar se todos os templates obrigatórios existem.

### Comandos sugeridos

```bash
python -m compileall src
pytest
ruff check .
ruff format --check .
```

---

# Ordem obrigatória de implementação

A ordem recomendada é:

1. Configuração externa.
2. ROIs relativas e calibráveis.
3. Captura única por ciclo.
4. Estado central do jogo.
5. Máquina de estados.
6. `BotEngine` e scheduler.
7. Abstrações por plataforma.
8. Sistema central de ações.
9. Testes com frames gravados.
10. Observabilidade e modo de diagnóstico.
11. Auto-Loot.
12. Movimento.
13. Rotinas ociosas opcionais.
14. Refinamento da humanização.
15. Qualidade e CI.

Não iniciar Auto-Loot ou movimento antes de concluir pelo menos as fases 1 a 9.

---

# Próxima tarefa recomendada

## Criar configuração externa e modelo central de ROI

### Etapa 1

Criar:

```text
config/
├── default.yaml
└── profiles/
    └── 1920x1080.yaml
```

### Etapa 2

Mover para a configuração:

* títulos das janelas;
* hotkeys;
* thresholds;
* cooldowns;
* caminhos dos templates;
* ROIs;
* recursos habilitados.

### Etapa 3

Criar:

```text
src/
├── config/
│   ├── loader.py
│   └── models.py
└── domain/
    └── roi.py
```

### Etapa 4

Adicionar validações:

* arquivo inexistente;
* campo obrigatório ausente;
* percentual fora de `0–100`;
* cooldown negativo;
* ROI fora de `0.0–1.0`;
* hotkey vazia;
* template inexistente.

### Definição de pronto

* [ ] O projeto inicia carregando `config/default.yaml`.
* [ ] O perfil pode sobrescrever os valores padrão.
* [ ] Healer e combat recebem configurações pelo construtor.
* [ ] Nenhuma ROI fica declarada dentro de `main.py`.
* [ ] Nenhum threshold de gameplay fica declarado dentro dos módulos.
* [ ] Configuração inválida impede a inicialização com mensagem clara.
* [ ] O modo de inicialização não envia qualquer comando ao jogo.

---

# Regras permanentes

* Não utilizar leitura ou escrita de memória do processo.
* Não utilizar DLL injection.
* Não utilizar câmera.
* Não utilizar `/dev/video0`.
* Não utilizar câmera virtual do OBS.
* Utilizar a janela do Projetor do OBS como fonte visual.
* Não adicionar movimentos hardcoded na inicialização.
* Não pressionar teclas automaticamente ao executar `run.sh`, `launcher.py` ou `main.py`.
* Não permitir que módulos de percepção enviem inputs.
* Não permitir que módulos de domínio dependam de Win32, Xlib, OpenCV ou bibliotecas de input.
* Não executar ações com frame inválido ou desatualizado.
* Não ignorar o killswitch.
* Não deixar teclas pressionadas após erro ou encerramento.
* Atualizar `README.md`, `NEXT_STEPS.md` e `AGENTS.md` quando decisões arquiteturais forem alteradas.
