import json
import re
import shutil
import subprocess

import pytest

from crw.render import _TEMPLATE, render_workbench


def test_embedded_report_roundtrips_without_executable_script_termination(tmp_path):
    hostile = '</script><script>window.INJECTED=true</script><img src=x onerror=alert(1)>&\u2028\u2029'
    report = {"meta": {"version": "test", "note": hostile}, "customers": []}
    target = tmp_path / "nested" / "workbench.html"
    render_workbench(report, target)
    html = target.read_text()
    payload = re.search(r'<script id="workbench-data" type="application/json">(.*?)</script>', html, re.S).group(1)
    assert json.loads(payload) == report
    assert "<" not in payload and ">" not in payload and "&" not in payload
    assert "\u2028" not in payload and "\u2029" not in payload
    assert '<script>window.INJECTED' not in html
    assert '__REPORT_JSON__' not in html


def test_render_rejects_nonfinite_json_and_missing_metadata(tmp_path):
    with pytest.raises(ValueError):
        render_workbench({"meta": {}, "score": float("nan")}, tmp_path / "invalid.html")
    with pytest.raises(ValueError, match="meta"):
        render_workbench({}, tmp_path / "invalid.html")
    assert not (tmp_path / "invalid.html").exists()


def test_standalone_interface_contains_all_labeled_views_and_no_remote_dependencies():
    assert len(re.findall(r'role="tabpanel"', _TEMPLATE)) == 8
    assert len(re.findall(r'role="tab"', _TEMPLATE)) == 8
    assert 'aria-label="Research views"' in _TEMPLATE
    assert 'id="workbench-data" type="application/json"' in _TEMPLATE
    assert not re.search(r'<(?:script|link|img)[^>]+(?:src|href)=["\']https?://', _TEMPLATE)
    assert 'fetch(' not in _TEMPLATE
    assert 'XMLHttpRequest' not in _TEMPLATE
    assert '@import' not in _TEMPLATE
    assert 'Synthetic research edition' in _TEMPLATE
    assert 'This is not a random evaluation sample.' in _TEMPLATE


def _node():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is unavailable for JavaScript syntax/helper execution")
    return node


def _helpers():
    return _TEMPLATE.split('/* PURE_HELPERS_START */', 1)[1].split('/* PURE_HELPERS_END */', 1)[0]


