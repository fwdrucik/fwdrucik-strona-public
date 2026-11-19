<?php
declare(strict_types=1);
require_once __DIR__.'/_asystent.php';
try {
 $key=(string)(getenv('SHERLOCK_API_KEY') ?: (fw_konfiguracja()['sherlock_api_key']??''));
 if(fw_metoda()==='GET'&&($_GET['akcja']??'')==='status')fw_odpowiedz(['ok'=>true,'dostepny'=>$key!==''&&fw_spolecznosc_gotowa(),'model'=>'Bielik 11B v3','kontakt'=>'601 726 924']);
 fw_blad(426,'Odśwież stronę i rozpocznij rozmowę w nowym oknie czatu.');
} catch(Throwable $e){fw_blad(503,'Czat chwilowo niedostępny. Kontakt: 601 726 924.');}
