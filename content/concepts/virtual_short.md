The two golden rules for analysing op-amp circuits with **negative feedback**:

1. $V_+ = V_-$ — the **virtual short** (if $V_+$ is grounded, $V_-$ is a **virtual ground**).
2. No current flows into either input.

They are not a property of the op-amp alone: they are the *result* of negative feedback plus a huge gain. They fail when

* there is no feedback or the feedback is positive,
* the output **saturates** at a rail — then the op-amp can no longer correct, and $V_+ - V_-$ can be volts.

"Short" because the voltages are equal as if wired together; "virtual" because no current flows between them.
