# 🤖 AGENTS.md - Diretrizes do Projeto Tibia Bot

1. **Visão Computacional Pura**: NUNCA usar leitura de memória (`ReadProcessMemory` / DLL injection). Todo estado vem de captura de tela MSS/OpenCV do Projetor OBS.
2. **Scan Codes de Hardware & Humanização**: Todo input utiliza `pydirectinput` em `src/utils/input.py` e distribuição gaussiana / Bézier de `src/utils/humanizer.py`.
3. **Pausa em PZ**: Não disparar curas ou ataques quando `is_in_pz()` for True.
4. **Encoding no Windows**: Manter `sys.stdout` em UTF-8 com fallback para marcadores ASCII (`[OK]`, `[X]`, `[!]`).
