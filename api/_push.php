<?php
declare(strict_types=1);
require_once __DIR__ . '/_lib.php';

/** Server-only FCM HTTP v1. Never return this result (device tokens) to a public client. */
function fw_push_http(string $url, array $headers, string $body): array {
    if (!function_exists('curl_init')) return [0, []];
    $allowed = $url === 'https://oauth2.googleapis.com/token' || preg_match('~^https://fcm\.googleapis\.com/v1/projects/[a-z][a-z0-9-]{4,62}/messages:send$~D', $url);
    if (!$allowed) return [0, []];
    $response = ''; $retryAfter = 0;
    $ch = curl_init($url);
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_POSTFIELDS => $body,
        CURLOPT_HTTPHEADER => $headers, CURLOPT_CONNECTTIMEOUT => 3, CURLOPT_TIMEOUT => 8,
        CURLOPT_HEADERFUNCTION => static function ($ch, string $line) use (&$retryAfter): int {
            if (stripos($line, 'Retry-After:') === 0) {
                $value = trim(substr($line, 12));
                $seconds = ctype_digit($value) ? (int) $value : max(0, (int) strtotime($value) - time());
                $retryAfter = max($retryAfter, $seconds);
            }
            return strlen($line);
        },
        CURLOPT_FOLLOWLOCATION => false, CURLOPT_PROTOCOLS => CURLPROTO_HTTPS,
        CURLOPT_SSL_VERIFYPEER => true, CURLOPT_SSL_VERIFYHOST => 2,
        CURLOPT_WRITEFUNCTION => static function ($ch, string $chunk) use (&$response): int {
            if (strlen($response) + strlen($chunk) > 32768) return 0;
            $response .= $chunk; return strlen($chunk);
        }]);
    $ok = curl_exec($ch); $status = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    $parsed = json_decode($response, true);
    return [$ok === false ? 0 : $status, is_array($parsed) ? $parsed : [], $retryAfter];
}

function fw_push_service_account(): ?array {
    $cfg = fw_konfiguracja();
    $file = (string) ($cfg['fcm_service_account_file'] ?? getenv('FCM_SERVICE_ACCOUNT_FILE') ?: '');
    if ($file === '' || !is_file($file)) return null;
    $real = realpath($file);
    // Configuration must point outside both the site tree and actual document root.
    foreach ([dirname(__DIR__), (string) ($_SERVER['DOCUMENT_ROOT'] ?? '')] as $root) {
        $root = $root !== '' ? realpath($root) : false;
        if ($real && $root && str_starts_with(strtolower(str_replace('\\', '/', $real)), rtrim(strtolower(str_replace('\\', '/', $root)), '/') . '/')) return null;
    }
    if (!$real || filesize($real) > 32768 || !is_readable($real)) return null;
    $raw = @file_get_contents($real, false, null, 0, 32769);
    $account = is_string($raw) ? json_decode($raw, true) : null;
    if (!is_array($account) || ($account['type'] ?? '') !== 'service_account'
        || !preg_match('/^[a-z][a-z0-9-]{4,62}$/D', (string) ($account['project_id'] ?? ''))
        || !filter_var($account['client_email'] ?? '', FILTER_VALIDATE_EMAIL)
        || !is_string($account['private_key'] ?? null)) return null;
    return $account;
}

