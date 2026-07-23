# Melhoria — Configuração de Monstros por Hunt

Cada arquivo de hunt poderá definir os monstros que devem ser atacados, ignorados e sua estratégia de combate.

## Exemplo de JSON

```json
{
  "combat": {
    "targets": [
      {
        "name": "Minotaur Archer",
        "attack_type": "RANGED",
        "strategy": {
          "priority": 60,
          "use_amp_res": true
        }
      },
      {
        "name": "Minotaur Guard",
        "attack_type": "MELEE",
        "strategy": {
          "priority": 90,
          "use_amp_res": false
        }
      }
    ],
    "ignore": [
      "Minotaur Mage"
    ]
  }
}
```

Cada alvo poderá definir:

- `name`: nome identificado na Battle List;
- `attack_type`: característica do monstro;
- `priority`: prioridade configurável para a hunt;
- `use_amp_res`: indica se o bot pode utilizar `amp res`;
- `ignore`: monstros que não devem ser atacados.

A característica do monstro deve permanecer separada da estratégia da hunt. O estado atual do combate, alvo selecionado e monstros visíveis continuam no `GameState` e no controlador de combate.
