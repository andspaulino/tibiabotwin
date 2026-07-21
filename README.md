# Tibia Bot - Reconhecimento de Imagem 🎮👁️

Este é um projeto para o desenvolvimento de um bot para Tibia utilizando técnicas de **Visão Computacional (Reconhecimento de Imagem)** e simulação de input físico de teclado/mouse via hardware scan codes. 

Diferente de bots que leem ou injetam dados na memória do jogo, este bot age puramente observando a tela (pixels e padrões) e simulando comandos de teclado/mouse de forma humanizada, o que torna sua detecção por sistemas como o BattlEye extremamente mais complexa.

📌 **Acompanhe o roadmap detalhado e próximos passos em [NEXT_STEPS.md](file:///c:/Users/ander/Projects/tibia-bot/NEXT_STEPS.md)**.

---

## 🚀 Funcionalidades Concluídas

### 1. Captura Otimizada & Janela Invisível (`launcher.py` + `src/utils/window.py`)
- Ocultação da janela do Tibia com opacidade 1 via Win32 API `SetLayeredWindowAttributes`.
- Captura de tela ao vivo sem lag focando na janela do **Projetor do OBS Studio**.
- Restauração automática da visibilidade nativa da janela ao encerrar o bot.

### 2. Visão Computacional & Análise de Barras (`src/utils/screen.py`)
- **Barra de Vida (HP)**: Análise por amostragem de dominância de cor BGR.
- **Barra de Mana (MP)**: Filtro de cor azul que desconsidera textos brancos e bordas cinzas.
- **Barra de Status**: Leitura de atividade de ícones de status.
- **Protection Zone (PZ)**: Template Matching (`templates/pz.png`) + validação de cor azul (`is_in_pz()`) com emissão de logs em tempo real.

### 3. Auto-Healer Inteligente (`src/bot/healer.py`)
- **Hotkey 1**: Magia de Cura (disparada quando `HP <= 90%`).
- **Hotkey 2**: Poção de Mana (disparada quando `MP <= 50%`).
- **Hotkey 3**: Poção de Vida (Emergência - disparada quando `HP <= 30%`).
- **Pausa Automática em PZ**: Interrompe magias e poções em Protection Zone.
- **Gerenciador de Cooldowns**: Intervalo seguro (1.0s) para evitar envio excessivo de teclas.

---

## 🎥 Captura de Tela com OBS Studio ⚠️

Devido ao bloqueio de renderização direta do cliente do Tibia (tela preta), o bot utiliza o seguinte fluxo:
1. O **OBS Studio** roda com uma fonte de **Captura de Jogo / Janela** apontando para o Tibia.
2. Abrimos um **Projetor em Janela** no OBS.
3. O iniciador deixa o Tibia invisível (`opacidade = 1`), mas o OBS continua capturando o DirectX/Vulkan perfeitamente!
4. O bot lê a área do cliente do Projetor OBS e envia os comandos diretamente para o Tibia via `pydirectinput`.

---

## 🚀 Como Executar

1. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Execute o iniciador**:
   ```bash
   python launcher.py
   ```

---

## 📁 Estrutura do Projeto

```text
tibia-bot/
├── src/
│   ├── bot/
│   │   ├── healer.py      # Módulo AutoHealer (Hotkeys 1, 2, 3)
│   │   └── combat.py      # Módulo AutoAttacker (Fase 3)
│   ├── utils/
│   │   ├── window.py      # Controle Win32 e opacidade de janelas
│   │   ├── screen.py      # Captura MSS, leitura de HP/MP/PZ e OpenCV
│   │   └── input.py       # Simulação DirectX (pydirectinput)
│   └── main.py            # Motor principal e loop de monitoramento
├── templates/             # Templates para Template Matching (ex: pz.png)
├── tests/                 # Utilitários de testes e ROI
│   ├── test_bars.py       # Teste de leitura de HP/MP/Status
│   ├── test_pz.py         # Teste de detecção dinâmica de PZ
│   ├── get_roi.py         # Seletor interativo de coordenadas de ROI
│   └── get_mouse_pos.py   # Inspetor de posição do cursor
├── launcher.py            # Atalho/Iniciador principal na raiz
├── requirements.txt       # Dependências do projeto
└── README.md              # Documentação principal
```

---

## ⚠️ Isenção de Responsabilidade (Disclaimer)

Este projeto tem fins estritamente de estudo e aprendizado sobre visão computacional e automação. O uso de softwares de automação (bots) viola os Termos de Serviço do Tibia (CipSoft) e pode resultar na exclusão permanente da sua conta. Use por sua conta e risco.
