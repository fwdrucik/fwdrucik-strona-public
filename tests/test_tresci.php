<?php
require __DIR__.'/../api/_tresci.php';
$source='<section><h1>Tytuł &amp; znak</h1><p class="x">Pierwszy <strong>ważny</strong> tekst.</p><script>const x="<p>zły</p>";</script><pre><code>kod</code></pre><form><p>formularz</p></form><!-- komentarz --><p>koniec</p></section>';
$b=fw_tresci_bloki($source);
assert(count($b)===5);
assert($b[0]['tekst']==='Tytuł & znak');
$out=fw_tresci_zmien($source,[0=>'<img src=x onerror=alert(1)>',2=>'nowy',4=>'']);
assert(str_contains($out,'&lt;img src=x onerror=alert(1)&gt;'));
assert(str_contains($out,'<strong>nowy</strong>'));
assert(str_contains($out,'<script>const x="<p>zły</p>";</script>'));
assert(str_contains($out,'<pre><code>kod</code></pre><form><p>formularz</p></form>'));
assert(str_contains($out,'<p></p></section>'));
try{fw_tresci_zmien($source,[999=>'bad']);throw new RuntimeException('Expected invalid id');}catch(InvalidArgumentException $e){}
try{fw_tresci_zmien($source,[0=>[1]]);throw new RuntimeException('Expected invalid type');}catch(InvalidArgumentException $e){}
echo "CMS parser: 9 assertions passed\n";
