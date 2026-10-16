# Cultuurkalender

Grote culturele evenementen in en rond Amsterdam (festivals, premières, seizoensopeningen en museumexposities) als agenda-abonnement.

- Overzicht met filter per genre: https://tlbakker.github.io/cultuurkalender/
- Alles: https://tlbakker.github.io/cultuurkalender/cultuur.ics
- Per genre: `klassiek.ics`, `pop.ics`, `theater.ics`, `opera.ics`, `expositie.ics`, `festival.ics`, `film.ics`

## Bijwerken

De evenementen staan in `events.json`. Na een wijziging:

```
python3 build.py events.json docs
```

Exposities en projecten langer dan drie weken krijgen een start- en een einddag-item. Geschatte datums zijn gemarkeerd met "(datum o.v.)".
