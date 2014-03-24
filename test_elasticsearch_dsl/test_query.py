from elasticsearch_dsl import query

from pytest import raises

def test_match_to_dict():
    assert {"match": {"f": "value"}} == query.Match(f='value').to_dict()

def test_bool_to_dict():
    bool = query.Bool(must=[query.Match(f='value')], should=[])

    assert {"bool": {"must": [{"match": {"f": "value"}}]}} == bool.to_dict()

def test_bool_converts_its_init_args_to_queries():
    q = query.Bool(must=[{"match": {"f": "value"}}])

    assert len(q.must) == 1
    assert q.must[0] == query.Match(f='value')

def test_two_queries_make_a_bool():
    q1 = query.Match(f='value1')
    q2 = query.Match(message={"query": "this is a test", "opeartor": "and"})
    q = q1 + q2

    assert isinstance(q, query.Bool)
    assert [q1, q2] == q.must

def test_other_and_bool_appends_other_to_must():
    q1 = query.Match(f='value1')
    qb = query.Bool()

    q = q1 + qb
    assert q is qb
    assert q.must[0] is q1

def test_bool_and_other_appends_other_to_must():
    q1 = query.Match(f='value1')
    qb = query.Bool()

    q = qb + q1
    assert q is qb
    assert q.must[0] is q1

def test_two_bools_are_combined():
    q1 = query.Bool(must=[query.MatchAll(), query.Match(f=42)], should=[query.Match(g="v")])
    q2 = query.Bool(must=[query.Match(x=42)], should=[query.Match(g="v2")], must_not=[query.Match(title='value')])

    q = q1 + q2
    assert isinstance(q, query.Bool)
    assert q.must == [query.MatchAll(), query.Match(f=42), query.Match(x=42)]
    assert q.should == [query.Match(g="v"), query.Match(g="v2")]
    assert q.must_not == [query.Match(title='value')]

def test_query_and_query_creates_bool():
    q1 = query.Match(f=42)
    q2 = query.Match(g=47)

    q = q1 & q2
    assert isinstance(q, query.Bool)
    assert q.must == [q1, q2]

def test_match_all_and_query_equals_other():
    q1 = query.Match(f=42)
    q2 = query.MatchAll()

    q = q1 & q2
    assert q1 == q

def test_inverted_query_becomes_bool_with_must_not():
    q = query.Match(f=42)
    q = ~q

    assert q == query.Bool(must_not=[query.Match(f=42)])

def test_double_invert_returns_original_query():
    q = query.Match(f=42)

    assert q == ~~q

def test_bool_query_gets_inverted_internally():
    q = query.Bool(must_not=[query.Match(f=42)], must=[query.Match(g='v')])
    q = ~q

    assert q == query.Bool(must=[query.Match(f=42)], must_not=[query.Match(g='v')])

def test_match_all_or_something_is_match_all():
    q1 = query.MatchAll()
    q2 = query.Match(f=42)

    assert (q1 | q2) == query.MatchAll()
    assert (q2 | q1) == query.MatchAll()

def test_or_produces_bool_with_should():
    q1 = query.Match(f=42)
    q2 = query.Match(g='v')

    q = q1|q2
    assert q == query.Bool(should=[q1, q2])

def test_bool_with_only_should_will_append_another_query_with_or():
    qb = query.Bool(should=[query.Match(f='v')])
    q = query.Match(g=42)

    assert (q | qb) == query.Bool(should=[query.Match(f='v'), q])

def test_two_bool_queries_append_one_to_should_if_possible():
    q1 = query.Bool(should=[query.Match(f='v')])
    q2 = query.Bool(must=[query.Match(f='v')])

    assert (q1 | q2) == query.Bool(should=[query.Match(f='v'), query.Bool(must=[query.Match(f='v')])])
    q1 = query.Bool(should=[query.Match(f='v')])
    q2 = query.Bool(must=[query.Match(f='v')])

    assert (q2 | q1) == query.Bool(should=[query.Match(f='v'), query.Bool(must=[query.Match(f='v')])])

def test_queries_are_registered():
    assert 'match' in query.QueryMeta._classes
    assert query.QueryMeta._classes['match'] is query.Match

def test_defining_query_registers_it():
    class MyQuery(query.Query):
        name = 'my_query'

    assert 'my_query' in query.QueryMeta._classes
    assert query.QueryMeta._classes['my_query'] is MyQuery

def test_Q_passes_query_through():
    q = query.Match(f='value1')

    assert query.Q(q) is q

def test_Q_constructs_query_by_name():
    q = query.Q('match', f='value')

    assert isinstance(q, query.Match)
    assert {'f': 'value'} == q._params

def test_Q_constructs_simple_query_from_dict():
    q = query.Q({'match': {'f': 'value'}})

    assert isinstance(q, query.Match)
    assert {'f': 'value'} == q._params

def test_Q_constructs_compound_query_from_dict():
    q = query.Q(
        {
            "bool": {
                "must": [
                    {'match': {'f': 'value'}},
                ]
            }
        }
    )

    assert q == query.Bool(must=[query.Match(f='value')])

def test_Q_raises_error_when_passed_in_dict_and_params():
    with raises(Exception):
        query.Q({"match": {'f': 'value'}}, f='value')

def test_Q_raises_error_when_passed_in_query_and_params():
    q = query.Match(f='value1')

    with raises(Exception):
        query.Q(q, f='value')

def test_Q_raises_error_on_unknown_query():
    with raises(Exception):
        query.Q('not a query', f='value')

def test_match_all_plus_anything_is_anything():
    q = query.MatchAll()

    s = object()
    assert q+s is s
    assert s+q is s
