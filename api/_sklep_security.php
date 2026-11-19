<?php
declare(strict_types=1);

if (basename((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === '_sklep_security.php') {
    http_response_code(404);
    exit;
}

function fw_json_ld(array $value): string
{
    return json_encode($value, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES
        | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_THROW_ON_ERROR);
}

/** Public Allegro links only. Invalid legacy values become a local-page fallback. */
function fw_allegro_url(?string $url): ?string
{
    if ($url === null || $url === '' || strlen($url) > 2048
        || preg_match('/[\x00-\x20\x7f<>"\'\\\\]/', rawurldecode($url))) {
        return null;
    }
    $p = parse_url($url);
    if (!$p || !filter_var($url, FILTER_VALIDATE_URL) || ($p['scheme'] ?? '') !== 'https'
        || isset($p['user']) || isset($p['pass']) || (isset($p['port']) && $p['port'] !== 443)) {
        return null;
    }
    $host = strtolower($p['host'] ?? '');
    if (!preg_match('/^(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)*(?:allegro\.pl|allegrolokalnie\.pl)$/D', $host)) {
        return null;
    }
    return $url;
}

/** Resolve once and pin cURL to a public IP: no proxy, redirects or TLS bypass. */
function fw_allegro_import_options(string $url, ?callable $resolve = null): ?array
{
    if (fw_allegro_url($url) === null) { return null; }
    $host = strtolower((string) parse_url($url, PHP_URL_HOST));
    $resolve ??= static fn($name) => dns_get_record($name, DNS_A | DNS_AAAA);
    try { $records = $resolve($host); } catch (Throwable $e) { return null; }
    if (!is_array($records) || !$records) { return null; }
    $ips = [];
    foreach ($records as $record) {
        $ip = $record['ip'] ?? $record['ipv6'] ?? '';
        if (!filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_GLOBAL_RANGE)
            || str_starts_with(strtolower($ip), '::ffff:')
            || str_starts_with(strtolower($ip), 'ff')
            || (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4) && (int) explode('.', $ip)[0] >= 224)) { return null; }
        $ips[] = $ip;
    }
    $ip = $ips[0];
    return [CURLOPT_URL => $url, CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => false, CURLOPT_MAXREDIRS => 0,
        CURLOPT_SSL_VERIFYPEER => true, CURLOPT_SSL_VERIFYHOST => 2,
        CURLOPT_PROTOCOLS => CURLPROTO_HTTPS, CURLOPT_REDIR_PROTOCOLS => CURLPROTO_HTTPS,
        CURLOPT_PROXY => '', CURLOPT_CONNECTTIMEOUT => 4, CURLOPT_TIMEOUT => 8,
        CURLOPT_RESOLVE => [$host . ':443:' . (str_contains($ip, ':') ? '[' . $ip . ']' : $ip)],
        CURLOPT_USERAGENT => FW_ALLEGRO_USER_AGENT];
}

/** Keep a small HTML vocabulary, never attributes or executable/imported markup. */
function fw_sklep_opis_html(string $text): string
{
    $doc = new DOMDocument();
    $previous = libxml_use_internal_errors(true);
    try { $doc->loadHTML('<?xml encoding="UTF-8"><body>' . $text . '</body>', LIBXML_NONET); }
    finally { libxml_clear_errors(); libxml_use_internal_errors($previous); }
    $render = function (DOMNode $node) use (&$render): string {
        if ($node instanceof DOMText) { return htmlspecialchars($node->textContent, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
        if (!($node instanceof DOMElement)) { return ''; }
        $tag = strtolower($node->tagName);
        if (in_array($tag, ['script','style','iframe','object','svg','template','head'], true)) { return ''; }
        $inside = '';
        foreach ($node->childNodes as $child) { $inside .= $render($child); }
        if ($tag === 'br') { return '<br>'; }
        return in_array($tag, ['p','b','strong','i','em','ul','ol','li','h1','h2','h3','h4','table','tr','th','td'], true)
            ? '<' . $tag . '>' . $inside . '</' . $tag . '>' : $inside;
    };
    $body = $doc->getElementsByTagName('body')->item(0);
    return $body ? $render($body) : '';
}
