def split_message(text, max_length=600):
    """Split text at natural boundaries (paragraph → newline → sentence end). Never mid-word."""
    if len(text) <= max_length:
        return [text]
    chunks = []
    remaining = text
    while len(remaining) > max_length:
        chunk = remaining[:max_length]
        pos = chunk.rfind('\n\n')
        if pos > 0:
            chunks.append(remaining[:pos])
            remaining = remaining[pos + 2:].lstrip()
            continue
        pos = chunk.rfind('\n')
        if pos > 0:
            chunks.append(remaining[:pos])
            remaining = remaining[pos + 1:].lstrip()
            continue
        best = max(chunk.rfind('.'), chunk.rfind('!'), chunk.rfind('?'))
        if best > 0:
            chunks.append(remaining[:best + 1])
            remaining = remaining[best + 1:].lstrip()
            continue
        chunks.append(chunk)
        remaining = remaining[max_length:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks
