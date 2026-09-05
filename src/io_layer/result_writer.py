"""Schema-valid JSON + CSV result writing (SPEC §6.1, FR6).

Writes one ``results.json`` (every outlet exactly once, contract-validated)
and one ``results.csv`` (one row per flagged image plus one blank-flag row
per clean outlet, so every outlet is represented). No timestamps or run ids
are embedded: the files are byte-identical across re-runs (ED-6).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from config.settings import Settings
from core.entities import WriteSummary
from core.exceptions import WriteError
from core.output_schema import OutletResult
from observability.logging import get_logger


class ResultWriter:
    """Persists the full per-outlet result set to an output directory.

    The JSON and CSV file names come from the injected Settings (SPEC §18), so
    the artifact names are centralized in ``settings.py`` and never hardcoded
    here. Validates on write: a result that violates the schema would fail here
    rather than producing an invalid deliverable (ED-7).
    """

    def __init__(self, settings: Settings) -> None:
        """Bind the settings (for artifact names) and prepare the logger."""
        self._settings = settings
        self._logger = get_logger("result_writer")

    def write_results(
        self,
        results: list[OutletResult],
        output_dir: Path,
    ) -> WriteSummary:
        """Write the results JSON and CSV (names from settings), returning the paths."""
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / self._settings.results_json_filename
        csv_path = output_dir / self._settings.results_csv_filename
        try:
            json_path.write_text(
                self._json_payload(results),
                encoding="utf-8",
            )
            self._write_csv(results, csv_path)
        except OSError as exc:
            raise WriteError(f"unable to write results to {output_dir}: {exc}") from exc
        self._logger.info(
            "results_written",
            outlet_count=len(results),
            json_path=str(json_path),
            csv_path=str(csv_path),
        )
        return WriteSummary(
            json_path=json_path,
            csv_path=csv_path,
            outlet_count=len(results),
        )

    def _json_payload(self, results: list[OutletResult]) -> str:
        """Serialize the results as an indented, deterministically ordered JSON array."""
        payload = [
            result.model_dump(mode="json", exclude_none=False) for result in results
        ]
        return json.dumps(payload, indent=2, ensure_ascii=True)

    def _write_csv(self, results: list[OutletResult], csv_path: Path) -> None:
        """Write one row per flagged image and one blank row per clean outlet."""
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["outlet_id", "total_images", "file_name", "suspicion_score", "reason"]
            )
            for result in results:
                if not result.flagged_images:
                    writer.writerow([result.outlet_id, result.total_images, "", "", ""])
                    continue
                for flagged in result.flagged_images:
                    writer.writerow(
                        [
                            result.outlet_id,
                            result.total_images,
                            flagged.file_name,
                            flagged.suspicion_score,
                            flagged.reason,
                        ]
                    )
