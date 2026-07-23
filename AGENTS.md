# AGENTS.md — Diretrizes e Memória do Projeto

Este arquivo é o guia definitivo para agentes de IA que trabalham no projeto `tibiabotwin`.

Ele registra:

* regras que nunca devem ser violadas;
* decisões arquiteturais;
* responsabilidades dos módulos;
* ordem de implementação;
* requisitos de segurança;
* comandos obrigatórios de validação;
* estado esperado da documentação.

As instruções deste arquivo têm prioridade sobre sugestões genéricas de arquitetura ou implementação.

---

# 1. Objetivo do projeto

O projeto é uma aplicação de estudo sobre:

* visão computacional;
* captura de janelas;
* análise de interfaces gráficas;
* máquinas de estado;
* automação de teclado e mouse;
* arquitetura modular em Python;
* integração com o Projetor em Janela do OBS Studio.

O fluxo arquitetural desejado é:

```text
Captura → Percepção → Estado → Decisão → Execução
```

Cada etapa deve possuir responsabilidade claramente separada.

```text
Captura
    ↓
CapturedFrame
    ↓
Detectores
    ↓
GameState
    ↓
Máquina de estados
    ↓
BotAction
    ↓
Executor de input
```

---

# 2. Regras críticas

## 2.1. Nunca utilizar câmera

É proibido:

* acessar `/dev/video0`;
* usar `cv2.VideoCapture(0)`;
* usar webcam;
* usar câmera virtual do OBS;
* tratar uma câmera virtual como fonte primária;
* adicionar fallback silencioso para câmera;
* solicitar permissão para câmera;
* instalar dependências cujo único propósito seja capturar uma câmera.

A fonte visual deve ser a janela do Projetor do OBS Studio.

No Linux/X11, a implementação esperada é uma captura direta da janela por meio de Xlib ou mecanismo equivalente de captura de janela.

No Windows, uma implementação específica pode existir, desde que continue capturando o Projetor do OBS e permaneça isolada atrás de uma abstração de plataforma.

---

## 2.2. Nunca ler ou modificar a memória do jogo

É proibido implementar:

* `ReadProcessMemory`;
* `WriteProcessMemory`;
* DLL injection;
* hooks dentro do processo do jogo;
* leitura de ponteiros;
* leitura de estruturas internas do cliente;
* abertura de handles para inspecionar a memória do processo;
* integração com Cheat Engine;
* alteração de pacotes de rede;
* interceptação do protocolo do jogo;
* leitura de dados internos não presentes visualmente na tela.

Todo estado deve ser inferido a partir de informações visíveis na imagem capturada.

Exemplos:

* vida pela barra de HP;
* mana pela barra de MP;
* Protection Zone pelo ícone visual;
* alvo ativo pela moldura ou indicador visual;
* criaturas pela Battle List;
* progresso por mudanças observadas entre frames.

---

## 2.3. Nunca executar movimentos na inicialização

É proibido adicionar qualquer ação automática ao iniciar:

* `W`, `A`, `S` ou `D`;
* setas direcionais;
* clique do mouse;
* seleção de alvo;
* uso de magia;
* uso de poção;
* ataque;
* rotação do personagem;
* rotina anti-AFK;
* teste automático de teclado ou mouse.

Os seguintes comandos devem iniciar a aplicação sem enviar inputs:

```bash
./run.sh
python launcher.py
python -m src.main
```

O programa deve:

1. carregar a configuração;
2. localizar as janelas;
3. inicializar os componentes;
4. iniciar o monitoramento;
5. aguardar condições válidas;
6. permanecer sem executar ações não solicitadas durante a inicialização.

Testes de teclado e mouse devem existir somente em scripts manuais claramente identificados.

---

## 2.4. Nunca executar inputs com estado inválido

Nenhum input pode ser enviado quando ocorrer qualquer uma destas condições:

* bot pausado;
* killswitch acionado;
* Projetor do OBS não encontrado;
* janela do Tibia não encontrada;
* frame inválido;
* frame antigo;
* captura congelada;
* ROI obrigatória inválida;
* foco incorreto;
* janela minimizada;
* estado visual desconhecido;
* aplicação em processo de encerramento;
* executor em estado de erro.

Na dúvida, a aplicação deve falhar de forma segura e não enviar comandos.

```text
Estado desconhecido ≠ estado seguro
```

Valores que não puderem ser determinados devem ser representados por `None`, `UNKNOWN` ou um tipo equivalente.

Nunca assumir:

```python
hp_percent = 100
mana_percent = 100
in_protection_zone = False
```

apenas porque uma detecção falhou.

---

## 2.5. O killswitch tem prioridade absoluta

A tecla configurada como killswitch deve:

* interromper novas ações imediatamente;
* limpar ações pendentes;
* cancelar movimentos agendados;
* impedir novos inputs;
* liberar teclas que estejam pressionadas;
* atualizar o estado global;
* registrar a mudança no log;
* atualizar o overlay.

Nenhum módulo pode ignorar ou sobrescrever o killswitch.

---

## 2.6. Desenvolver sempre em novas branches

Todo novo desenvolvimento, refatoração, correção ou implementação de fase/feature deve:

* ser iniciado a partir de uma branch Git dedicada (ex: `feature/auto-loot`, `feature/movement`, `fix/bug-name`);
* nunca ser realizado diretamente na branch `main`;
* passar por testes automatizados e validação de sintaxe antes do merge ou conclusão da tarefa.

---

# 3. Princípios arquiteturais obrigatórios

## 3.1. Separação entre percepção e execução

Detectores devem apenas interpretar imagens.

Eles podem retornar:

* percentuais;
* flags;
* coordenadas;
* contagem de elementos;
* nível de confiança;
* informações de diagnóstico.

Detectores não podem:

* pressionar teclas;
* mover o mouse;
* clicar;
* alterar cooldowns de gameplay;
* selecionar prioridades;
* alterar diretamente o modo do bot.

Exemplo correto:

```python
hp_result = hp_detector.detect(frame)
```

Exemplo incorreto:

```python
if hp_percent < 30:
    input_controller.press("3")
```

dentro do detector.

---

## 3.2. Captura única por ciclo

Cada ciclo principal deve produzir um único frame compartilhado entre os detectores.

Fluxo esperado:

```python
frame = capturer.capture()
game_state = analyzer.analyze(frame)
bot_state = state_machine.update(game_state)
actions = decision_controller.decide(game_state, bot_state)
executor.execute(actions)
```

É proibido que os módulos abaixo capturem a tela independentemente:

* healer;
* combat;
* loot;
* movement;
* overlay;
* state machine;
* action resolver.

Isso evita:

* análises de instantes diferentes;
* consumo desnecessário de CPU;
* frames inconsistentes;
* duplicação de infraestrutura;
* dificuldade de reproduzir testes.

---

## 3.3. Estado central e imutável

A percepção de cada ciclo deve ser representada por um estado central.

Modelo conceitual:

```python
@dataclass(frozen=True)
class GameState:
    timestamp: datetime
    capture_status: CaptureStatus
    hp_percent: float | None
    mana_percent: float | None
    in_protection_zone: bool | None
    has_battle_targets: bool | None
    has_active_target: bool | None
    tibia_focused: bool
    tibia_minimized: bool
    projector_available: bool
```

O estado deve:

* possuir timestamp;
* registrar validade da captura;
* diferenciar `False` de desconhecido;
* poder ser salvo em logs;
* poder ser criado em testes;
* não depender de APIs de input;
* não depender de Win32 ou Xlib;
* ser imutável sempre que possível.

---

## 3.4. Máquina de estados explícita

O bot deve possuir somente um modo principal ativo por ciclo.

Estados iniciais sugeridos:

```python
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

Prioridade esperada:

```text
1. Killswitch
2. Encerramento
3. Validade da captura
4. Validade das janelas
5. Foco e minimização
6. Cura de emergência
7. Cura normal
8. Recuperação de mana
9. Regras de Protection Zone
10. Combate
11. Loot
12. Movimento
13. Ações ociosas
```

As transições devem registrar:

* estado anterior;
* novo estado;
* motivo;
* timestamp.

É proibido permitir que cada módulo mantenha um “estado global” independente e conflitante.

---

## 3.5. Sistema central de ações

Módulos de decisão devem retornar intenções, não executar inputs.

Exemplo:

```python
@dataclass(frozen=True)
class BotAction:
    action_type: ActionType
    priority: int
    reason: str
    key: str | None = None
