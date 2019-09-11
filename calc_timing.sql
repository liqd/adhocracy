select
	t.measure_id, 
	t.measure_session,
	t.measure_point,
	t.call_count,
	(t.time_function / t.call_count) as time_per_call,
	t.recursive_call_count,
	t.time_total,
	t.time_function,
	(t.time_total - t.time_function) as time_other,
	t.code
from timings as t
order by
	t.time_total desc,
	t.time_function desc
limit 10;