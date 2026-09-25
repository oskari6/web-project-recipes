# Ruokareseptit

- Sovelluksessa käyttäjät pystyvät jakamaan ruokareseptejään. Reseptissä lukee tarvittavat ainekset ja valmistusohje.
- Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
- Käyttäjä pystyy lisäämään reseptejä ja muokkaamaan ja poistamaan niitä.
- Käyttäjä näkee sovellukseen lisätyt reseptit.
- Käyttäjä pystyy etsimään reseptejä hakusanalla.
- Käyttäjä pystyy etsimään käyttäjiä hakusanalla.
- Käyttäjäsivu näyttää, montako reseptiä käyttäjä on lisännyt ja listan käyttäjän lisäämistä resepteistä.
- Käyttäjä pystyy valitsemaan esimerkiksi seuraavia luokitteluja:
- Ruoan tyyppi, ruokavalio, valmistusaika, reseptistä saatava annosten määrä, kuvat ja muut lisätiedot.
- Käyttäjä pystyy antamaan reseptille kommentin ja arvosanan. Reseptistä näytetään kommentit ja keskimääräinen arvosana ja kaikki arvosanat.

Tässä pääasiallinen tietokohde on ruokaresepti ja toissijainen tietokohde on kommentti reseptiin.

# Projektin rakenne

## Kansiot

- `static/` – Staattiset tiedostot: kuvat, CSS ja fontit.
- `templates/` – HTML-templaatit.

## Tiedostot

- `app.py` – Sovelluksen entrypoint ja kaikki routet
- `database.db` – Generoitu tietokanta.
- `db.py` – Tietokantaan liittyvät toiminnot: migraatiot, datan alustus ja funktiot.
- `users.py` – Käyttäjien toiminnalliset funktiot.
- `recipes.py` – Reseptien toiminnalliset funktiot.
- `config.py` – Vakioarvot.
- `validator.py` – Validointi funktiot.

# Kehitys

## Sovelluksen käynnistys

Alusta kehitysympäristö:

Luo virtuaali ympäristö

```bash
python3 -m venv .venv
```

Asenna riippuvuudet

```bash
.venv/bin/pip install flask
```

Käynnistä sovellus kehitystilassa

```bash
.venv/bin/flask run --debug
```

Jos haluat enemmän dataa tietokantaan (db.py USER_COUNT ja RECIPE_COUNT numeroita saa vaihtaa):

```bash
.venv/bin/python -m seed_database.py
```

tietokantaan pääsee käsiksi komennolla:

```bash
sqlite3 database.db
```

Jos tietokanta pitää nollata, komento on:

```
.venv/bin/python -c "from db import reset_database; reset_database()"
```

## Ongelmatilanteet

Ongelmatilanteissa ota yhteyttä:

`oskari.anton.sulkakoski@helsinki.fi`

# Suorituskyky

- 10^6 käyttäjää
- 10^6 reseptiä

käyttäjä ja resepti haku noin 1.5s

käyttäjät ja reseptit sivut latautuu noin 1s
käyttäjä ja resepti sivu latautuu noin 1s