```

O resolvedor central deve:

* ordenar ações;
* eliminar conflitos;
* aplicar cooldowns;
* verificar o estado de segurança;
* registrar ações descartadas;
* permitir cancelamento imediato;
* selecionar no máximo as ações compatíveis no ciclo.

Toda ação executada precisa possuir uma justificativa rastreável.

Exemplo:

```text
EMERGENCY_HEAL
reason="HP detectado em 27%, abaixo do limite de 30%"
```

---

## 3.6. `main.py` deve ser apenas o ponto de composição

O arquivo `main.py` não deve concentrar:

* captura;
* análise de pixels;
* regras de cura;
* regras de combate;
* manipulação de overlay;
* lógica de plataforma;
* cooldowns;
* humanização;
* execução de teclado e mouse.

Responsabilidades aceitáveis para `main.py`:

* carregar configuração;
* construir dependências;
* selecionar implementação da plataforma;
* criar o `BotEngine`;
* iniciar o loop;
* tratar encerramento de alto nível.

Exemplo:

```python
def main() -> None:
    config = load_config()
    dependencies = build_dependencies(config)
    engine = BotEngine(**dependencies)
    engine.run()
```

---

# 4. Configuração

## 4.1. Não adicionar configurações de gameplay hardcoded

Devem ficar fora do código:

* títulos de janelas;
* hotkeys;
* limites de HP;
* limites de mana;
* cooldowns;
* ROIs;
* caminhos de templates;
* thresholds de cor;
* thresholds de template matching;
* intervalos;
* módulos habilitados;
* frequência do loop.

Estrutura recomendada:

```text
config/
├── default.yaml
├── profiles/
│   ├── 1920x1080.yaml
│   └── character-example.yaml
└── schemas/
    └── config.schema.json
```

Um perfil deve poder sobrescrever valores do arquivo padrão.

---

## 4.2. Validar configuração antes de iniciar

A inicialização deve falhar com uma mensagem clara quando existir:

* arquivo ausente;
* YAML ou JSON inválido;
* campo obrigatório ausente;
* ROI fora dos limites;
* percentual fora de `0–100`;
* cooldown negativo;
* hotkey vazia;
* template inexistente;
* plataforma não suportada;
* combinação de configurações incompatível.

Não usar valores silenciosos que escondam erros importantes.

---

## 4.3. ROIs relativas

Novas ROIs devem preferencialmente utilizar valores relativos:

```yaml
regions:
  hp:
    x: 0.187
    y: 0.000
    width: 0.281
    height: 0.018
