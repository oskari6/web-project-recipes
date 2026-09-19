![alt text]({5FC884BD-7B8C-4EC5-BAE9-9BBD871A8241}.png)

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

* `.vscode/` – Kehitysympäristön konfiguraatio.
* `db/` – Tietokantaan liittyvät toiminnot: migraatiot, datan alustus ja funktiot.
* `routes/` – Reititykset eri resursseille.
* `services/` – Resurssien toiminnalliset funktiot.
* `static/` – Staattiset tiedostot: kuvat, CSS ja fontit.
* `templates/` – HTML-templaatit.
* `utils/` – Muut yleiset apufunktiot ja resurssit, kuten dekoraattorit ja muuttumattomat muuttujat.

## Tiedostot

* `.env` – Säilytyspaikka session secretille ja muille salaisuuksille.
* `app.py` – Sovelluksen entrypoint.
* `database.db` – Generoitu tietokanta.
* `Makefile` – Komentojen ajon abstrahointiin käytettävä tiedosto.
* `requirements.txt` – Ulkoiset kirjastoriippuvuudet.
* `setup.sh` – Kehitysympäristön alustus ja tietokannan generointi.

# Kehitys

## Sovelluksen käynnistys

Jos `make`-pakettia ei ole vielä asennettu, asenna se komennolla:

```bash
sudo apt install make
```

Alusta kehitysympäristö:

```bash
make setup
```

Käynnistä sovellus kehitystilassa:

```bash
make dev
```

Tai vaihtoehtoisesti ilman debuggausta:

```bash
make start
```

## Ongelmatilanteet

Ongelmatilanteissa ota yhteyttä:

`oskari.anton.sulkakoski@helsinki.fi`

## VS Code -lisäosat

Avaa VS Coden lisäosat:

```text
Ctrl + Shift + X
```

Kirjoita hakukenttään:

```text
@recommended
```

Asenna **Workspace Recommendations** -otsikon alla näkyvät suositellut lisäosat.


# Suorituskyky

- 10^6 käyttäjää
- 10^6 reseptiä

käyttäjä ja resepti haku noin 1.5s

käyttäjät ja reseptit sivut latautuu noin 1s
käyttäjä ja resepti sivu latautuu noin 1s
