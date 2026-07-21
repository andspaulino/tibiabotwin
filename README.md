# Tibia Bot - Reconhecimento de Imagem 🎮👁️

Este é um projeto para o desenvolvimento de um bot para Tibia utilizando técnicas de **Visão Computacional (Reconhecimento de Imagem)** e simulação de input físico de teclado/mouse. 

Diferente de bots que leem ou injetam dados na memória do jogo, este bot age puramente observando a tela (pixels e padrões) e simulando comandos de teclado/mouse de forma humanizada, o que torna sua detecção por sistemas como o BattlEye extremamente mais complexa.

---

## 🚀 Funcionalidades Planejadas

### Fase 1: Core & Sobrevivência (MVP)
*   **Captura Otimizada de Tela**: Sistema de alto desempenho para monitorar regiões específicas da tela do Tibia sem causar quedas de FPS no jogo.
*   **Auto-Healer (Cura Automática)**:
    *   Monitoramento em tempo real das barras de Vida (HP) e Mana (MP).
    *   Configuração de limiares (ex: usar magia de cura se HP < 80%, usar poção de cura se HP < 50%).
    *   Uso de poções de mana para manter o nível de mana estável.
*   **Simulador de Hardware Emulado**: Envio de comandos de teclado/mouse via DirectX Scan Codes para simular inputs reais de teclado/mouse.

### Fase 2: Combate & Looting
*   **Auto-Attacker**: Detecção de criaturas na *Battle List* e ataque automático.
*   **Auto-Loot**: Coleta automática de itens ao redor do personagem ou abrindo corpos.
*   **Anti-Idle**: Movimentações aleatórias para evitar que o personagem seja desconectado por inatividade.

---

## 🎥 Captura de Tela e Contorno com OBS Studio ⚠️

Durante os testes de desenvolvimento, foi constatado que o cliente do Tibia **bloqueia capturas de tela diretas** (a tela capturada fica toda preta) devido a restrições do sistema de renderização e anti-cheat (BattlEye).

### Solução (Workaround com OBS Studio + Janela Invisível):
Para fazer a captura de imagem de forma 100% segura e sem ler a memória do jogo:
1. Abrimos o **OBS Studio** e criamos uma fonte de **Captura de Jogo** ou **Captura de Janela** apontando para o Tibia.
2. Clicamos com o botão direito na visualização do OBS e selecionamos **Projetor em janela (Fonte)** ou **Projetor em janela (Cena)**.
3. O script Python fará a captura de tela focando na janela do **Projetor do OBS**, contornando o bloqueio de tela preta com sucesso!
4. **Controle de Opacidade da Janela**: O projeto conta com o módulo `src/utils/window.py` para alterar a opacidade da janela do Tibia para `1` (praticamente invisível via Win32 `SetLayeredWindowAttributes`). Como o OBS Studio captura a renderização do DirectX diretamente, ele continua capturando o jogo perfeitamente mesmo com a janela do jogo invisível para o usuário!
5. **Restauração Limpa da Janela**: Para restaurar a visibilidade normal (opacidade 255), é necessário remover a flag `WS_EX_LAYERED` do estilo estendido da janela no Windows e invocar `SetWindowPos` e `RedrawWindow` para forçar o DWM a redesenhar a janela em seu estado nativo original.

---

## 🛠️ Stack Tecnológica

O projeto é desenvolvido em **Python 3.10+** utilizando as seguintes bibliotecas:

*   **[OpenCV (opencv-python)](https://opencv.org/)**: Processamento de imagens e localização de elementos da interface do jogo por correspondência de modelos (Template Matching).
*   **[MSS](https://python-mss.readthedocs.io/)**: Captura de tela ultra-rápida.
*   **[PyDirectInput](https://github.com/learncodebygaming/pydirectinput)**: Simulação de mouse e teclado que envia scan codes de nível mais baixo, cruciais para que o Tibia (DirectX) processe as teclas corretamente.
*   **[Keyboard](https://github.com/boppreh/keyboard)**: Para atalhos globais do sistema, permitindo pausar ou fechar o bot instantaneamente a qualquer momento.
*   **[NumPy](https://numpy.org/)**: Para manipulação eficiente das matrizes de imagens capturadas.

---

## 📁 Estrutura do Projeto (Proposta)

```text
tibia-bot/
├── src/
│   ├── bot/
│   │   ├── healer.py      # Lógica de cura (HP/Mana)
│   │   └── combat.py      # Lógica de ataque/alvo (futuro)
│   ├── utils/
│   │   ├── screen.py      # Captura de tela e processamento de imagem
│   │   └── input.py       # Simulação de teclado e mouse
│   └── main.py            # Executável principal (Loop e interface de controle)
├── templates/             # Imagens base para template matching (barras, botões, monstros)
├── requirements.txt       # Dependências do Python
└── README.md              # Documentação do projeto
```

---

## ⚙️ Instalação e Requisitos

1.  **Instale o Python 3.10 ou superior**: Certifique-se de marcar a opção "Add Python to PATH" durante a instalação.
2.  **Clone o repositório** e navegue até a pasta:
    ```bash
    cd tibia-bot
    ```
3.  **Instale as dependências**:
    ```bash
    pip install -r requirements.txt
    ```

---

## ⚠️ Isenção de Responsabilidade (Disclaimer)

Este projeto tem fins estritamente de estudo e aprendizado sobre visão computacional e automação. O uso de softwares de automação (bots) viola os Termos de Serviço do Tibia (CipSoft) e pode resultar na exclusão permanente da sua conta. Use por sua conta e risco.
