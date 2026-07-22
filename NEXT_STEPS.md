# Próximos Passos — Tibia Bot

Este documento registra o estado atual, as decisões arquiteturais e a ordem recomendada para evolução do projeto.

O objetivo é evoluir o projeto de um conjunto de módulos que observam a tela e enviam comandos para um fluxo centralizado:

```text
Captura → Percepção → Estado → Decisão → Execução
```

---

## Estado atual do projeto

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
* [ ] Criar um estado global de segurança.
* [ ] Bloquear todas as ações quando o estado da captura for inválido.
* [ ] Bloquear ações quando uma ROI obrigatória não puder ser analisada.
* [ ] Garantir que nenhuma ação automática seja executada na inicialização.

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
* [ ] Remover thresholds fixos do código.
* [ ] Carregar hotkeys, limites e cooldowns pela configuração.
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

* [ ] Mover o título da janela do Tibia para a configuração.
* [ ] Mover o título do Projetor do OBS para a configuração.
* [ ] Permitir busca parcial por título.
* [ ] Permitir selecionar entre múltiplas janelas encontradas.
* [ ] Validar a configuração antes de iniciar o loop.

### Configurações do healer

* [ ] Externalizar hotkey da magia de cura.
* [ ] Externalizar percentual de HP da magia.
* [ ] Externalizar cooldown da magia.
* [ ] Externalizar hotkey da poção de mana.
* [ ] Externalizar percentual mínimo de mana.
* [ ] Externalizar hotkey da poção de emergência.
* [ ] Externalizar percentual crítico de HP.
* [ ] Permitir habilitar ou desabilitar cada recurso.

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

* [ ] Externalizar a hotkey de ataque.
* [ ] Externalizar o limite mínimo de pixels da Battle List.
* [ ] Externalizar thresholds das cores utilizadas.
* [ ] Externalizar cooldown para seleção de alvo.
* [ ] Permitir ativar ou desativar o AutoAttacker.

### Critérios de conclusão

* [ ] Nenhuma hotkey de gameplay permanece hardcoded.
* [ ] Nenhum threshold de HP ou mana permanece hardcoded.
* [ ] Nenhum caminho de template permanece hardcoded.
* [ ] Erros de configuração apresentam mensagens claras.
* [ ] Existe pelo menos um arquivo de configuração de exemplo.
* [ ] O README explica como criar um perfil.

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

* [ ] Criar uma classe responsável por converter ROI relativa em pixels.
* [ ] Calcular as coordenadas a partir da dimensão real do frame.
* [ ] Impedir ROIs fora dos limites do frame.
* [ ] Validar largura e altura mínimas.
* [ ] Manter suporte temporário para ROIs absolutas.
* [ ] Registrar no log as coordenadas calculadas.
* [ ] Criar ferramenta visual para desenhar as ROIs sobre o frame.
* [ ] Permitir salvar a calibração em um perfil.
* [ ] Permitir recalibrar sem alterar o código.
* [ ] Criar perfis diferentes para resoluções ou layouts distintos.

### Critérios de conclusão

* [ ] O mesmo código funciona com mais de uma resolução.
* [ ] Redimensionar o Projetor atualiza corretamente as regiões.
* [ ] Uma ROI inválida pausa o bot de forma segura.
* [ ] O overlay consegue desenhar todas as regiões configuradas.

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

* [ ] Criar uma abstração `FrameCapturer`.
* [ ] Fazer uma única captura em cada iteração.
* [ ] Adicionar timestamp ao frame.
* [ ] Enviar o mesmo frame para todos os detectores.
* [ ] Remover capturas duplicadas dentro dos módulos.
* [ ] Medir o tempo gasto em cada etapa.
* [ ] Definir uma frequência máxima para o loop.
* [ ] Detectar frames repetidos ou congelados.
* [ ] Pausar ações quando o frame estiver antigo.
* [ ] Registrar falhas consecutivas de captura.
* [ ] Tentar recuperar a captura sem reiniciar todo o processo.

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

* [ ] Cada ciclo realiza somente uma captura principal.
* [ ] Todos os detectores recebem o mesmo frame.
* [ ] O loop continua funcionando após uma falha temporária.
* [ ] Nenhuma tecla é enviada a partir de um frame inválido.

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

