from Server.Regiment import *
from Server.Vision.Court import Court

def make_lesson(court: Court):
    rule = Regiment(Rule(HitType.SERVE), Rule(HitType.HIT))
    stationary_hit = Regiment(
        StationaryTarget(HitType.HIT, court.A),
        StationaryTarget(HitType.HIT, court.A),
        StationaryTarget(HitType.HIT, court.A),
        StationaryTarget(HitType.HIT, court.A),
        StationaryTarget(HitType.HIT, court.A),)
    pattern = MovePattern(court.C, court.D)
    moving_hit = Regiment(
        MovingTarget(HitType.HIT, pattern),
        MovingTarget(HitType.HIT, pattern),
        MovingTarget(HitType.HIT, pattern),
        MovingTarget(HitType.HIT, pattern),
        MovingTarget(HitType.HIT, pattern)
    )

    return deque([rule, stationary_hit, moving_hit])