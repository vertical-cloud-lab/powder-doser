"""Actuator drivers: hobby servos, the DRV8871 tapper, the backlight and
the accessory stepper on a Tic T500 (cam or stage profile).

They take machine.PWM / machine.Pin / tic.TicSerial objects (or the fakes
in sim_hw), so the CPython tests run the same code.
"""

import units


class Servo:
    """50 Hz hobby servo. Not driven until the first write (see config)."""

    def __init__(self, pwm, min_us, max_us, min_deg, max_deg, rest_deg,
                 period_us=20000):
        self.pwm = pwm
        self.min_us, self.max_us = min_us, max_us
        self.min_deg, self.max_deg = min_deg, max_deg
        self.period_us = period_us
        self.angle = float(rest_deg)
        self.driven = False

    def clamp(self, deg):
        return units.clamp(deg, self.min_deg, self.max_deg)

    def write(self, deg):
        deg = self.clamp(deg)
        self.pwm.duty_u16(units.servo_duty_u16(deg, self.min_deg, self.max_deg,
                                               self.min_us, self.max_us, self.period_us))
        self.angle = deg
        self.driven = True

    def release(self):
        self.pwm.duty_u16(0)
        self.driven = False


class Tapper:
    """DRV8871: IN1 PWM, IN2 low = forward drive; both low = coast."""

    def __init__(self, in1_pwm, in2_pin, duty=1.0):
        self.in1 = in1_pwm
        self.in2 = in2_pin
        self.duty = duty
        self.is_on = False
        self.count = 0
        self.off()

    def on(self):
        self.in2.value(0)
        self.in1.duty_u16(int(units.clamp(self.duty, 0.0, 1.0) * 65535))
        self.is_on = True
        self.count += 1

    def off(self):
        self.in1.duty_u16(0)
        self.is_on = False


class Light:
    def __init__(self, pwm):
        self.pwm = pwm
        self.level = 0
        self.set(0)

    def set(self, pct):
        pct = units.clamp(int(round(pct)), 0, 100)
        self.pwm.duty_u16(int(pct * 65535 // 100))
        self.level = pct


class TicMotor:
    """The accessory stepper. Positions are in microsteps of the physical
    axis (cam turns or stage travel); ``dir`` flips the sign at the Tic."""

    def __init__(self, tic, clock, name, profile, set_current=True):
        self.tic = tic
        self.clock = clock
        self.readback = None        # unknown until the first read
        self.select(name, profile, set_current)

    # -- profile -----------------------------------------------------------
    def select(self, name, p, set_current=True):
        self.name = name
        self.p = p
        self.usteps_rev = units.usteps_per_rev(p["full_steps"], p["microsteps"])
        self.dir = 1 if p.get("dir", 1) >= 0 else -1
        t = self.tic
        t.exit_safe_start()
        t.clear_driver_error()
        t.set_step_mode(p["microsteps"])
        self.current_code = None
        if set_current:
            self.current_code = units.tic_t500_current_code(p["current_ma"])
            t.set_current_limit_code(self.current_code)
        if "lead_mm" in p:
            accel = units.mm_s_to_usteps_s(p["accel_mm_s2"], p["lead_mm"], self.usteps_rev)
            speed = units.mm_s_to_usteps_s(p["default_mm_s"], p["lead_mm"], self.usteps_rev)
        else:
            accel = p["accel_rev_s2"] * self.usteps_rev
            speed = units.rpm_to_usteps_s(60.0, self.usteps_rev)
        self.accel = accel
        t.set_max_accel(units.usteps_s2_to_tic(accel))
        t.set_max_decel(units.usteps_s2_to_tic(accel))
        self.set_speed(speed)
        t.halt_and_set_position(0)
        self.pos = 0                # shadow position (usteps)
        self.target = 0
        self.energized = False
        t.deenergize()

    # -- units -------------------------------------------------------------
    def mm(self, usteps):
        return units.usteps_to_mm(usteps, self.p["lead_mm"], self.usteps_rev)

    def usteps(self, mm):
        return units.mm_to_usteps(mm, self.p["lead_mm"], self.usteps_rev)

    def mm_s(self, v_mm_s):
        return units.mm_s_to_usteps_s(v_mm_s, self.p["lead_mm"], self.usteps_rev)

    # -- motion --------------------------------------------------------------
    def set_speed(self, usteps_s):
        self.speed = max(1.0, float(usteps_s))
        self.tic.set_max_speed(units.usteps_s_to_tic(self.speed))

    def energize(self):
        self.tic.energize()
        self.tic.exit_safe_start()
        self.energized = True

    def deenergize(self):
        self.tic.deenergize()
        self.energized = False

    def move_to(self, target):
        if not self.energized:
            self.energize()
        self.target = int(target)
        self.tic.set_target_position(self.dir * self.target)
        return units.move_time_s(self.target - self.pos, self.speed, self.accel)

    def run_velocity(self, usteps_s):
        """Spin at a signed speed. The Tic caps velocity at its max speed,
        so raise that first (a slow UCS move may have left it at 0.1 mm/s)."""
        if not self.energized:
            self.energize()
        self.set_speed(abs(usteps_s))
        self.tic.set_target_velocity(self.dir * units.usteps_s_to_tic(usteps_s))

    def halt_set(self, pos=0):
        self.tic.halt_and_set_position(self.dir * int(pos))
        self.pos = int(pos)
        self.target = int(pos)

    def halt_hold(self):
        self.tic.halt_and_hold()
        p = self.read_position()
        if p is not None:
            self.pos = p
            self.target = p

    def keepalive(self):
        self.tic.reset_command_timeout()

    def read_position(self):
        """Position from the Tic (needs Tic TX -> GP5), else None."""
        if self.readback is False:
            return None
        p = self.tic.current_position()
        if p is None:
            if self.readback is None:
                self.readback = False
            return None
        self.readback = True
        self.pos = self.dir * p
        return self.pos
