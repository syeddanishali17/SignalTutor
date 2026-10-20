"""Registered answer functions for parameterised problems.

Problem YAML refers to these by name (``answer: {fn: bridge.full_output_mag}``).
Content strings are never evaluated: every computation lives here, in code,
and is covered by tests.

Each function receives the problem's parameter dict *as shown to the learner*
(e.g. ``R_k`` in kΩ, ``eps_ue`` in µε) and returns the answer in SI base units.
"""

from __future__ import annotations

from typing import Callable

from tutor.sim import amplifiers, bridge, circuits

Params = dict[str, float]
AnswerFn = Callable[[Params], float]

ANSWERS: dict[str, AnswerFn] = {}
MISCONCEPTION_VALUES: dict[str, AnswerFn] = {}


def answer(name: str):
    def deco(fn: AnswerFn) -> AnswerFn:
        if name in ANSWERS:
            raise KeyError(f"Duplicate answer function {name!r}")
        ANSWERS[name] = fn
        return fn

    return deco


def misconception_value(name: str):
    def deco(fn: AnswerFn) -> AnswerFn:
        if name in MISCONCEPTION_VALUES:
            raise KeyError(f"Duplicate misconception function {name!r}")
        MISCONCEPTION_VALUES[name] = fn
        return fn

    return deco


# --- foundations -----------------------------------------------------------------


@answer("ohm.current")
def _ohm_current(p: Params) -> float:
    return circuits.ohm_current(p["V"], p["R_k"] * 1e3)


@answer("divider.vout")
def _divider_vout(p: Params) -> float:
    return circuits.divider(p["Vin"], p["R1_k"] * 1e3, p["R2_k"] * 1e3).Vout


@misconception_value("divider.top_resistor_used")
def _divider_swapped(p: Params) -> float:
    return p["Vin"] * p["R1_k"] / (p["R1_k"] + p["R2_k"])


@answer("divider.current_mA_to_A")
def _divider_current(p: Params) -> float:
    return circuits.divider(p["Vin"], p["R1_k"] * 1e3, p["R2_k"] * 1e3).I


@answer("kcl.remaining")
def _kcl_remaining(p: Params) -> float:
    return circuits.kcl_remaining([p["I_in_mA"] * 1e-3], [p["I_out_mA"] * 1e-3])


@misconception_value("kcl.added")
def _kcl_added(p: Params) -> float:
    return (p["I_in_mA"] + p["I_out_mA"]) * 1e-3


@answer("reference.relabel_top")
def _relabel_top(p: Params) -> float:
    pots = {"top": p["V_top"], "mid": p["V_mid"], "bottom": 0.0}
    return circuits.relabel_potentials(pots, "mid")["top"]


@misconception_value("reference.unchanged")
def _relabel_unchanged(p: Params) -> float:
    return p["V_top"]


# --- Wheatstone bridge -------------------------------------------------------------


@answer("bridge.full_output_mag")
def _full_mag(p: Params) -> float:
    x = bridge.dR_rel_from_strain(p["G"], p["eps_ue"] * 1e-6)
    return abs(bridge.full_output(p["Vb"], x))


@misconception_value("bridge.full_with_raw_microstrain")
def _full_raw_ue(p: Params) -> float:
    return abs(bridge.full_output(p["Vb"], p["G"] * p["eps_ue"]))


@answer("bridge.quarter_output_mag")
def _quarter_mag(p: Params) -> float:
    return abs(bridge.quarter_exact(p["V0"], p["dR"] / p["R"]))


@answer("bridge.quarter_output_signed")
def _quarter_signed(p: Params) -> float:
    return bridge.quarter_exact(p["V0"], p["dR"] / p["R"])


@answer("bridge.gauge_dR")
def _gauge_dR(p: Params) -> float:
    return bridge.dR_rel_from_strain(p["G"], p["eps_ue"] * 1e-6) * p["R"]


@misconception_value("bridge.gauge_dR_raw_microstrain")
def _gauge_dR_raw(p: Params) -> float:
    return p["G"] * p["eps_ue"] * p["R"]


@answer("bridge.h_eps_v")
def _h_eps_v(p: Params) -> float:
    return p["G"] * p["Vb"]


@answer("bridge.approx_rel_error")
def _approx_err(p: Params) -> float:
    return bridge.quarter_approx_rel_error(p["x_pct"] / 100)


@answer("bridge.midpoint_balanced")
def _midpoint(p: Params) -> float:
    return bridge.simulate("balanced", p["V0"], 1e3, 0.0).V1


@misconception_value("zero")
def _zero(p: Params) -> float:
    return 0.0


# --- amplifiers ----------------------------------------------------------------------


@answer("opamp.open_loop")
def _open_loop(p: Params) -> float:
    return amplifiers.open_loop(p["vd_uV"] * 1e-6, 0.0, p["A_k"] * 1e3, p["Vs"])


@misconception_value("opamp.no_rails")
def _open_loop_no_rails(p: Params) -> float:
    return p["A_k"] * 1e3 * p["vd_uV"] * 1e-6


@answer("noninv.gain")
def _noninv_gain(p: Params) -> float:
    return amplifiers.noninv_gain_ideal(p["R1_k"], p["R2_k"])


@misconception_value("noninv.ratio_only")
def _noninv_ratio_only(p: Params) -> float:
    return p["R1_k"] / p["R2_k"]


@misconception_value("noninv.swapped")
def _noninv_swapped(p: Params) -> float:
    return 1.0 + p["R2_k"] / p["R1_k"]


@answer("noninv.bridge_node_out")
def _noninv_bridge(p: Params) -> float:
    return amplifiers.clamp(p["G"] * p["V2"], p["Vs"])


@misconception_value("noninv.bridge_no_rails")
def _noninv_bridge_no_rails(p: Params) -> float:
    return p["G"] * p["V2"]


@misconception_value("noninv.only_signal")
def _noninv_only_signal(p: Params) -> float:
    return p["G"] * p["dV_mV"] * 1e-3


@answer("diffamp.vout")
def _diffamp_vout(p: Params) -> float:
    return p["k"] * p["dV_mV"] * 1e-3


@answer("diffamp.cm_leak")
def _diffamp_cm_leak(p: Params) -> float:
    k, m = p["k"], p["mis_pct"] / 100
    _, a_cm = amplifiers.diffamp_gains(1e3, k * 1e3, 1e3, k * 1e3 * (1 + m))
    return abs(a_cm) * p["Vcm"]


@answer("ina.gain")
def _ina_gain(p: Params) -> float:
    return amplifiers.ina_gain_ideal(p["R1_k"], p["R2_k"])


@misconception_value("ina.forgot_two")
def _ina_forgot_two(p: Params) -> float:
    return 1.0 + p["R2_k"] / p["R1_k"]


@answer("ina.r1_for_gain")
def _ina_r1(p: Params) -> float:
    return amplifiers.ina_r1_for_gain(p["G"], p["R2_k"] * 1e3)


@misconception_value("ina.r1_forgot_two")
def _ina_r1_forgot_two(p: Params) -> float:
    return p["R2_k"] * 1e3 / (p["G"] - 1.0)


@answer("ina.vout")
def _ina_vout(p: Params) -> float:
    return amplifiers.ina_gain_ideal(p["R1_k"], p["R2_k"]) * p["dV_mV"] * 1e-3


@misconception_value("ina.vout_forgot_two")
def _ina_vout_forgot_two(p: Params) -> float:
    return (1.0 + p["R2_k"] / p["R1_k"]) * p["dV_mV"] * 1e-3
