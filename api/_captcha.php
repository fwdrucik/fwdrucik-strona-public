<?php
declare(strict_types=1);

/**
 * Captcha — część wspólna: tabela wyzwań i sprawdzanie odpowiedzi.
 *
 * Wydzielone z `captcha.php`, bo tamten plik jest końcówką HTTP: ustala akcję
 * z adresu i kończy odpowiedzią. Wciągnięcie go przez `require` z auth.php
 * uruchamiało tę logikę przy każdym logowaniu i przewracało całe żądanie.
 * Tutaj są wyłącznie funkcje — plik nic nie wypisuje i niczego nie kończy.
 */

if (basename((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === '_captcha.php') {
    http_response_code(404);
    exit;
}

const FW_CAPTCHA_ZNAKI = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // bez I, O, 0, 1
const FW_CAPTCHA_DLUGOSC = 5;
const FW_CAPTCHA_WAZNOSC_S = 900;

function fw_zapewnij_tabele_captcha(): void
{
    static $gotowe = false;
    if ($gotowe) {
        return;
    }
    fw_baza()->exec(
        'CREATE TABLE IF NOT EXISTS ' . fw_tabela('captcha') . ' ('
        . ' id        CHAR(32)         NOT NULL,'
        . ' odpowiedz VARCHAR(16)      NOT NULL,'
        . ' proby     TINYINT UNSIGNED NOT NULL DEFAULT 0,'
        . ' wygasa    DATETIME         NOT NULL,'
        . ' PRIMARY KEY (id),'
        . ' KEY idx_wygasa (wygasa)'
        . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
    );
    $gotowe = true;
}

/** Sprzątanie starych wyzwań — tabela nie ma rosnąć w nieskończoność. */
function fw_captcha_posprzataj(): void
{
    fw_baza()->prepare('DELETE FROM ' . fw_tabela('captcha') . ' WHERE wygasa < ?')
        ->execute([fw_teraz()]);
}

/**
 * Sprawdza odpowiedź i zużywa wyzwanie.
 *
 * Wyzwanie ginie po pierwszym sprawdzeniu niezależnie od wyniku: inaczej
 * jeden rozwiązany obrazek dałoby się użyć do setek rejestracji.
 */
function fw_captcha_sprawdz(string $id, string $odpowiedz): void
{
    fw_zapewnij_tabele_captcha();
    if (!preg_match('/^[a-f0-9]{32}$/', $id)) {
        fw_blad(422, 'Przepisz kod z obrazka.');
    }
    $pdo = fw_baza();
    $st = $pdo->prepare('SELECT odpowiedz, wygasa FROM ' . fw_tabela('captcha') . ' WHERE id = ?');
    $st->execute([$id]);
    $wiersz = $st->fetch();

    $pdo->prepare('DELETE FROM ' . fw_tabela('captcha') . ' WHERE id = ?')->execute([$id]);

    if (!$wiersz || $wiersz['wygasa'] < fw_teraz()) {
        fw_blad(422, 'Kod z obrazka wygasł. Odśwież obrazek i spróbuj ponownie.');
    }
    // hash_equals zamiast !== : porownanie o stalym czasie, zeby nie dalo sie
    // zgadywac znak po znaku po czasie odpowiedzi.
    if (!hash_equals($wiersz['odpowiedz'], strtoupper(trim($odpowiedz)))) {
        fw_blad(422, 'Kod z obrazka jest niepoprawny. Spróbuj jeszcze raz.');
    }
}