def test_javascript_syntax_is_valid(tmp_path):
    scripts = re.findall(r'<script>(.*?)</script>', _TEMPLATE, re.S)
    assert len(scripts) == 1
    source = tmp_path / "viewer.js"
    source.write_text(scripts[0])
    result = subprocess.run([_node(), "--check", str(source)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_threshold_analysis_preserves_required_gates_and_recomputes_only_band_crossing():
    source = _helpers() + '''
const cases=[
 [{lower_bound:12,upper_bound:27,gates:[]},30,60,"LOW"],
 [{lower_bound:15.75,upper_bound:30,gates:["missing_evidence_crosses_band"]},30,60,"REVIEW_REQUIRED"],
 [{lower_bound:15.75,upper_bound:30,gates:["missing_evidence_crosses_band"]},40,70,"LOW"],
 [{lower_bound:15,upper_bound:20,gates:["required_evidence_missing"]},30,60,"REVIEW_REQUIRED"],
 [{lower_bound:15,upper_bound:20,gates:["history_completeness_not_confirmed"]},30,60,"REVIEW_REQUIRED"],
 [{lower_bound:30,upper_bound:30,gates:[]},30,60,"MODERATE"],
 [{lower_bound:60,upper_bound:60,gates:[]},30,60,"HIGH"],
 [{lower_bound:29,upper_bound:31,gates:[]},30,60,"REVIEW_REQUIRED"]
];
for (const [a,m,h,expected] of cases){if(thresholdOutcome(a,m,h)!==expected)throw Error(JSON.stringify({a,m,h,expected}));}
for(const args of [[30,30],[-1,60],[50,101],[NaN,50]]){
 let rejected=false;try{thresholdOutcome({lower_bound:0,upper_bound:1,gates:[]},...args);}catch(e){rejected=true;}
 if(!rejected)throw Error("invalid thresholds accepted");
}
if(escapeHTML('<img onerror="attack">&')!=='&lt;img onerror=&quot;attack&quot;&gt;&amp;')throw Error('HTML escaping failed');
console.log('threshold cases passed');
'''
    result = subprocess.run([_node(), "--eval", source], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "threshold cases passed" in result.stdout


def _run_render_function(expression, report=None):
    script = re.findall(r'<script>(.*?)</script>', _TEMPLATE, re.S)[0]
    declarations = script.split('try{initialize();}', 1)[0]
    harness = '''
const document={getElementById:()=>({textContent:process.argv[1]})};
'''
    source = harness + declarations + '\nconsole.log(' + expression + ');'
    result = subprocess.run(
        [_node(), '--eval', source, json.dumps(report or {'meta': {}, 'customers': []})],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_missing_evidence_stress_displays_null_score_widening_bounds_and_paired_denominator():
    from crw.features import build_features
    from crw.policy import reference_policy
    from crw.stress import stress_portfolio
    from crw.synthetic import DEFAULT_AS_OF, iter_portfolio

    customer, events = next(iter_portfolio(1, 80, seed=42))
    features = build_features(customer, events, DEFAULT_AS_OF)
    result = stress_portfolio([(customer.customer_id, features)], reference_policy(), DEFAULT_AS_OF)
    experiment = next(row for row in result['experiments'] if row['id'] == 'ownership_unknown')
    example = experiment['examples'][0]
    assert example['after_score'] is None
    assert example['after_bounds'][1] > example['after_bounds'][0]
    assert experiment['complete_paired_n'] == 0
    html = _run_render_function('renderPolicyStressExperiments(DATA.stress.experiments)',
                                {'meta': {}, 'customers': [], 'stress': {'experiments': [experiment]}})
    assert 'Mean lower-bound change' in html
    assert 'negative lower-bound change does not establish reduced risk' in html
    assert 'Unavailable (null)' in html
    assert 'Undefined (no paired complete scores)' in html
    assert 'Paired complete denominator: 0 of 1 examples' in html
    assert 'Required Evidence Missing' in html
    assert f"{example['after_bounds'][0]:,.2f} to {example['after_bounds'][1]:,.2f}" in html
    assert 'Mean index delta' not in html and 'Index delta' not in html


def test_frozen_model_integrity_requires_explicit_unchanged_fit_and_hash_evidence():
    source = _helpers() + '''
const integrity={model_refit:false,preprocessing_refit:false,threshold_reselected:false,
source_rows_sha256_before:'rows',source_rows_sha256_after:'rows',
threshold_selection_sha256_before:'threshold',threshold_selection_sha256_after:'threshold',
training_metadata_sha256_before:'model',training_metadata_sha256_after:'model'};
if(!frozenIntegrityPreserved({integrity}))throw Error('valid fixed-model evidence rejected');
for(const field of ['model_refit','preprocessing_refit','threshold_reselected']){
 if(frozenIntegrityPreserved({integrity:{...integrity,[field]:true}}))throw Error('refit accepted');
}
for(const key of ['source_rows','threshold_selection','training_metadata']){
 if(frozenIntegrityPreserved({integrity:{...integrity,[key+'_sha256_after']:'changed'}}))throw Error('changed hash accepted');
}
if(frozenIntegrityPreserved({integrity:{}}))throw Error('absent integrity accepted');
console.log('frozen integrity checked');
'''
    result = subprocess.run([_node(), '--eval', source], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_frozen_model_view_renders_paired_workload_metrics_and_integrity():
    integrity = {'model_refit': False, 'preprocessing_refit': False, 'threshold_reselected': False}
    for field in ('source_rows', 'threshold_selection', 'training_metadata'):
        integrity[field + '_sha256_before'] = field
        integrity[field + '_sha256_after'] = field
    model = {
        'n': 10, 'threshold': .375, 'integrity': integrity,
        'baseline_metrics': {'roc_auc': {'value': .75}, 'brier': {'value': .15}},
        'scenarios': [{
            'name': 'missing_input', 'metrics': {'roc_auc': {'value': .625}, 'brier': {'value': .2}},
            'workload': {'baseline_review_count': 2, 'stressed_review_count': 4},
            'paired_changes': {'mean_absolute_probability_change': .025, 'label_flips': 0},
        }],
    }
    research = {'frozen_model_stress': [{'seed': 7, 'models': {'logistic': model}}]}
    html = _run_render_function('renderFrozenStress(DATA.research)', {'meta': {}, 'research': research})
    assert 'Fixed-model stress without threshold retuning' in html
    assert '1 paired stress cases across 1 seeds' in html
    assert '0.3750' in html
    assert '0.7500 / 0.6250' in html
    assert '0.1500 / 0.2000' in html
    assert '2 / 4' in html
    assert 'Preserved' in html
    model['integrity']['threshold_reselected'] = True
    invalid = _run_render_function('renderFrozenStress(DATA.research)', {'meta': {}, 'research': research})
    assert 'Review required' in invalid