```

Valores válidos devem permanecer entre `0.0` e `1.0`.

A conversão para pixels deve ocorrer com base no tamanho real do frame.

ROIs absolutas podem continuar temporariamente por compatibilidade, mas não devem ser a arquitetura definitiva.

---

# 5. Abstrações por plataforma

O domínio não deve depender diretamente de Windows ou Linux.

Interfaces devem isolar:

* captura;
* descoberta de janelas;
* foco;
* minimização;
* opacidade;
* teclado;
* mouse;
* overlay.

Estrutura recomendada:

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

## Regras

* Não espalhar `if platform.system()` pelo domínio.
* Não importar Win32 dentro de healer, combat ou movement.
* Não importar Xlib dentro de healer, combat ou movement.
* Selecionar a implementação durante a composição da aplicação.
* Permitir substituir implementações por mocks nos testes.
* Apresentar erro claro quando a plataforma não possuir implementação.

A direção prioritária atual é suportar Linux/X11 por captura nativa da janela do Projetor do OBS.

Implementações existentes para Windows não devem ser removidas sem necessidade, mas devem ser gradualmente isoladas atrás das interfaces.

---

# 6. Humanização e scheduler

Todos os delays e tempos de retenção devem permanecer centralizados.

Nenhum módulo deve possuir chamadas longas e bloqueantes de:

```python
time.sleep(...)
```

Ações futuras devem ser programadas por scheduler sempre que possível.

A humanização deve:

* poder ser desabilitada nos testes;
* usar semente determinística nos testes;
* respeitar limites configurados;
* nunca atrasar cura de emergência;
* nunca bloquear o killswitch;
* nunca impedir encerramento imediato;
* nunca substituir regras de segurança.

A humanização não deve ser usada para esconder uma arquitetura incorreta.

---

# 7. Segurança de input

Todo input deve passar por um único executor central.

O executor deve:

1. verificar o killswitch;
2. verificar o estado global;
3. verificar foco e minimização;
4. verificar validade e idade do frame;
5. verificar cooldown;
6. executar a ação;
7. registrar o resultado.

Em caso de exceção:

* liberar todas as teclas;
* cancelar ações pendentes;
* marcar o estado como inseguro;
* registrar o erro;
* impedir continuação silenciosa.

O encerramento da aplicação deve sempre usar `try/finally` ou mecanismo equivalente para restaurar recursos.

---

# 8. Modo de observação

Deve existir um modo sem inputs reais:

```bash
python -m src.main --observe-only
```

Nesse modo, o sistema pode:

* capturar;
* analisar;
* criar `GameState`;
* atualizar a máquina de estados;
* produzir ações simuladas;
* atualizar logs;
* atualizar overlay;
* salvar frames de diagnóstico.

Nesse modo, o sistema não pode:

* pressionar teclas;
* mover o mouse;
* clicar;
* alterar a janela do jogo de maneira irreversível.

Toda nova funcionalidade deve ser testável primeiro no modo de observação.

---

# 9. Logging e observabilidade

Logs devem registrar eventos e transições, evitando repetir a mesma mensagem em todos os frames.

Informações recomendadas:

* início da sessão;
* perfil carregado;
* plataforma selecionada;
* fonte de captura;
* dimensões do frame;
* falhas de captura;
* frame congelado;
* perda de foco;
* pausa automática;
* ativação do killswitch;
* transições da máquina de estados;
* ações propostas;
* ações executadas;
* ações descartadas;
* exceções;
* encerramento.

Não registrar credenciais, tokens ou dados sensíveis.

O overlay deve mostrar informações resumidas. Os detalhes completos devem permanecer nos logs.

---

# 10. Testes

## 10.1. Testes não podem enviar inputs reais por padrão

Testes automatizados devem usar:

* capturador falso;
* relógio falso;
* executor falso;
* gerenciador de janelas falso;
* frames gravados;
* estados construídos manualmente.

Scripts que enviam inputs reais devem:

* ficar em `tests/manual/`;
* possuir nome explícito;
* exigir execução manual;
* não ser executados pelo Pytest padrão;
* exibir aviso antes de iniciar.

---

## 10.2. Testes de visão computacional

Detectores devem ser validados com imagens versionadas em fixtures.

Estrutura recomendada:

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

Cobertura mínima esperada:

* HP cheio;
* HP intermediário;
* HP crítico;
* mana cheia;
* mana baixa;
* PZ ativa;
* PZ inativa;
* Battle List vazia;
* Battle List preenchida;
* alvo ativo;
* alvo ausente;
* frame preto;
* frame inválido;
* frame congelado;
* ROI fora do frame;
* perda de foco;
* janela minimizada;
* killswitch;
* prioridade da cura;
* conflito entre ações;
* encerramento com tecla pressionada.

---

## 10.3. Testar transições, não somente valores isolados

Sempre que uma funcionalidade depender do tempo, testar sequências como:

```text
sem alvo → alvo detectado → alvo ativo → alvo perdido
```

```text
HP normal → HP baixo → cura solicitada → cooldown → HP recuperado
```

```text
captura válida → frame congelado → UNSAFE → captura recuperada
```

---

# 11. Ordem de implementação

Agentes devem seguir a ordem registrada em `NEXT_STEPS.md`.

Prioridade atual:

1. configuração externa;
2. ROIs relativas e calibráveis;
3. captura única por ciclo;
4. estado central;
5. máquina de estados;
6. `BotEngine` e scheduler;
7. abstrações por plataforma;
8. sistema central de ações;
9. testes com frames gravados;
10. observabilidade;
11. Auto-Loot;
12. movimento;
13. rotinas ociosas;
14. refinamento da humanização;
15. qualidade e CI.

Não antecipar Auto-Loot, movement ou rotinas ociosas enquanto as fundações anteriores não estiverem concluídas.

Quando o usuário solicitar explicitamente uma tarefa fora dessa ordem, o agente deve:

1. informar as dependências relevantes;
2. implementar da maneira mais isolada possível;
3. não quebrar as regras críticas;
4. registrar a dívida ou dependência em `NEXT_STEPS.md`.

---

# 12. Estrutura-alvo do projeto

A migração deve ocorrer gradualmente.

```text
tibiabotwin/
├── config/
│   ├── default.yaml
│   ├── profiles/
│   └── schemas/
├── src/
│   ├── application/
│   │   ├── bot_engine.py
│   │   ├── decision_controller.py
│   │   ├── scheduler.py
│   │   └── state_machine.py
│   ├── config/
│   │   ├── loader.py
│   │   └── models.py
│   ├── domain/
│   │   ├── actions.py
│   │   ├── bot_state.py
│   │   ├── game_state.py
│   │   ├── player_state.py
│   │   ├── roi.py
│   │   └── target_state.py
│   ├── modules/
│   │   ├── healer/
│   │   ├── combat/
│   │   ├── loot/
│   │   └── movement/
│   └── infrastructure/
│       ├── capture/
│       ├── input/
│       ├── logging/
│       ├── overlay/
│       └── window/
├── templates/
├── tests/
│   ├── fixtures/
│   ├── unit/
│   ├── integration/
│   └── manual/
├── launcher.py
├── run.sh
├── pyproject.toml
├── README.md
├── NEXT_STEPS.md
└── AGENTS.md
```

Não é necessário mover todos os arquivos em uma única alteração.

Evitar refatorações massivas sem testes. Preferir migrações pequenas e verificáveis.

---

# 13. Padrões de código

## Python

* Utilizar type hints nas APIs principais.
* Preferir `dataclass` para estados e configurações.
* Preferir objetos imutáveis para snapshots.
* Utilizar `pathlib.Path` para caminhos.
* Utilizar `Enum` para estados fechados.
* Evitar variáveis globais mutáveis.
* Evitar singletons para estado de gameplay.
* Evitar `except Exception: pass`.
* Registrar exceções relevantes.
* Manter funções pequenas e com uma responsabilidade.
* Não adicionar abstrações sem uso concreto.
* Não duplicar thresholds ou cooldowns.
* Não misturar código de domínio com infraestrutura.

## Imports

Preferir dependência nesta direção:

```text
domain
    ↑
