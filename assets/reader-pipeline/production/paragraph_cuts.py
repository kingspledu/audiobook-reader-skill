"""Plan browser-only silence trims from the actual boundary paragraphs."""
def boundary(segment, end=False):
 refs=segment.get('word_map',[])
 if not refs or any(ref is None for ref in refs):return None
 return refs[-1 if end else 0][0].split('-s')[0]

def plan(segments,index,level,original_duration,sample_rate=24000):
 current=segments[index]
 same_before=index>0 and boundary(current) is not None and boundary(current)==boundary(segments[index-1],True)
 same_after=index+1<len(segments) and boundary(current,True) is not None and boundary(current,True)==boundary(segments[index+1])
 start=level['trim_start']/sample_rate if same_before else 0
 end=min(original_duration,level['trim_end']/sample_rate) if same_after else original_duration
 if not 0<=start<end<=original_duration:raise ValueError('Invalid paragraph cut bounds')
 return start,end
