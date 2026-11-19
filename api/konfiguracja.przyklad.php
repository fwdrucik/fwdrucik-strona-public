<?php
/**
 * Wzór konfiguracji API — ten plik jest w repozytorium i NIE zawiera haseł.
 *
 * Na serwerze skopiuj go pod jedną z dwóch nazw i uzupełnij danymi:
 *
 *   1. public_html/autoinstalator/fw-konfiguracja.php   <- zalecane
 *      (katalog leży poza obszarem serwowanym przez WWW, bo domena wskazuje
 *       na public_html/autoinstalator/joomla — pliku nie da się pobrać z sieci)
 *
 *   2. public_html/autoinstalator/joomla/api/konfiguracja.php   <- awaryjnie
 *      (chroniony tylko regułą z api/.htaccess)
 *
 * Danych dostępowych do bazy NIE wpisuj do repozytorium i nie wysyłaj ich
 * skryptem wyslij.py — build.py celowo pomija pliki konfiguracja*.php.
 */

return [
    // Publiczny asystent Bielik: klucz Sherlock pozostaje wyłącznie na serwerze.
    'sherlock_api_key' => '',
    // 5 EUR miesięcznie, konserwatywne rezerwacje; 1 EUR = 1 000 000 mikroEUR.
    'asystent_budzet_microeur' => 5000000,
    // Dane NOWEJ bazy założonej w panelu hosting-home.pl (nie bazy Joomli).
    'db_host'       => 'localhost',
    'db_port'       => 3306,
    'db_nazwa'      => 'nazwa_bazy',
    'db_uzytkownik' => 'uzytkownik_bazy',
    'db_haslo'      => 'haslo_do_bazy',

    // Prefiks tabel — musi zgadzać się z tym w schemat.sql.
    'prefiks'       => 'fw_',

    // --- agent bloga -------------------------------------------------------
    // Wspólny sekret dla api/wpisy.php. Tę samą wartość wpisz jako sekret
    // AGENT_TOKEN w repozytorium GitHuba — workflow melduje nim nowy szkic.
    // Wygeneruj coś losowego i długiego, np. `openssl rand -hex 32`.
    'agent_token'   => '',

    // Drobnoziarnisty token GitHuba (PAT) ograniczony do repozytorium
    // fwdrucik/fwdrucik-strona, uprawnienie Contents: Read and write.
    // Panel wysyła nim repository_dispatch, czyli odpala publikację wpisu.
    // Pusty token = akceptacja zapisze status w bazie, ale nic nie opublikuje.
    'github_token'  => '',
    'github_repo'   => 'fwdrucik/fwdrucik-strona',
];
