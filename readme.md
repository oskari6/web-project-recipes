# Ruokareseptit

- Sovelluksessa käyttäjät pystyvät jakamaan ruokareseptejään. Reseptissä lukee tarvittavat ainekset ja valmistusohje.
- Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
- Käyttäjä pystyy lisäämään reseptejä ja muokkaamaan ja poistamaan niitä.
- Käyttäjä näkee sovellukseen lisätyt reseptit.
- Käyttäjä pystyy etsimään reseptejä hakusanalla.
- Käyttäjäsivu näyttää, montako reseptiä käyttäjä on lisännyt ja listan käyttäjän lisäämistä resepteistä.
- Käyttäjä pystyy valitsemaan esimerkiksi seuraavia luokitteluja:
- Ruoan tyyppi: alkuruoka, pääruoka tai jälkiruoka
- Ruokavalio: laktoositon, gluteeniton tai vegaaninen
- Käyttäjä pystyy antamaan reseptille kommentin ja arvosanan. Reseptistä näytetään kommentit ja keskimääräinen arvosana.

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

starting application:
make setup
make dev
tai vaihtoehtoisesti ilman debuggausta:
make start

extensions:
SHIFT + CTRL + X → Find extensions
Type in searchfield @recommended and install Workspace Recommendations -header sections extensions
