"""Local, deterministic CV text enhancer (no AI/API required).

Used as a fallback so the Enhance tab always returns visibly improved text
even when no Groq/OpenAI key is configured or the API call fails.
"""
import re
import textwrap


STRONG_VERBS = {
    'lead': 'led', 'manage': 'managed', 'work': 'worked', 'handle': 'handled',
    'make': 'built', 'do': 'delivered', 'get': 'achieved', 'help': 'supported',
    'responsible for': '',  # handled explicitly
}


def _clean(section: str, text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and ln.strip() != '•']
    return lines


def _action_improve(text: str) -> str:
    lines = _clean('', text)
    if not lines:
        return text
    out = []
    for ln in lines:
        # Capitalize start, ensure terminal period
        s = ln.strip().rstrip('.,;:')
        s = s[:1].upper() + s[1:]
        if not s.endswith('.'):
            s += '.'
        # Replace generic weak verbs / phrases
        lowered = s.lower()
        if lowered.startswith('responsible for'):
            rest = s[len('Responsible for'):].strip().capitalize()
            s = f'Owned and delivered on {rest}.'
        elif lowered.startswith('worked on'):
            rest = s[len('Worked on'):].strip().capitalize()
            s = f'Drove {rest} to completion.'.replace('Drove to completion.', 'Drove this work to completion.')
        elif lowered.startswith('helped'):
            rest = s[len('Helped'):].strip().capitalize()
            s = f'Contributed to {rest}.'
        elif lowered.startswith('made'):
            rest = s[len('Made'):].strip().capitalize()
            s = f'Built {rest}.'
        out.append(s)
    return '\n'.join(out)


def _action_grammar(text: str) -> str:
    # Basic spelling/casing/tidiness fixes that work offline.
    s = text.strip()
    s = re.sub(r'\s{2,}', ' ', s)
    s = re.sub(r'\s+([,.;:!?])', r'\1', s)
    s = re.sub(r'([a-z]) ,', r'\1,', s)
    # Capitalize start of each sentence
    sentences = re.split(r'(?<=[.!?])\s+', s)
    for i, sent in enumerate(sentences):
        if sent:
            sentences[i] = sent[0].upper() + sent[1:]
    return ' '.join(sentences)


def _action_tone(text: str) -> str:
    swap = {
        'team player': 'collaborative professional',
        'hard working': 'diligent',
        'good': 'strong',
        'great': 'exceptional',
        'a lot of': 'extensive',
        'lots of': 'extensive',
        'stuff': 'responsibilities',
        'really': '',
        'very ': '',
    }
    s = text
    for k, v in swap.items():
        s = re.sub(r'\b' + re.escape(k) + r'\b', v, s, flags=re.IGNORECASE)
    s = re.sub(r'\s{2,}', ' ', s).strip()
    return s


def _action_impact(text: str) -> str:
    lines = _clean('', text)
    if not lines:
        return text
    out = []
    for ln in lines:
        s = ln.strip().rstrip('.,;:')
        if s and s[0].isalpha() and not s[0].isupper() and not s.startswith('•'):
            s = s[0].upper() + s[1:]
        if not s.endswith('.'):
            s += '.'
        s = re.sub(r'\b(\w+)ed\b', r'\1ed', s)  # keep past tense
        out.append(s)
    return '\n'.join(out)


def _action_bullet(text: str) -> str:
    lines = _clean('', text)
    if not lines:
        return text
    out = []
    for ln in lines:
        s = ln.strip().lstrip('-•*').strip().rstrip('.')
        if s:
            s = s[:1].upper() + s[1:]
            out.append(f'• {s}')
    return '\n'.join(out)


def _action_summary(text: str) -> str:
    s = ' '.join(text.split())[:1200]
    # Extract a plain, factual first sentence if present
    parts = re.split(r'(?<=[.!?])\s+', s)
    core = parts[0] if parts else s
    return (
        f'Professional summary: {core[:1].upper() + core[1:]} '
        f'Bringing hands-on expertise backed by measurable results, I combine '
        f'technical depth with a track record of delivering projects end to end.'
    )


ACTIONS = {
    'improve': _action_improve,
    'grammar': _action_grammar,
    'tone': _action_tone,
    'impact': _action_impact,
    'bullet': _action_bullet,
    'summary': _action_summary,
}


def enhance_local(text: str, action: str = 'improve') -> str:
    """Return a rule-based enhancement for the given CV text."""
    fn = ACTIONS.get(action, ACTIONS['improve'])
    result = fn(text or '')
    result = result.strip()
    if not result:
        return (text or '').strip() or 'Provide text to enhance.'
    if action in ('bullet', 'improve') and result != (text or '').strip():
        return result
    # Never return identical output for improve/grammar/tone/impact
    if result == (text or '').strip():
        return _action_improve(text) or result
    return result
