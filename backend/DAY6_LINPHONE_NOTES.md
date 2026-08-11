# Day 6 — Linphone free-SIP trunk notes

Working notes from getting Pooja's outbound reminder call (`src/outbound_caller.py`) running through **Linphone's free SIP service** (`sip.linphone.org`) instead of a paid Twilio Elastic SIP Trunk. Kept separate from `README.md` because this is troubleshooting log, not settled documentation — fold the working parts back into `README.md` once this path is fully confirmed end-to-end.

## Why Linphone instead of Twilio

Twilio's **Elastic SIP Trunking is a paid-only feature** — trial accounts get a hard `Error 20003: This feature is not available on a Trial account` the moment you try to create a trunk, via Console or the Twilio CLI. Upgrading needs a real top-up. Linphone's free SIP service (`sip.linphone.org`) was tried as a zero-cost alternative: create a free `username@sip.linphone.org` account in the Linphone app, and point a LiveKit outbound trunk at `sip.linphone.org` instead of a carrier.

**Important caveat:** `sip.linphone.org` is built for registered Linphone app users calling each other — it is not a general-purpose SIP trunk provider like Telnyx/Twilio/Plivo. LiveKit's own docs confirm LiveKit has no carrier connectivity of its own and always needs a real SIP trunk provider on the other end. This path is **not officially supported or documented by either LiveKit or Linphone** — everything below is reverse-engineered from error messages.

## Setup steps that worked

1. Install the Linphone app, run through the setup wizard, choose "Create account" → generates `username@sip.linphone.org` for free. Keep the app open and showing **registered/connected** — it must be actively registered to receive the call.
2. Create a LiveKit outbound trunk pointed at it (no Twilio-style numbers/auth needed since it's not PSTN):
   ```json
   {
     "trunk": {
       "name": "pooja-outbound-linphone",
       "address": "sip.linphone.org",
       "numbers": ["*"]
     }
   }
   ```
   ```bash
   lk sip outbound create outbound-trunk-linphone.json
   ```
   → returns a trunk id (`ST_...`). Set that as `SIP_OUTBOUND_TRUNK_ID` in `.env.local`.
3. Dial using the Linphone **username only** (not the full `user@sip.linphone.org`) as `--phone`:
   ```bash
   uv run python src/outbound_caller.py --name "..." --phone "linphoneusername" --scheme pmjdy --deadline "31 August"
   ```

## Bugs found and fixed along the way

- **`AttributeError: 'int' object has no attribute 'seconds'`** — `CreateSIPParticipantRequest.ringing_timeout` and `.max_call_duration` are protobuf `Duration` fields, not plain numbers. Fixed in `outbound_caller.py` by passing `datetime.timedelta(seconds=...)` instead of a raw int.
- **`invalid media codec: "opus/48000/2", expected: <name> or <name>/<sample-rate>`** — the `lk sip outbound update --codecs` flag takes `<name>` (for fixed-rate codecs like `PCMU`/`PCMA`) or `<name>/<sample-rate>` (for `opus`, no channel count) — not the SDP-style `opus/48000/2`. Correct form: `--codecs opus/48000`.

## Unresolved: `488 Not Acceptable Here`

The actual `CreateSIPParticipant` call consistently fails with:
```
twirp error unknown: INVITE failed: sip status: 488: Not acceptable here
```
Tried so far, no change in outcome:
- Widening codecs from LiveKit's defaults to an explicit `PCMU`, `PCMA`, `opus/48000` list.
- `--media-enc disable` (force plain RTP, no SRTP) — still 488.
- Next untried idea: `--media-enc allow` (let either side negotiate SRTP vs plain RTP) — plain RTP being forced when Linphone's client defaults to preferring/requiring encrypted media is a plausible cause.

**Most likely root cause:** `sip.linphone.org`'s proxy (Flexisip) is rejecting the SDP offer or the INVITE itself because it doesn't recognize LiveKit's SIP trunk as a legitimate peer/registered device — this would explain why the response is a clean protocol-level rejection rather than a timeout or auth challenge. Confirming this needs a real SIP trace (e.g. Wireshark, or Linphone's own in-app connection logs), which wasn't available in this debugging session.

## Fallback if this remains unresolved

Switch the trunk back to a real paid provider — Twilio (top-up required) or a cheaper alternative (Telnyx/Plivo, which typically have lower minimum top-ups than Twilio). No code changes needed either way: `outbound_caller.py` and `agent.py` are provider-agnostic, only `SIP_OUTBOUND_TRUNK_ID` and the trunk's own config change.
