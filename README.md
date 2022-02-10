# Gesetze aus dem Internet

[![license](https://img.shields.io/github/license/nfelger/gesetze-aus-dem-internet.svg)](LICENSE)

Details folgen.

## Entwickeln

### Projektabhängigkeiten installieren

```sh
pipenv install --dev
```

### Tool: `pipenv shell`

`pipenv shell` öffnet eine Shell, in der alle Python-Abhängigkeiten des Projekts verfügbar sind.

Alles Folgende wird in einer solchen Shell ausgeführt.

### Datenbank initialisieren

```sh
# Postgres Datenbank erzeugen, z.B. mit:
createdb gadi
# Datenbank URI setzen. Format ist: postgresql://$username:$password@$host:$port/$database. Z.B.:
export DB_URI="postgresql://localhost:5432/gadi"
# Datenbanktabellen initialisieren
invoke database.init
```

### Tests ausführen

```sh
invoke tests
```

### Tool: `invoke`

Mit [`invoke`](http://www.pyinvoke.org/) lassen sich alle wichtigen Tasks ausführen. Einen Überblick gibt:

```sh
invoke --list
```

Tasks sind definiert in [tasks.py](tasks.py).

### Daten importieren

Die Abhängigkeiten sind installiert, die Datenbank aufgesetzt - Zeit, sie mit Daten zu befüllen:

```sh
# Daten von gesetze-im-internet.de herunterladen
invoke ingest.download-laws ./downloads/gii/
# Heruntergeladene Daten parsen und in die Datenbank importieren
invoke ingest.ingest-data ./downloads/gii/
```

Die Daten werden in `./downloads/gii/` gespeichert und mit Timestamps versehen, so dass bei späterem Ausführen nur diejenigen Gesetze aktualisiert werden, für die es Änderungen auf gesetze-im-internet.de gibt.
