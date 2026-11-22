"""Fail-closed sentence metadata validation; no automatic speaker confirmation."""
import re
def validate_sentence(segment):
    for key in ('sentence_id','paragraph_id'):
        if not isinstance(segment.get(key),str) or not segment[key].strip():raise ValueError('Missing '+key)
    if any(not isinstance(segment.get(k),list) for k in ('context_before','context_after')):raise ValueError('Context sentence IDs required')
    review=segment.get('review',{})
    for key in ('attribution','classification','performance','speaker_pass','cue_pass','continuity_pass'):
        if review.get(key)!='confirmed':raise ValueError('User review required: '+key)
    for key in ('evidence','sentence_boundary_evidence'):
        if not review.get(key,'').strip():raise ValueError('Missing review evidence: '+key)
    p=segment.get('performance',{})
    if not p.get('sentence_persona','').strip():raise ValueError('Sentence persona required')
    if not isinstance(p.get('cue_links'),list):raise ValueError('Cue links must be explicit')
    for k in ('addressee_intention','outer_inner','pivot','prosody','nonverbal','continuation'):
        if not p.get('design',{}).get(k,'').strip():raise ValueError('Sentence acting design required: '+k)
    for cue in p['cue_links']:
        if cue.get('target_sentence_id')!=segment['sentence_id'] or any(not cue.get(k) for k in ('source_sentence_id','cue_text','instruction')):raise ValueError('Invalid cue target/evidence')
    # Conservative assistance only: quoted punctuation is included, decimals are excluded.
    text=segment.get('text','')
    if re.search(r'[!?。！？](?:[!?。！？]|["”’\'])*\s+\S|(?<!\d)\.(?:["”’\'])*\s+\S',text):raise ValueError('Multiple sentence boundaries: split and review')
    return True
