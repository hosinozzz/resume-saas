// viewer-request: resumeai.jp (apex) → https://www.resumeai.jp 301リダイレクト
function handler(event) {
    var host = event.request.headers.host.value;
    if (host === 'resumeai.jp') {
        return {
            statusCode: 301,
            statusDescription: 'Moved Permanently',
            headers: {
                location: { value: 'https://www.resumeai.jp' + event.request.uri }
            }
        };
    }
    return event.request;
}
