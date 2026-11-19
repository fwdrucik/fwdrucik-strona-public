-- ---------------------------------------------------------------------------
-- fwdrucik.pl — schemat bazy dla kont, forum i komentarzy
--
-- Wklej całość w phpMyAdmin (zakładka SQL) po utworzeniu NOWEJ, pustej bazy
-- w panelu hosting-home.pl. Nie uruchamiaj tego na bazie Joomli.
--
-- Kodowanie utf8mb4 — potrzebne dla polskich znaków i emoji w treściach.
-- ---------------------------------------------------------------------------

SET NAMES utf8mb4;

-- --------------------------------------------------------------- użytkownicy
CREATE TABLE IF NOT EXISTS fw_uzytkownicy (
  id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nick              VARCHAR(40)  NOT NULL,
  email             VARCHAR(190) NOT NULL,
  haslo_hash        VARCHAR(255) NOT NULL,
  rola              ENUM('user','admin') NOT NULL DEFAULT 'user',
  -- zaufany = 1 oznacza, że użytkownik ma już zatwierdzony wpis i jego kolejne
  -- treści trafiają na stronę od razu, bez kolejki moderacyjnej.
  zaufany           TINYINT      NOT NULL DEFAULT 0,
  zablokowany       TINYINT      NOT NULL DEFAULT 0,
  utworzony         DATETIME     NOT NULL,
  ostatnie_logowanie DATETIME    DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uniq_email (email),
  UNIQUE KEY uniq_nick (nick)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------- sesje
-- Trzymany jest wyłącznie skrót SHA-256 tokenu; sam token żyje tylko
-- w ciasteczku HttpOnly. Wyciek bazy nie pozwala przejąć sesji.
CREATE TABLE IF NOT EXISTS fw_sesje (
  token_hash    CHAR(64)     NOT NULL,
  uzytkownik_id INT UNSIGNED NOT NULL,
  utworzona     DATETIME     NOT NULL,
  wygasa        DATETIME     NOT NULL,
  ip            VARCHAR(45)  DEFAULT NULL,
  przegladarka  VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (token_hash),
  KEY idx_uzytkownik (uzytkownik_id),
  KEY idx_wygasa (wygasa),
  CONSTRAINT fk_sesje_uzytkownik FOREIGN KEY (uzytkownik_id)
    REFERENCES fw_uzytkownicy (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------- wątki
CREATE TABLE IF NOT EXISTS fw_watki (
  id                 INT UNSIGNED NOT NULL AUTO_INCREMENT,
  kategoria          VARCHAR(24)  NOT NULL,
  tytul              VARCHAR(160) NOT NULL,
  tresc              TEXT         NOT NULL,
  autor_id           INT UNSIGNED NOT NULL,
  status             ENUM('oczekuje','opublikowany','odrzucony') NOT NULL DEFAULT 'oczekuje',
  wyswietlenia       INT UNSIGNED NOT NULL DEFAULT 0,
  utworzony          DATETIME     NOT NULL,
  ostatnia_aktywnosc DATETIME     NOT NULL,
  PRIMARY KEY (id),
  KEY idx_lista (status, kategoria, ostatnia_aktywnosc),
  KEY idx_autor (autor_id),
  CONSTRAINT fk_watki_autor FOREIGN KEY (autor_id)
    REFERENCES fw_uzytkownicy (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------- odpowiedzi
CREATE TABLE IF NOT EXISTS fw_odpowiedzi (
  id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
  watek_id   INT UNSIGNED NOT NULL,
  autor_id   INT UNSIGNED NOT NULL,
  tresc      TEXT         NOT NULL,
  status     ENUM('oczekuje','opublikowany','odrzucony') NOT NULL DEFAULT 'oczekuje',
  utworzona  DATETIME     NOT NULL,
  PRIMARY KEY (id),
  KEY idx_watek (watek_id, status, utworzona),
  KEY idx_autor (autor_id),
  CONSTRAINT fk_odp_watek FOREIGN KEY (watek_id)
    REFERENCES fw_watki (id) ON DELETE CASCADE,
  CONSTRAINT fk_odp_autor FOREIGN KEY (autor_id)
    REFERENCES fw_uzytkownicy (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------- komentarze
-- slug = identyfikator wpisu blogowego, np. "regeneracja-alternatorow-pultusk"
CREATE TABLE IF NOT EXISTS fw_komentarze (
  id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
  slug      VARCHAR(120) NOT NULL,
  autor_id  INT UNSIGNED NOT NULL,
  tresc     TEXT         NOT NULL,
  status    ENUM('oczekuje','opublikowany','odrzucony') NOT NULL DEFAULT 'oczekuje',
  utworzony DATETIME     NOT NULL,
  PRIMARY KEY (id),
  KEY idx_wpis (slug, status, utworzony),
  KEY idx_autor (autor_id),
  CONSTRAINT fk_kom_autor FOREIGN KEY (autor_id)
    REFERENCES fw_uzytkownicy (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------------------- limity
-- Ślad po każdej próbie rejestracji, logowania i dodania treści.
-- Służy do limitu tempa; stare wpisy kasuje samo API.
CREATE TABLE IF NOT EXISTS fw_limity (
  id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  ip     VARCHAR(45) NOT NULL,
  akcja  VARCHAR(32) NOT NULL,
  kiedy  DATETIME    NOT NULL,
  PRIMARY KEY (id),
  KEY idx_limit (ip, akcja, kiedy)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Konto administratora
--
-- W repozytorium NIE ma żadnego hasła ani jego skrótu — to celowe.
-- Zrób tak:
--   1. Wejdź na https://fwdrucik.pl/konto/ i zarejestruj się normalnie
--      (adres fwdrucik@gmail.com, własne mocne hasło).
--   2. Wróć do phpMyAdmin i wykonaj poniższe zapytanie.
--
-- UPDATE fw_uzytkownicy SET rola = 'admin', zaufany = 1
--   WHERE email = 'fwdrucik@gmail.com';
-- ---------------------------------------------------------------------------


-- ---------------------------------------------------------------------------
-- Wpisy blogowe czekające na akceptację
--
-- Agent bloga (GitHub Actions) publikuje wpis od razu na serwer, ale jako
-- szkic: strona ma noindex, nie ma jej na /blog/ ani w sitemap.xml. Rekord
-- w tej tabeli jest jedynym miejscem, z którego panel wie, że coś czeka.
--
-- Kolumny autor_id celowo nie ma — autorem jest agent, nie użytkownik,
-- więc moderacja wpisów nie nadaje nikomu statusu "zaufany".
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fw_wpisy (
  id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
  slug           VARCHAR(190) NOT NULL,
  tytul          VARCHAR(255) NOT NULL,
  `lead`         TEXT         NOT NULL,
  url            VARCHAR(255) NOT NULL,
  status         ENUM('oczekuje','opublikowany','odrzucony') NOT NULL DEFAULT 'oczekuje',
  utworzony      DATETIME     NOT NULL,
  rozstrzygniety DATETIME     NULL,
  rozstrzygnal   INT UNSIGNED NULL,
  run_url        VARCHAR(255) NULL,
  -- Notatka agenta kontroli treści: co poprawił albo czemu wpisu nie przepuścił.
  notatka        TEXT         NULL,
  PRIMARY KEY (id),
  UNIQUE KEY idx_slug (slug),
  KEY idx_kolejka (status, utworzony)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