application
    ↑
modules
    ↑
infrastructure/composition
```

O domínio não deve importar infraestrutura.

## Encoding

Arquivos de texto devem usar UTF-8.

Quando necessário no Windows, configurar `stdout` e `stderr` para UTF-8 sem prejudicar Linux ou testes.

Logs de console devem preferir marcadores compatíveis:

```text
[OK]
[X]
[!]
[*]
[DEBUG]
```

Não depender de emojis para comunicar erros críticos.

---

# 14. Dependências

Antes de adicionar uma biblioteca:

1. verificar se a funcionalidade já existe no projeto;
2. avaliar se a biblioteca funciona na plataforma alvo;
3. evitar dependência exclusiva de Windows no domínio;
4. evitar dependências abandonadas;
5. justificar a necessidade;
6. atualizar o arquivo de dependências;
7. atualizar instruções de instalação;
8. adicionar tratamento para ausência da dependência quando aplicável.

Não instalar uma biblioteca apenas para substituir poucas linhas simples da biblioteca padrão.

---

# 15. Compatibilidade

A compatibilidade atual pode estar incompleta.

Ao alterar componentes específicos de plataforma:

* preservar comportamento existente quando possível;
* não prometer suporte sem teste;
* documentar recursos não suportados;
* separar claramente Windows, Linux/X11 e outros ambientes;
* não implementar fallback para câmera;
* não mascarar erro de captura usando screenshot da área de trabalho inteira sem informar.

O projeto deve conseguir identificar e registrar:

```text
platform=linux
display_server=x11
capture_backend=xlib_projector
```

ou equivalente.

---

# 16. Documentação obrigatória

Após uma alteração arquitetural relevante, revisar:

* `README.md`;
* `NEXT_STEPS.md`;
* `AGENTS.md`;
* exemplos de configuração;
* comentários sobre execução;
* estrutura de diretórios;
* comandos de teste.

Não adicionar links locais como:

```text
file:///c:/Users/...
```

Links entre arquivos do repositório devem ser relativos:

```markdown
[NEXT_STEPS.md](NEXT_STEPS.md)
```

O README deve refletir o comportamento real do código.

Não marcar uma funcionalidade como concluída antes de ela existir e estar minimamente validada.

---

# 17. Verificações obrigatórias

Depois de modificar código Python, executar conforme disponível:

```bash
python -m compileall src
```

Quando o projeto possuir Pytest configurado:

```bash
pytest
```

Quando Ruff estiver configurado:

```bash
ruff check .
ruff format --check .
```

Quando houver type checker configurado:

```bash
mypy src
```

ou o comando equivalente registrado no projeto.

Para arquivos específicos, também pode ser utilizado:

```bash
python -m py_compile caminho/do/arquivo.py
```

## O agente deve informar

Ao finalizar uma tarefa, registrar claramente:

* arquivos alterados;
* comportamento implementado;
* testes executados;
* testes que passaram;
* testes que não puderam ser executados;
* limitações conhecidas;
* próximos passos diretamente relacionados.

Nunca afirmar que um teste passou sem tê-lo executado.

---

# 18. Checklist antes de finalizar uma alteração

## Arquitetura

* [ ] A captura continua vindo do Projetor do OBS.
* [ ] Nenhuma câmera foi adicionada.
* [ ] Nenhuma leitura de memória foi adicionada.
* [ ] Detectores continuam sem enviar inputs.
* [ ] Módulos de decisão continuam sem capturar frames.
* [ ] Inputs passam pelo executor central.
* [ ] Configurações não foram hardcoded desnecessariamente.
* [ ] Dependências de plataforma estão isoladas.

## Segurança

* [ ] O killswitch continua funcionando.
* [ ] Nenhuma ação ocorre na inicialização.
* [ ] Nenhuma ação ocorre sem foco válido.
* [ ] Nenhuma ação ocorre com frame inválido.
* [ ] Teclas são liberadas no encerramento.
* [ ] Exceções não deixam o bot executando silenciosamente.

## Testes

* [ ] A sintaxe foi validada.
* [ ] Testes relevantes foram executados.
* [ ] Testes automatizados não enviam inputs reais.
* [ ] Novas regras possuem testes quando viável.
* [ ] Falhas conhecidas foram documentadas.

## Documentação

* [ ] README continua correto.
* [ ] NEXT_STEPS foi atualizado quando necessário.
* [ ] AGENTS foi atualizado quando uma regra mudou.
* [ ] Exemplos de configuração continuam válidos.
* [ ] Não existem links locais absolutos.

---

# 19. Regras permanentes resumidas

1. Não usar câmera ou `/dev/video0`.
2. Não usar câmera virtual do OBS.
3. Capturar diretamente a janela do Projetor do OBS.
4. Não ler ou modificar memória do processo.
5. Não enviar ações automáticas durante a inicialização.
6. Não executar inputs com estado inválido ou desconhecido.
7. Tratar o killswitch como prioridade absoluta.
8. Realizar somente uma captura principal por ciclo.
9. Separar percepção, estado, decisão e execução.
10. Não permitir que detectores executem inputs.
11. Não permitir que módulos capturem a tela.
12. Centralizar inputs, cooldowns e prioridades.
13. Utilizar uma máquina de estados explícita.
14. Manter configurações fora do código.
15. Preferir ROIs relativas e calibráveis.
16. Isolar Windows e Linux atrás de abstrações.
17. Criar testes que não dependam do jogo aberto.
18. Não adicionar movimento antes das fundações arquiteturais.
19. Não afirmar que testes foram executados quando não foram.
20. Manter `README.md`, `NEXT_STEPS.md` e `AGENTS.md` sincronizados.
