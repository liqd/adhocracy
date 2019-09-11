select
	tc.measure_id,
	tc.measure_point,
	tc.call_count,
	(tc.time_function / tc.call_count) as time_per_call,
	tc.recursive_call_count,
	tc.time_total,
	tc.time_function,
	(tc.time_total - tc.time_function) as time_other,
	tc.code
from timings_calls as tc
where tc.measure_id = 411
order by
	tc.time_total desc,
	tc.time_function desc,
	time_other desc
limit 5;