function fw_push_access_token(array $account): ?string {
    static $cache = [];
    $key = hash('sha256', $account['client_email'] . $account['private_key']);
    if (($cache[$key]['expires'] ?? 0) > time() + 60) return $cache[$key]['token'];
    if (!function_exists('openssl_sign')) return null;
    $b64 = static fn(string $s): string => rtrim(strtr(base64_encode($s), '+/', '-_'), '=');
    $now = time();
    $jwt = $b64('{"alg":"RS256","typ":"JWT"}') . '.' . $b64((string) json_encode([
        'iss' => $account['client_email'], 'scope' => 'https://www.googleapis.com/auth/firebase.messaging',
        'aud' => 'https://oauth2.googleapis.com/token', 'iat' => $now - 30, 'exp' => $now + 3300]));
    $signature = '';
    if (!@openssl_sign($jwt, $signature, $account['private_key'], OPENSSL_ALGO_SHA256)) return null;
    [$status, $result] = fw_push_http('https://oauth2.googleapis.com/token', ['Content-Type: application/x-www-form-urlencoded'],
        http_build_query(['grant_type' => 'urn:ietf:params:oauth:grant-type:jwt-bearer', 'assertion' => $jwt . '.' . $b64($signature)]));
    $token = $result['access_token'] ?? null;
    if ($status !== 200 || !is_string($token) || $token === '' || strlen($token) > 8192 || preg_match('/[\r\n]/', $token)) return null;
    $cache[$key] = ['token' => $token, 'expires' => $now + min(3600, max(0, (int) ($result['expires_in'] ?? 0)))];
    return $token;
}

/** Every message gets a unique notification tag; retries reuse it to avoid duplicate tray entries. */
function fw_push_payload(string $token, int $conversationId, int $messageId): array {
    return ['message'=>['token'=>$token,
        'data'=>['typ'=>'czat','type'=>'czat','rozmowa'=>(string)$conversationId,'wiadomosc'=>(string)$messageId,'title'=>'F.W. DRUCIK — czat','body'=>'Nowa wiadomość klienta na stronie. Otwórz rozmowę.'],
        'android'=>['priority'=>'HIGH','ttl'=>'86400s']]];
}

function fw_push_wynik(int $status, array $body): string {
    if ($status >= 200 && $status < 300 && is_string($body['name'] ?? null)) return 'sent';
    foreach (($body['error']['details'] ?? []) as $detail) {
        if (is_array($detail) && ($detail['@type'] ?? '') === 'type.googleapis.com/google.firebase.fcm.v1.FcmError'
            && ($detail['errorCode'] ?? '') === 'UNREGISTERED') return 'invalid';
    }
    return 'retry';
}

function fw_push_wyslij(array $tokens, int $conversationId, int $messageId): array {
    $tokens = array_values(array_unique(array_filter($tokens, static fn($t): bool => is_string($t) && strlen($t) >= 20 && strlen($t) <= 4096 && !preg_match('/[\x00-\x20\x7f]/', $t))));
    $out = ['sent' => 0, 'invalid_tokens' => [], 'retry_tokens' => [], 'retry_after' => 60, 'error' => null];
    if (!$tokens) return $out;
    if ($conversationId < 1 || $messageId < 1) return array_replace($out, ['retry_tokens' => $tokens, 'error' => 'invalid_message']);
    $account = fw_push_service_account();
    if (!$account) return array_replace($out, ['retry_tokens' => $tokens, 'error' => 'not_configured']);
    $access = fw_push_access_token($account);
    if (!$access) return array_replace($out, ['retry_tokens' => $tokens, 'error' => 'oauth_unavailable']);
    // Bound a worker invocation; durable queue must retain the unattempted remainder.
    $deadline = microtime(true) + 20;
    foreach ($tokens as $i => $token) {
        if ($i >= 20 || microtime(true) > $deadline) {
            $out['retry_tokens'] = array_merge($out['retry_tokens'], array_slice($tokens, $i));
            $out['error'] = 'batch_limit'; break;
        }
        $response = fw_push_http('https://fcm.googleapis.com/v1/projects/' . $account['project_id'] . '/messages:send',
            ['Content-Type: application/json', 'Authorization: Bearer ' . $access], (string) json_encode(fw_push_payload($token, $conversationId, $messageId), JSON_UNESCAPED_UNICODE));
        [$status, $body] = $response;
        $out['retry_after'] = max($out['retry_after'], (int) ($response[2] ?? 0));
        $kind = fw_push_wynik($status, $body);
        if ($kind === 'sent') $out['sent']++;
        elseif ($kind === 'invalid') $out['invalid_tokens'][] = $token;
        else { $out['retry_tokens'][] = $token; $out['error'] = 'delivery_unavailable'; }
    }
    return $out;
}