* [ ] Criar `GameState`.
* [ ] Criar `PlayerState`.
* [ ] Criar `TargetState`.
* [ ] Criar `WindowState`.
* [ ] Criar `CaptureState`.
* [ ] Fazer os detectores retornarem dados, sem enviar comandos.
* [ ] Fazer o healer consumir somente o estado.
* [ ] Fazer o combat consumir somente o estado.
* [ ] Fazer o overlay consumir somente o estado.
* [ ] Preservar o estado anterior para detectar transições.
* [ ] Registrar mudanças importantes, em vez de repetir o mesmo log.
* [ ] Adicionar nível de confiança às detecções.
* [ ] Marcar valores desconhecidos como `None`, sem assumir valores seguros.

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

* [ ] Detectores não pressionam teclas.
* [ ] Detectores não movem o mouse.
* [ ] Módulos não capturam a tela.
* [ ] O executor não interpreta pixels.
* [ ] Um estado pode ser salvo e reproduzido em testes.

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

* [ ] Criar `BotMode`.
* [ ] Criar controlador de transições.
* [ ] Registrar cada mudança de estado.
* [ ] Impedir estados incompatíveis simultaneamente.
* [ ] Impedir movimento durante cura de emergência.
* [ ] Impedir loot enquanto existir alvo ativo.
* [ ] Impedir ações de combate em Protection Zone.
* [ ] Pausar quando a captura estiver inválida.
* [ ] Pausar quando a janela perder foco.
* [ ] Retomar somente quando todas as condições forem válidas.
* [ ] Definir tempo mínimo em estados sensíveis.
* [ ] Adicionar timeout para estados que não progridem.

### Critérios de conclusão

* [ ] Existe somente um modo principal ativo por ciclo.
* [ ] Toda transição possui causa registrada.
* [ ] As prioridades são testadas automaticamente.
* [ ] Nenhum módulo ignora o estado global de segurança.

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

* [ ] Criar `BotEngine`.
* [ ] Manter `main.py` somente como composition root.
* [ ] Criar scheduler para controlar a frequência do loop.
* [ ] Evitar `sleep()` espalhado pelos módulos.
* [ ] Centralizar cooldowns.
* [ ] Centralizar prioridades.
* [ ] Permitir encerramento gracioso.
* [ ] Restaurar recursos dentro de `finally`.
* [ ] Garantir que uma exceção de módulo não deixe teclas pressionadas.
* [ ] Adicionar métricas do ciclo.

### Critérios de conclusão

* [ ] `main.py` apenas cria dependências e inicia o motor.
* [ ] Módulos podem ser habilitados ou desabilitados.
* [ ] O motor pode executar um único ciclo em testes.
* [ ] O motor pode ser encerrado sem deixar recursos ativos.

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

* [ ] Criar interfaces independentes de plataforma.
* [ ] Isolar chamadas Win32.
* [ ] Isolar chamadas X11/Xlib.
* [ ] Isolar implementação de teclado e mouse.
* [ ] Selecionar implementação pela plataforma.
* [ ] Apresentar erro claro para plataforma não suportada.
* [ ] Evitar condicionais de sistema operacional dentro do domínio.
* [ ] Documentar diferenças de suporte entre plataformas.
* [ ] Garantir que a captura continue sendo feita pelo Projetor do OBS.
* [ ] Não utilizar câmera ou `/dev/video0`.
* [ ] Não adicionar captura automática por câmera virtual do OBS.

### Critérios de conclusão

* [ ] Healer e combat não importam APIs de sistema operacional.
* [ ] O motor principal não conhece detalhes de Win32 ou Xlib.
* [ ] A implementação de plataforma pode ser substituída por mocks.
* [ ] A origem da captura aparece claramente nos logs.

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

* [ ] Fazer cada módulo retornar zero ou mais intenções.
* [ ] Criar resolvedor de conflitos.
* [ ] Ordenar ações por prioridade.
* [ ] Permitir somente ações compatíveis no mesmo ciclo.
* [ ] Centralizar cooldowns por tipo de ação.
* [ ] Registrar ações descartadas e o motivo.
* [ ] Impedir repetição da mesma ação sem necessidade.
* [ ] Fazer o executor validar o estado antes do input.
* [ ] Cancelar a fila quando o killswitch for acionado.

