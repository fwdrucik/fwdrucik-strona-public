<?php
declare(strict_types=1);
/** Byte-offset text edits preserve all original tags, attributes and embedded code. */
function fw_tresci_bloki(string $html): array {
    preg_match_all('~<!--[\s\S]*?-->|<![^>]*>|<\?[^>]*\?>|</?[a-zA-Z][a-zA-Z0-9:-]*(?:"[^"]*"|\x27[^\x27]*\x27|[^\x27">])*?>~', $html, $matches, PREG_OFFSET_CAPTURE);
    $stack=[]; $blocks=[]; $offset=0; $raw=null;
    $forbidden=['script','style','pre','code','textarea','select','option','button','form','svg','math','template','noscript'];
    $void=['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'];
    foreach ($matches[0] as [$tag,$start]) {
        if ($raw!==null && !preg_match('~^</'.preg_quote($raw,'~').'\s*>$~i',$tag)) continue;
        $text=substr($html,$offset,$start-$offset);
        if ($raw===null && $text!=='' && !array_intersect($stack,$forbidden)) {
            $decoded=html_entity_decode($text,ENT_QUOTES|ENT_HTML5,'UTF-8');
            if (trim($decoded)!=='') $blocks[]=['id'=>count($blocks),'tekst'=>$decoded,'element'=>end($stack)?:'tekst','offset'=>$offset,'length'=>strlen($text)];
        }
        if (preg_match('~^<(\/?)\s*([a-zA-Z0-9:-]+)~',$tag,$m)) {
            $name=strtolower($m[2]);
            if ($m[1]==='/') { $pos=array_search($name,array_reverse($stack,true),true); if($pos!==false)$stack=array_slice($stack,0,$pos); if($raw===$name)$raw=null; }
            elseif (!in_array($name,$void,true) && !str_ends_with($tag,'/>')) { $stack[]=$name; if(in_array($name,['script','style','textarea'],true))$raw=$name; }
        }
        $offset=$start+strlen($tag);
    }
    return $blocks;
}
function fw_tresci_zmien(string $html,array $changes): string {
    $blocks=fw_tresci_bloki($html); $replacements=[];
    foreach($changes as $id=>$text) {
        if(!ctype_digit((string)$id)||!isset($blocks[(int)$id])||!is_string($text)||mb_strlen($text)>12000||preg_match('/[\x00-\x08\x0B\x0C\x0E-\x1F]/',$text)) throw new InvalidArgumentException('Niepoprawny fragment tekstu.');
        $b=$blocks[(int)$id];$b['nowy']=htmlspecialchars($text,ENT_QUOTES|ENT_SUBSTITUTE|ENT_HTML5,'UTF-8');$replacements[]=$b;
    }
    usort($replacements,fn($a,$b)=>$b['offset']<=>$a['offset']);
    foreach($replacements as $b)$html=substr_replace($html,$b['nowy'],$b['offset'],$b['length']);
    return $html;
}
