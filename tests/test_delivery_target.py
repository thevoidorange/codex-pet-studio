from __future__ import annotations

import json
import re
import struct
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET_PATH = ROOT / "delivery-targets" / "codex-pet-v2.json"
TARGET_SCHEMA_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "pet-studio"
    / "schemas"
    / "delivery-target.schema.json"
)
PREVIEW_SCHEMA_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "pet-studio"
    / "schemas"
    / "preview-config.schema.json"
)
ADAPTER_PATH = ROOT / "previewer" / "target-data.js"
EXAMPLE_ATLAS_PATH = (
    ROOT / "previewer" / "sample-assets" / "v002" / "spritesheet.png"
)


def paeth_predictor(left: int, above: int, upper_left: int) -> int:
    prediction = left + above - upper_left
    distance_left = abs(prediction - left)
    distance_above = abs(prediction - above)
    distance_upper_left = abs(prediction - upper_left)
    if distance_left <= distance_above and distance_left <= distance_upper_left:
        return left
    if distance_above <= distance_upper_left:
        return above
    return upper_left


def decode_rgba_alpha(path: Path) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AssertionError(f"{path} is not a PNG")
    offset = 8
    ihdr = None
    idat_parts: list[bytes] = []
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            ihdr = payload
        elif chunk_type == b"IDAT":
            idat_parts.append(payload)
        elif chunk_type == b"IEND":
            break
    if ihdr is None or not idat_parts:
        raise AssertionError(f"{path} is missing PNG image data")
    width, height, depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB",
        ihdr,
    )
    if (depth, color_type, compression, filtering, interlace) != (8, 6, 0, 0, 0):
        raise AssertionError(f"{path} must be an 8-bit non-interlaced RGBA PNG")
    bytes_per_pixel = 4
    row_bytes = width * bytes_per_pixel
    raw = zlib.decompress(b"".join(idat_parts))
    if len(raw) != height * (row_bytes + 1):
        raise AssertionError(f"{path} has unexpected scanline data")
    previous = bytearray(row_bytes)
    alpha = bytearray(width * height)
    raw_offset = 0
    for row_index in range(height):
        filter_type = raw[raw_offset]
        raw_offset += 1
        encoded = raw[raw_offset : raw_offset + row_bytes]
        raw_offset += row_bytes
        decoded = bytearray(row_bytes)
        for index, encoded_byte in enumerate(encoded):
            left = decoded[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            above = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                predictor = paeth_predictor(left, above, upper_left)
            else:
                raise AssertionError(f"{path} uses unsupported filter {filter_type}")
            decoded[index] = (encoded_byte + predictor) & 0xFF
        alpha[row_index * width : (row_index + 1) * width] = decoded[3::4]
        previous = decoded
    return width, height, bytes(alpha)


class DeliveryTargetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.target = json.loads(TARGET_PATH.read_text(encoding="utf-8"))

    def test_canonical_codex_pet_v2_contract_is_complete_and_consistent(self) -> None:
        target = self.target
        self.assertEqual(1, target["schemaVersion"])
        self.assertEqual("codex-pet-v2", target["id"])
        self.assertGreaterEqual(target["revision"], 1)
        self.assertTrue(TARGET_SCHEMA_PATH.is_file())
        self.assertEqual(
            "../.agents/skills/pet-studio/schemas/delivery-target.schema.json",
            target["$schema"],
        )

        package = target["package"]
        self.assertEqual("pet.json", package["manifestFile"])
        self.assertEqual(
            ".agents/skills/pet-studio/schemas/pet-v2.schema.json",
            package["manifestSchema"],
        )
        self.assertEqual(2, package["spriteVersionNumber"])
        self.assertEqual(["png", "webp"], package["spritesheetFormats"])
        self.assertTrue((ROOT / package["manifestSchema"]).is_file())

        atlas = target["atlas"]
        self.assertEqual(
            {
                "columns": 8,
                "rows": 11,
                "cellWidthPx": 192,
                "cellHeightPx": 208,
            },
            atlas,
        )
        self.assertEqual(1536, atlas["columns"] * atlas["cellWidthPx"])
        self.assertEqual(2288, atlas["rows"] * atlas["cellHeightPx"])

        expected_states = [
            ("idle", 0, [280, 110, 110, 140, 140, 320]),
            ("running-right", 1, [120, 120, 120, 120, 120, 120, 120, 220]),
            ("running-left", 2, [120, 120, 120, 120, 120, 120, 120, 220]),
            ("waving", 3, [140, 140, 140, 280]),
            ("jumping", 4, [140, 140, 140, 140, 280]),
            ("failed", 5, [140, 140, 140, 140, 140, 140, 140, 240]),
            ("waiting", 6, [150, 150, 150, 150, 150, 260]),
            ("running", 7, [120, 120, 120, 120, 120, 220]),
            ("review", 8, [150, 150, 150, 150, 150, 280]),
        ]
        observed_states = [
            (
                state["id"],
                state["row"],
                state["durationsMs"],
            )
            for state in target["states"]
        ]
        self.assertEqual(expected_states, observed_states)
        self.assertEqual(
            [0] * len(target["states"]),
            [state["firstColumn"] for state in target["states"]],
        )
        self.assertEqual(
            len(target["states"]),
            len({state["id"] for state in target["states"]}),
        )
        self.assertEqual(
            len(target["states"]),
            len({state["row"] for state in target["states"]}),
        )
        for state in target["states"]:
            self.assertLess(state["row"], atlas["rows"])
            self.assertLessEqual(
                state["firstColumn"] + len(state["durationsMs"]),
                atlas["columns"],
            )
            self.assertTrue(all(duration > 0 for duration in state["durationsMs"]))

        runtime = target["runtime"]
        self.assertEqual("codex-client", runtime["owner"])
        self.assertEqual("idle", runtime["idleStateId"])
        self.assertEqual(6, runtime["idleDurationMultiplier"])
        self.assertEqual(3, runtime["actionLoops"])
        self.assertEqual("idle", runtime["actionReturnStateId"])

        directions = target["lookDirections"]
        self.assertEqual("screen-clockwise-from-up", directions["coordinateSystem"])
        self.assertIs(True, directions["clockwise"])
        self.assertEqual("idle", directions["neutralStateId"])
        self.assertEqual(16, len(directions["slots"]))
        self.assertEqual(
            [index * 22.5 for index in range(16)],
            [slot["degree"] for slot in directions["slots"]],
        )
        self.assertEqual(
            [(9, column) for column in range(8)]
            + [(10, column) for column in range(8)],
            [(slot["row"], slot["column"]) for slot in directions["slots"]],
        )
        state_slots = {
            (state["row"], column)
            for state in target["states"]
            for column in range(
                state["firstColumn"],
                state["firstColumn"] + len(state["durationsMs"]),
            )
        }
        look_slots = {
            (slot["row"], slot["column"]) for slot in directions["slots"]
        }
        self.assertTrue(state_slots.isdisjoint(look_slots))

        self.assertEqual(
            {
                "owner": "codex-client-setting",
                "minimumPx": 80,
                "maximumPx": 224,
            },
            target["display"],
        )

    def test_checked_in_previewer_adapter_exactly_matches_canonical_contract(self) -> None:
        adapter = ADAPTER_PATH.read_text(encoding="utf-8")
        expected = (
            "// Generated from the canonical Delivery Target contract.\n"
            "// Run `studio.py target sync` after intentionally revising that contract.\n"
            "window.PET_DELIVERY_TARGET = "
            + json.dumps(self.target, ensure_ascii=False, indent=2, sort_keys=True)
            + ";\n"
        )
        self.assertEqual(expected, adapter)
        match = re.fullmatch(
            r"// Generated from the canonical Delivery Target contract\.\n"
            r"// Run `studio\.py target sync` after intentionally revising that contract\.\n"
            r"window\.PET_DELIVERY_TARGET = (.*);\n",
            adapter,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        self.assertEqual(self.target, json.loads(match.group(1)))

    def test_bundled_example_uses_only_target_declared_atlas_slots(self) -> None:
        atlas = self.target["atlas"]
        width, height, alpha = decode_rgba_alpha(EXAMPLE_ATLAS_PATH)
        self.assertEqual(
            (
                atlas["columns"] * atlas["cellWidthPx"],
                atlas["rows"] * atlas["cellHeightPx"],
            ),
            (width, height),
        )
        used_slots = {
            (state["row"], column)
            for state in self.target["states"]
            for column in range(
                state["firstColumn"],
                state["firstColumn"] + len(state["durationsMs"]),
            )
        }
        used_slots.update(
            (slot["row"], slot["column"])
            for slot in self.target["lookDirections"]["slots"]
        )
        cell_width = atlas["cellWidthPx"]
        cell_height = atlas["cellHeightPx"]
        for row in range(atlas["rows"]):
            for column in range(atlas["columns"]):
                visible = any(
                    any(
                        alpha[
                            (row * cell_height + y) * width
                            + column * cell_width :
                            (row * cell_height + y) * width
                            + (column + 1) * cell_width
                        ]
                    )
                    for y in range(cell_height)
                )
                with self.subTest(row=row, column=column):
                    self.assertEqual((row, column) in used_slots, visible)

    def test_preview_schema_is_target_neutral(self) -> None:
        schema = json.loads(PREVIEW_SCHEMA_PATH.read_text(encoding="utf-8"))
        target_ref = schema["properties"]["deliveryTarget"]
        self.assertEqual(["id", "revision"], target_ref["required"])
        self.assertEqual(1, target_ref["properties"]["revision"]["minimum"])

        frame_group = schema["$defs"]["frameTakeGroup"]
        self.assertEqual(
            ["stateId", "frameIndex", "takes"],
            frame_group["required"],
        )
        self.assertEqual("string", frame_group["properties"]["stateId"]["type"])
        self.assertNotIn("enum", frame_group["properties"]["stateId"])
        self.assertNotIn("const", frame_group["properties"]["stateId"])
        self.assertEqual(0, frame_group["properties"]["frameIndex"]["minimum"])
        self.assertNotIn("maximum", frame_group["properties"]["frameIndex"])
        self.assertNotIn("oneOf", frame_group)

        atlas_slot = schema["$defs"]["atlasSlot"]["properties"]
        self.assertEqual(0, atlas_slot["row"]["minimum"])
        self.assertEqual(0, atlas_slot["column"]["minimum"])
        self.assertNotIn("maximum", atlas_slot["row"])
        self.assertNotIn("maximum", atlas_slot["column"])

        schema_text = PREVIEW_SCHEMA_PATH.read_text(encoding="utf-8")
        for state in self.target["states"]:
            self.assertNotIn(f'"const": "{state["id"]}"', schema_text)

    def test_delivery_target_schema_declares_the_contract_sections(self) -> None:
        schema = json.loads(TARGET_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "schemaVersion",
                "revision",
                "id",
                "displayName",
                "verifiedAgainst",
                "package",
                "atlas",
                "runtime",
                "states",
                "lookDirections",
                "display",
            },
            set(schema["required"]),
        )
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