### Critérios de conclusão

* [ ] Nenhum módulo chama diretamente `pydirectinput`, `keyboard` ou equivalente.
* [ ] Toda entrada passa pelo executor.
* [ ] Toda ação executada possui uma justificativa.
* [ ] A cura de emergência sempre vence ações menos importantes.

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

* [ ] Separar testes automatizados de scripts manuais.
* [ ] Criar fixtures versionadas.
* [ ] Testar cálculo de HP.
* [ ] Testar cálculo de mana.
* [ ] Testar detecção de PZ.
* [ ] Testar detecção de Battle List.
* [ ] Testar detecção de alvo ativo.
* [ ] Testar conversão de ROI relativa.
* [ ] Testar prioridades de ação.
* [ ] Testar máquina de estados.
* [ ] Testar cooldowns com relógio falso.
* [ ] Testar falhas de captura.
* [ ] Testar perda de foco.
* [ ] Testar comportamento em janela minimizada.
* [ ] Testar encerramento gracioso.
* [ ] Adicionar regressão para falsos positivos conhecidos.

### Critérios de conclusão

* [ ] Os detectores podem ser testados sem abrir o jogo.
* [ ] Os testes não enviam comandos reais.
* [ ] Existe cobertura das transições críticas.
* [ ] Alterações nos thresholds podem ser comparadas com fixtures.

---

## Fase 10 — Observabilidade e diagnóstico

### Tarefas

* [ ] Adicionar tempo total de cada ciclo.
* [ ] Adicionar tempo de captura.
* [ ] Adicionar tempo de análise.
* [ ] Adicionar tempo de decisão.
* [ ] Adicionar contagem de falhas consecutivas.
* [ ] Adicionar taxa de frames válidos.
* [ ] Adicionar modo de diagnóstico sem inputs.
* [ ] Adicionar opção para salvar frames problemáticos.
* [ ] Adicionar rotação de arquivos de log.
* [ ] Evitar logs repetidos em todos os ciclos.
* [ ] Adicionar identificador da sessão.
* [ ] Adicionar nível de log configurável.
* [ ] Ocultar informações excessivas do HUD visual.
* [ ] Manter detalhes completos no arquivo de log.

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

* [ ] É possível diagnosticar detectores sem executar ações.
* [ ] Frames inválidos podem ser identificados posteriormente.
* [ ] O overlay informa claramente quando inputs estão desabilitados.

---

## Fase 11 — Auto-Loot

Esta fase deve começar somente após captura única, estado central, máquina de estados e testes estarem funcionais.

### Requisitos anteriores

* [ ] Detectar transição de alvo ativo para alvo derrotado.
* [ ] Saber se ainda existem criaturas na Battle List.
* [ ] Conhecer a posição relativa do personagem.
* [ ] Garantir que nenhuma cura crítica esteja pendente.
* [ ] Garantir que o bot não esteja em estado inseguro.
* [ ] Garantir que o loot não conflite com combate ou movimento.

### Tarefas

* [ ] Mapear a área central do jogo.
* [ ] Definir posições relativas dos possíveis corpos.
* [ ] Detectar o momento correto para iniciar o loot.
* [ ] Criar uma janela curta para coleta.
* [ ] Criar ação de clique pelo executor central.
* [ ] Evitar clicar repetidamente no mesmo ponto.
* [ ] Cancelar loot quando surgir um novo alvo.
* [ ] Cancelar loot durante cura de emergência.
* [ ] Registrar tentativa e conclusão do loot.
* [ ] Adicionar cooldown entre tentativas.
* [ ] Permitir desabilitar o recurso na configuração.
* [ ] Criar testes sem movimento real do mouse.

### Critérios de conclusão

* [ ] Loot não interrompe cura.
* [ ] Loot não ocorre com captura inválida.
* [ ] Loot é cancelado ao detectar novo combate.
* [ ] O módulo não controla o mouse diretamente.

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
