# Candle Lighting Scheduler Lambda

This lambda is responsible of running every Friday at a fixed time, and then it creates 2 new schedules, 
it calculates the time 5 and 10 minutes before the candle lighting time, and creates an appropriate eventbridge rule schedule with those times.