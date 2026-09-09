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

# Rakenne

kansiot:
/.vscode/ - kehitysympräistö konfiguraatio
/db/ - tietokantaan liittyvät toiminnot: migraatio, datan alustus ja funktiot
/routes/ - reititykset eri resursseille
/services/ - toiminnalliset funktiot resursseille
/static/ - staattiset tiedostot: kuvat, css, fontit
/templates/ - html templaatit
/utils/ - muut yleiset apufunktiot ja resurssit: dekoraattorit ja muuttumattomat muuttujat

tiedostot:
.env - säilytys paikka session secretille ja muulle salaiselle
app.py - sovelluksen entrypoint
database.db - generoitu tietokanta
Makefile - komentojen ajon abstraktio tiedosto
requirements.txt - ulkoiset kirjasto riippuvuudet
setup.sh - kehitysympäristön alustus ja tietokannan generointi

# Kehitys

sovelluksen käynnistys:
(jos sinulta ei löydy jo make -pakettia, asenna se sudo apt install make -komennolla)
make setup
make dev
tai vaihtoehtoisesti ilman debuggausta:
make start

ongelmien tullessa: oskari.anton.sulkakoski@helsinki.fi

lisäosat:
SHIFT + CTRL + X → Find extensions
Kirjoita hakukenttään @recommended ja asenna Workspace Recommendations -header osion lisäosat
