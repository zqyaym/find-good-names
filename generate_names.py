#!/usr/bin/env python3
"""Deterministic name enumeration; Python 3 standard library only; no model calls."""
import argparse
import collections
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read(name):
    return json.loads((ROOT / 'data' / name).read_text(encoding='utf-8'))

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--min-usage', type=int, default=65)
    ap.add_argument('--max-rarity', type=int, default=1)
    ap.add_argument('--max-gender-bias', type=float, default=0.3)
    ap.add_argument('--preview', type=int, default=48)
    args = ap.parse_args()
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    entries = read('naming-dict.json')['characters']
    cn = read('cnchar-info.json')
    mapping = read('five-element.json')
    qi = read('wuxing.json')
    translated = dict(shui='水', jin='金', mu='木', huo='火', tu='土')
    by_char = collections.defaultdict(set)
    for element, counts in qi.items():
        for chars in counts.values():
            for ch in chars:
                by_char[ch].add(translated[element])
    full = {'水': [], '金': []}
    audit = []
    for entry in entries:
        e = dict(entry)
        ch = e['char']
        value = cn.get(ch, '')
        primary = mapping.get(value[1], '') if len(value) > 1 else ''
        secondary = sorted(by_char.get(ch, set()))
        e['cncharElement'] = primary
        e['qimingElements'] = secondary
        e['agreement'] = primary in ('水','金') and secondary == [primary]
        if primary in ('水','金') or any(v in ('水','金') for v in secondary):
            audit.append(e)
        if e['agreement']:
            full[primary].append(e)
    for group in full.values():
        group.sort(key=lambda e:e['char'])
    save(out / 'character_audit.json', audit)
    save(out / 'conflicts_or_missing.json', [e for e in audit if not e['agreement']])
    # All combinations remain available even when the optional semantic filter rejects a character.
    with (out / 'all_combinations.txt').open('w', encoding='utf-8') as f:
        for a,b in itertools.product(full['水'], full['金']):
            f.write('朱'+a['char']+b['char']+'\n')

    def eligible(e):
        return (e.get('namingUsage') is not None and e['namingUsage'] >= args.min_usage
                and e.get('rarityLevel') is not None and e['rarityLevel'] <= args.max_rarity
                and e.get('sentiment') == 'positive'
                and e.get('genderBias',0) <= args.max_gender_bias
                and bool(e.get('pinyinPlain')))
    pools = {k:[e for e in v if eligible(e)] for k,v in full.items()}
    save(out / 'filtered_character_pools.json', pools)
    # Small explicit Mandarin homophone list, never a comprehensive safety guarantee.
    blocked = {'wu xin':'无心','wu qing':'无情','wu chi':'无耻','wu shi':'无视',
               'hai ren':'害人','fan ren':'烦人','liu chan':'流产','mei qian':'没钱',
               'wu chang':'无常','wu sheng':'无声','zi sha':'自杀','zi jin':'自尽',
               'zhu fei':'猪肺','zhu pi':'猪皮','zhu rou':'猪肉'}
    candidates, rejected = [], []
    for a,b in itertools.product(pools['水'],pools['金']):
        name = '朱'+a['char']+b['char']
        p = ['zhu', a['pinyinPlain'], b['pinyinPlain']]
        reasons=[]
        if len(set(name))<3: reasons.append('字形重复')
        if p[0]==p[1] or p[1]==p[2]: reasons.append('相邻音节相同（忽略声调）')
        for pair in (' '.join(p[:2]),' '.join(p[1:])):
            if pair in blocked: reasons.append('小型谐音表命中：'+blocked[pair])
        if reasons:
            rejected.append({'name':name,'reasons':reasons});continue
        tones = [1,a['toneLevel'],b['toneLevel']]
        # Transparent heuristic, NOT a name quality, luck, or population-frequency metric.
        score = (a['namingUsage']+b['namingUsage'])/2
        score += 4*(tones[0]!=tones[1])+4*(tones[1]!=tones[2])
        score += 3*(len(set(tones))==3)
        score += 4*max(0,-a.get('genderBias',0))+4*max(0,-b.get('genderBias',0))
        row={'name':name,'pinyin':'zhū '+a['pinyin']+' '+b['pinyin'],
             'tones':'-'.join(map(str,tones)), 'heuristicScore':round(score,2),
             'waterChar':a['char'],'metalChar':b['char'],
             'waterGloss':a.get('meaningBrief'),'metalGloss':b.get('meaningBrief'),
             'waterRadical':a['radical'],'metalRadical':b['radical'],
             'styleTags':sorted(set(a.get('styleTags',[])+b.get('styleTags',[]))),
             'review':'仍需人工朗读、核对多音字与方言谐音；未查真实重名率'}
        candidates.append(row)
    candidates.sort(key=lambda r:(-r['heuristicScore'],r['name']))
    save(out/'filtered_candidates.json',candidates)
    save(out/'rejected_pairs.json',rejected)
    # Greedy diversity: discourage repeated first/second characters, deterministic tie break.
    counts=collections.Counter();selected=[];remaining=list(candidates)
    while remaining and len(selected)<args.preview:
        row=min(remaining,key=lambda r:(-(r['heuristicScore']-10*counts[r['waterChar']]-10*counts[r['metalChar']]),r['name']))
        remaining.remove(row);selected.append(row)
        counts[row['waterChar']]+=1;counts[row['metalChar']]+=1
    save(out/'preview.json',selected)
    stats={'dictionaryCharacters':len(entries),'agreementWater':len(full['水']),
           'agreementMetal':len(full['金']),'allCombinations':len(full['水'])*len(full['金']),
           'filteredWater':len(pools['水']),'filteredMetal':len(pools['金']),
           'filteredCartesian':len(pools['水'])*len(pools['金']),
           'rejectedPairs':len(rejected),'filteredCandidates':len(candidates),
           'previewCount':len(selected),'parameters':vars(args)}
    save(out/'stats.json',stats)
    lines=['# 朱姓「水＋金」姓名候选','',
           '组合由 Python 穷举；五行按 cnchar 与 qiming 两份表一致标注选取。两库未证明相互独立，一致不等于权威认证。',
           '下面是程序分散选字后的预览，不是人工精选，也不是姓名吉凶排名。',
           '字义、适用度、风格标签来自第三方 AI 离线标注，供初筛；完整组合未使用这些分数。','',
           '| 姓名 | 普通话 | 声调 | 水字释义（待核） | 金字释义（待核） |',
           '|---|---|---|---|---|']
    for r in selected:
        lines.append('| '+' | '.join(str(r[k]).replace('|','／') for k in ('name','pinyin','tones','waterGloss','metalGloss'))+' |')
    lines += ['', '## 运行统计','', '```json',json.dumps(stats,ensure_ascii=False,indent=2),'```']
    (out/'姓名候选预览.md').write_text('\n'.join(lines),encoding='utf-8')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').glob('*.json')}
    save(out/'source_hashes.json',hashes)
    assert len(set(r['name'] for r in candidates)) == len(candidates)
    assert all(r['waterChar'] in {e['char'] for e in full['水']} and r['metalChar'] in {e['char'] for e in full['金']} for r in candidates)
    print(json.dumps(stats,ensure_ascii=False,indent=2))
    print('预览前24名：')
    for r in selected[:24]:print(r['name'],r['pinyin'],r['heuristicScore'])

if __name__=='__main__':main()
