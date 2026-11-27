# used in shader_manager.py and also on analysis

from collections import Counter
from collections.abc import Iterable
from pathlib import Path
import statistics
from typing import Literal

exclude_list = [
    # --- intro related ---
    "intro_gateway_with_lensflare.txt",
    "intro_gateway_with_lensflare_rainbow_1.txt",
    "intro_gateway_with_lensflare_rainbow_2.txt",
    "intro_gateway_with_lensflare_magenta.txt",
    "intro_light_sprites.txt",
    "star_lens_flare.txt",
    "alien_orb.txt",
    "bioscanner.txt",
    "dof_dna.txt",
    "dof_dna_rainbow.txt",
    "bioscanner_rainbow.txt",
    "3d_grid_rainbow.txt",
    "3d_grid.txt",
    "specular_bands.txt",
    "kaleidoscope_2.txt",
    "__hyperjump.txt",
    "ethereal_magma.txt",
    "shining_hope_star.txt",
    "shining_hope_star_rainbow.txt",
    "matrix_twirl_rainbow.txt",
    "matrixy_rainbow_vortex.txt",
    "rainbow_circle.txt",
    "crack_monochrome.txt",
    "crack_monochrome_glitch.txt",
    "kaleidoscope_1.txt",
    "bw_dot_rotation.txt",
    "bw_transformation.txt",

    # --- main_seq related ---
    "chromatic_test.txt",
    "cubic_lens_dist.txt",
    "ephemeral_fx.txt",
    "ripple_effect.txt",
    "singular_effect_ease_in_out_1.txt",
    "singular_effect_ease_in_out_2.txt",
    "singular_effect_ease_in_out_2_rainbow.txt",
    "video_ascii_art.txt",
    "video_ascii_art_bioscanner.txt",
    "video_ascii_art_bioscanner_magenta.txt",
    "video_ascii_art_layered.txt",
    "video_chromatic_barrel.txt",
    "video_dither.txt",
    "video_flownoise.txt",
    "video_flownoise_bioscanner.txt",
    "video_flownoise_diagonal.txt",
    "video_flownoise_diagonal_layered.txt",
    "video_flownoise_half_horiz.txt",
    "video_flownoise_half_vert.txt",
    "video_flownoise_layered.txt",
    "video_glitchy_glitch.txt",
    "video_glitch_1.txt",
    "video_glitch_2.txt",
    "video_glitch_matrix.txt",
    "video_glitch_matrix_half_horiz.txt",
    "video_glitch_matrix_half_vert.txt",
    "video_glitch_matrix_layered.txt",
    "video_glitch_matrix_magenta.txt",
    "video_glitch_matrix_magenta_half_horiz.txt",
    "video_glitch_matrix_magenta_half_vert.txt",
    "video_glitch_matrix_magenta_layered.txt",
    "video_glitch_matrix_magenta_layered_half_horiz.txt",
    "video_glitch_matrix_magenta_layered_half_vert.txt",
    "video_glitch_rgb_shift_1.txt",
    "video_glitch_rgb_shift_2.txt",
    "video_glitch_ripple.txt",
    "video_glitch_ripple_box_rot.txt",
    "video_pixelated_fx.txt",
    "video_play_normal.txt",
    "video_something_fx.txt",
]

class AssetUsageAnalyzer:
    """Reads an asset log file, counts occurrences, and analyzes usage statistics."""

    def __init__(
        self,
        filepath: str | Path | None = None,
        exclude: Iterable[str] | None = None,
    ) -> None:
        self.counts: Counter[str] = Counter()
        self.exclude: set[str] = (
            {item.strip() for item in exclude} if exclude else set()
        )
        if filepath is not None:
            self.load_file(filepath)

    def load_file(
        self,
        filepath: str | Path,
        ignore_empty: bool = True,
        exclude: Iterable[str] | None = None,
    ) -> None:
        """
        Read asset names from a file and count occurrences,
        skipping any assets in the exclude list.
        """
        path = Path(filepath)
        self.counts.clear()

        # If an exclude list is passed directly to load_file, update self.exclude
        if exclude is not None:
            self.exclude = {item.strip() for item in exclude}

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                asset = line.strip()
                if ignore_empty and not asset:
                    continue
                if asset in self.exclude:
                    continue
                self.counts[asset] += 1

    def get_min_max(self) -> tuple[int, int]:
        """Return (min_count, max_count) among all counted assets."""
        if not self.counts:
            raise ValueError("No asset data loaded.")
        values = self.counts.values()
        return min(values), max(values)

