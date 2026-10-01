# Protocol: initial evidence

This reference is partial. The complete C→S/S→C catalog must be derived from
the executable. Names below follow existing code for convenience; EP8 layouts
are not presumed compatible.

| Opcode | Observed/analyzed use | Status |
| --- | --- | --- |
| `0xA301` | World handshake | Received locally; full specification pending |
| `0x0101` | S→C character list | Reader `0x57C790`; additional writer unvalidated |
| `0x0104` | Character selection | First selection/entry observed; repetition pending |
| `0x0105` | S→C character details | Sent on first entry; field audit pending |
| `0x0106` | S→C initial inventory | 34-byte record identified; first entry confirmed |
| `0x0107` | Logout | Received/responded; complete return to selection pending |
| `0x0109` | S→C faction/mode limit | Observed; UI state effects need documentation |
| `0x010B` | Quickbar | Client reader indicates count plus 5-byte records; compare directions |
| `0x0201` | C→S map entry | Received after loading in a local session |
| `0xB106` | World-start-related packet | Received; historical `CHANGE_ENCRYPTION` name, full semantics unknown |

## Initial inventory `0x0106`

Client reader: `0x57CC60`. Payload begins with a one-byte count; each record
contains 34 bytes:

| Record offset | Length | Field |
| --- | --- | --- |
| 0 | 1 | Bag |
| 1 | 1 | Slot |
| 2 | 1 | Type |
| 3 | 1 | TypeId |
| 4 | 2 | Little-endian quality |
| 6 | 6 | Six one-byte gem identifiers |
| 12 | 1 | Count |
| 13 | 21 | Fixed craft name with terminator |

The reader allocates six bags with 24 slots. The observed fault at `0x57CE8D`
followed interpretation of larger EP8 records. The experimental writer rejects
out-of-range bags/slots and gems not representable in one byte. Other inventory
packets still need mapping.

## Character list `0x0101`

Reader `0x57C790` consumes slot/ID and, for nonzero IDs, basic data, eight
equipment types and eight equipment IDs, followed by 21 bytes. The additional
writer interprets those bytes as a 19-byte name and historical deletion/rename
flags. Verify flag semantics through UI flows. Six extra bytes occur when
equipment type at index 7 is nonzero. EP8's 17-element arrays and additional
fields do not match this observed reader.

The additional writer has not been compiled or exercised. Missing second
selection after logout alone does not prove that this packet causes the failure.

## Encryption and states

Current backend code uses AES during selection and expanded XOR keys for
World responses. Quickbar sending is linked to a client mode change; logout
dispatch calls `0x4015A0`. Document key derivation, counters, buffers, ordering,
and transition effects before modifying sessions. A complete state contract
for this sample is not yet available.

Every new packet needs a specification ID, direction, offset layout, variants/
limits, client builder/reader, and static/runtime evidence. Encrypted bytes
and bench responses alone cannot establish field semantics.