#    def get_threshold(
#        self, method: Literal["midpoint", "mean", "median"] = "midpoint"
#    ) -> float:
#        """
#        Calculate the dividing threshold.
#        - 'midpoint': (min + max) / 2  (the half-way line between least and most used)
#        - 'mean': arithmetic average of all asset counts
#        - 'median': median of all asset counts
#        """
#        if not self.counts:
#            raise ValueError("No asset data loaded.")
#
#        values = list(self.counts.values())
#        if method == "midpoint":
#            min_val, max_val = min(values), max(values)
#            return (min_val + max_val) / 2
#        elif method == "mean":
#            return statistics.mean(values)
#        elif method == "median":
#            return statistics.median(values)
#        else:
#            raise ValueError(f"Unknown threshold method: {method}")

    def get_threshold(
        self,
        method: Literal["midpoint", "mean", "median"] = "midpoint",
        ratio: float = 0.5,
    ) -> float:
        """
        Calculate the dividing threshold at a given ratio (default 0.5 = half-point).
        Pass e.g. ratio=1/3 or ratio=0.33 for a one-third threshold.

        - 'midpoint': linear position between min and max at `ratio`
        - 'mean': interpolated relative to min/mean/max (equals arithmetic mean at 0.5)
        - 'median': the `ratio`-th quantile/percentile (equals median at 0.5)
        """
        if not self.counts:
            raise ValueError("No asset data loaded.")
        if not 0.0 <= ratio <= 1.0:
            raise ValueError("ratio must be between 0.0 and 1.0.")

        values = list(self.counts.values())

        if method == "midpoint":
            min_val, max_val = min(values), max(values)
            return min_val + ratio * (max_val - min_val)

        elif method == "mean":
            mean_val = statistics.mean(values)
            if ratio <= 0.5:
                min_val = min(values)
                return min_val + (ratio / 0.5) * (mean_val - min_val)
            else:
                max_val = max(values)
                return mean_val + ((ratio - 0.5) / 0.5) * (max_val - mean_val)

        elif method == "median":
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            if n == 1:
                return float(sorted_vals[0])
            pos = ratio * (n - 1)
            lower = int(pos)
            upper = min(lower + 1, n - 1)
            weight = pos - lower
            return sorted_vals[lower] * (1 - weight) + sorted_vals[upper] * weight

        else:
            raise ValueError(f"Unknown threshold method: {method}")

    def get_least_used(
        self,
        method: Literal["midpoint", "mean", "median"] = "midpoint",
        inclusive: bool = True,
    ) -> list[str]:
        """
        Return a list of least-used asset names based on the threshold,
        sorted from lowest count to highest.
        """
        if not self.counts:
            return []

        threshold = self.get_threshold(method=method, ratio=0.55)

        if inclusive:
            filtered = [
                (asset, count)
                for asset, count in self.counts.items()
                if count <= threshold
            ]
        else:
            filtered = [
                (asset, count)
                for asset, count in self.counts.items()
                if count < threshold
            ]

        # Sort by usage count ascending, then alphabetically by asset name
        filtered.sort(key=lambda item: (item[1], item[0]))
        return [asset for asset, _ in filtered]

    def get_statistics(self) -> dict:
        """Return general occurrence statistics for pure usage analysis."""
        if not self.counts:
            return {
                "total_occurrences": 0,
                "unique_assets": 0,
                "min_count": 0,
                "max_count": 0,
                "midpoint": 0.0,
                "mean": 0.0,
                "median": 0.0,
                "counts": {},
            }

        values = list(self.counts.values())
        min_val, max_val = min(values), max(values)

        return {
            "total_occurrences": sum(values),
            "unique_assets": len(self.counts),
            "min_count": min_val,
            "max_count": max_val,
            "midpoint": (min_val + max_val) / 2,
            "mean": round(statistics.mean(values), 2),
            "median": statistics.median(values),
            "most_common": self.counts.most_common(5),
            "counts": dict(self.counts.most_common()),
        }


#analyzer = AssetUsageAnalyzer("LOG_SHADERS.txt", exclude=exclude_list)

# 1. Get general statistics
#stats = analyzer.get_statistics()
#print("Statistics:", stats)
# min_count: 1 (helmet_iron), max_count: 4 (sword_01), midpoint: 2.5

# 2. Get the least-used assets (using the min/max midpoint of 2.5)
#least_used = analyzer.get_least_used(method="midpoint", inclusive=True)
#print("Least used assets:", least_used)
#Output: ['helmet_iron', 'potion_health', 'shield_wood']

# 3. Direct access to raw counts if needed later
#print("Raw count for sword_01:", analyzer.counts["sword_01"])
